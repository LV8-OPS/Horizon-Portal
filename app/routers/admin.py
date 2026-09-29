from fastapi import APIRouter, HTTPException, Request
from ..database import SessionLocal
from ..crud import (
    list_users, delete_user, list_downloads, delete_download,
    update_entitlements, get_user_by_auth_id,
)
from ..security import SESSION_COOKIE, decode_token

router = APIRouter()


def _admin_user(db, request: Request):
    token = request.cookies.get(SESSION_COOKIE)
    if not token:
        return None
    payload = decode_token(token)
    if not payload:
        return None
    user = get_user_by_auth_id(db, payload["auth_id"])
    if not user or user.role != "admin":
        return None
    if int(user.auth_version or 1) != int(payload["auth_version"]):
        return None
    return user


def _require_admin(db, request: Request):
    user = _admin_user(db, request)
    if not user:
        raise HTTPException(status_code=403, detail="Admin access required")
    return user
@router.get("/users")
def users(request: Request):
    db = SessionLocal()
    try:
        _require_admin(db, request)
        return list_users(db)
    finally:
        db.close()


@router.delete("/users/{user_id}")
def remove_user(user_id: int, request: Request):
    db = SessionLocal()
    try:
        admin = _require_admin(db, request)
        target = db.query(type(admin)).filter(type(admin).id == user_id).first()
        if not target:
            raise HTTPException(status_code=404, detail="User not found")
        if target.id == admin.id:
            raise HTTPException(status_code=400, detail="You cannot delete the active admin account.")
        if target.role == "admin" and db.query(type(admin)).filter(type(admin).role == "admin").count() <= 1:
            raise HTTPException(status_code=400, detail="The last admin account cannot be deleted.")
        ok = delete_user(db, user_id)
        if not ok:
            raise HTTPException(status_code=404, detail="User not found")
        return {"ok": True}
    finally:
        db.close()


@router.get("/downloads")
def admin_downloads(request: Request):
    db = SessionLocal()
    try:
        _require_admin(db, request)
        return list_downloads(db)
    finally:
        db.close()


@router.delete("/downloads/{download_id}")
def remove_download(download_id: int, request: Request):
    db = SessionLocal()
    try:
        _require_admin(db, request)
        ok = delete_download(db, download_id)
        if not ok:
            raise HTTPException(status_code=404, detail="Download not found")
        return {"ok": True}
    finally:
        db.close()
@router.patch("/users/{user_id}/entitlements")
def set_entitlements(user_id: int, payload: dict, request: Request):
    db = SessionLocal()
    try:
        _require_admin(db, request)
        donation_eur = payload.get("donation_eur")
        try:
            donation_cents = None if donation_eur is None else max(0, round(float(donation_eur) * 100))
        except (TypeError, ValueError):
            raise HTTPException(status_code=422, detail="Invalid donation amount")
        result = update_entitlements(
            db,
            user_id,
            donation_cents=donation_cents,
            creator_badge=payload.get("creator_badge"),
            beta_access=payload.get("beta_access"),
        )
        if not result:
            raise HTTPException(status_code=404, detail="User not found")
        return result
    finally:
        db.close()
