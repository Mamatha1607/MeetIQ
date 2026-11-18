
"""
Tests password hashing and verification.
"""

from app.core.security import (
    hash_password,
    verify_password,
)


def test_password_hashing():
    password = "MySecurePassword123!"

    hashed = hash_password(password)

    # The original password must never be stored directly.
    assert hashed != password

    # Argon2id hash format.
    assert hashed.startswith("$argon2id$")

    # Correct password should succeed.
    assert verify_password(password, hashed) is True

    # Incorrect password should fail.
    assert verify_password("WrongPassword", hashed) is False


def test_password_hashes_are_unique():
    password = "MySecurePassword123!"

    first_hash = hash_password(password)
    second_hash = hash_password(password)

    # Random salts produce different hashes.
    assert first_hash != second_hash

    # Both hashes must verify successfully.
    assert verify_password(password, first_hash)
    assert verify_password(password, second_hash)


def test_invalid_password_hash():
    assert verify_password(
        "MySecurePassword123!",
        "invalid-hash",
    ) is False
