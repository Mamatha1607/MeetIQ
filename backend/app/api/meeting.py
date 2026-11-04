from fastapi import APIRouter, Depends,status, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
import uuid
from pathlib import Path
from datetime import datetime, timezone
from kombu.exceptions import OperationalError
from app.worker.tasks import process_meeting_task

from fastapi import File, UploadFile

from app.db.session import get_db
from app.models.meeting import Meeting, MeetingStatus
from app.models.meeting_file import MeetingFile
from app.schemas.meeting import MeetingCreate, MeetingResponse
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
)
#Postmethod
@router.post(
    "/",
    #Serialize the returned object using this schema.
    response_model = MeetingResponse,
    status_code = status.HTTP_201_CREATED,
)
def create_meeting(
    #FastAPI reads the incoming JSON and validates it using MeetingCreate
    meeting_data : MeetingCreate,
    db: Session = Depends(get_db),
):
    """
    Creates and stores a new meeting.
    """
    meeting = Meeting(
        #so the json becomes becomes a Python object:
        title = meeting_data.title,
        description = meeting_data.description,
    )
    #start tracking this object so it can be inserted into the database.
    db.add(meeting)
    #This commits the transaction.
    db.commit()
   #We wanted the object to contain the latest database-generated information before returning it.
    db.refresh(meeting)

    return meeting


@router.get(
    "/",
    response_model = list[MeetingResponse],
)
def list_meetings(
        db: Session = Depends(get_db),
):
    #return data
    statement = select(Meeting)
    """
    execute query
→ extract Meeting objects
→ return them as a list
    """
    meetings = db.scalars(statement).all()

    return meetings


#get one specific meeting
@router.get(
    "/{meeting_id}",
    response_model = MeetingResponse
)
def get_meeting(
    meeting_id: uuid.UUID,
    db: Session = Depends(get_db),
):
    meeting = db.get(Meeting,meeting_id)
    
    if meeting is None:
        raise HTTPException(
            status_code = status.HTTP_404_NOT_FOUND,
            detail = "Meeting Notfound"
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
):
    meeting = db.get(Meeting,meeting_id)
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
):
    """
    Queue an uploaded meeting for background transcription.
    """

    # STEP 1: Lock and retrieve the meeting.
    # This prevents two simultaneous requests from both
    # submitting the same meeting.
    statement = (
        select(Meeting)
        .where(Meeting.id == meeting_id)
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
    meeting.status = MeetingStatus.PROCESSING
    meeting.processing_started_at = datetime.now(timezone.utc)
    meeting.processing_completed_at = None
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
        db.refresh(meeting)

        meeting.status = MeetingStatus.FAILED
        meeting.processing_completed_at = datetime.now(timezone.utc)
        meeting.error_message = "Unable to queue meeting processing"

        db.commit()
        db.refresh(meeting)

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
):
    """
    Returns the transcript generated for a meeting.
    """

    # First make sure the meeting itself exists.
    meeting = db.get(Meeting, meeting_id)

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