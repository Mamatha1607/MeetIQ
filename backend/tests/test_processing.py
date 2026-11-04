
import pytest
from sqlalchemy import select
from unittest.mock import Mock
from app.api import meeting as meeting_api
from app.ai.transcription.service import TranscriptionResult
from app.models.meeting import Meeting
from app.models.transcript import Transcript
from app.services import meeting_processing
import uuid

from app.worker.tasks import process_meeting_task
from app.models.meeting import MeetingStatus

from kombu.exceptions import OperationalError


def test_start_processing_uploaded_meeting(
    client,
    db_session,
    temporary_upload_dir,
    monkeypatch,
):
    """
    Verify that an uploaded meeting is queued for background
    processing without running Whisper inside the API.
    """

    # STEP 1: Create a meeting.
    create_response = client.post(
        "/meetings/",
        json={
            "title": "Async Processing Test",
            "description": "Testing Celery task submission",
        },
    )

    assert create_response.status_code == 201
    meeting_id = create_response.json()["id"]

    # STEP 2: Upload a recording.
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

    # STEP 3: Replace Celery's delay method with a mock.
    # No task will be sent to Redis during this test.
    mock_delay = Mock()

    monkeypatch.setattr(
        meeting_api.process_meeting_task,
        "delay",
        mock_delay,
    )

    # STEP 4: Request background processing.
    response = client.post(
        f"/meetings/{meeting_id}/process"
    )

    # The API accepts the job without waiting for Whisper.
    assert response.status_code == 202

    data = response.json()

    # STEP 5: Verify the meeting is marked PROCESSING.
    assert data["status"] == "processing"
    assert data["processing_started_at"] is not None
    assert data["processing_completed_at"] is None
    assert data["error_message"] is None

    # STEP 6: Verify Celery was called exactly once.
    mock_delay.assert_called_once_with(meeting_id)

    # STEP 7: Verify no transcript exists yet.
    # The worker has not executed because delay was mocked.
    statement = select(Transcript).where(
        Transcript.meeting_id == meeting_id
    )

    transcript = db_session.scalar(statement)

    assert transcript is None

def test_redis_failure_marks_meeting_failed(
    client,
    db_session,
    temporary_upload_dir,
    monkeypatch,
):
    """
    Verify that a Redis publishing failure returns HTTP 503
    and records the failure in PostgreSQL.
    """

    # STEP 1: Create a meeting.
    create_response = client.post(
        "/meetings/",
        json={
            "title": "Redis Failure Test",
            "description": "Testing queue connection failure",
        },
    )

    assert create_response.status_code == 201
    meeting_id = create_response.json()["id"]

    # STEP 2: Upload a recording.
    upload_response = client.post(
        f"/meetings/{meeting_id}/upload",
        files={
            "file": (
                "meeting.mp3",
                b"fake audio content",
                "audio/mpeg",
            )
        },
    )

    assert upload_response.status_code == 200

    # STEP 3: Simulate a Redis connection failure.
    def failing_delay(meeting_id):
        raise OperationalError("Redis connection unavailable")

    monkeypatch.setattr(
        meeting_api.process_meeting_task,
        "delay",
        failing_delay,
    )

    # STEP 4: Attempt to queue the meeting.
    response = client.post(
        f"/meetings/{meeting_id}/process"
    )

    # The API should report a temporary service failure.
    assert response.status_code == 503
    assert response.json() == {
        "detail": "Background processing is temporarily unavailable"
    }

    # STEP 5: Verify the database state.
    meeting = db_session.get(Meeting, meeting_id)
    db_session.refresh(meeting)

    assert meeting.status.value == "failed"
    assert meeting.processing_completed_at is not None
    assert meeting.error_message == "Unable to queue meeting processing"

    # STEP 6: No transcript should exist.
    statement = select(Transcript).where(
        Transcript.meeting_id == meeting_id
    )

    assert db_session.scalar(statement) is None


def test_duplicate_processing_request(
    client,
    temporary_upload_dir,
    monkeypatch,
):
    """
    Verify that the same meeting cannot be queued twice.
    """

    # STEP 1: Create a meeting.
    create_response = client.post(
        "/meetings/",
        json={
            "title": "Duplicate Processing Test",
            "description": "Testing duplicate Celery submissions",
        },
    )

    assert create_response.status_code == 201
    meeting_id = create_response.json()["id"]

    # STEP 2: Upload a recording.
    upload_response = client.post(
        f"/meetings/{meeting_id}/upload",
        files={
            "file": (
                "meeting.mp3",
                b"fake audio content",
                "audio/mpeg",
            )
        },
    )

    assert upload_response.status_code == 200

    # STEP 3: Mock Celery so no real task is submitted.
    mock_delay = Mock()

    monkeypatch.setattr(
        meeting_api.process_meeting_task,
        "delay",
        mock_delay,
    )

    # STEP 4: First processing request.
    first_response = client.post(
        f"/meetings/{meeting_id}/process"
    )

    assert first_response.status_code == 202

    # STEP 5: Attempt to process the same meeting again.
    second_response = client.post(
        f"/meetings/{meeting_id}/process"
    )

    # The meeting is already PROCESSING.
    assert second_response.status_code == 409

    assert second_response.json() == {
        "detail": "Meeting must be uploaded before processing"
    }

    # STEP 6: Verify only one task was submitted.
    mock_delay.assert_called_once_with(meeting_id)


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
    Verify that a Whisper failure inside the Celery worker
    marks the meeting FAILED and saves the error.
    """

    # STEP 1: Create a meeting.
    create_response = client.post(
        "/meetings/",
        json={
            "title": "Whisper Failure Test",
            "description": "Testing worker failure handling",
        },
    )

    assert create_response.status_code == 201
    meeting_id = create_response.json()["id"]

    # STEP 2: Upload a fake recording.
    upload_response = client.post(
        f"/meetings/{meeting_id}/upload",
        files={
            "file": (
                "meeting.mp3",
                b"fake audio content",
                "audio/mpeg",
            )
        },
    )

    assert upload_response.status_code == 200

    # STEP 3: Mock task submission.
    # This lets FastAPI update the status without using Redis.
    mock_delay = Mock()

    monkeypatch.setattr(
        meeting_api.process_meeting_task,
        "delay",
        mock_delay,
    )

    response = client.post(
        f"/meetings/{meeting_id}/process"
    )

    assert response.status_code == 202

    # STEP 4: Simulate Whisper failing.
    def failing_transcription(file_path):
        raise RuntimeError("Transcription failed")

    monkeypatch.setattr(
        meeting_processing,
        "transcribe_audio",
        failing_transcription,
    )

    # STEP 5: Execute the processing service using the test DB.
    # We call the service directly to avoid Celery opening
    # a separate session connected to the development database.
    meeting = db_session.get(Meeting, uuid.UUID(meeting_id))
    db_session.refresh(meeting)

    assert meeting.status == MeetingStatus.PROCESSING

    with pytest.raises(RuntimeError, match="Transcription failed"):
        meeting_processing.process_meeting(
            meeting=meeting,
            db=db_session,
        )

    # STEP 6: Refresh the meeting to verify persisted changes.
    db_session.refresh(meeting)

    assert meeting.status == MeetingStatus.FAILED
    assert meeting.processing_completed_at is not None
    assert meeting.error_message == "Transcription failed"

    # STEP 7: Verify no transcript was saved.
    statement = select(Transcript).where(
        Transcript.meeting_id == uuid.UUID(meeting_id)
    )

    assert db_session.scalar(statement) is None
