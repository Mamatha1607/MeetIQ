
"""
Tests user registration, login, and JWT-protected endpoints.
"""

from datetime import datetime, timedelta, timezone

import jwt

from app.core.config import settings


TEST_EMAIL = "auth_test@example.com"
TEST_PASSWORD = "SecurePassword123!"


def register_test_user(client):
    """
    Registers a user for authentication tests.
    """

    return client.post(
        "/auth/register",
        json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD,
        },
    )


def test_register_user(client):
    response = register_test_user(client)

    assert response.status_code == 201

    data = response.json()

    assert data["email"] == TEST_EMAIL
    assert data["is_active"] is True
    assert "id" in data
    assert "hashed_password" not in data
    assert "password" not in data


def test_duplicate_registration(client):
    first_response = register_test_user(client)
    second_response = register_test_user(client)

    assert first_response.status_code == 201
    assert second_response.status_code == 409


def test_login_success(client):
    register_test_user(client)

    response = client.post(
        "/auth/login",
        json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD,
        },
    )

    assert response.status_code == 200
    assert response.json()["token_type"] == "bearer"
    assert response.json()["access_token"]


def test_login_wrong_password(client):
    register_test_user(client)

    response = client.post(
        "/auth/login",
        json={
            "email": TEST_EMAIL,
            "password": "IncorrectPassword123!",
        },
    )

    assert response.status_code == 401


def test_profile_without_token(client):
    response = client.get("/auth/me")

    assert response.status_code == 401


def test_profile_with_invalid_token(client):
    response = client.get(
        "/auth/me",
        headers={
            "Authorization": "Bearer invalid.token.value"
        },
    )

    assert response.status_code == 401


def test_profile_with_valid_token(client):
    register_test_user(client)

    login_response = client.post(
        "/auth/login",
        json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD,
        },
    )

    assert login_response.status_code == 200

    token = login_response.json()["access_token"]

    response = client.get(
        "/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    assert response.json()["email"] == TEST_EMAIL


def test_profile_with_expired_token(client):
    registration_response = register_test_user(client)

    assert registration_response.status_code == 201

    user_id = registration_response.json()["id"]

    expired_token = jwt.encode(
        {
            "sub": user_id,
            "iat": datetime.now(timezone.utc)
            - timedelta(hours=2),
            "exp": datetime.now(timezone.utc)
            - timedelta(hours=1),
        },
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )

    response = client.get(
        "/auth/me",
        headers={
            "Authorization": f"Bearer {expired_token}"
        },
    )

    assert response.status_code == 401
