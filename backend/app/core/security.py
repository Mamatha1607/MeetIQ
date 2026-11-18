
"""
Provides password hashing and verification utilities
for MeetIQ authentication.
"""

from argon2 import PasswordHasher
from argon2.exceptions import (
    InvalidHashError,
    VerificationError,
    VerifyMismatchError,
)

# Argon2id password hasher with library-maintained defaults.
password_hasher = PasswordHasher()


def hash_password(password: str) -> str:
    """
    Securely hashes a plaintext password.

    Used when registering a new user.
    """
    return password_hasher.hash(password)


def verify_password(
    plain_password: str,
    hashed_password: str,
) -> bool:
    """
    Verifies a plaintext password against its stored hash.

    Returns True if the password matches.
    Returns False otherwise.
    """
    try:
        return password_hasher.verify(
            hashed_password,
            plain_password,
        )
    except (
        VerifyMismatchError,
        InvalidHashError,
        VerificationError,
    ):
        return False
