"""Pydantic schemas for authentication endpoints."""

from __future__ import annotations

from pydantic import BaseModel, EmailStr, Field


class RegisterRequest(BaseModel):
    """Payload for registering a new user."""

    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., min_length=8, description="User password (min 8 characters)")


class LoginRequest(BaseModel):
    """Payload for logging in."""

    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., description="User password")


class RefreshRequest(BaseModel):
    """Payload for refreshing tokens."""

    refresh_token: str = Field(..., description="Opaque refresh token previously issued by /login or /refresh")


class LogoutRequest(BaseModel):
    """Payload for logout (revokes refresh token)."""

    refresh_token: str = Field(..., description="Opaque refresh token to revoke")


class UserPublic(BaseModel):
    """Public user fields returned to clients."""

    id: int = Field(..., description="User id")
    email: EmailStr = Field(..., description="User email address")
    role: str = Field(..., description='User role (e.g., "user" or "admin")')


class TokenPairResponse(BaseModel):
    """Auth token response returned to clients."""

    access_token: str = Field(..., description="JWT access token")
    refresh_token: str = Field(..., description="Opaque refresh token")
    token_type: str = Field("bearer", description='Token type. Always "bearer" for access_token usage.')
    expires_in: int = Field(..., description="Access token expiration time in seconds")
    user: UserPublic = Field(..., description="Logged-in user information")
