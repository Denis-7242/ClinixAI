"""Engine and session management for ClinixAI.

Usage:
    from database.db import init_db, get_session
    init_db()
    with get_session() as s:
        ...
"""
from __future__ import annotations

import os
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator, Optional

from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from database.models import Base

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DB_PATH = PROJECT_ROOT / "data" / "clinixai.db"

_engine: Optional[Engine] = None
_SessionFactory: Optional[sessionmaker] = None


def _enable_sqlite_fk(dbapi_connection, _record) -> None:
    """SQLite ignores foreign keys unless this pragma is set on each connection."""
    cur = dbapi_connection.cursor()
    cur.execute("PRAGMA foreign_keys=ON")
    cur.close()


def init_db(db_url: Optional[str] = None) -> Engine:
    """Create the engine (once) and all tables. Safe to call repeatedly.

    Priority for the URL: argument > CLINIXAI_DB_URL env var > default SQLite file.
    """
    global _engine, _SessionFactory
    url = db_url or os.getenv("CLINIXAI_DB_URL")
    if url is None:
        DEFAULT_DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        url = f"sqlite:///{DEFAULT_DB_PATH}"

    _engine = create_engine(url, future=True)
    if url.startswith("sqlite"):
        event.listen(_engine, "connect", _enable_sqlite_fk)
    Base.metadata.create_all(_engine)
    _SessionFactory = sessionmaker(bind=_engine, expire_on_commit=False, future=True)
    return _engine


@contextmanager
def get_session() -> Iterator[Session]:
    """Transactional scope: commits on success, rolls back on error."""
    if _SessionFactory is None:
        init_db()
    assert _SessionFactory is not None
    session = _SessionFactory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def reset_db() -> None:
    """Drop and recreate all tables. Destroys all stored data."""
    if _engine is None:
        init_db()
    assert _engine is not None
    Base.metadata.drop_all(_engine)
    Base.metadata.create_all(_engine)