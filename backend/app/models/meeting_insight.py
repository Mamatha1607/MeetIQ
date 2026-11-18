
"""
Stores AI-generated summaries and action items for meetings.
"""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, JSON, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class MeetingInsight(Base):
    __tablename__ = "meeting_insights"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
    )

    meeting_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("meetings.id"),
        unique=True,
        nullable=False,
    )

    summary: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    key_points: Mapped[list] = mapped_column(
        JSON,
        nullable=False,
    )

    decisions: Mapped[list] = mapped_column(
        JSON,
        nullable=False,
    )

    action_items: Mapped[list] = mapped_column(
        JSON,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
