from fastapi import APIRouter, Depends,status, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
import uuid
from pathlib import Path


from fastapi import File, UploadFile

from app.db.session import get_db
from app.models.meeting import Meeting, MeetingStatus
from app.models.meeting_file import MeetingFile
from app.schemas.meeting import MeetingCreate, MeetingResponse
from app.schemas.meeting_file import MeetingFileUploadResponse
from app.services.meeting_processing import process_meeting
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
    response_model = MeetingResponse,
)
def start_meeting_processing(
    meeting_id : uuid.UUID,
    db : Session = Depends(get_db),
):
     """
    Starts processing for an uploaded meeting.
    """
      # Find the meeting that the client wants to process.
     meeting = db.get(Meeting, meeting_id)

     # The requested meeting must exist before processing can start
     if meeting is None:
         raise HTTPException(
             status_code = status.HTTP_404_NOT_FOUND,
             detail = "Meeting is not found",
         )
       # Delegate the actual processing lifecycle logic to the service layer.
     try:
         meeting = process_meeting(
             meeting = meeting,
             db = db,
         )
     except ValueError as exc:
         # The meeting exists, but its current state does not allow processing
          raise HTTPException(
              status_code = status.HTTP_409_CONFLICT,
              detail = str(exc)
          ) from exc
     except Exception as exc:
        # The processing service has already recorded the failure
        # in PostgreSQL. Return a safe error to the API client.
            raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Meeting processing failed",
        ) from exc

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