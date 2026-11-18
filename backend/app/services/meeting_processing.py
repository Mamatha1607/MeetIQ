
"""
Meeting processing service.

Responsibilities:
1. Validate the meeting status.
2. Retrieve the uploaded recording.
3. Call Whisper to generate a transcript.
4. Save the transcript in PostgreSQL.
5. Update meeting processing status.
6. Handle processing failures.
"""

from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.ai.transcription.service import transcribe_audio
from app.models.meeting import Meeting, MeetingStatus
from app.models.meeting_file import MeetingFile
from app.models.transcript import Transcript
import uuid
from sqlalchemy import select, update
from app.ai.summarization.service import generate_meeting_insights
from app.models.meeting_insight import MeetingInsight

def process_meeting(
    meeting: Meeting,
    db: Session,
    attempt_id: uuid.UUID,
) -> Meeting:
    """
    Process an uploaded meeting and manage its lifecycle.
    """

    # STEP 1: Validate meeting status.
    # Only meetings already marked PROCESSING can be handled by the worker.
    if meeting.status != MeetingStatus.PROCESSING:
        raise ValueError("Meeting must be queued before processing")
    print(
        f"[Processing] Meeting {meeting.id} started.",
        flush=True,
    )

    try:
        # STEP 3: Retrieve the uploaded recording.
        statement = select(MeetingFile).where(
            MeetingFile.meeting_id == meeting.id
        )

        meeting_file = db.scalar(statement)

        # Stop processing if no recording is found.
        if meeting_file is None:
            raise ValueError(
                "Meeting recording not found"
            )

        # Convert the stored file path into a Path object.
        file_path = Path(meeting_file.storage_path)
        # Finish the database read transaction before transcription.
        db.commit()

        print(
            f"[Processing] Recording found: {file_path.name}",
            flush=True,
        )

        # STEP 4: Call the Whisper transcription service.
        print(
            "DEBUG: PROCESSING SERVICE CALLING WHISPER",
            flush=True,
        )

        transcription_result = transcribe_audio(file_path)

        print(
            "[Processing] Whisper transcription completed.",
            flush=True,
        )
        # Generate structured meeting insights using Ollama.
        print("[Processing] Generating AI insights...", flush=True)

        insights_result = generate_meeting_insights(
            transcription_result.text
        )

        print("[Processing] AI insights generated.", flush=True)

        # STEP 5: Save the generated transcript.
        transcript = Transcript(
            meeting_id=meeting.id,
            text=transcription_result.text,
            language=transcription_result.language,
        )
        meeting_insight = MeetingInsight(
            meeting_id=meeting.id,
            summary=insights_result.summary,
            key_points=insights_result.key_points,
            decisions=insights_result.decisions,
            action_items=[
                item.model_dump()
                for item in insights_result.action_items
            ],
        )
        # Atomically verify ownership and mark the meeting completed.
        statement = (
            update(Meeting)
            .where(
                Meeting.id == meeting.id,
                Meeting.status == MeetingStatus.PROCESSING,
                Meeting.processing_attempt_id == attempt_id,
            )
            .values(
                status=MeetingStatus.COMPLETED,
                processing_completed_at=datetime.now(timezone.utc),
            )
            .execution_options(synchronize_session=False)
        )

        result = db.execute(statement)

        if result.rowcount != 1:
            db.rollback()
            raise RuntimeError(
                "Processing attempt no longer owns this meeting"
            )

        # Save transcript in the same transaction as the status update.
        db.add(transcript)
        db.add(meeting_insight)
        db.commit()
        db.refresh(meeting)

        print(
            f"[Processing] Meeting {meeting.id} completed.",
            flush=True,
        )

        return meeting

    except Exception as exc:
        db.rollback()
        if isinstance(exc, RuntimeError) and str(exc) == (
            "Processing attempt no longer owns this meeting"
        ):
            raise

        # Only the current processing attempt can mark the meeting FAILED.
        statement = (
            update(Meeting)
            .where(
                Meeting.id == meeting.id,
                Meeting.status == MeetingStatus.PROCESSING,
                Meeting.processing_attempt_id == attempt_id,
            )
            .values(
                status=MeetingStatus.FAILED,
                processing_completed_at=datetime.now(timezone.utc),
                error_message=str(exc),
            )
            .execution_options(synchronize_session=False)
        )

        result = db.execute(statement)

        if result.rowcount == 1:
            db.commit()
        else:
            # Ownership was lost; do not modify the meeting.
            db.rollback()

        raise
