"""
THis file 
connect to meetiq_test_db
→ create test DB sessions
→ override FastAPI's normal get_db()
→ give tests a TestClient
→ clean up test data

contains fixtures and shared test setup that multiple tests can use.
"""
"""
Provides shared fixtures and database setup for API tests.
"""

import pytest

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.api import meeting as meeting_api
from app.models.transcript import Transcript

# Import models so their tables are registered with Base.metadata.
from app.models.meeting import Meeting
from app.models.meeting_file import MeetingFile

# Connect automated tests to the separate test database.
test_engine = create_engine(
    settings.test_database_url,
    pool_pre_ping=True,
)

# Creates database sessions that use the test database.
TestingSessionLocal = sessionmaker(
    bind=test_engine,
    autoflush=False,
    autocommit=False,
)

def override_get_db():
    """
    Provides a database session connected to the test database.
    """

    db = TestingSessionLocal()

    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db
@pytest.fixture
def client():
        """
        Provides a FastAPI test client with a clean test database.
         """
        Base.metadata.create_all(bind=test_engine)

        with TestClient(app) as test_client:
            yield test_client

        Base.metadata.drop_all(bind=test_engine)

@pytest.fixture
def temporary_upload_dir(tmp_path, monkeypatch):
    """
    Redirects uploaded files to a temporary directory during tests.
    """

    upload_dir = tmp_path / "uploads"
    upload_dir.mkdir()

    #Monkeypatch = temporarily replace application configuration or behavior without permanently modifying production code.
    monkeypatch.setattr(
        meeting_api,
        "UPLOAD_DIR",
        upload_dir,
    )

    return upload_dir

@pytest.fixture
def db_session():
    """
    Provides a direct SQLAlchemy session connected to the test database.

    This fixture is useful when a test needs to verify database state
    directly instead of only checking HTTP responses.
    """

    db = TestingSessionLocal()

    try:
        yield db
    finally:
        db.close()