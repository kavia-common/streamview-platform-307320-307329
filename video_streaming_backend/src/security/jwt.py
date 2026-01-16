"""JWT helper utilities.

This module centralizes JWT encoding/decoding based on application settings.
Routes/services can import these helpers later when implementing auth endpoints.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Dict

import jwt

from src.settings import get_settings

_settings = get_settings()


# PUBLIC_INTERFACE
def create_access_token(subject: str, extra_claims: Dict[str, Any] | None = None) -> str:
    """Create a signed JWT access token.

    Args:
        subject: Typically the user ID or email.
        extra_claims: Additional JWT claims to embed.

    Returns:
        Signed JWT string.
    """
    now = datetime.now(tz=timezone.utc)
    exp = now + timedelta(minutes=_settings.access_token_expire_minutes)
    payload: Dict[str, Any] = {"sub": subject, "iat": int(now.timestamp()), "exp": exp}
    if extra_claims:
        payload.update(extra_claims)
    return jwt.encode(payload, _settings.jwt_secret, algorithm=_settings.jwt_alg)


# PUBLIC_INTERFACE
def decode_token(token: str) -> Dict[str, Any]:
    """Decode and validate a JWT.

    Args:
        token: JWT string.

    Returns:
        Decoded payload as dict.

    Raises:
        jwt.PyJWTError: If invalid or expired.
    """
    return jwt.decode(token, _settings.jwt_secret, algorithms=[_settings.jwt_alg])
