
"""
Tests JWT access token creation and validation.
"""

from datetime import datetime, timedelta, timezone
import uuid

import jwt
import pytest

from app.core.config import settings
from app.core.jwt import (
    create_access_token,
    decode_access_token,
)


def test_create_and_decode_access_token():
    user_id = uuid.uuid4()

    token = create_access_token(user_id)

    assert isinstance(token, str)
    assert decode_access_token(token) == user_id


def test_reject_invalid_token():
    with pytest.raises(ValueError):
        decode_access_token("invalid.token.value")


def test_reject_expired_token():
    user_id = uuid.uuid4()

    token = jwt.encode(
        {
            "sub": str(user_id),
            "iat": datetime.now(timezone.utc)
            - timedelta(hours=2),
            "exp": datetime.now(timezone.utc)
            - timedelta(hours=1),
        },
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )

    with pytest.raises(ValueError):
        decode_access_token(token)


def test_reject_invalid_subject():
    token = jwt.encode(
        {
            "sub": "not-a-valid-uuid",
            "iat": datetime.now(timezone.utc),
            "exp": datetime.now(timezone.utc)
            + timedelta(minutes=30),
        },
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )

    with pytest.raises(ValueError):
        decode_access_token(token)
