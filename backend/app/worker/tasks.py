import uuid

from app.worker.celery_app import celery_app
from app.db.session import SessionLocal
from app.models.meeting import Meeting
from app.services.meeting_processing import process_meeting


@celery_app.task(name="meetiq.process_meeting")
def process_meeting_task(meeting_id: str):
    """
    Background task that transcribes an uploaded meeting.

    Each Celery task creates its own database session.
    """

    # Convert the string back into a UUID.
    meeting_uuid = uuid.UUID(meeting_id)

    # Create an independent database session for the worker.
    with SessionLocal() as db:

        # Retrieve the meeting from PostgreSQL.
        meeting = db.get(Meeting, meeting_uuid)

        if meeting is None:
            raise ValueError(f"Meeting {meeting_id} not found")

        # Reuse our existing Whisper processing service.
        process_meeting(meeting=meeting, db=db)

    return {"meeting_id": meeting_id, "status": "COMPLETED"}