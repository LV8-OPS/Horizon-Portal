from fastapi import APIRouter, HTTPException, Request
from ..database import SessionLocal
from ..crud import list_users, delete_user, list_downloads, delete_download, update_entitlements, get_user
from ..security import SESSION_COOKIE, decode_token

router = APIRouter()


def _admin_user(db, request: Request):
    token = request.cookies.get(SESSION_COOKIE)
    if not token:
        return None
    user_id = decode_token(token)
    user = get_user(db, user_id) if user_id else None
    return user if user and user.role == "admin" else None


@router.get("/users")
def users():
    db = SessionLocal()
    try:
        return list_users(db)
    finally:
        db.close()

@router.delete("/users/{user_id}")
def remove_user(user_id: int):
    db = SessionLocal()
    try:
        ok = delete_user(db, user_id)
        if not ok:
            raise HTTPException(status_code=404, detail="User not found")
        return {"ok": True}
    finally:
        db.close()

@router.get("/downloads")
def admin_downloads():
    db = SessionLocal()
    try:
        return list_downloads(db)
    finally:
        db.close()

@router.delete("/downloads/{download_id}")
def remove_download(download_id: int):
    db = SessionLocal()
    try:
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
        if not _admin_user(db, request):
            raise HTTPException(status_code=403, detail="Admin access required")
        donation_eur = payload.get("donation_eur")
        donation_cents = None if donation_eur is None else max(0, round(float(donation_eur) * 100))
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