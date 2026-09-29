from sqlalchemy import Column, Integer, String, Text, DateTime
from datetime import datetime
from .database import Base
import uuid

class Creator(Base):
    __tablename__ = "creators"
    id = Column(Integer, primary_key=True, index=True)
    slug = Column(String(255), unique=True, index=True, nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text, default="")
    image_url = Column(String(500), default="")
    download_url = Column(String(500), default="")

class Download(Base):
    __tablename__ = "downloads"
    id = Column(Integer, primary_key=True, index=True)
    slug = Column(String(255), unique=True, index=True, nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text, default="")
    file_url = Column(String(500), default="")
    version = Column(String(50), default="1.0.0")

class Theme(Base):
    __tablename__ = "themes"
    id = Column(Integer, primary_key=True, index=True)
    slug = Column(String(255), unique=True, index=True, nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text, default="")
    preview_url = Column(String(500), default="")
    unlock_type = Column(String(100), default="free")

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    username = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(50), default="user", nullable=False)
    donation_cents = Column(Integer, default=0, nullable=False)
    creator_badge = Column(Integer, default=0, nullable=False)
    beta_access = Column(Integer, default=0, nullable=False)
    discord_id = Column(String(32), unique=True, index=True, nullable=True)
    discord_username = Column(String(255), default="", nullable=False)
    # Immutable authentication identity. Tokens use this instead of the recyclable
    # numeric primary key so a deleted account can never inherit an old token.
    auth_id = Column(String(36), unique=True, index=True, nullable=False, default=lambda: str(uuid.uuid4()))
    auth_version = Column(Integer, default=1, nullable=False)

class OAuthTransaction(Base):
    __tablename__ = "oauth_transactions"
    id = Column(Integer, primary_key=True, index=True)
    state_hash = Column(String(64), unique=True, index=True, nullable=False)
    mode = Column(String(20), nullable=False)
    browser_nonce = Column(String(64), nullable=False)
    code_verifier = Column(String(128), nullable=False)
    launcher_code_challenge = Column(String(128), nullable=True)
    expires_at = Column(DateTime, nullable=False)
    used_at = Column(DateTime, nullable=True)

class LauncherAuthCode(Base):
    __tablename__ = "launcher_auth_codes"
    id = Column(Integer, primary_key=True, index=True)
    code_hash = Column(String(64), unique=True, index=True, nullable=False)
    auth_id = Column(String(36), nullable=False, index=True)
    auth_version = Column(Integer, nullable=False)
    code_challenge = Column(String(128), nullable=True)
    expires_at = Column(DateTime, nullable=False)
    used_at = Column(DateTime, nullable=True)


class RedeemCode(Base):
    __tablename__ = "redeem_codes"
    id = Column(Integer, primary_key=True, index=True)
    code_hash = Column(String(64), unique=True, index=True, nullable=False)
    entitlement = Column(String(100), nullable=False, default="beta")
    redeemed_by_auth_id = Column(String(36), nullable=True, index=True)
    redeemed_by_device_id = Column(String(64), nullable=True, index=True)
    redeemed_at = Column(DateTime, nullable=True)

class ModUploadRequest(Base):
    __tablename__ = "mod_upload_requests"
    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(String(64), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    game = Column(String(50), nullable=False)
    description = Column(Text, default="")
    file_name = Column(String(255), default="")
    file_size = Column(Integer, default=0)
    status = Column(String(50), default="pending", nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
