"""Database session and engine management.

This module exposes:
- SQLAlchemy engine creation (from DATABASE_URL)
- SessionLocal factory
- FastAPI dependency for request-scoped sessions
- A lightweight DB connectivity check for app startup
"""

from __future__ import annotations

from contextlib import contextmanager
from typing import Generator

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from src.settings import get_settings

_settings = get_settings()


def _build_engine() -> Engine:
    """Create the SQLAlchemy engine based on settings.

    We use pool_pre_ping=True to proactively detect stale connections.
    """
    return create_engine(_settings.database_url, pool_pre_ping=True)


# Engine is created once per process.
engine: Engine = _build_engine()

# SessionLocal is a factory for new Session objects.
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


# PUBLIC_INTERFACE
def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency that yields a DB session and guarantees cleanup.

    Yields:
        Session: SQLAlchemy session bound to the configured engine.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# PUBLIC_INTERFACE
def check_db_connection() -> None:
    """Verify that the configured DATABASE_URL is reachable.

    Raises:
        RuntimeError: if the database can't be reached or queried.
    """
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
    except Exception as exc:  # pragma: no cover
        raise RuntimeError(
            "Database connectivity check failed. Verify DATABASE_URL and database availability."
        ) from exc


@contextmanager
def db_session() -> Generator[Session, None, None]:
    """Context manager for non-FastAPI code paths (scripts, migrations helpers)."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
