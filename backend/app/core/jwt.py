
"""
Provides JWT access token creation and validation.
"""

from datetime import datetime, timedelta, timezone
import uuid

import jwt
from jwt import InvalidTokenError

from app.core.config import settings


def create_access_token(user_id: uuid.UUID) -> str:
    """
    Creates a signed JWT access token for a user.
    """

    now = datetime.now(timezone.utc)

    expires_at = now + timedelta(
        minutes=settings.access_token_expire_minutes
    )

    payload = {
        "sub": str(user_id),
        "iat": now,
        "exp": expires_at,
    }

    return jwt.encode(
        payload,
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )


def decode_access_token(token: str) -> uuid.UUID:
    """
    Validates a JWT and returns its user ID.

    Raises ValueError for invalid or expired tokens.
    """

    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
            options={"require": ["sub", "iat", "exp"]},
        )

        user_id = payload.get("sub")

        if not isinstance(user_id, str):
            raise ValueError("Invalid token subject.")

        return uuid.UUID(user_id)

    except (InvalidTokenError, ValueError) as exc:
        raise ValueError(
            "Invalid or expired access token."
        ) from exc
