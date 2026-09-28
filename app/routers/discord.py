import os
import secrets
import urllib.parse
import urllib.request
import urllib.error
import json
import traceback
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import RedirectResponse
from sqlalchemy import or_

from ..database import SessionLocal
from ..models import User
from ..crud import theme_entitlements, _public_user
from ..security import create_access_token, decode_access_token, create_token, SESSION_COOKIE

router = APIRouter()

DISCORD_API = "https://discord.com/api/v10"


def _env(name: str, required: bool = False) -> str:
    value = os.getenv(name, "").strip()
    if required and not value:
        raise RuntimeError(f"Missing environment variable: {name}")
    return value


def _discord_request(url: str, access_token: str | None = None, bot_token: str | None = None):
    headers = {"User-Agent": "Horizon-Portal/1.0"}
    if access_token:
        headers["Authorization"] = f"Bearer {access_token}"
    elif bot_token:
        headers["Authorization"] = f"Bot {bot_token}"
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=10) as response:
        return json.loads(response.read().decode("utf-8"))


def _exchange_code(code: str, redirect_uri: str):
    client_id = _env("DISCORD_CLIENT_ID", True)
    client_secret = _env("DISCORD_CLIENT_SECRET", True)
    body = urllib.parse.urlencode({
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": redirect_uri,
    }).encode()
    request = urllib.request.Request(
        f"{DISCORD_API}/oauth2/token",
        data=body,
        headers={
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "application/json",
            "User-Agent": "Horizon-Portal (https://horizon-portal-lv-8-e7ea.vercel.app, 1.0)",
        },
        method="POST",
    )
    auth = f"{client_id}:{client_secret}".encode()
    import base64
    request.add_header("Authorization", "Basic " + base64.b64encode(auth).decode())

    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        error_body = exc.read().decode("utf-8", errors="replace")
        print("DISCORD OAUTH TOKEN ERROR")
        print("HTTP STATUS:", exc.code)
        print("RESPONSE:", error_body)
        raise
    except Exception as exc:
        print("DISCORD OAUTH TOKEN REQUEST ERROR:", repr(exc))
        traceback.print_exc()
        raise


def _state_token(mode: str) -> str:
    from jose import jwt
    import time
    secret = _env("SECRET_KEY", True)
    return jwt.encode(
        {
            "type": "discord_oauth_state",
            "mode": mode,
            "nonce": secrets.token_urlsafe(24),
            "exp": int(time.time()) + 600,
        },
        secret,
        algorithm="HS256",
    )


def _validate_state(state: str):
    from jose import jwt, JWTError
    try:
        payload = jwt.decode(state, _env("SECRET_KEY", True), algorithms=["HS256"])
        if payload.get("type") != "discord_oauth_state":
            return None
        return payload
    except JWTError:
        return None


def _launcher_redirect(access_token: str) -> str:
    return "horizon://auth?" + urllib.parse.urlencode({"access_token": access_token})


@router.get("/discord/start")
def discord_start(mode: str = "launcher"):
    if mode not in {"launcher", "web"}:
        mode = "launcher"
    client_id = _env("DISCORD_CLIENT_ID", True)
    redirect_uri = _env("DISCORD_REDIRECT_URI", True)
    scopes = "identify guilds"
    params = {
        "response_type": "code",
        "client_id": client_id,
        "scope": scopes,
        "redirect_uri": redirect_uri,
        "state": _state_token(mode),
    }
    return RedirectResponse(
        "https://discord.com/oauth2/authorize?" + urllib.parse.urlencode(params),
        status_code=302,
    )


@router.get("/discord/callback")
def discord_callback(code: str = "", state: str = ""):
    state_payload = _validate_state(state)
    if not code or not state_payload:
        raise HTTPException(status_code=400, detail="Invalid Discord authorization.")

    redirect_uri = _env("DISCORD_REDIRECT_URI", True)

    try:
        token_data = _exchange_code(code, redirect_uri)
        discord_token = token_data["access_token"]
    except urllib.error.HTTPError as exc:
        error_body = exc.read().decode("utf-8", errors="replace")
        print("DISCORD OAUTH CALLBACK HTTP ERROR:", exc.code, error_body)
        raise HTTPException(
            status_code=502,
            detail=f"Discord token exchange failed ({exc.code}): {error_body[:500]}",
        ) from exc
    except Exception as exc:
        print("DISCORD OAUTH CALLBACK ERROR:", repr(exc))
        traceback.print_exc()
        raise HTTPException(
            status_code=502,
            detail=f"Discord OAuth error: {type(exc).__name__}: {str(exc)[:300]}",
        ) from exc

    try:
        discord_user = _discord_request(
            f"{DISCORD_API}/users/@me",
            access_token=discord_token,
        )
    except Exception as exc:
        print("DISCORD USER API ERROR:", repr(exc))
        traceback.print_exc()
        raise HTTPException(status_code=502, detail="Discord user lookup failed.") from exc

    guild_id = _env("DISCORD_GUILD_ID", True)
    bot_token = _env("DISCORD_BOT_TOKEN")
    role_ids = {
        "donator": "1554117251458801754",
        "corrupted_donator": "1554117420589908078",
        "aria_donator": "1554117573862498454",
        "creator": "1554117678996922488",
        "beta": "1554117795334197278",
    }
    role_names = {
        "beta": "BETA",
        "creator": "Creator",
        "donator": "Donator",
        "corrupted_donator": "Corrupted Donator",
        "aria_donator": "Aria Donator",
    }

    roles = set()
    role_name_set = set()
    if guild_id and bot_token:
        try:
            member = _discord_request(
                f"{DISCORD_API}/guilds/{guild_id}/members/{discord_user['id']}",
                bot_token=bot_token,
            )
            roles = set(member.get("roles", []))
            guild_roles = _discord_request(
                f"{DISCORD_API}/guilds/{guild_id}/roles",
                bot_token=bot_token,
            )
            role_names_by_id = {
                str(role.get("id")): str(role.get("name", "")).strip()
                for role in guild_roles
            }
            role_name_set = {
                role_names_by_id[role_id]
                for role_id in roles
                if role_id in role_names_by_id
            }
        except Exception as exc:
            print("DISCORD ROLE VERIFICATION ERROR:", repr(exc))
            traceback.print_exc()
            raise HTTPException(status_code=403, detail="Unable to verify Discord server roles.") from exc
    elif guild_id:
        try:
            guilds = _discord_request(f"{DISCORD_API}/users/@me/guilds", access_token=discord_token)
            if not any(str(g.get("id")) == guild_id for g in guilds):
                raise HTTPException(status_code=403, detail="Your Discord account is not a member of the Horizon server.")
        except HTTPException:
            raise
        except Exception as exc:
            print("DISCORD GUILD MEMBERSHIP ERROR:", repr(exc))
            traceback.print_exc()
            raise HTTPException(status_code=502, detail="Unable to verify Discord server membership.") from exc

    username = discord_user.get("global_name") or discord_user.get("username") or f"user-{discord_user['id']}"
    username = username.strip()[:240] or f"user-{discord_user['id']}"
    email = f"discord-{discord_user['id']}@horizon.local"

    db = SessionLocal()
    try:
        user = db.query(User).filter(User.discord_id == str(discord_user["id"])).first()
        if not user:
            existing = db.query(User).filter(or_(User.email == email, User.username == username)).first()
            if existing and existing.role == "admin":
                username = f"{username}-{discord_user['id'][-6:]}"
                existing = None
            if existing:
                user = existing
            else:
                user = User(
                    email=email,
                    username=username,
                    password_hash=secrets.token_hex(32),
                    role="user",
                )
                db.add(user)

        user.discord_id = str(discord_user["id"])
        user.discord_username = discord_user.get("username", "")

        # Discord roles are the source of truth. Recompute entitlements on
        # every login so a removed role also removes its Horizon access.
        if guild_id and bot_token:
            has_donator = role_ids["donator"] in roles
            has_corrupted = role_ids["corrupted_donator"] in roles
            has_aria = role_ids["aria_donator"] in roles

            if has_aria:
                user.donation_cents = 1000
            elif has_corrupted:
                user.donation_cents = 500
            elif has_donator:
                user.donation_cents = 100
            else:
                user.donation_cents = 0

            user.creator_badge = 1 if role_ids["creator"] in roles else 0
            user.beta_access = 1 if role_ids["beta"] in roles else 0

        db.commit()
        db.refresh(user)

        access_token = create_access_token(user.id, theme_entitlements(user))
        if state_payload.get("mode") == "web":
            response = RedirectResponse("/account", status_code=303)
            response.set_cookie(
                SESSION_COOKIE,
                create_token(user.id),
                max_age=60 * 60 * 24 * 30,
                httponly=True,
                samesite="lax",
                secure=True,
            )
            return response
        return RedirectResponse(_launcher_redirect(access_token), status_code=302)
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
        user = db.query(User).filter(User.id == int(payload["user_id"])).first()
        if not user:
            raise HTTPException(status_code=401, detail="Horizon account not found.")
        return {"authenticated": True, **_public_user(user)}
    finally:
        db.close()
    