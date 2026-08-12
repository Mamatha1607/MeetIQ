"""
===========================================================================
File: session.py

Purpose:
    This file is responsible for establishing communication between our
    FastAPI application and the PostgreSQL database.
===========================================================================
    """
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from collections.abc import Generator
from app.core.config import settings


# The engine manages the application's connection pool and
# communication with PostgreSQL.
engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,
)
# SessionLocal creates a new database session for each request.
# Each session represents one unit of work with the database
SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
)
def get_db() -> Generator[Session, None, None]:
    """
    Provides a database session for a single request
    and ensures that it is closed afterward.
    """

    db = SessionLocal()

    try:
        yield db #yield temporarily gives the session to FastAPI:
    finally:
        db.close() #after yeield clean it up