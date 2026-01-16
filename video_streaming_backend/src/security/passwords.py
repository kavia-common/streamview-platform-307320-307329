"""Password hashing utilities.

We use passlib's bcrypt scheme for robust password hashing.
"""

from __future__ import annotations

from passlib.context import CryptContext

_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# PUBLIC_INTERFACE
def hash_password(password: str) -> bytes:
    """Hash a plaintext password using bcrypt.

    Args:
        password: Plaintext password.

    Returns:
        Password hash as bytes (suitable for storing in LargeBinary).
    """
    if not password:
        raise ValueError("Password must not be empty.")
    return _pwd_context.hash(password).encode("utf-8")


# PUBLIC_INTERFACE
def verify_password(password: str, password_hash: bytes) -> bool:
    """Verify a plaintext password against a stored bcrypt hash.

    Args:
        password: Plaintext password.
        password_hash: Stored password hash bytes.

    Returns:
        True if the password matches; otherwise False.
    """
    if not password or not password_hash:
        return False
    # Stored as bytes in DB; passlib expects str.
    return _pwd_context.verify(password, password_hash.decode("utf-8"))
