import base64
import hashlib
import json
import os
import secrets
import traceback
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timedelta

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import RedirectResponse
from sqlalchemy import or_

from ..database import SessionLocal
from ..models import User, OAuthTransaction, LauncherAuthCode, RedeemCode
from ..crud import theme_entitlements, _public_user
from ..security import create_access_token, decode_access_token, create_token, SESSION_COOKIE

router = APIRouter()
DISCORD_API = "https://discord.com/api/v10"
OAUTH_COOKIE = "horizon_oauth_nonce"


def _env(name: str, required: bool = False) -> str:
    value = os.getenv(name, "").strip()
    if required and not value:
        raise RuntimeError(f"Missing environment variable: {name}")
    return value


def _secure_cookie() -> bool:
    return bool(os.getenv("VERCEL") or os.getenv("HORIZON_ENV", "").lower() == "production")


def _discord_request(url: str, access_token: str | None = None, bot_token: str | None = None):
    headers = {"User-Agent": "Horizon-Portal/1.0"}
    if access_token:
        headers["Authorization"] = f"Bearer {access_token}"
    elif bot_token:
        headers["Authorization"] = f"Bot {bot_token}"
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=10) as response:
        return json.loads(response.read().decode("utf-8"))


def _exchange_code(code: str, redirect_uri: str, code_verifier: str):
    client_id = _env("DISCORD_CLIENT_ID", True)
    client_secret = _env("DISCORD_CLIENT_SECRET", True)
    body = urllib.parse.urlencode({
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": redirect_uri,
        "code_verifier": code_verifier,
    }).encode()
    request = urllib.request.Request(
        f"{DISCORD_API}/oauth2/token",
        data=body,
        headers={
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "application/json",
            "User-Agent": "Horizon-Portal/1.0",
        },
        method="POST",
    )
    auth = f"{client_id}:{client_secret}".encode()
    request.add_header("Authorization", "Basic " + base64.b64encode(auth).decode())
    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        raise HTTPException(status_code=502, detail="Discord authorization failed.") from exc


def _pkce_challenge(verifier: str) -> str:
    digest = hashlib.sha256(verifier.encode("ascii")).digest()
    return base64.urlsafe_b64encode(digest).rstrip(b"=").decode("ascii")


def _hash_value(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _new_launcher_code() -> str:
    return secrets.token_urlsafe(32)
@router.get("/discord/start")
def discord_start(request: Request, mode: str = "launcher", code_challenge: str = ""):
    if mode not in {"launcher", "web"}:
        raise HTTPException(status_code=400, detail="Invalid authentication mode.")
    if mode == "launcher" and not code_challenge:
        raise HTTPException(status_code=400, detail="Launcher PKCE challenge is required.")
    if code_challenge and len(code_challenge) > 128:
        raise HTTPException(status_code=400, detail="Invalid PKCE challenge.")

    client_id = _env("DISCORD_CLIENT_ID", True)
    redirect_uri = _env("DISCORD_REDIRECT_URI", True)
    state = secrets.token_urlsafe(32)
    browser_nonce = secrets.token_urlsafe(32)
    code_verifier = secrets.token_urlsafe(48)

    db = SessionLocal()
    try:
        db.query(OAuthTransaction).filter(
            OAuthTransaction.expires_at < datetime.utcnow()
        ).delete(synchronize_session=False)
        db.add(OAuthTransaction(
            state_hash=_hash_value(state),
            mode=mode,
            browser_nonce=browser_nonce,
            code_verifier=code_verifier,
            launcher_code_challenge=code_challenge or None,
            expires_at=datetime.utcnow() + timedelta(minutes=10),
        ))
        db.commit()
    finally:
        db.close()

    params = {
        "response_type": "code",
        "client_id": client_id,
        # The launcher only needs the Discord identity OAuth scope.
        # Guild membership/roles are verified server-side with the bot token.
        "scope": "identify",
        "redirect_uri": redirect_uri,
        "state": state,
        "code_challenge": _pkce_challenge(code_verifier),
        "code_challenge_method": "S256",
    }
    response = RedirectResponse(
        "https://discord.com/oauth2/authorize?" + urllib.parse.urlencode(params),
        status_code=302,
    )
    response.set_cookie(
        OAUTH_COOKIE,
        browser_nonce,
        max_age=600,
        httponly=True,
        samesite="lax",
        secure=_secure_cookie(),
        path="/api/auth/discord/callback",
    )
    return response


@router.get("/discord/callback")
def discord_callback(request: Request, code: str = "", state: str = ""):
    if not code or not state:
        raise HTTPException(status_code=400, detail="Invalid Discord authorization.")

    db = SessionLocal()
    try:
        transaction = db.query(OAuthTransaction).filter(
            OAuthTransaction.state_hash == _hash_value(state)
        ).first()
        if not transaction or transaction.used_at or transaction.expires_at < datetime.utcnow():
            raise HTTPException(status_code=400, detail="Expired or already used authorization.")
        if request.cookies.get(OAUTH_COOKIE) != transaction.browser_nonce:
            raise HTTPException(status_code=400, detail="Authorization must be completed in the same browser.")
        # Consume state before the external exchange so it cannot be replayed.
        transaction.used_at = datetime.utcnow()
        db.commit()
        mode = transaction.mode
        code_verifier = transaction.code_verifier
        launcher_code_challenge = transaction.launcher_code_challenge
    finally:
        db.close()

    redirect_uri = _env("DISCORD_REDIRECT_URI", True)
    try:
        token_data = _exchange_code(code, redirect_uri, code_verifier)
        discord_token = token_data["access_token"]
        discord_user = _discord_request(
            f"{DISCORD_API}/users/@me",
            access_token=discord_token,
        )
    except HTTPException:
        raise
    except Exception as exc:
        print("DISCORD OAUTH ERROR:", repr(exc))
        traceback.print_exc()
        raise HTTPException(status_code=502, detail="Unable to complete Discord authentication.") from exc

    # Keep the OAuth callback fast: Discord identity is established here,
    # while guild membership and roles are verified immediately by /launcher/me.
    # This avoids making the Discord authorization page wait on a second Discord
    # API request before it can hand the deep link back to Horizon Manager.
    discord_id = str(discord_user["id"])
    requested_username = (discord_user.get("global_name") or discord_user.get("username") or f"user-{discord_id}").strip()
    requested_username = requested_username[:240] or f"user-{discord_id}"
    email = f"discord-{discord_id}@horizon.local"

    db = SessionLocal()
    try:
        # Discord identity is keyed only by immutable Discord ID. Never attach a
        # Discord login to an existing account merely because names/emails match.
        user = db.query(User).filter(User.discord_id == discord_id).first()
        if not user:
            username = requested_username
            if db.query(User).filter(User.username == username).first():
                username = f"{requested_username}-{discord_id[-8:]}"
            if db.query(User).filter(User.email == email).first():
                email = f"discord-{discord_id}-{secrets.token_hex(4)}@horizon.local"

            user = User(
                email=email,
                username=username,
                password_hash=secrets.token_hex(48),
                role="user",
            )
            db.add(user)
            db.flush()

        user.discord_id = discord_id
        user.discord_username = str(discord_user.get("username", ""))[:255]

        # Do not grant or revoke entitlements in the OAuth callback.
        # /launcher/me performs the authoritative guild/role refresh.
        if user.donation_cents is None:
            user.donation_cents = 0
        if user.creator_badge is None:
            user.creator_badge = 0
        if user.beta_access is None:
            user.beta_access = 0

        db.commit()
        db.refresh(user)

        if mode == "web":
            guild_id = _env("DISCORD_GUILD_ID", True)
            bot_token = _env("DISCORD_BOT_TOKEN", True)
            role_ids = {
                "donator": "1554117251458801754",
                "corrupted_donator": "1554117420589908078",
                "aria_donator": "1554117573862498454",
                "creator": "1554117678996922488",
                "beta": "1554117795334197278",
            }
            try:
                member = _discord_request(
                    f"{DISCORD_API}/guilds/{guild_id}/members/{discord_id}",
                    bot_token=bot_token,
                )
                roles = {str(role) for role in member.get("roles", [])}
            except Exception as exc:
                raise HTTPException(status_code=403, detail="Unable to verify Discord server membership and roles.") from exc

            user.donation_cents = (
                1000 if role_ids["aria_donator"] in roles
                else 500 if role_ids["corrupted_donator"] in roles
                else 100 if role_ids["donator"] in roles
                else 0
            )
            user.creator_badge = 1 if role_ids["creator"] in roles else 0
            user.beta_access = 1 if role_ids["beta"] in roles else int(user.beta_access or 0)
            db.commit()
            db.refresh(user)

        if mode == "web":
            response = RedirectResponse("/account", status_code=303)
            response.set_cookie(
                SESSION_COOKIE,
                create_token(user.auth_id, user.auth_version),
                max_age=7 * 24 * 3600,
                httponly=True,
                samesite="lax",
                secure=_secure_cookie(),
                path="/",
            )
            return response

        if not launcher_code_challenge:
            raise HTTPException(status_code=400, detail="Launcher PKCE challenge is required.")

        code_value = _new_launcher_code()
        db.add(LauncherAuthCode(
            code_hash=_hash_value(code_value),
            auth_id=user.auth_id,
            auth_version=user.auth_version,
            code_challenge=launcher_code_challenge,
            expires_at=datetime.utcnow() + timedelta(minutes=2),
        ))
        db.commit()

        response = RedirectResponse(
            "horizon://auth?" + urllib.parse.urlencode({"code": code_value}),
            status_code=302,
        )
        response.delete_cookie(OAUTH_COOKIE, path="/api/auth/discord/callback")
        return response
    finally:
        db.close()
@router.post("/launcher/exchange")
def launcher_exchange(payload: dict):
    code = str(payload.get("code", "")).strip()
    code_verifier = str(payload.get("code_verifier", "")).strip()
    if not code or not code_verifier:
        raise HTTPException(status_code=400, detail="Authorization code and verifier are required.")
    if len(code_verifier) > 128:
        raise HTTPException(status_code=400, detail="Invalid verifier.")

    db = SessionLocal()
    try:
        item = db.query(LauncherAuthCode).filter(
            LauncherAuthCode.code_hash == _hash_value(code)
        ).with_for_update().first()
        if not item or item.used_at or item.expires_at < datetime.utcnow():
            raise HTTPException(status_code=401, detail="Authorization code expired or already used.")
        if _pkce_challenge(code_verifier) != item.code_challenge:
            raise HTTPException(status_code=401, detail="Invalid authorization verifier.")

        user = db.query(User).filter(User.auth_id == item.auth_id).first()
        if not user or int(user.auth_version or 1) != int(item.auth_version):
            raise HTTPException(status_code=401, detail="Account session is no longer valid.")

        item.used_at = datetime.utcnow()
        db.commit()
        access_token = create_access_token(
            user.auth_id,
            user.auth_version,
            theme_entitlements(user),
        )
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "expires_in": 900,
            "user": _public_user(user),
        }
    finally:
        db.close()


@router.get("/launcher/me")
def launcher_me(request: Request):
    authorization = request.headers.get("Authorization", "")
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Launcher authentication required.")

    payload = decode_access_token(authorization[7:].strip())
    if not payload:
        raise HTTPException(status_code=401, detail="Launcher session expired.")

    db = SessionLocal()
    try:
        user = db.query(User).filter(User.auth_id == payload["auth_id"]).first()
        if not user or int(user.auth_version or 1) != int(payload["auth_version"]):
            raise HTTPException(status_code=401, detail="Horizon account session is no longer valid.")

        guild_id = _env("DISCORD_GUILD_ID", True)
        bot_token = _env("DISCORD_BOT_TOKEN", True)
        if not user.discord_id:
            raise HTTPException(status_code=403, detail="Discord account is not linked.")

        try:
            member = _discord_request(
                f"{DISCORD_API}/guilds/{guild_id}/members/{user.discord_id}",
                bot_token=bot_token,
            )
        except Exception as exc:
            raise HTTPException(status_code=403, detail="Unable to verify Discord server membership and roles.") from exc

        roles = {str(role) for role in member.get("roles", [])}
        role_ids = {
            "donator": "1554117251458801754",
            "corrupted_donator": "1554117420589908078",
            "aria_donator": "1554117573862498454",
            "creator": "1554117678996922488",
            "beta": "1554117795334197278",
        }
        new_donation_cents = (
            1000 if role_ids["aria_donator"] in roles
            else 500 if role_ids["corrupted_donator"] in roles
            else 100 if role_ids["donator"] in roles
            else 0
        )
        new_creator_badge = 1 if role_ids["creator"] in roles else 0
        new_beta_access = 1 if role_ids["beta"] in roles else int(user.beta_access or 0)
        entitlements_changed = (
            int(getattr(user, "donation_cents", 0) or 0) != new_donation_cents
            or int(getattr(user, "creator_badge", 0) or 0) != new_creator_badge
            or int(getattr(user, "beta_access", 0) or 0) != new_beta_access
        )
        user.donation_cents = new_donation_cents
        user.creator_badge = new_creator_badge
        user.beta_access = new_beta_access
        if entitlements_changed:
            user.auth_version = int(user.auth_version or 1) + 1
        db.commit()
        db.refresh(user)

        response = {"authenticated": True, **_public_user(user)}
        if entitlements_changed:
            response["access_token"] = create_access_token(
                user.auth_id,
                user.auth_version,
                theme_entitlements(user),
            )
            response["expires_in"] = 900
        return response
    finally:
        db.close()


@router.post("/launcher/redeem")
def launcher_redeem(request: Request, payload: dict):
    authorization = request.headers.get("Authorization", "")
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Launcher authentication required.")

    token_payload = decode_access_token(authorization[7:].strip())
    if not token_payload:
        raise HTTPException(status_code=401, detail="Launcher session expired.")

    code = str(payload.get("code", "")).strip().upper()
    if not code:
        raise HTTPException(status_code=400, detail="Redeem code is required.")

    code_hash = hashlib.sha256(code.encode("utf-8")).hexdigest()

    db = SessionLocal()
    try:
        user = db.query(User).filter(User.auth_id == token_payload["auth_id"]).first()
        if not user or int(user.auth_version or 1) != int(token_payload["auth_version"]):
            raise HTTPException(status_code=401, detail="Launcher session expired.")

        item = (
            db.query(RedeemCode)
            .filter(RedeemCode.code_hash == code_hash)
            .with_for_update()
            .first()
        )
        if not item:
            raise HTTPException(status_code=404, detail="Invalid redeem code.")
        if item.redeemed_by_auth_id:
            if item.redeemed_by_auth_id == user.auth_id:
                raise HTTPException(status_code=409, detail="This code has already been redeemed on this account.")
            raise HTTPException(status_code=409, detail="This redeem code has already been used.")

        if item.entitlement == "beta":
            user.beta_access = 1
            user.auth_version = int(user.auth_version or 1) + 1
        else:
            raise HTTPException(status_code=400, detail="Unsupported redeem entitlement.")

        item.redeemed_by_auth_id = user.auth_id
        item.redeemed_at = datetime.utcnow()
        db.commit()
        db.refresh(user)

        return {
            "success": True,
            "message": "BETA theme unlocked.",
            "entitlement": item.entitlement,
            "theme_entitlements": theme_entitlements(user),
            "access_token": create_access_token(
                user.auth_id,
                user.auth_version,
                theme_entitlements(user),
            ),
            **_public_user(user),
        }
    finally:
        db.close()


@router.post("/launcher/logout")
def launcher_logout(request: Request):
    authorization = request.headers.get("Authorization", "")
    if not authorization.startswith("Bearer "):
        return {"authenticated": False}

    payload = decode_access_token(authorization[7:].strip())
    if not payload:
        return {"authenticated": False}

    db = SessionLocal()
    try:
        user = db.query(User).filter(User.auth_id == payload["auth_id"]).first()
        if user and int(user.auth_version or 1) == int(payload["auth_version"]):
            user.auth_version = int(user.auth_version or 1) + 1
            db.commit()
        return {"authenticated": False}
    finally:
        db.close()
