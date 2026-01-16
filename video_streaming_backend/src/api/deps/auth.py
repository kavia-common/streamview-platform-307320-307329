"""Auth-related FastAPI dependencies (current user, role guards)."""

from __future__ import annotations

from typing import Annotated, Callable

import jwt
from fastapi import Depends, HTTPException, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from src.db.models import User, UserRole
from src.db.session import get_db
from src.security.jwt import decode_token

_bearer = HTTPBearer(auto_error=False)


def _unauthorized(detail: str = "Not authenticated") -> HTTPException:
    return HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=detail)


def _forbidden(detail: str = "Not enough permissions") -> HTTPException:
    return HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=detail)


# PUBLIC_INTERFACE
def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Security(_bearer)],
    db: Annotated[Session, Depends(get_db)],
) -> User:
    """Resolve and return the current user from a Bearer access token.

    The access token is expected in the Authorization header:
        Authorization: Bearer <jwt>

    Raises:
        HTTPException(401): if token missing/invalid/expired or user inactive/not found.
    """
    if credentials is None or not credentials.credentials:
        raise _unauthorized()

    token = credentials.credentials
    try:
        payload = decode_token(token)
    except jwt.PyJWTError:
        raise _unauthorized("Invalid or expired token")

    if payload.get("typ") != "access":
        raise _unauthorized("Invalid token type")

    sub = payload.get("sub")
    if not sub:
        raise _unauthorized("Invalid token payload")

    # We encode subject as user id string.
    try:
        user_id = int(sub)
    except ValueError:
        raise _unauthorized("Invalid token subject")

    user = db.get(User, user_id)
    if user is None or not user.is_active:
        raise _unauthorized("User not found or inactive")

    return user


# PUBLIC_INTERFACE
def require_roles(*allowed_roles: UserRole) -> Callable[..., User]:
    """Create a dependency that enforces that the current user has an allowed role.

    Usage:
        @router.get(..., dependencies=[Depends(require_roles(UserRole.ADMIN))])

    Args:
        allowed_roles: One or more allowed roles.

    Returns:
        Dependency callable returning User if allowed.

    Raises:
        HTTPException(403): if user role not allowed.
    """

    def _dep(user: Annotated[User, Depends(get_current_user)]) -> User:
        if not allowed_roles:
            return user
        if user.role not in allowed_roles:
            raise _forbidden()
        return user

    return _dep
