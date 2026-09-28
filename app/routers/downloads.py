from fastapi import APIRouter, HTTPException
from ..database import SessionLocal
from ..crud import list_downloads, get_download_by_slug

router = APIRouter()

@router.get("/")
def downloads():
    db = SessionLocal()
    try:
        return list_downloads(db)
    finally:
        db.close()

@router.get("/{slug}")
def download(slug: str):
    db = SessionLocal()
    try:
        item = get_download_by_slug(db, slug)
        if not item:
            raise HTTPException(status_code=404, detail="Not found")
        return item
    finally:
        db.close()