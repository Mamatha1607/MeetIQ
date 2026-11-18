from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session
import threading

import uuid
from sqlalchemy import update

from app.models.meeting import Meeting, MeetingStatus

def find_stale_meetings(
    db: Session,
    timeout_minutes: int = 60,
) -> list[Meeting]:

    if timeout_minutes <= 0:
        raise ValueError("timeout_minutes must be positive")

    cutoff_time = datetime.now(timezone.utc) - timedelta(
        minutes=timeout_minutes
    )

    statement = (
        select(Meeting)
        .where(
            Meeting.status == MeetingStatus.PROCESSING,
            Meeting.last_heartbeat_at < cutoff_time
        )
    )

    return list(db.scalars(statement).all())

def update_meeting_heartbeat(
    db: Session,
    meeting_id: uuid.UUID,
     attempt_id: uuid.UUID,
) -> bool:
    """
    Update heartbeat only if this worker still owns the meeting.
    """
    statement = (
        update(Meeting)
        .where(
            Meeting.id == meeting_id,
            Meeting.status == MeetingStatus.PROCESSING,
            Meeting.processing_attempt_id == attempt_id,
        )
        .values(
            last_heartbeat_at=datetime.now(timezone.utc)
        )
    )

    result = db.execute(statement)
    db.commit()

    return result.rowcount == 1
def run_heartbeat(
    meeting_id: uuid.UUID,
    attempt_id: uuid.UUID,
    session_factory,
    stop_event: threading.Event,
    interval_seconds: int = 30,
) -> None:

    if interval_seconds <= 0:
        raise ValueError("interval_seconds must be positive")

    print("[Heartbeat] Thread started")

    while not stop_event.wait(interval_seconds):
        print("[Heartbeat] Attempting database update")

        try:
            with session_factory() as db:
                updated = update_meeting_heartbeat(
                    db=db,
                    meeting_id=meeting_id,
                    attempt_id=attempt_id,
                )

            print(f"[Heartbeat] Updated: {updated}")

            if not updated:
                break

        except Exception as exc:
            print(f"[Heartbeat] Error: {exc}")

    print("[Heartbeat] Thread stopped")