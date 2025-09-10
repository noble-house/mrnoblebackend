import pytest
import asyncio
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.db import get_db, Base
from app.models import Admin
from app.services.auth import get_password_hash

# Test database URL (in-memory SQLite for fast testing)
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="function")
def db_session():
    """Create a fresh database session for each test."""
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def client(db_session):
    """Create a test client with database dependency override."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()

@pytest.fixture(scope="function")
def admin_user(db_session):
    """Create a test admin user."""
    admin = Admin(
        email="test@mrnoble.app",
        hashed_password=get_password_hash("testpassword"),
        is_active=True
    )
    db_session.add(admin)
    db_session.commit()
    db_session.refresh(admin)
    return admin

@pytest.fixture(scope="function")
def auth_headers(client, admin_user):
    """Get authentication headers for test requests."""
    response = client.post("/auth/login", json={
        "email": admin_user.email,
        "password": "testpassword"
    })
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

@pytest.fixture(scope="function")
def sample_job(db_session):
    """Create a sample job for testing."""
    from app.models import Job
    job = Job(
        title="Test Job",
        jd_text="This is a test job description",
        jd_json={"must_have": ["Python", "FastAPI"], "nice_to_have": ["Docker"]}
    )
    db_session.add(job)
    db_session.commit()
    db_session.refresh(job)
    return job

@pytest.fixture(scope="function")
def sample_candidate(db_session):
    """Create a sample candidate for testing."""
    from app.models import Candidate
    candidate = Candidate(
        name="Test Candidate",
        email="candidate@example.com",
        phone="+1-555-123-4567",
        resume_json={"skills": ["Python", "JavaScript"], "text": "Test resume content"}
    )
    db_session.add(candidate)
    db_session.commit()
    db_session.refresh(candidate)
    return candidate

@pytest.fixture(scope="function")
def sample_application(db_session, sample_job, sample_candidate):
    """Create a sample application for testing."""
    from app.models import Application, FitStatus
    application = Application(
        candidate_id=sample_candidate.id,
        job_id=sample_job.id,
        fit_score=0.85,
        fit_status=FitStatus.FIT,
        reasons=["Strong Python skills", "Relevant experience"]
    )
    db_session.add(application)
    db_session.commit()
    db_session.refresh(application)
    return application
