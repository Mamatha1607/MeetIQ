

"""
Defines the base class used by all SQLAlchemy database models.
"""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """
    Base class inherited by every SQLAlchemy model in the application.
    """

    pass