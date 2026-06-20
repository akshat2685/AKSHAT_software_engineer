"""
Database connection configuration.

Supports both SQLite (local dev) and PostgreSQL (production) via the
``DATABASE_URL`` environment variable. When a non-SQLite backend is detected
we enable connection pooling (QueuePool), pre-ping, and sane pool sizes —
SQLite cannot be pooled this way and would throw "database is locked" under
concurrent agent workers (Issue 3).

Move the memory store off the default SQLite path for production by setting::

    DATABASE_URL=postgresql://user:password@host:5432/akshat?sslmode=require
"""

import os
import logging
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

logger = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parents[2]
DB_PATH = ROOT / "workspace" / "memory" / "akshat_memory.sqlite3"
DB_PATH.parent.mkdir(parents=True, exist_ok=True)

DATABASE_URL = os.environ.get("DATABASE_URL", f"sqlite:///{DB_PATH}")

IS_SQLITE = DATABASE_URL.startswith("sqlite")


def _build_engine(db_url: str):
    """Create a SQLAlchemy engine with backend-appropriate options.

    • SQLite: ``check_same_thread=False`` so worker threads can share it.
    • Postgres / MySQL: QueuePool with pre-ping, overflow, and recycle so
      long-lived connections don't go stale behind a load balancer.
    """
    if db_url.startswith("sqlite"):
        return create_engine(
            db_url,
            connect_args={"check_same_thread": False},
            # SQLite ignores pool options, but set a small pool so concurrent
            # agents don't all hit the single-writer lock at once.
            pool_size=5,
            max_overflow=0,
        )

    from sqlalchemy.pool import QueuePool

    return create_engine(
        db_url,
        poolclass=QueuePool,
        pool_size=20,
        max_overflow=10,
        pool_pre_ping=True,      # drop dead connections before use
        pool_recycle=1800,       # recycle connections every 30 min
        pool_timeout=30,         # wait up to 30s for a connection
        echo=bool(os.environ.get("DATABASE_ECHO", "").lower() in {"1", "true"}),
    )


engine = _build_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

logger.info("Database backend: %s", "SQLite" if IS_SQLITE else "PostgreSQL/MySQL")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    from backend.database import models  # noqa: F401 — ensure tables register on Base
    Base.metadata.create_all(bind=engine)
