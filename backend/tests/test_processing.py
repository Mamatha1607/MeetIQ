
import pytest
from sqlalchemy import select

from app.ai.transcription.service import TranscriptionResult
from app.models.meeting import Meeting
from app.models.transcript import Transcript
from app.services import meeting_processing


def test_start_processing_uploaded_meeting(
    client,
    db_session,
    temporary_upload_dir,
    monkeypatch,
):
    """
    Verify that an uploaded meeting can be processed successfully
    and that the generated transcript is stored in PostgreSQL.
    """

    # Step 1: Create a meeting.
    create_response = client.post(
        "/meetings/",
        json={
            "title": "Processing Test",
            "description": "Meeting used to test processing",
        },
    )

    assert create_response.status_code == 201

    meeting_id = create_response.json()["id"]

    # Step 2: Upload a recording.
    # Fake audio bytes are sufficient because Whisper will be mocked.
    files = {
        "file": (
            "meeting.mp3",
            b"fake audio content",
            "audio/mpeg",
        )
    }

    upload_response = client.post(
        f"/meetings/{meeting_id}/upload",
        files=files,
    )

    assert upload_response.status_code == 200

    # Step 3: Mock the Whisper transcription function.
    # This prevents the test from loading a real AI model.
    def fake_transcription(file_path):
        return TranscriptionResult(
            text="This is a test meeting transcript.",
            language="en",
        )

    # Replace the transcription function used by the processing service.
    # monkeypatch automatically restores the original after this test.
    monkeypatch.setattr(
        meeting_processing,
        "transcribe_audio",
        fake_transcription,
    )

    # Step 4: Process the uploaded meeting.
    process_response = client.post(
        f"/meetings/{meeting_id}/process"
    )

    assert process_response.status_code == 200

    data = process_response.json()

    # Step 5: Verify the meeting processing lifecycle.
    # Our current implementation processes synchronously.
    assert data["status"] == "completed"

    # Processing start and completion timestamps must be recorded.
    assert data["processing_started_at"] is not None
    assert data["processing_completed_at"] is not None

    # Successful processing should not contain an error.
    assert data["error_message"] is None

    # Step 6: Retrieve the transcript directly from the test database.
    statement = select(Transcript).where(
        Transcript.meeting_id == meeting_id
    )

    transcript = db_session.scalar(statement)

    # A transcript should exist after successful processing.
    assert transcript is not None

    # Verify that the mocked Whisper output was saved correctly.
    assert transcript.text == "This is a test meeting transcript."
    assert transcript.language == "en"


def test_created_meeting_cannot_start_processing(client):
    """
    Verify that a meeting without an uploaded recording
    cannot start processing.
    """

    # Step 1: Create a meeting without uploading a file.
    create_response = client.post(
        "/meetings/",
        json={
            "title": "Invalid Processing Test",
            "description": "Meeting has no recording yet",
        },
    )

    assert create_response.status_code == 201

    meeting_id = create_response.json()["id"]

    # Step 2: Attempt to process the meeting.
    response = client.post(
        f"/meetings/{meeting_id}/process"
    )

    # Processing should be rejected because the meeting is CREATED.
    assert response.status_code == 409

    assert response.json() == {
        "detail": "Meeting must be uploaded before processing"
    }


def test_nonexistent_meeting_cannot_start_processing(client):
    """
    Verify that processing a nonexistent meeting returns HTTP 404.
    """

    # Use a valid UUID that does not belong to any meeting.
    missing_meeting_id = "11111111-1111-1111-1111-111111111111"

    # Attempt to process a meeting that does not exist.
    response = client.post(
        f"/meetings/{missing_meeting_id}/process"
    )

    # The API should return HTTP 404.
    assert response.status_code == 404

    assert response.json() == {
        "detail": "Meeting is not found"
    }


def test_processing_failure_marks_meeting_failed(
    client,
    db_session,
    temporary_upload_dir,
    monkeypatch,
):
    """
    Verify that a transcription failure updates the meeting
    status to FAILED and stores the error message.
    """

    # Step 1: Create a meeting.
    create_response = client.post(
        "/meetings/",
        json={
            "title": "Failure Test",
            "description": "Testing transcription failure handling",
        },
    )

    assert create_response.status_code == 201

    meeting_id = create_response.json()["id"]

    # Step 2: Upload a recording.
    files = {
        "file": (
            "meeting.mp3",
            b"fake audio content",
            "audio/mpeg",
        )
    }

    upload_response = client.post(
        f"/meetings/{meeting_id}/upload",
        files=files,
    )

    assert upload_response.status_code == 200

    # Step 3: Mock Whisper to simulate a transcription failure.
    def failing_transcription(file_path):
        raise RuntimeError("Transcription failed")

    monkeypatch.setattr(
        meeting_processing,
        "transcribe_audio",
        failing_transcription,
    )
    
# Step 4: Attempt processing.
# The API should catch the internal transcription error
# and return a safe HTTP 500 response.
    response = client.post(
        f"/meetings/{meeting_id}/process"
    )

    # Verify the HTTP response.
    assert response.status_code == 500

    # Internal error details should not be exposed to API clients.
    assert response.json() == {
        "detail": "Meeting processing failed"
    }

    # Step 5: Retrieve the meeting directly from the test database.
    meeting = db_session.get(Meeting, meeting_id)

    assert meeting is not None

    db_session.refresh(meeting)

    # Processing failure should transition the meeting to FAILED.
    assert meeting.status.value == "failed"

    # Verify that failure information was persisted.
    assert meeting.processing_completed_at is not None
    assert meeting.error_message == "Transcription failed"

    # Step 6: Verify that no transcript was saved after the failure.
    statement = select(Transcript).where(
        Transcript.meeting_id == meeting_id
    )

    transcript = db_session.scalar(statement)

    assert transcript is None
