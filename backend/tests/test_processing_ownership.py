import uuid
from datetime import datetime, timezone
from unittest.mock import Mock

import pytest
from sqlalchemy import select

from app.models.meeting import Meeting, MeetingStatus
from app.models.meeting_file import MeetingFile
from app.models.transcript import Transcript
from app.services import meeting_processing
def test_outdated_worker_cannot_save_transcript(
    client,
    db_session,
    monkeypatch,
):
    old_attempt_id = uuid.uuid4()
    new_attempt_id = uuid.uuid4()

    meeting = Meeting(
        title="Ownership Protection Test",
        status=MeetingStatus.PROCESSING,
        processing_attempt_id=old_attempt_id,
        processing_started_at=datetime.now(timezone.utc),
        last_heartbeat_at=datetime.now(timezone.utc),
    )

    db_session.add(meeting)
    db_session.flush()

    meeting_file = MeetingFile(
        meeting_id=meeting.id,
        original_filename="meeting.mp3",
        storage_path="fake/meeting.mp3",
        content_type="audio/mpeg",
        size_bytes=100,
    )

    db_session.add(meeting_file)
    db_session.commit()

    def fake_transcription(file_path):
        # Simulate recovery assigning the meeting to a new worker.
        with db_session.bind.connect() as connection:
            connection.execute(
                Meeting.__table__.update()
                .where(Meeting.id == meeting.id)
                .values(processing_attempt_id=new_attempt_id)
            )
            connection.commit()

        return Mock(text="Old worker transcript", language="en")

    monkeypatch.setattr(
        meeting_processing,
        "transcribe_audio",
        fake_transcription,
    )

    with pytest.raises(
        RuntimeError,
        match="Processing attempt no longer owns this meeting",
    ):
        meeting_processing.process_meeting(
            meeting=meeting,
            db=db_session,
            attempt_id=old_attempt_id,
        )

    db_session.expire_all()

    updated_meeting = db_session.get(Meeting, meeting.id)

    assert updated_meeting.status == MeetingStatus.PROCESSING
    assert updated_meeting.processing_attempt_id == new_attempt_id

    transcript = db_session.scalar(
        select(Transcript).where(
            Transcript.meeting_id == meeting.id
        )
    )

    assert transcript is None