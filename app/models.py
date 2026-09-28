from sqlalchemy import Column, Integer, String, Text
from .database import Base

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