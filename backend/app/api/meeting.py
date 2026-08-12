from fastapi import APIRouter, Depends,status, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select
import uuid

from app.db.session import get_db
from app.models.meeting import Meeting
from app.schemas.meeting import MeetingCreate, MeetingResponse


router = APIRouter(
    #This means every route in this file automatically begins with /meetings
    prefix="/meetings",
    #This affects Swagger documentation.
    #It groups meeting endpoints under a section named:
    tags=["Meetings"],
)
#Postmethod
@router.post(
    "/",
    #Serialize the returned object using this schema.
    response_model=MeetingResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_meeting(
    #FastAPI reads the incoming JSON and validates it using MeetingCreate
    meeting_data:MeetingCreate,
    db:Session=Depends(get_db),
):
    """
    Creates and stores a new meeting.
    """
    meeting=Meeting(
        #so the json becomes becomes a Python object:
        title=meeting_data.title,
        description=meeting_data.description,
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
    response_model=list[MeetingResponse],
)
def list_meetings(
        db:Session=Depends(get_db),    
):
    #return data
    statement=select(Meeting)
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
    response_model=MeetingResponse
)
def get_meeting(
    meeting_id:uuid.UUID,
    db:Session=Depends(get_db),
):
    meeting=db.get(Meeting,meeting_id)
    
    if meeting is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Meeting Notfound"
        )
    return meeting