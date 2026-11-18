
"""
Security tests for MeetIQ JWT authentication.

Covers:
- Valid and expired tokens
- Invalid signatures and tampered tokens
- Missing and malformed JWT claims
- Unsupported signing algorithms
- Missing and malformed Authorization headers
- Deleted and inactive users
- Invalid credentials
- Duplicate registration
"""

from datetime import datetime, timedelta, timezone
import uuid

import jwt
import pytest

from app.core.config import settings
from app.core.jwt import create_access_token, decode_access_token
from app.core.security import hash_password
from app.models.user import User


# --------------------------------------------------
# Helpers
# --------------------------------------------------

def make_token(
    *,
    user_id=None,
    expires_in_minutes=30,
    secret=None,
    algorithm=None,
    include_sub=True,
    include_iat=True,
    include_exp=True,
):
    """Create JWTs with controlled claims for security tests."""
    now = datetime.now(timezone.utc)

    payload = {}

    if include_sub:
        payload["sub"] = str(user_id or uuid.uuid4())

    if include_iat:
        payload["iat"] = now

    if include_exp:
        payload["exp"] = now + timedelta(
            minutes=expires_in_minutes
        )

    return jwt.encode(
        payload,
        secret or settings.jwt_secret_key,
        algorithm=algorithm or settings.jwt_algorithm,
    )


# --------------------------------------------------
# JWT validation tests
# --------------------------------------------------

def test_valid_access_token():
    user_id = uuid.uuid4()
    token = create_access_token(user_id)

    assert decode_access_token(token) == user_id


def test_expired_access_token():
    token = make_token(expires_in_minutes=-30)

    with pytest.raises(ValueError, match="Invalid or expired"):
        decode_access_token(token)


def test_tampered_access_token():
    token = create_access_token(uuid.uuid4())

    header, payload, signature = token.split(".")

    # Alter the payload while keeping the original signature.
    replacement = "A" if payload[0] != "A" else "B"
    tampered = (
        f"{header}.{replacement}{payload[1:]}.{signature}"
    )

    with pytest.raises(ValueError):
        decode_access_token(tampered)


def test_token_signed_with_wrong_secret():
    token = make_token(secret="different-test-secret")

    with pytest.raises(ValueError):
        decode_access_token(token)


@pytest.mark.parametrize(
    "missing_claim",
    ["sub", "iat", "exp"],
)
def test_token_missing_required_claim(missing_claim):
    token = make_token(
        include_sub=missing_claim != "sub",
        include_iat=missing_claim != "iat",
        include_exp=missing_claim != "exp",
    )

    with pytest.raises(ValueError):
        decode_access_token(token)


def test_token_with_invalid_uuid():
    now = datetime.now(timezone.utc)

    token = jwt.encode(
        {
            "sub": "not-a-uuid",
            "iat": now,
            "exp": now + timedelta(minutes=30),
        },
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )

    with pytest.raises(ValueError):
        decode_access_token(token)


def test_token_with_non_string_subject():
    now = datetime.now(timezone.utc)

    token = jwt.encode(
        {
            "sub": 12345,
            "iat": now,
            "exp": now + timedelta(minutes=30),
        },
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )

    with pytest.raises(ValueError):
        decode_access_token(token)


def test_token_with_future_issued_at():
    now = datetime.now(timezone.utc)

    token = jwt.encode(
        {
            "sub": str(uuid.uuid4()),
            "iat": now + timedelta(hours=1),
            "exp": now + timedelta(hours=2),
        },
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )

    with pytest.raises(ValueError):
        decode_access_token(token)


def test_token_with_unsupported_algorithm():
    # The decoder must not accept a different signing algorithm.
    alternate_algorithm = (
        "HS512"
        if settings.jwt_algorithm != "HS512"
        else "HS256"
    )

    token = make_token(algorithm=alternate_algorithm)

    with pytest.raises(ValueError):
        decode_access_token(token)


def test_malformed_jwt():
    with pytest.raises(ValueError):
        decode_access_token("not.a.valid.jwt")


def test_empty_jwt():
    with pytest.raises(ValueError):
        decode_access_token("")


# --------------------------------------------------
# Protected endpoint tests
# --------------------------------------------------

def test_profile_without_token(client):
    response = client.get("/auth/me")

    assert response.status_code == 401


def test_profile_with_invalid_token(client):
    response = client.get(
        "/auth/me",
        headers={
            "Authorization": "Bearer invalid-token"
        },
    )

    assert response.status_code == 401


def test_profile_with_expired_token(client):
    token = make_token(expires_in_minutes=-30)

    response = client.get(
        "/auth/me",
        headers={
            "Authorization": f"Bearer {token}"
        },
    )

    assert response.status_code == 401


def test_profile_with_wrong_auth_scheme(client):
    token = make_token()

    response = client.get(
        "/auth/me",
        headers={
            "Authorization": f"Basic {token}"
        },
    )

    assert response.status_code == 401


def test_profile_with_unknown_user(client):
    # Valid token, but the user does not exist in PostgreSQL.
    token = create_access_token(uuid.uuid4())

    response = client.get(
        "/auth/me",
        headers={
            "Authorization": f"Bearer {token}"
        },
    )

    assert response.status_code == 401


def test_profile_with_deleted_user(
    client,
    db_session,
):
    user = User(
        email="deleted-user@meetiq.com",
        hashed_password=hash_password("TestPassword123!"),
        is_active=True,
    )

    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    token = create_access_token(user.id)

    db_session.delete(user)
    db_session.commit()

    response = client.get(
        "/auth/me",
        headers={
            "Authorization": f"Bearer {token}"
        },
    )

    assert response.status_code == 401


def test_profile_with_inactive_user(
    client,
    db_session,
):
    user = User(
        email="inactive-user@meetiq.com",
        hashed_password=hash_password("TestPassword123!"),
        is_active=False,
    )

    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    token = create_access_token(user.id)

    response = client.get(
        "/auth/me",
        headers={
            "Authorization": f"Bearer {token}"
        },
    )

    assert response.status_code == 401


# --------------------------------------------------
# Login and registration security tests
# --------------------------------------------------

def test_login_with_wrong_password(client):
    client.post(
        "/auth/register",
        json={
            "email": "login-test@meetiq.com",
            "password": "CorrectPassword123!",
        },
    )

    response = client.post(
        "/auth/login",
        json={
            "email": "login-test@meetiq.com",
            "password": "WrongPassword123!",
        },
    )

    assert response.status_code == 401


def test_login_with_nonexistent_user(client):
    response = client.post(
        "/auth/login",
        json={
            "email": "unknown@meetiq.com",
            "password": "TestPassword123!",
        },
    )

    assert response.status_code == 401


def test_duplicate_registration_rejected(client):
    payload = {
        "email": "duplicate@meetiq.com",
        "password": "TestPassword123!",
    }

    first_response = client.post(
        "/auth/register",
        json=payload,
    )

    assert first_response.status_code == 201

    second_response = client.post(
        "/auth/register",
        json=payload,
    )

    assert second_response.status_code == 409


def test_successful_login_returns_valid_token(client):
    payload = {
        "email": "successful-login@meetiq.com",
        "password": "TestPassword123!",
    }

    register_response = client.post(
        "/auth/register",
        json=payload,
    )

    assert register_response.status_code == 201

    login_response = client.post(
        "/auth/login",
        json=payload,
    )

    assert login_response.status_code == 200

    token = login_response.json()["access_token"]

    user_id = decode_access_token(token)

    assert isinstance(user_id, uuid.UUID)

    profile_response = client.get(
        "/auth/me",
        headers={
            "Authorization": f"Bearer {token}"
        },
    )

    assert profile_response.status_code == 200
