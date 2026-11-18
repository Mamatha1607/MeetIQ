
"""
Defines the Meeting database model.
"""

from datetime import datetime
from enum import Enum
import uuid

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.user import User
from sqlalchemy import DateTime, Enum as SqlEnum, Integer, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class MeetingStatus(str, Enum):
    """
    Defines the valid lifecycle states of a meeting.
    """

    CREATED = "created"
    UPLOADED = "uploaded"
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class Meeting(Base):
    """
    Represents a meeting stored in PostgreSQL.
    """

    __tablename__ = "meetings"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
    )
        # Identifies the user who owns this meeting.
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )

    user: Mapped["User"] = relationship(
        "User",
        back_populates="meetings",
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

    processing_started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    queued_at: Mapped[datetime | None] = mapped_column(
    DateTime(timezone=True),
    nullable=True,
    )

    processing_completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    error_message: Mapped[str | None] = mapped_column(
        String(2000),
        nullable=True,
    )
    last_heartbeat_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
        # Identifies the worker attempt currently allowed to process this meeting.
    processing_attempt_id: Mapped[uuid.UUID | None] = mapped_column(
        nullable=True,
    )
    retry_count: Mapped[int] = mapped_column(
    Integer,
    nullable=False,
    default=0,
    server_default="0",
)