import hashlib
import re
from datetime import datetime
from fastapi import APIRouter, HTTPException

from ..database import SessionLocal
from ..models import RedeemCode, ModUploadRequest

router = APIRouter()
CODE_RE = re.compile(r"^HZN-CODE-[A-F0-9]{8}$")


def _hash(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _state(db, device_id: str) -> dict:
    rows = db.query(RedeemCode).filter(
        RedeemCode.redeemed_by_device_id == device_id
    ).all()
    entitlements = {row.entitlement for row in rows}
    return {
        "authenticated": True,
        "username": "Guest",
        "beta_access": "beta" in entitlements,
        "creator_badge": "creator" in entitlements,
        "entitlements": sorted(entitlements),
    }


@router.post("/redeem")
def redeem(payload: dict):
    code = str(payload.get("code", "")).strip().upper()
    device_id = str(payload.get("device_id", "")).strip()
    if not CODE_RE.fullmatch(code):
        raise HTTPException(status_code=400, detail="Invalid code format. Use HZN-CODE-XXXXXXXX.")
    if not device_id or len(device_id) > 64:
        raise HTTPException(status_code=400, detail="A local account identifier is required.")

    db = SessionLocal()
    try:
        item = db.query(RedeemCode).filter(
            RedeemCode.code_hash == _hash(code)
        ).with_for_update().first()
        if not item:
            raise HTTPException(status_code=404, detail="Invalid redeem code.")
        if item.redeemed_by_device_id:
            if item.redeemed_by_device_id == device_id:
                raise HTTPException(status_code=409, detail="This code is already redeemed on this account.")
            raise HTTPException(status_code=409, detail="This redeem code has already been used.")
        item.redeemed_by_device_id = device_id
        item.redeemed_at = datetime.utcnow()
        db.commit()
        state = _state(db, device_id)
        message = "Creator access unlocked." if item.entitlement == "creator" else "BETA access unlocked."
        return {"success": True, "message": message, "entitlement": item.entitlement, **state}
    finally:
        db.close()


@router.get("/state")
def state(device_id: str):
    device_id = str(device_id or "").strip()
    if not device_id or len(device_id) > 64:
        raise HTTPException(status_code=400, detail="A local account identifier is required.")
    db = SessionLocal()
    try:
        return _state(db, device_id)
    finally:
        db.close()


@router.post("/mod-request")
def mod_request(payload: dict):
    device_id = str(payload.get("device_id", "")).strip()
    title = str(payload.get("title", "")).strip()
    game = str(payload.get("game", "")).strip().lower()
    description = str(payload.get("description", "")).strip()
    file_name = str(payload.get("file_name", "")).strip()
    file_size = int(payload.get("file_size", 0) or 0)

    if not device_id or not title or game not in {"destiny2", "dawn", "sunrise", "sundial"}:
        raise HTTPException(status_code=400, detail="Creator request data is incomplete.")
    if len(title) > 255 or len(description) > 5000 or len(file_name) > 255:
        raise HTTPException(status_code=400, detail="One or more fields are too long.")
    if file_size < 0 or file_size > 2 * 1024 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="Invalid file size.")

    db = SessionLocal()
    try:
        creator = db.query(RedeemCode).filter(
            RedeemCode.redeemed_by_device_id == device_id,
            RedeemCode.entitlement == "creator",
        ).first()
        if not creator:
            raise HTTPException(status_code=403, detail="Creator access is required.")

        item = ModUploadRequest(
            device_id=device_id,
            title=title,
            game=game,
            description=description,
            file_name=file_name,
            file_size=file_size,
            status="pending",
        )
        db.add(item)
        db.commit()
        db.refresh(item)
        return {"success": True, "request_id": item.id, "status": item.status}
    finally:
        db.close()
