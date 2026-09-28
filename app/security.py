import bcrypt
from jose import jwt, JWTError

SESSION_COOKIE = "horizon_session"

import os

SECRET_KEY = os.getenv("SECRET_KEY", "horizon-portal-dev-secret-change-in-production")
ALGORITHM = "HS256"
TOKEN_MAX_AGE = 60 * 60 * 24 * 30
ACCESS_TOKEN_MAX_AGE = 60 * 15


def hash_password(password: str) -> str:
    password_bytes = password.encode("utf-8")

    if len(password_bytes) > 72:
        raise ValueError("Password must be 72 bytes or less")

    return bcrypt.hashpw(
        password_bytes,
        bcrypt.gensalt()
    ).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    password_bytes = password.encode("utf-8")

    if len(password_bytes) > 72:
        return False

    try:
        return bcrypt.checkpw(
            password_bytes,
            password_hash.encode("utf-8")
        )
    except (ValueError, TypeError):
        return False


def create_token(user_id: int) -> str:
    return jwt.encode(
        {"user_id": user_id},
        SECRET_KEY,
        algorithm=ALGORITHM
    )


def decode_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload.get("user_id")
    except JWTError:
        return None


def create_access_token(user_id: int, theme_entitlements: list[str]) -> str:
    import time
    return jwt.encode(
        {
            "user_id": user_id,
            "type": "launcher_access",
            "themes": theme_entitlements,
            "exp": int(time.time()) + ACCESS_TOKEN_MAX_AGE,
        },
        SECRET_KEY,
        algorithm=ALGORITHM,
    )


def decode_access_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("type") != "launcher_access":
            return None
        return payload
    except JWTError:
        return None