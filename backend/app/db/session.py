"""
===========================================================================
File: session.py

Purpose:
    This file is responsible for establishing communication between our
    FastAPI application and the PostgreSQL database.
===========================================================================
    """
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

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