from fastapi import APIRouter, HTTPException, Request
from ..database import SessionLocal
from ..crud import list_themes, get_theme_by_slug, theme_access, theme_entitlements, get_user
from ..security import SESSION_COOKIE, decode_token, decode_access_token

router = APIRouter()

def _current_user(db, request: Request):
    token = request.cookies.get(SESSION_COOKIE)
    if token:
        user_id = decode_token(token)
        if user_id:
            return get_user(db, user_id)

    authorization = request.headers.get("Authorization", "")
    if authorization.lower().startswith("bearer "):
        payload = decode_access_token(authorization[7:].strip())
        if payload:
            return get_user(db, payload.get("user_id"))
    return None


@router.get("/")
def themes(request: Request):
    db = SessionLocal()
    try:
        user = _current_user(db, request)
        items = list_themes(db)
        allowed = set(theme_entitlements(user))
        for item in items:
            item["unlocked"] = item["slug"] in allowed
        return items
    finally:
        db.close()


@router.get("/{slug}")
def theme(slug: str, request: Request):
    db = SessionLocal()
    try:
        item = get_theme_by_slug(db, slug)
        if not item:
            raise HTTPException(status_code=404, detail="Not found")
        user = _current_user(db, request)
        if not theme_access(user, slug):
            raise HTTPException(status_code=403, detail="Theme access denied")
        return {**item, "unlocked": True}
    finally:
        db.close()