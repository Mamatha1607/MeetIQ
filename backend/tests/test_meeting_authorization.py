
"""
Tests JWT authentication and meeting-level authorization.

Ensures users can access their own meetings but cannot
access or modify meetings belonging to another user.
"""

import uuid

import pytest

from app.core.jwt import create_access_token
from app.core.security import hash_password
from app.models.user import User


@pytest.fixture
def two_users(authenticated_client, db_session):
    """
    Create a second user and return separate JWTs for User A
    and User B. The authenticated client belongs to User A.
    """
    user_b = User(
        email=f"userb-{uuid.uuid4().hex}@meetiq.com",
        hashed_password=hash_password("TestPassword123!"),
        is_active=True,
    )

    db_session.add(user_b)
    db_session.commit()
    db_session.refresh(user_b)

    token_b = create_access_token(user_b.id)

    return {
        "client": authenticated_client,
        "user_b_headers": {
            "Authorization": f"Bearer {token_b}"
        },
    }


@pytest.fixture
def private_meeting(two_users):
    """
    Create a meeting owned by User A.
    """
    client = two_users["client"]

    response = client.post(
        "/meetings/",
        json={
            "title": "Private Engineering Meeting",
            "description": "Confidential planning discussion",
        },
    )

    assert response.status_code == 201

    return response.json()["id"]


# --------------------------------------------------
# 1. User A can access their own meeting
# --------------------------------------------------

def test_owner_can_access_meeting(two_users, private_meeting):
    response = two_users["client"].get(
        f"/meetings/{private_meeting}"
    )

    assert response.status_code == 200
    assert response.json()["id"] == private_meeting


# --------------------------------------------------
# 2. User B cannot retrieve User A's meeting
# --------------------------------------------------

def test_other_user_cannot_get_meeting(two_users, private_meeting):
    response = two_users["client"].get(
        f"/meetings/{private_meeting}",
        headers=two_users["user_b_headers"],
    )

    assert response.status_code == 404
    assert response.json() == {
        "detail": "Meeting not found"
    }


# --------------------------------------------------
# 3. User B cannot see User A's meeting in the list
# --------------------------------------------------

def test_other_user_cannot_list_private_meeting(
    two_users,
    private_meeting,
):
    response = two_users["client"].get(
        "/meetings/",
        headers=two_users["user_b_headers"],
    )

    assert response.status_code == 200

    meeting_ids = {
        meeting["id"] for meeting in response.json()
    }

    assert private_meeting not in meeting_ids


# --------------------------------------------------
# 4. User B cannot update User A's meeting
# --------------------------------------------------

def test_other_user_cannot_update_meeting(
    two_users,
    private_meeting,
):
    response = two_users["client"].patch(
        f"/meetings/{private_meeting}",
        json={"title": "Unauthorized Update"},
        headers=two_users["user_b_headers"],
    )

    assert response.status_code == 404

    owner_response = two_users["client"].get(
        f"/meetings/{private_meeting}"
    )

    assert owner_response.status_code == 200
    assert owner_response.json()["title"] == (
        "Private Engineering Meeting"
    )


# --------------------------------------------------
# 5. User B cannot delete User A's meeting
# --------------------------------------------------

def test_other_user_cannot_delete_meeting(
    two_users,
    private_meeting,
):
    response = two_users["client"].delete(
        f"/meetings/{private_meeting}",
        headers=two_users["user_b_headers"],
    )

    assert response.status_code == 404

    # Confirm the meeting still exists for its owner.
    owner_response = two_users["client"].get(
        f"/meetings/{private_meeting}"
    )

    assert owner_response.status_code == 200


# --------------------------------------------------
# 6. User B cannot upload to User A's meeting
# --------------------------------------------------

def test_other_user_cannot_upload_file(
    two_users,
    private_meeting,
    temporary_upload_dir,
):
    response = two_users["client"].post(
        f"/meetings/{private_meeting}/upload",
        files={
            "file": (
                "meeting.mp3",
                b"fake audio content",
                "audio/mpeg",
            )
        },
        headers=two_users["user_b_headers"],
    )

    assert response.status_code == 404

    # Unauthorized uploads must not leave stored files.
    assert list(temporary_upload_dir.iterdir()) == []


# --------------------------------------------------
# 7. User B cannot start processing User A's meeting
# --------------------------------------------------

def test_other_user_cannot_process_meeting(
    two_users,
    private_meeting,
    monkeypatch,
):
    from unittest.mock import Mock
    from app.api import meeting as meeting_api

    mock_delay = Mock()

    monkeypatch.setattr(
        meeting_api.process_meeting_task,
        "delay",
        mock_delay,
    )

    response = two_users["client"].post(
        f"/meetings/{private_meeting}/process",
        headers=two_users["user_b_headers"],
    )

    assert response.status_code == 404

    # Unauthorized requests must not enqueue Celery tasks.
    mock_delay.assert_not_called()


# --------------------------------------------------
# 8. User B cannot access User A's transcript
# --------------------------------------------------

def test_other_user_cannot_get_transcript(
    two_users,
    private_meeting,
):
    response = two_users["client"].get(
        f"/meetings/{private_meeting}/transcript",
        headers=two_users["user_b_headers"],
    )

    assert response.status_code == 404


# --------------------------------------------------
# 9. User B cannot access User A's AI insights
# --------------------------------------------------

def test_other_user_cannot_get_insights(
    two_users,
    private_meeting,
):
    response = two_users["client"].get(
        f"/meetings/{private_meeting}/insights",
        headers=two_users["user_b_headers"],
    )

    assert response.status_code == 404


# --------------------------------------------------
# 10. Requests without JWT must be rejected
# --------------------------------------------------

@pytest.mark.parametrize(
    "method,path",
    [
        ("GET", "/meetings/"),
        ("POST", "/meetings/"),
        ("GET", "/meetings/{meeting_id}"),
        ("PATCH", "/meetings/{meeting_id}"),
        ("DELETE", "/meetings/{meeting_id}"),
        ("POST", "/meetings/{meeting_id}/upload"),
        ("POST", "/meetings/{meeting_id}/process"),
        ("GET", "/meetings/{meeting_id}/transcript"),
        ("GET", "/meetings/{meeting_id}/insights"),
    ],
)
def test_meeting_endpoints_require_authentication(
    client,
    method,
    path,
):
    path = path.format(meeting_id=uuid.uuid4())

    response = client.request(
        method,
        path,
    )

    assert response.status_code == 401
