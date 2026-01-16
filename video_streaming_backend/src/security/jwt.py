"""JWT helper utilities.

This module centralizes JWT encoding/decoding based on application settings.

We issue two token types:
- Access token: short-lived JWT used for authorization (Authorization: Bearer <token>)
- Refresh token: opaque random string stored server-side (DB) and rotated on refresh
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
        subject: Token subject. We use the user id (as string).
        extra_claims: Additional JWT claims to embed (e.g. role).

    Returns:
        Signed JWT string.
    """
    now = datetime.now(tz=timezone.utc)
    exp = now + timedelta(minutes=_settings.access_token_expire_minutes)
    payload: Dict[str, Any] = {
        "sub": subject,
        "typ": "access",
        "iat": int(now.timestamp()),
        "exp": exp,
    }
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
