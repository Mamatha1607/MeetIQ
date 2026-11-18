from fastapi import APIRouter, Depends,status, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select,delete
from sqlalchemy.exc import IntegrityError
import uuid
from sqlalchemy import update
from app.api.dependencies import get_current_user
from app.models.user import User
from pathlib import Path
from datetime import datetime, timezone
from kombu.exceptions import OperationalError
from app.worker.tasks import process_meeting_task
from app.models.meeting_insight import MeetingInsight
from app.schemas.meeting_insight import MeetingInsightResponse
from app.schemas.meeting import (
    MeetingCreate,
    MeetingUpdate,
    MeetingResponse,
)
from fastapi import File, UploadFile

from app.db.session import get_db
from app.models.meeting import Meeting, MeetingStatus
from app.models.meeting_file import MeetingFile
from app.schemas.meeting_file import MeetingFileUploadResponse
from app.models.transcript import Transcript
from app.schemas.transcript import TranscriptResponse

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

ALLOWED_CONTENT_TYPES = {
    "audio/mpeg",
    "audio/wav",
    "audio/x-wav",
    "video/mp4",
    "video/mpeg",
}
MAX_FILE_SIZE = 100 * 1024 * 1024

#create APIS
router = APIRouter(
    #This means every route in this file automatically begins with /meetings
    prefix = "/meetings",
    #This affects Swagger documentation.
    #It groups meeting endpoints under a section named:
    tags = ["Meetings"],
    dependencies=[Depends(get_current_user)],
)
def get_owned_meeting(
    db: Session,
    meeting_id: uuid.UUID,
    user_id: uuid.UUID,
) -> Meeting:
    """
    Retrieves a meeting only when it belongs to the user.
    """

    meeting = db.scalar(
        select(Meeting).where(
            Meeting.id == meeting_id,
            Meeting.user_id == user_id,
        )
    )

    if meeting is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Meeting not found",
        )

    return meeting
#Postmethod
@router.post(
    "/",
    response_model=MeetingResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_meeting(
    meeting_data: MeetingCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Creates a meeting owned by the authenticated user.
    """

    meeting = Meeting(
        title=meeting_data.title,
        description=meeting_data.description,
        user_id=current_user.id,
    )

    db.add(meeting)
    db.commit()
    db.refresh(meeting)

    return meeting

@router.get(
    "/",
    response_model=list[MeetingResponse],
)
def list_meetings(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Returns meetings belonging to the authenticated user.
    """

    statement = select(Meeting).where(
        Meeting.user_id == current_user.id
    )

    return db.scalars(statement).all()

#get one specific meeting
@router.get(
    "/{meeting_id}",
    response_model=MeetingResponse,
)
def get_meeting(
    meeting_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Returns a meeting owned by the authenticated user.
    """

    meeting = get_owned_meeting(
        db,
        meeting_id,
        current_user.id,
    )

    return meeting


#UPLOAD MEETING
@router.post(
        "/{meeting_id}/upload",
        response_model = MeetingFileUploadResponse,
        )
def upload_meeting_file(
    meeting_id:uuid.UUID,
    #File(...) mean This parameter must come from a multipart file field.
    file:UploadFile=File(...),
    db: Session=Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    meeting = get_owned_meeting(
    db,
    meeting_id,
    current_user.id,
)
    #Validate meeting exists
    if meeting is None:
        raise HTTPException(
            status_code = status.HTTP_404_NOT_FOUND,
            detail = "No meeting found",
        )
    #Validate content type
    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code = status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail = "File type not allowed",
        )
    #read the file
    file_bytes = file.file.read()

    #Validate size
    if len(file_bytes)>MAX_FILE_SIZE:
        raise HTTPException(
            status_code = status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail = "File is too large",
        )
    #Generate a safe storage filename

    #Get the file extension and conver it to lowercase MP3->mp3
    #file.filename or ""? ->Sometimes file.filename could be None.
    suffix=Path(file.filename or "").suffix.lower()

    #Generate our own filename it becomes id.mps
    stored_filename = f"{uuid.uuid4()}{suffix}"

    #Build the location where the file will be saved
    storage_path = UPLOAD_DIR / stored_filename

    #save files "wb" = write binary
    with storage_path.open("wb") as destination:
        destination.write(file_bytes)
    try:
        #Create MeetingFile row
        meeting_file = MeetingFile(
        meeting_id = meeting.id,
        original_filename = file.filename or "unknown",
        storage_path = str(storage_path),
        content_type = file.content_type or "application/octet-stream",
        size_bytes = len(file_bytes),
        )

        #Update meeting status
        db.add(meeting_file)
        meeting.status = MeetingStatus.UPLOADED
        #save
        db.commit()
        db.refresh(meeting_file)#refresh
        db.refresh(meeting)

        #And if the database rejects the insert:
    except  IntegrityError:
        db.rollback()

        if storage_path.exists():
            storage_path.unlink()

        raise HTTPException(
        status_code = status.HTTP_409_CONFLICT,
        detail = "duplicate upload"

    )

    #return the response
    return {
    "message": "File uploaded successfully",
    "meeting_id": meeting.id,
    "filename": meeting_file.original_filename,
    "status": meeting.status,
}
@router.post(
    "/{meeting_id}/process",
    response_model=MeetingResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
def start_meeting_processing(
    meeting_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Queue an uploaded meeting for background transcription.
    """

    # STEP 1: Lock and retrieve the meeting.
    # This prevents two simultaneous requests from both
    # submitting the same meeting.
    statement = (
    select(Meeting)
    .where(
        Meeting.id == meeting_id,
        Meeting.user_id == current_user.id,
    )
    .with_for_update()
)

    meeting = db.scalar(statement)

    # STEP 2: Validate the meeting exists.
    if meeting is None:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Meeting is not found",
        )

    # STEP 3: Only uploaded meetings can be queued.
    if meeting.status != MeetingStatus.UPLOADED:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Meeting must be uploaded before processing",
        )

    # STEP 4: Reserve the meeting for processing.
    now = datetime.now(timezone.utc)

    meeting.status = MeetingStatus.QUEUED
    meeting.queued_at = now
    meeting.processing_started_at = None
    meeting.processing_completed_at = None
    meeting.last_heartbeat_at = None
    meeting.processing_attempt_id = None
    meeting.error_message = None

    # Save the status before submitting the task.
    db.commit()
    db.refresh(meeting)

    try:
        # STEP 5: Submit the meeting ID to Redis.
        # Celery will execute this task separately.
        process_meeting_task.delay(str(meeting.id))

    except (OperationalError, ConnectionError, TimeoutError) as exc:
    # STEP 6: Handle a task submission failure.
        db.rollback()

        result = db.execute(
            update(Meeting)
            .where(
                Meeting.id == meeting_id,
                Meeting.status == MeetingStatus.QUEUED,
            )
            .values(
                status=MeetingStatus.FAILED,
                processing_completed_at=datetime.now(timezone.utc),
                error_message="Unable to queue meeting processing",
            )
            .execution_options(synchronize_session=False)
        )

        db.commit()

    raise HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail="Background processing is temporarily unavailable",
    ) from exc

    # STEP 7: Return immediately.
    # Whisper will run inside the Celery worker.
    return meeting

@router.get(
    "/{meeting_id}/transcript",
    response_model=TranscriptResponse,
)
def get_meeting_transcript(
    meeting_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Returns the transcript generated for a meeting.
    """

    # First make sure the meeting itself exists.
    meeting = get_owned_meeting(
    db,
    meeting_id,
    current_user.id,
)

    if meeting is None:
        raise HTTPException(
            status_code=404,
            detail="Meeting not found",
        )

    # Find the transcript associated with this meeting.
    statement = select(Transcript).where(
        Transcript.meeting_id == meeting_id
    )

    transcript = db.scalar(statement)

    # A meeting may exist but may not have been processed yet.
    if transcript is None:
        raise HTTPException(
            status_code=404,
            detail="Transcript not found",
        )

    return transcript
@router.patch(
    "/{meeting_id}",
    response_model=MeetingResponse,
)
def update_meeting(
    meeting_id: uuid.UUID,
    meeting_data: MeetingUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Update a meeting's title and/or description.
    """

    # STEP 1: Find the meeting.
    meeting = get_owned_meeting(
    db,
    meeting_id,
    current_user.id,
)

    if meeting is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Meeting not found",
        )

    # STEP 2: Extract only fields explicitly provided.
    update_data = meeting_data.model_dump(
        exclude_unset=True
    )

    # STEP 3: Prevent a null title.
    if "title" in update_data and update_data["title"] is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Meeting title cannot be null",
        )

    # STEP 4: Update the supplied fields.
    for field, value in update_data.items():
        setattr(meeting, field, value)

    # STEP 5: Save the changes.
    db.commit()
    db.refresh(meeting)

    return meeting
@router.delete(
    "/{meeting_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_meeting(
    meeting_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Delete a meeting and its associated data.
    """

    # STEP 1: Lock the meeting to prevent concurrent status changes.
    meeting = db.scalar(
    select(Meeting)
    .where(
        Meeting.id == meeting_id,
        Meeting.user_id == current_user.id,
    )
    .with_for_update()
)

    if meeting is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Meeting not found",
        )

    # STEP 2: Don't delete active processing jobs.
    if meeting.status in {
        MeetingStatus.QUEUED,
        MeetingStatus.PROCESSING,
    }:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Cannot delete a meeting while processing",
        )

    # STEP 3: Retrieve uploaded file paths before deleting DB rows.
    meeting_files = db.scalars(
        select(MeetingFile).where(
            MeetingFile.meeting_id == meeting_id
        )
    ).all()

    file_paths = [Path(item.storage_path) for item in meeting_files]

    # STEP 4: Delete dependent database records first.
    db.execute(
        delete(MeetingInsight).where(
            MeetingInsight.meeting_id == meeting_id
        )
    )

    db.execute(
        delete(Transcript).where(
            Transcript.meeting_id == meeting_id
        )
    )

    db.execute(
        delete(MeetingFile).where(
            MeetingFile.meeting_id == meeting_id
        )
    )

    # STEP 5: Delete parent meeting.
    db.delete(meeting)

    # STEP 6: Commit all database changes together.
    db.commit()

    # STEP 7: Delete physical recordings after successful commit.
    for path in file_paths:
        try:
            path.unlink(missing_ok=True)
        except OSError:
            # File cleanup failure should be logged for later retry.
            # Do not turn a committed deletion into a 500 response.
            import logging
            logging.getLogger(__name__).exception(
                "Failed to delete recording: %s", path
            )
@router.get(
    "/{meeting_id}/insights",
    response_model=MeetingInsightResponse,
)
def get_meeting_insights(
    meeting_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieve AI-generated insights for a meeting."""

    meeting = get_owned_meeting(
    db,
    meeting_id,
    current_user.id,
)

    if meeting is None:
        raise HTTPException(
            status_code=404,
            detail="Meeting not found",
        )

    insights = db.scalar(
        select(MeetingInsight).where(
            MeetingInsight.meeting_id == meeting_id
        )
    )

    if insights is None:
        raise HTTPException(
            status_code=404,
            detail="Meeting insights not found",
        )

    return insights
