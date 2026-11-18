
import uuid
from datetime import datetime, timezone

from sqlalchemy import update
import threading
import app.models

from app.services.meeting_recovery import run_heartbeat

from app.worker.celery_app import celery_app
from app.db.session import SessionLocal
from app.models.meeting import Meeting, MeetingStatus
from app.services.meeting_processing import process_meeting


@celery_app.task(name="meetiq.process_meeting")
def process_meeting_task(meeting_id: str):
    """
    Atomically claim a queued meeting before transcription.
    """

    meeting_uuid = uuid.UUID(meeting_id)
    # Generate a unique ID for this processing attempt.
    attempt_id = uuid.uuid4()

    with SessionLocal() as db:
        now = datetime.now(timezone.utc)

        # STEP 1: Atomically claim the meeting.
        statement = (
            update(Meeting)
            .where(
                Meeting.id == meeting_uuid,
                Meeting.status == MeetingStatus.QUEUED,
            )
            .values(
                status=MeetingStatus.PROCESSING,
                processing_started_at=now,
                last_heartbeat_at=now,
                processing_attempt_id=attempt_id,
            )
        )

        try:
            result = db.execute(statement)
            claimed = result.rowcount == 1
            db.commit()
        except Exception:
            db.rollback()
            raise

        # STEP 2: Skip duplicate tasks.
        if not claimed:
            meeting = db.get(Meeting, meeting_uuid)

            if meeting is None:
                raise ValueError(
                    f"Meeting {meeting_id} not found"
                )

            return {
                "meeting_id": meeting_id,
                "status": meeting.status.value,
                "skipped": True,
            }

        # STEP 3: Retrieve the claimed meeting.
        meeting = db.get(Meeting, meeting_uuid)

        stop_event = threading.Event()

        heartbeat_thread = threading.Thread(
            target=run_heartbeat,
            kwargs={
                "meeting_id": meeting_uuid,
                "attempt_id": attempt_id,
                "session_factory": SessionLocal,
                "stop_event": stop_event,
                "interval_seconds": 30,
            },
            daemon=True,
        )

        heartbeat_thread.start()

        try:
            process_meeting(
            meeting=meeting,
            db=db,
            attempt_id=attempt_id,
        )
        finally:
            stop_event.set()
            heartbeat_thread.join(timeout=5)
    return {
            "meeting_id": meeting_id,
            "status": "completed",
            "skipped": False,
        }
@celery_app.task(name="meetiq.recover_queued")
def recover_queued_task():
    from app.services.queue_recovery import recover_queued_meetings

    with SessionLocal() as db:
        return recover_queued_meetings(db)