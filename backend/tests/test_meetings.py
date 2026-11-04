"""
Tests meeting API endpoints.
"""


def test_create_meeting(client):
    payload = {
        "title": "Weekly Engineering Sync",
        "description": "Backend planning meeting",
    }

    response = client.post(
        "/meetings/",
        json=payload,
    )

    assert response.status_code == 201

    data = response.json()

    assert data["title"] == "Weekly Engineering Sync"
    assert data["description"] == "Backend planning meeting"
    assert data["status"] == "created"

    assert "id" in data
    assert "created_at" in data
    assert "updated_at" in data


def test_list_meetings(client):
    payload = {
        "title": "Sprint Planning",
        "description": "Weekly sprint planning meeting",
    }

    create_response = client.post(
        "/meetings/",
        json=payload,
    )

    assert create_response.status_code == 201

    response = client.get("/meetings/")

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 1
    assert data[0]["title"] == "Sprint Planning"
    assert data[0]["description"] == "Weekly sprint planning meeting"
    assert data[0]["status"] == "created"


def test_get_meeting_by_id(client):
    payload = {
        "title": "Architecture Review",
        "description": "Backend design discussion",
    }

    create_response = client.post(
        "/meetings/",
        json=payload,
    )

    assert create_response.status_code == 201

    created_meeting = create_response.json()
    meeting_id = created_meeting["id"]

    response = client.get(f"/meetings/{meeting_id}")

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == meeting_id
    assert data["title"] == "Architecture Review"
    assert data["description"] == "Backend design discussion"
    assert data["status"] == "created"


def test_get_nonexistent_meeting_returns_404(client):
    missing_meeting_id = "11111111-1111-1111-1111-111111111111"

    response = client.get(
        f"/meetings/{missing_meeting_id}"
    )

    assert response.status_code == 404
    assert response.json() == {
        "detail": "Meeting Notfound"
    }