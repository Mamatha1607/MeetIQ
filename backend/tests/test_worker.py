
import uuid
from unittest.mock import Mock

from sqlalchemy import select

from app.api import meeting as meeting_api
from app.models.meeting import Meeting, MeetingStatus
from app.models.transcript import Transcript
from app.services import meeting_processing
from app.worker import tasks as worker_tasks




def test_duplicate_worker_task_skips_transcription(
    authenticated_client,
    db_session,
    temporary_upload_dir,
    monkeypatch,
    test_session_factory,
):
    """
    Running the same Celery task twice should
    transcribe the recording only once.
    """

    # STEP 1: Create a meeting.
    create_response = authenticated_client.post(
        "/meetings/",
        json={
            "title": "Worker Idempotency Test",
            "description": "Testing duplicate task execution",
        },
    )

    assert create_response.status_code == 201
    meeting_id = create_response.json()["id"]

    # STEP 2: Upload a fake recording.
    upload_response = authenticated_client.post(
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

    # STEP 3: Mock Celery submission.
    monkeypatch.setattr(
        meeting_api.process_meeting_task,
        "delay",
        Mock(),
    )

    # FastAPI transitions UPLOADED -> QUEUED.
    process_response = authenticated_client.post(
        f"/meetings/{meeting_id}/process"
    )

    assert process_response.status_code == 202
    assert process_response.json()["status"] == "queued"

    # STEP 4: Ensure the worker uses the test database.
    monkeypatch.setattr(
    worker_tasks,
    "SessionLocal",
    test_session_factory,
)

    # STEP 5: Mock Whisper and count its executions.
    transcription_mock = Mock()

    transcription_mock.return_value.text = (
        "This meeting was transcribed once."
    )
    transcription_mock.return_value.language = "en"

    monkeypatch.setattr(
        meeting_processing,
        "transcribe_audio",
        transcription_mock,
    )

    # STEP 6: Execute the worker task twice.
    first_result = worker_tasks.process_meeting_task.run(
        meeting_id
    )

    second_result = worker_tasks.process_meeting_task.run(
        meeting_id
    )

    # STEP 7: Verify the first task completed.
    assert first_result["status"] == "completed"
    assert first_result["skipped"] is False

    # The second task should skip processing.
    assert second_result["status"] == "completed"
    assert second_result["skipped"] is True

    # Whisper must run only once.
    transcription_mock.assert_called_once()

    # STEP 8: Verify the database.
    meeting_uuid = uuid.UUID(meeting_id)

    db_session.expire_all()

    meeting = db_session.get(Meeting, meeting_uuid)

    assert meeting.status == MeetingStatus.COMPLETED

    transcripts = db_session.scalars(
        select(Transcript).where(
            Transcript.meeting_id == meeting_uuid
        )
    ).all()

    assert len(transcripts) == 1
    assert transcripts[0].text == (
        "This meeting was transcribed once."
    )
