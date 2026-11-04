def test_upload_meeting_file(client, temporary_upload_dir):
    # First create a meeting.
    create_response = client.post(
        "/meetings/",
        json={
            "title": "Upload Test",
            "description": "Testing recording upload",
        },
    )

    assert create_response.status_code == 201

    meeting = create_response.json()
    meeting_id = meeting["id"]

    # Simulate a multipart file upload.
    files = {
        "file": (
            "meeting.mp3",
            b"fake audio content",
            "audio/mpeg",
        )
    }

    response = client.post(
        f"/meetings/{meeting_id}/upload",
        files=files,
    )

    assert response.status_code == 200

    data = response.json()

    assert data["message"] == "File uploaded successfully"
    assert data["meeting_id"] == meeting_id
    assert data["filename"] == "meeting.mp3"
    assert data["status"] == "uploaded"


def test_duplicate_upload_returns_409(client, temporary_upload_dir):
    create_response = client.post(
        "/meetings/",
        json={
            "title": "Duplicate Upload Test",
            "description": "Testing duplicate upload handling",
        },
    )

    assert create_response.status_code == 201

    meeting_id = create_response.json()["id"]

    files = {
        "file": (
            "meeting.mp3",
            b"first fake audio content",
            "audio/mpeg",
        )
    }

    first_response = client.post(
        f"/meetings/{meeting_id}/upload",
        files=files,
    )

    assert first_response.status_code == 200

    second_files = {
        "file": (
            "meeting2.mp3",
            b"second fake audio content",
            "audio/mpeg",
        )
    }

    second_response = client.post(
        f"/meetings/{meeting_id}/upload",
        files=second_files,
    )

    assert second_response.status_code == 409
    assert second_response.json() == {
        "detail": "duplicate upload"
    }
    saved_files = list(temporary_upload_dir.iterdir())

    # Only the first successful upload should remain; the rejected duplicate file should be deleted.
    assert len(saved_files) == 1


def test_unsupported_file_type_returns_415(client, temporary_upload_dir):
    # Create a valid meeting first.
    create_response = client.post(
        "/meetings/",
        json={
            "title": "Invalid File Test",
            "description": "Testing unsupported file types",
        },
    )

    assert create_response.status_code == 201

    meeting_id = create_response.json()["id"]

    # Simulate uploading a text file instead of audio/video.
    files = {
        "file": (
            "notes.txt",
            b"this is not a meeting recording",
            "text/plain",
        )
    }

    response = client.post(
        f"/meetings/{meeting_id}/upload",
        files=files,
    )

    assert response.status_code == 415
    assert response.json() == {
        "detail": "File type not allowed"
    }

    # Rejected files should never be written to storage.
    assert len(list(temporary_upload_dir.iterdir())) == 0


def test_upload_to_nonexistent_meeting_returns_404(
    client,
    temporary_upload_dir,
):
    missing_meeting_id = "11111111-1111-1111-1111-111111111111"

    files = {
        "file": (
            "meeting.mp3",
            b"fake audio content",
            "audio/mpeg",
        )
    }

    response = client.post(
        f"/meetings/{missing_meeting_id}/upload",
        files=files,
    )

    assert response.status_code == 404
    assert response.json() == {
        "detail": "No meeting found"
    }

    # Nothing should be stored when the meeting does not exist.
    assert len(list(temporary_upload_dir.iterdir())) == 0