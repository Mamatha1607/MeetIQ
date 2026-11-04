"""
Defines API response schemas for meeting file operations.
"""
"""
Defines API response schemas for meeting file operations.
"""

import uuid

from pydantic import BaseModel

from app.models.meeting import MeetingStatus


class MeetingFileUploadResponse(BaseModel):
    """
    Defines the response returned after a meeting file is uploaded.
    """

    message: str
    meeting_id: uuid.UUID
    filename: str
    status: MeetingStatus