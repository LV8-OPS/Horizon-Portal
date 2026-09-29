import os
import secrets
import bcrypt
import uuid
from jose import jwt, JWTError

SESSION_COOKIE = "horizon_session"
ALGORITHM = "HS256"
WEB_TOKEN_MAX_AGE = 60 * 60 * 24 * 7
ACCESS_TOKEN_MAX_AGE = 60 * 15

_configured_secret = os.getenv("SECRET_KEY", "").strip()
if not _configured_secret:
    if os.getenv("VERCEL") or os.getenv("HORIZON_ENV", "").lower() == "production":
        raise RuntimeError("SECRET_KEY must be configured in production.")
    # Never use a public, predictable development key.
    _configured_secret = secrets.token_urlsafe(48)

SECRET_KEY = _configured_secret


def hash_password(password: str) -> str:
    password_bytes = password.encode("utf-8")
    if len(password_bytes) > 72:
        raise ValueError("Password must be 72 bytes or less")
    return bcrypt.hashpw(password_bytes, bcrypt.gensalt()).decode("utf-8")
def verify_password(password: str, password_hash: str) -> bool:
    password_bytes = password.encode("utf-8")
    if len(password_bytes) > 72:
        return False
    try:
        return bcrypt.checkpw(password_bytes, password_hash.encode("utf-8"))
    except (ValueError, TypeError):
        return False


def _base_claims(auth_id: str, auth_version: int, token_type: str, max_age: int) -> dict:
    import time
    now = int(time.time())
    return {
        "sub": auth_id,
        "auth_id": auth_id,
        "auth_version": int(auth_version),
        "type": token_type,
        "jti": str(uuid.uuid4()),
        "iat": now,
        "exp": now + max_age,
    }


def create_token(auth_id: str, auth_version: int) -> str:
    return jwt.encode(
        _base_claims(auth_id, auth_version, "web_session", WEB_TOKEN_MAX_AGE),
        SECRET_KEY,
        algorithm=ALGORITHM,
    )


def decode_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("type") != "web_session":
            return None
        if not payload.get("auth_id") or not payload.get("auth_version"):
            return None
        return payload
    except JWTError:
        return None
def create_access_token(auth_id: str, auth_version: int, theme_entitlements: list[str]) -> str:
    claims = _base_claims(auth_id, auth_version, "launcher_access", ACCESS_TOKEN_MAX_AGE)
    claims["themes"] = list(theme_entitlements)
    return jwt.encode(claims, SECRET_KEY, algorithm=ALGORITHM)


def decode_access_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("type") != "launcher_access":
            return None
        if not payload.get("auth_id") or not payload.get("auth_version"):
            return None
        return payload
    except JWTError:
        return None
