"""SQLAlchemy ORM models for the StreamView backend."""

from __future__ import annotations

import enum
from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    LargeBinary,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db.base import Base


class UserRole(str, enum.Enum):
    """Role values assigned to users."""

    USER = "user"
    ADMIN = "admin"


class VideoVisibility(str, enum.Enum):
    """Visibility values for videos."""

    PRIVATE = "private"
    UNLISTED = "unlisted"
    PUBLIC = "public"


class TimestampMixin:
    """Adds created_at/updated_at columns managed by the DB."""

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )


class User(Base, TimestampMixin):
    """Application user account."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(320), unique=True, index=True, nullable=False)
    password_hash: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)

    # Roles are modeled as a simple enum column for now.
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole, name="user_role"), nullable=False, default=UserRole.USER
    )

    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    videos: Mapped[list["Video"]] = relationship(
        back_populates="uploader",
        cascade="all,delete-orphan",
        passive_deletes=True,
    )
    refresh_tokens: Mapped[list["RefreshToken"]] = relationship(
        back_populates="user",
        cascade="all,delete-orphan",
        passive_deletes=True,
    )


class Video(Base, TimestampMixin):
    """Uploaded video metadata."""

    __tablename__ = "videos"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    title: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Either a filesystem path in a mounted volume or a URL to object storage.
    filepath: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    url: Mapped[str | None] = mapped_column(String(2048), nullable=True)

    duration_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)
    size_bytes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    mime_type: Mapped[str | None] = mapped_column(String(100), nullable=True)

    visibility: Mapped[VideoVisibility] = mapped_column(
        Enum(VideoVisibility, name="video_visibility"),
        nullable=False,
        default=VideoVisibility.PRIVATE,
        index=True,
    )

    uploader_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    uploader: Mapped[User | None] = relationship(back_populates="videos")


class RefreshToken(Base):
    """Refresh token record for JWT authentication flows.

    Notes:
      - `token` stores the opaque refresh token string (or a hash if you later decide to hash at rest).
      - `revoked` allows server-side invalidation without deleting rows.
    """

    __tablename__ = "refresh_tokens"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    token: Mapped[str] = mapped_column(String(512), unique=True, index=True, nullable=False)

    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    user: Mapped[User] = relationship(back_populates="refresh_tokens")

    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    revoked: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
