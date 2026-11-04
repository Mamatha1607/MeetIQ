import uuid
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field

from app.models.meeting import MeetingStatus
#BaseModel = Make this class a Pydantic validation model.
class MeetingCreate(BaseModel):
   #Pydantic knows title must be a str because of : str, and Field adds the extra length rules.
    title: str = Field( #Field → lets us add validation rules
        min_length=1,
        max_length=255,
    )

    description: str | None = Field(
        default=None,
        max_length=2000,
    )

class MeetingResponse(BaseModel):

    """
    Defines the data returned for a meeting.
    """

    id: uuid.UUID
    title: str
    description: str | None
    status: MeetingStatus
    created_at: datetime
    updated_at: datetime

    processing_started_at: datetime | None
    processing_completed_at: datetime | None
    error_message: str | None

    #from_attributes=True → Allows Pydantic to read data from database objects.
    model_config = ConfigDict(from_attributes=True) 