from fastapi import APIRouter, HTTPException
from ..database import SessionLocal
from ..crud import login_user, register_user, authenticate_user, theme_entitlements
from ..security import create_access_token

router = APIRouter()

@router.post("/login")
def login(payload: dict):
    db = SessionLocal()
    try:
        user = login_user(db, payload)
        if not user:
            raise HTTPException(status_code=401, detail="Invalid credentials")
        return user
    finally:
        db.close()

@router.post("/register")
def register(payload: dict):
    db = SessionLocal()
    try:
        return register_user(db, payload)
    finally:
        db.close()


@router.post("/token")
def token(payload: dict):
    identifier = payload.get("identifier") or payload.get("email") or payload.get("username") or ""
    password = payload.get("password", "")
    db = SessionLocal()
    try:
        user = authenticate_user(db, identifier, password)
        if not user:
            raise HTTPException(status_code=401, detail="Invalid credentials")
        themes = theme_entitlements(user)
        return {
            "access_token": create_access_token(user.id, themes),
            "token_type": "bearer",
            "expires_in": 900,
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "role": user.role,
            },
            "theme_entitlements": themes,
        }
    finally:
        db.close()