from sqlalchemy import or_

from .models import Creator, Download, Theme, User
from .security import hash_password, verify_password


def seed(db):
    if not db.query(Creator).first():
        db.add_all([
            Creator(slug="dawn", name="Dawn", description="Dawn creator pack"),
            Creator(slug="sunrise", name="SunRise", description="SunRise creator pack"),
        ])
    if not db.query(Download).first():
        db.add(Download(slug="core-pack", title="Core Pack", description="Main download pack", version="1.0.0"))
    theme_seed = [
        ("destiny2", "Destiny 2", "Default Horizon theme.", "free"),
        ("destiny1", "Destiny 1", "Destiny 1 art direction.", "free"),
        ("hive", "Hive", "Free Horizon theme.", "free"),
        ("cabal", "Cabal", "Free Horizon theme.", "free"),
        ("fallen", "Fallen", "Free Horizon theme.", "free"),
        ("corrupted", "Corrupted", "Free Horizon theme.", "free"),
        ("aria", "Aria", "Free Horizon theme.", "free"),
        ("vex", "Vex", "Creator badge only.", "creator"),
        ("beta", "BETA", "Beta players only.", "beta"),
    ]
    db.query(Theme).filter(Theme.slug == "legacy").delete(synchronize_session=False)
    for slug, title, description, unlock_type in theme_seed:
        if not db.query(Theme).filter(Theme.slug == slug).first():
            db.add(Theme(slug=slug, title=title, description=description, unlock_type=unlock_type))
    import os
    admin_password = os.getenv("HORIZON_ADMIN_PASSWORD", "").strip()
    if admin_password and not db.query(User).filter(User.username == "admin").first():
        db.add(User(
            email="admin@horizon.local",
            username="admin",
            password_hash=hash_password(admin_password),
            role="admin",
        ))
    db.commit()


THEME_ACCESS = {
    "destiny2": {"kind": "free", "min_donation": 0},
    "destiny1": {"kind": "free", "min_donation": 0},
    "hive": {"kind": "free", "min_donation": 0},
    "cabal": {"kind": "free", "min_donation": 0},
    "fallen": {"kind": "free", "min_donation": 0},
    "corrupted": {"kind": "free", "min_donation": 0},
    "aria": {"kind": "free", "min_donation": 0},
    "vex": {"kind": "creator"},
    "beta": {"kind": "beta"},
}


def theme_entitlements(user: User | None) -> list[str]:
    access = ["destiny2", "destiny1", "hive", "cabal", "fallen", "corrupted", "aria"]
    if user and bool(getattr(user, "creator_badge", 0)):
        access.append("vex")
    if user and bool(getattr(user, "beta_access", 0)):
        access.append("beta")
    return access

def theme_access(user: User | None, slug: str) -> bool:
    return slug in theme_entitlements(user)


def _public_user(user: User) -> dict:
    return {
        "id": user.id,
        "email": user.email,
        "username": user.username,
        "role": user.role,
        "donation_cents": int(getattr(user, "donation_cents", 0) or 0),
        "creator_badge": bool(getattr(user, "creator_badge", 0)),
        "beta_access": bool(getattr(user, "beta_access", 0)),
        "theme_entitlements": theme_entitlements(user),
    }


def register_user(db, payload: dict):
    email = payload.get("email", "").strip().lower()
    username = payload.get("username", "").strip()
    password = payload.get("password", "")

    if not email or not username or not password:
        return None

    existing = db.query(User).filter(or_(User.email == email, User.username == username)).first()
    if existing:
        return None

    user = User(
        email=email,
        username=username,
        password_hash=hash_password(password),
        role="user",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return _public_user(user)


def authenticate_user(db, identifier: str, password: str):
    identifier = identifier.strip()
    user = db.query(User).filter(
        or_(User.email == identifier.lower(), User.username == identifier)
    ).first()
    if not user or not verify_password(password, user.password_hash):
        return None
    return user


def login_user(db, payload: dict):
    identifier = payload.get("identifier") or payload.get("email") or payload.get("username") or ""
    password = payload.get("password", "")
    user = authenticate_user(db, identifier, password)
    return _public_user(user) if user else None


def get_user(db, user_id: int):
    return db.query(User).filter(User.id == user_id).first()


def _creator(item):
    return {"id": item.id, "slug": item.slug, "name": item.name, "description": item.description, "image_url": item.image_url, "download_url": item.download_url}


def _download(item):
    return {"id": item.id, "slug": item.slug, "title": item.title, "description": item.description, "file_url": item.file_url, "version": item.version}


def _theme(item):
    return {"id": item.id, "slug": item.slug, "title": item.title, "description": item.description, "preview_url": item.preview_url, "unlock_type": item.unlock_type}


def _user(item):
    return _public_user(item)


def list_creators(db): return [_creator(x) for x in db.query(Creator).order_by(Creator.id.asc()).all()]
def get_creator_by_slug(db, slug: str):
    item = db.query(Creator).filter(Creator.slug == slug).first()
    return _creator(item) if item else None


def list_downloads(db): return [_download(x) for x in db.query(Download).order_by(Download.id.asc()).all()]
def get_download_by_slug(db, slug: str):
    item = db.query(Download).filter(Download.slug == slug).first()
    return _download(item) if item else None


def list_themes(db): return [_theme(x) for x in db.query(Theme).order_by(Theme.id.asc()).all()]
def get_theme_by_slug(db, slug: str):
    item = db.query(Theme).filter(Theme.slug == slug).first()
    return _theme(item) if item else None


def list_users(db): return [_user(x) for x in db.query(User).order_by(User.id.asc()).all()]


def delete_user(db, user_id: int):
    user = db.query(User).filter(User.id == user_id).first()
    if not user: return False
    db.delete(user); db.commit(); return True


def delete_download(db, download_id: int):
    item = db.query(Download).filter(Download.id == download_id).first()
    if not item: return False
    db.delete(item); db.commit(); return True


def update_entitlements(db, user_id: int, donation_cents: int | None = None, creator_badge: bool | None = None, beta_access: bool | None = None):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return None
    if donation_cents is not None:
        user.donation_cents = max(0, int(donation_cents))
    if creator_badge is not None:
        user.creator_badge = 1 if creator_badge else 0
    if beta_access is not None:
        user.beta_access = 1 if beta_access else 0
    db.commit()
    db.refresh(user)
    return _public_user(user)
