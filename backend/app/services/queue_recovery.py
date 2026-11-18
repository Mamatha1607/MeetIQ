
"""Recover meetings stuck in the Celery queue."""

from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.meeting import Meeting, MeetingStatus
from app.worker.celery_app import celery_app


QUEUE_TIMEOUT_MINUTES = 5
MAX_RECOVERY_ATTEMPTS = 3



def recover_queued_meetings(db: Session) -> dict:
    recovered = 0
    failed = 0

    while True:
        now = datetime.now(timezone.utc)
        cutoff = now - timedelta(minutes=QUEUE_TIMEOUT_MINUTES)

        meeting = db.scalar(
            select(Meeting)
            .where(
                Meeting.status == MeetingStatus.QUEUED,
                Meeting.queued_at.is_not(None),
                Meeting.queued_at < cutoff,
            )
            .order_by(Meeting.queued_at)
            .with_for_update(skip_locked=True)
            .limit(1)
        )

        if meeting is None:
            db.rollback()
            break

        meeting_id = str(meeting.id)

        if meeting.retry_count >= MAX_RECOVERY_ATTEMPTS:
            meeting.status = MeetingStatus.FAILED
            meeting.error_message = "Queue recovery attempts exhausted"
            meeting.processing_completed_at = now
            db.commit()
            failed += 1
            continue

        meeting.retry_count += 1
        meeting.queued_at = now
        db.commit()

        try:
            celery_app.send_task(
                "meetiq.process_meeting",
                args=[meeting_id],
            )
            recovered += 1

        except Exception:
            db.rollback()

            import logging
            logging.getLogger(__name__).exception(
                "Failed to resubmit meeting %s",
                meeting_id,
            )

            # Stop this scan if the broker is unavailable.
            break

    return {
        "recovered": recovered,
        "failed": failed,
    }
