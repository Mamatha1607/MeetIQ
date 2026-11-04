
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


def process_meeting(
    meeting: Meeting,
    db: Session,
) -> Meeting:
    """
    Process an uploaded meeting and manage its lifecycle.
    """

    # STEP 1: Validate meeting status.
    # Only uploaded meetings can start processing.
    if meeting.status != MeetingStatus.UPLOADED:
        raise ValueError(
            "Meeting must be uploaded before processing"
        )

    # STEP 2: Mark the meeting as PROCESSING.
    meeting.status = MeetingStatus.PROCESSING

    # Record when processing started.
    meeting.processing_started_at = datetime.now(timezone.utc)

    # Clear any previous error.
    meeting.error_message = None

    # Save the PROCESSING state before transcription begins.
    db.commit()
    db.refresh(meeting)

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

        # STEP 5: Save the generated transcript.
        transcript = Transcript(
            meeting_id=meeting.id,
            text=transcription_result.text,
            language=transcription_result.language,
        )

        db.add(transcript)

        # STEP 6: Mark processing as completed.
        meeting.status = MeetingStatus.COMPLETED

        # Record completion time.
        meeting.processing_completed_at = datetime.now(timezone.utc)

        # Save the transcript and updated meeting status.
        db.commit()
        db.refresh(meeting)

        print(
            f"[Processing] Meeting {meeting.id} completed.",
            flush=True,
        )

        return meeting

    except Exception as exc:
        # STEP 7: Handle processing failures.

        # Roll back any uncommitted database changes.
        db.rollback()

        # Mark the meeting as FAILED.
        meeting.status = MeetingStatus.FAILED

        # Record when processing failed.
        meeting.processing_completed_at = datetime.now(timezone.utc)

        # Store the failure reason for debugging.
        meeting.error_message = str(exc)

        # Persist the FAILED state.
        db.commit()
        db.refresh(meeting)

        print(
            f"[Processing] Meeting {meeting.id} failed: {exc}",
            flush=True,
        )

        # Re-raise the error so the API can return HTTP 500.
        raise
