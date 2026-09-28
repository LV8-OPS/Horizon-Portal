import os
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

BASE_DIR = Path(__file__).resolve().parent.parent

# Vercel's deployment filesystem is read-only. Use an external DATABASE_URL when
# available, otherwise keep a temporary SQLite database for preview/demo use.
DATABASE_URL = os.getenv("DATABASE_URL")
if DATABASE_URL:
    SQLALCHEMY_DATABASE_URL = DATABASE_URL
    engine = create_engine(SQLALCHEMY_DATABASE_URL, pool_pre_ping=True)
else:
    db_path = Path("/tmp/horizon.db") if os.getenv("VERCEL") else (BASE_DIR / "horizon.db")
    SQLALCHEMY_DATABASE_URL = f"sqlite:///{db_path.as_posix()}"
    engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()
