"""Authentication routes.

Routes:
- POST /api/auth/register
- POST /api/auth/login
- POST /api/auth/refresh
- POST /api/auth/logout

Design notes:
- Access token is a JWT used for Authorization (Bearer).
- Refresh token is an opaque random string stored in DB for rotation/revocation.
"""

from __future__ import annotations

import secrets
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.api.schemas.auth import (
    LoginRequest,
    LogoutRequest,
    RefreshRequest,
    RegisterRequest,
    TokenPairResponse,
    UserPublic,
)
from src.db.models import RefreshToken, User, UserRole
from src.db.session import get_db
from src.security.jwt import create_access_token
from src.security.passwords import hash_password, verify_password
from src.settings import get_settings

router = APIRouter(prefix="/api/auth", tags=["Auth"])

_settings = get_settings()


def _utcnow() -> datetime:
    return datetime.now(tz=timezone.utc)


def _access_expires_in_seconds() -> int:
    return int(timedelta(minutes=_settings.access_token_expire_minutes).total_seconds())


def _issue_refresh_token(db: Session, user: User) -> RefreshToken:
    """Create and persist a new refresh token record."""
    token = secrets.token_urlsafe(48)  # ~64 chars
    expires_at = _utcnow() + timedelta(days=_settings.refresh_token_expire_days)

    rt = RefreshToken(token=token, user_id=user.id, expires_at=expires_at, revoked=False)
    db.add(rt)
    return rt


def _revoke_refresh_token(db: Session, rt: RefreshToken) -> None:
    """Revoke a refresh token (server-side invalidation)."""
    rt.revoked = True
    db.add(rt)


def _get_user_by_email(db: Session, email: str) -> User | None:
    stmt = select(User).where(User.email == email)
    return db.execute(stmt).scalar_one_or_none()


def _to_user_public(user: User) -> UserPublic:
    return UserPublic(id=user.id, email=user.email, role=user.role.value)


def _token_response(user: User, refresh_token: str) -> TokenPairResponse:
    access = create_access_token(subject=str(user.id), extra_claims={"role": user.role.value})
    return TokenPairResponse(
        access_token=access,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=_access_expires_in_seconds(),
        user=_to_user_public(user),
    )


@router.post(
    "/register",
    response_model=TokenPairResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
    description="Creates a new user account and returns access/refresh tokens.",
    operation_id="auth_register",
)
def register(payload: RegisterRequest, db: Session = Depends(get_db)) -> TokenPairResponse:
    """Register endpoint.

    Args:
        payload: Email/password registration data.
        db: DB session.

    Returns:
        Token pair + user info.

    Raises:
        409 if email already exists.
    """
    existing = _get_user_by_email(db, payload.email)
    if existing is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")

    user = User(
        email=str(payload.email).lower(),
        password_hash=hash_password(payload.password),
        role=UserRole.USER,
        is_active=True,
    )
    db.add(user)
    db.flush()  # assign user.id

    rt = _issue_refresh_token(db, user)
    db.commit()

    return _token_response(user=user, refresh_token=rt.token)


@router.post(
    "/login",
    response_model=TokenPairResponse,
    summary="Login",
    description="Validates credentials and returns access/refresh tokens.",
    operation_id="auth_login",
)
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> TokenPairResponse:
    """Login endpoint.

    Args:
        payload: Email/password.
        db: DB session.

    Returns:
        Token pair + user info.

    Raises:
        401 if credentials are invalid or user is inactive.
    """
    user = _get_user_by_email(db, str(payload.email).lower())
    if user is None or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    if not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    rt = _issue_refresh_token(db, user)
    db.commit()

    return _token_response(user=user, refresh_token=rt.token)


@router.post(
    "/refresh",
    response_model=TokenPairResponse,
    summary="Refresh access token",
    description="Rotates a refresh token and issues a new access token.",
    operation_id="auth_refresh",
)
def refresh(payload: RefreshRequest, db: Session = Depends(get_db)) -> TokenPairResponse:
    """Refresh endpoint (rotation).

    Rules:
    - Refresh token must exist, not be revoked, and not be expired.
    - On success: revoke the old refresh token and issue a new refresh token.
    """
    stmt = select(RefreshToken).where(RefreshToken.token == payload.refresh_token)
    rt = db.execute(stmt).scalar_one_or_none()
    if rt is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

    if rt.revoked:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token revoked")

    if rt.expires_at <= _utcnow():
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token expired")

    user = db.get(User, rt.user_id)
    if user is None or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found or inactive")

    # Rotate token
    _revoke_refresh_token(db, rt)
    new_rt = _issue_refresh_token(db, user)

    db.commit()

    return _token_response(user=user, refresh_token=new_rt.token)


@router.post(
    "/logout",
    status_code=status.HTTP_200_OK,
    summary="Logout",
    description="Revokes a refresh token server-side.",
    operation_id="auth_logout",
)
def logout(payload: LogoutRequest, db: Session = Depends(get_db)) -> dict:
    """Logout endpoint.

    Revokes a provided refresh token (idempotent).
    """
    stmt = select(RefreshToken).where(RefreshToken.token == payload.refresh_token)
    rt = db.execute(stmt).scalar_one_or_none()
    if rt is not None and not rt.revoked:
        _revoke_refresh_token(db, rt)
        db.commit()

    return {"message": "Logged out"}
