import os

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Override settings for testing BEFORE imports
os.environ["DATABASE_URL"] = "sqlite:///./test.db"
os.environ["SECRET_KEY"] = "test-secret-key"
os.environ["ADMIN_TOKEN"] = "test-admin-token"
os.environ["SHORT_URL_LENGTH"] = "6"

from app.auth import hash_api_key
from app.database import Base, get_db
from app.main import app
from app.models import ApiKey

# Create test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    """Override the database dependency for testing"""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


# Override the dependency
app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(scope="function")
def db_session():
    """Create a fresh database session for each test"""
    # Create all tables
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture(scope="function")
def client(db_session):
    """Create a TestClient for each test"""
    # Use a simpler initialization that's compatible with both old and new versions
    test_client = TestClient(app)
    try:
        yield test_client
    finally:
        test_client.close()


@pytest.fixture
def admin_headers():
    """Headers with admin token for admin endpoints"""
    return {"X-Admin-Token": "test-admin-token"}


@pytest.fixture
def api_key_record(db_session):
    """Create a test API key record"""
    key_hash = hash_api_key("test-api-key-123456789012345678901234")
    api_key = ApiKey(key_hash=key_hash, name="Test API Key", is_active=True)
    db_session.add(api_key)
    db_session.commit()
    db_session.refresh(api_key)
    return api_key


@pytest.fixture
def api_key_data(api_key_record):
    """Legacy fixture name for backward compatibility"""
    return {
        "id": api_key_record.id,
        "key": "test-api-key-123456789012345678901234",
        "name": api_key_record.name,
        "is_active": api_key_record.is_active,
    }


@pytest.fixture
def api_headers(api_key_record):
    """Headers with API key for authenticated endpoints"""
    return {"X-API-Key": "test-api-key-123456789012345678901234"}


@pytest.fixture
def sample_url_data():
    """Sample URL data for testing"""
    return {"original_url": "https://example.com/test"}


@pytest.fixture
def sample_custom_url_data():
    """Sample URL data with custom short URL for testing"""
    return {"original_url": "https://example.com/custom", "short_url": "custom123"}
