import uuid
from datetime import datetime

from sqlalchemy.orm import Mapped,MappedColumn
from sqlalchemy import String, DateTime,func,ForeignKey, BigInteger

from app.db.base import Base

class MeetingFile(Base):
    """
    Represents an uploaded recording associated with a meeting.
    """
    """CREATE TABLE"""
    __tablename__="meeting_files"
    #uuid.UUID       → Python type
    id:Mapped[uuid.UUID]=MappedColumn(
        #uuid.uuid4      → function that generates IDs
        default=uuid.uuid4,
        primary_key=True
    )
    """CREATE MEETING_ID COLUMN"""
    meeting_id:Mapped[uuid.UUID]=MappedColumn(
    #Every meeting_id stored here must reference an existing id in the meetings table.
        ForeignKey("meetings.id"),
        nullable=False,
        unique=True,
    )
    """CREATE FILE NAME COLUMN"""
    original_filename:Mapped[str]=MappedColumn(
        String(255),
        nullable=False
    )
    """Create storagepath column"""
    storage_path:Mapped[str]=MappedColumn(
        String(500),
        nullable=False
    )
    """create content type column"""
    content_type:Mapped[str]=MappedColumn(
        String(100),
        nullable=False,
    )
    """create size of file column"""
    size_bytes:Mapped[int]=MappedColumn(
        BigInteger,
        nullable=False,
    )
    """create created at column"""
    created_at:Mapped[datetime]=MappedColumn(
       DateTime(timezone=True),
    server_default=func.now(),
        nullable=False
    )