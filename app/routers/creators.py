from fastapi import APIRouter, HTTPException
from ..database import SessionLocal
from ..crud import list_creators, get_creator_by_slug

router = APIRouter()

@router.get("/")
def creators():
    db = SessionLocal()
    try:
        return list_creators(db)
    finally:
        db.close()

@router.get("/{slug}")
def creator(slug: str):
    db = SessionLocal()
    try:
        item = get_creator_by_slug(db, slug)
        if not item:
            raise HTTPException(status_code=404, detail="Not found")
        return item
    finally:
        db.close()