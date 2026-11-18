
"""
Response schemas for AI-generated meeting insights.
"""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.ai.summarization.service import ActionItem


class MeetingInsightResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    meeting_id: uuid.UUID
    summary: str
    key_points: list[str] = Field(default_factory=list)
    decisions: list[str] = Field(default_factory=list)
    action_items: list[ActionItem] = Field(default_factory=list)
    created_at: datetime
