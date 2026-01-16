"""Database base classes and shared mixins.

This module defines the SQLAlchemy declarative Base used across all ORM models.
"""

from __future__ import annotations

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy ORM models."""
