from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class TranscriptResponse(BaseModel):
    """
    Response returned when retrieving a meeting transcript.
    """

    id: UUID
    meeting_id: UUID
    text: str
    language: str | None
    created_at: datetime
    updated_at: datetime

    # Allows Pydantic to build this response from a SQLAlchemy model.
    model_config = ConfigDict(from_attributes=True)