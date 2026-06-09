import os
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

ROOT = Path(__file__).resolve().parents[2]
DB_PATH = ROOT / "workspace" / "memory" / "akshat_memory.sqlite3"
DB_PATH.parent.mkdir(parents=True, exist_ok=True)

DATABASE_URL = os.environ.get("DATABASE_URL", f"sqlite:///{DB_PATH}")

# check_same_thread is only needed for SQLite
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    from backend.database import models
    Base.metadata.create_all(bind=engine)
