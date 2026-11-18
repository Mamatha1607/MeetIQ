
"""
Defines the User database model for authentication.
"""

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, String, func
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.meeting import Meeting
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base


class User(Base):
    """
    Represents a registered MeetIQ user.
    """

    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
    )

    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        index=True,
        nullable=False,
    )

    # Store only a securely generated password hash.
    hashed_password: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
        # Meetings owned by this user.
    meetings: Mapped[list["Meeting"]] = relationship(
        "Meeting",
        back_populates="user",
    )