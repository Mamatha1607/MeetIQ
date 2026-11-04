"""
Defines the database model for generated meeting transcripts.
"""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Transcript(Base):
    """
    Represents the generated transcript for a meeting.
    """
    __tablename__ = "transcripts"

 # Unique identifier for the transcript record.
    id: Mapped[uuid.UUID] = mapped_column(
        primary_key = True,
        default = uuid.uuid4, 
    )
    # Connects this transcript to exactly one meeting.
    meeting_id : Mapped[uuid.UUID] = mapped_column(
        ForeignKey("meetings.id"),
        unique = True,
        nullable = False
    )
    # Stores the full transcription generated from the meeting recording.
    # Text is used because transcripts can be much larger than normal strings
    text : Mapped[str] = mapped_column(
        Text,
        nullable = False,
    )
     # Stores the detected language of the transcript, such as "en".
    # It is optional because language detection may not always be available.
    language : Mapped[str|None] = mapped_column(
        String(20),
        nullable = True,
    )
    # Records when the transcript was first created.
    created_at : Mapped[DateTime] = mapped_column(
        DateTime(timezone = True),
        server_default=func.now(),
        nullable = False,
    )

    # Records when the transcript was last updated.
    updated_at : Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        server_default = func.now(),
        onupdate=func.now(),
        nullable = False,
    )