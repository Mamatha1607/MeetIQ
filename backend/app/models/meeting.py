"""
Defines the Meeting database model.
"""
from datetime import datetime
from enum import Enum
import uuid

from sqlalchemy import DateTime, Enum as SqlEnum, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class MeetingStatus(str, Enum):
    """
    Defines the valid processing states for a meeting.
    """

    CREATED = "created"
    UPLOADED = "uploaded"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class Meeting(Base):
    """
    Represents a meeting stored in the database.
    """

    __tablename__ = "meetings"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
    )
    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    description: Mapped[str | None] = mapped_column(
        String(2000),
        nullable=True,
    )
    status: Mapped[MeetingStatus] = mapped_column(
        SqlEnum(MeetingStatus, name="meeting_status"),
        default=MeetingStatus.CREATED,
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
