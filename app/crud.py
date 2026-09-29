from sqlalchemy import or_
from hashlib import sha256

from .models import Creator, Download, Theme, User, RedeemCode
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
    rotate_admin = os.getenv("HORIZON_ROTATE_ADMIN_PASSWORD", "").strip() == "1"
    admin = db.query(User).filter(User.username == "admin").first()

    if admin_password and not admin:
        db.add(User(
            email="admin@horizon.local",
            username="admin",
            password_hash=hash_password(admin_password),
            role="admin",
        ))
    elif admin_password and rotate_admin and admin:
        # Explicit one-time rotation for a previously deployed admin secret.
        admin.password_hash = hash_password(admin_password)
        admin.auth_version = int(admin.auth_version or 1) + 1

    beta_codes = [
        "9f9a8236a22c1210e282a4431f49cb61f13e7b46e645d19eea767efff3d17cf4",
        "6f8987b361c1aa0490af6eac6e263e6b115bc9b6dd9f081882313a5c3f4d1ab9",
        "f4194ea22570ae92d332a48f1d1b1def157ee94a7cbe5fa36a27dfa96a785be8",
        "fecc057507f2e7d07cd1a236f3d3d0bfa02a6e35f5519d6134c52c3fe0b674ca",
        "5579c2c920778059f7e773a7a22bf6c499f057e61123e92d503372592d826a5a",
        "28121e4dbe861f9e726e20c327ac776f85eaa2524da26798bfdda7bdb8dfdbba",
    ]
    for code_hash in beta_codes:
        if not db.query(RedeemCode).filter(RedeemCode.code_hash == code_hash).first():
            db.add(RedeemCode(code_hash=code_hash, entitlement="beta"))

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

    # Public account creation is Discord-only. Keep this helper for legacy/admin
    # tooling, but never expose it as a public account-creation path.
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
    # Discord-linked users must authenticate through Discord. This prevents a
    # planted or previously known password from bypassing Discord identity/roles.
    if not user or user.role != "admin":
        return None
    if not verify_password(password, user.password_hash):
        return None
    return user


def login_user(db, payload: dict):
    identifier = payload.get("identifier") or payload.get("email") or payload.get("username") or ""
    password = payload.get("password", "")
    user = authenticate_user(db, identifier, password)
    return _public_user(user) if user else None


def get_user(db, user_id: int):
    return db.query(User).filter(User.id == user_id).first()


def get_user_by_auth_id(db, auth_id: str):
    return db.query(User).filter(User.auth_id == auth_id).first()


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
    # Entitlement changes invalidate previously issued launcher/web tokens.
    user.auth_version = int(user.auth_version or 1) + 1
    db.commit()
    db.refresh(user)
    return _public_user(user)
