from datetime import datetime, timedelta

import pytest
from sqlalchemy.exc import IntegrityError

from app.models import ApiKey, Url
from app.schemas import ApiKeyCreate, ApiKeyResponse, UrlCreate, UrlResponse, UrlUpdate


class TestDatabaseModels:
    """Test SQLAlchemy database models"""

    def test_api_key_creation(self, db_session):
        """Test creating an API key model"""
        api_key = ApiKey(key_hash="$2b$12$test_hash", name="Test API Key", is_active=True)

        db_session.add(api_key)
        db_session.commit()
        db_session.refresh(api_key)

        assert api_key.id is not None
        assert api_key.name == "Test API Key"
        assert api_key.is_active is True
        assert api_key.created_at is not None
        assert isinstance(api_key.created_at, datetime)

    def test_api_key_defaults(self, db_session):
        """Test API key model defaults"""
        api_key = ApiKey(
            key_hash="$2b$12$test_hash",
            name="Test Key",
            # is_active not specified, should default to True
        )

        db_session.add(api_key)
        db_session.commit()
        db_session.refresh(api_key)

        assert api_key.is_active is True
        assert api_key.created_at is not None

    def test_url_creation(self, db_session, api_key_data):
        """Test creating a URL model"""
        url = Url(
            short_url="test123",
            original_url="https://example.com",
            api_key_id=api_key_data["id"],
            expires_at=datetime.utcnow() + timedelta(days=30),
        )

        db_session.add(url)
        db_session.commit()
        db_session.refresh(url)

        assert url.id is not None
        assert url.short_url == "test123"
        assert url.original_url == "https://example.com"
        assert url.api_key_id == api_key_data["id"]
        assert url.created_at is not None
        assert url.expires_at is not None

    def test_url_without_expiry(self, db_session, api_key_data):
        """Test creating a URL without expiry"""
        url = Url(
            short_url="noexpiry",
            original_url="https://noexpiry.com",
            api_key_id=api_key_data["id"],
            # expires_at not specified, should default to None
        )

        db_session.add(url)
        db_session.commit()
        db_session.refresh(url)

        assert url.expires_at is None

    def test_url_unique_constraint(self, db_session, api_key_data):
        """Test that short URLs must be unique"""
        url1 = Url(
            short_url="unique", original_url="https://first.com", api_key_id=api_key_data["id"]
        )

        url2 = Url(
            short_url="unique",  # Same short URL
            original_url="https://second.com",
            api_key_id=api_key_data["id"],
        )

        db_session.add(url1)
        db_session.commit()

        db_session.add(url2)
        with pytest.raises(IntegrityError):
            db_session.commit()

    def test_api_key_url_relationship(self, db_session):
        """Test the relationship between API keys and URLs"""
        # Create an API key
        api_key = ApiKey(key_hash="$2b$12$test_hash", name="Relationship Test Key")
        db_session.add(api_key)
        db_session.commit()
        db_session.refresh(api_key)

        # Create URLs associated with this API key
        url1 = Url(short_url="rel1", original_url="https://rel1.com", api_key_id=api_key.id)
        url2 = Url(short_url="rel2", original_url="https://rel2.com", api_key_id=api_key.id)

        db_session.add_all([url1, url2])
        db_session.commit()

        # Test the relationship
        assert len(api_key.urls) == 2
        assert url1 in api_key.urls
        assert url2 in api_key.urls
        assert url1.api_key == api_key
        assert url2.api_key == api_key

    def test_api_key_cascade_delete(self, db_session):
        """Test that deleting an API key cascades to its URLs"""
        # Create an API key
        api_key = ApiKey(key_hash="$2b$12$test_hash", name="Cascade Test Key")
        db_session.add(api_key)
        db_session.commit()
        db_session.refresh(api_key)

        # Create a URL
        url = Url(short_url="cascade", original_url="https://cascade.com", api_key_id=api_key.id)
        db_session.add(url)
        db_session.commit()
        url_id = url.id

        # Delete the API key
        db_session.delete(api_key)
        db_session.commit()

        # URL should also be deleted
        deleted_url = db_session.query(Url).filter(Url.id == url_id).first()
        assert deleted_url is None


class TestPydanticSchemas:
    """Test Pydantic schemas for validation"""

    def test_api_key_create_schema(self):
        """Test API key creation schema"""
        data = {"name": "Test API Key"}
        schema = ApiKeyCreate(**data)

        assert schema.name == "Test API Key"

    def test_api_key_create_schema_validation(self):
        """Test API key creation schema validation"""
        # Missing name should raise validation error
        with pytest.raises(ValueError):
            ApiKeyCreate()

        # Empty name should raise validation error
        with pytest.raises(ValueError):
            ApiKeyCreate(name="")

    def test_api_key_response_schema(self):
        """Test API key response schema"""
        data = {
            "id": 1,
            "name": "Test API Key",
            "is_active": True,
            "created_at": datetime.utcnow(),
            "key": "test-key-123",
        }
        schema = ApiKeyResponse(**data)

        assert schema.id == 1
        assert schema.name == "Test API Key"
        assert schema.is_active is True
        assert schema.key == "test-key-123"

    def test_url_create_schema(self):
        """Test URL creation schema"""
        data = {
            "original_url": "https://example.com",
            "short_url": "custom",
            "expires_at": datetime.utcnow() + timedelta(days=30),
        }
        schema = UrlCreate(**data)

        assert schema.original_url == "https://example.com"
        assert schema.short_url == "custom"
        assert schema.expires_at is not None

    def test_url_create_schema_minimal(self):
        """Test URL creation schema with minimal data"""
        data = {"original_url": "https://example.com"}
        schema = UrlCreate(**data)

        assert schema.original_url == "https://example.com"
        assert schema.short_url is None
        assert schema.expires_at is None

    def test_url_create_schema_validation(self):
        """Test URL creation schema validation"""
        # Missing original_url should raise validation error
        with pytest.raises(ValueError):
            UrlCreate()

        # Invalid URL format should raise validation error
        with pytest.raises(ValueError):
            UrlCreate(original_url="not-a-url")

    def test_url_response_schema(self):
        """Test URL response schema"""
        data = {
            "id": 1,
            "short_url": "abc123",
            "original_url": "https://example.com",
            "created_at": datetime.utcnow(),
            "expires_at": None,
        }
        schema = UrlResponse(**data)

        assert schema.id == 1
        assert schema.short_url == "abc123"
        assert schema.original_url == "https://example.com"
        assert schema.expires_at is None

    def test_url_update_schema(self):
        """Test URL update schema validation"""
        data = {
            "original_url": "https://updated.com",
            "expires_at": datetime.now() + timedelta(days=30),
        }

        schema = UrlUpdate(**data)
        assert schema.original_url == "https://updated.com"
        assert schema.expires_at is not None

    def test_url_update_schema_partial(self):
        """Test URL update schema with partial data"""
        data = {"original_url": "https://partial.com"}

        schema = UrlUpdate(**data)
        assert schema.original_url == "https://partial.com"
        assert schema.expires_at is None

    def test_schema_json_serialization(self):
        """Test that schemas can be serialized to JSON"""
        api_key_data = {
            "id": 1,
            "name": "Test Key",
            "is_active": True,
            "created_at": datetime.utcnow(),
            "key": "test-key",
        }
        api_key_schema = ApiKeyResponse(**api_key_data)

        # Should be able to serialize to dict
        json_data = api_key_schema.model_dump()
        assert isinstance(json_data, dict)
        assert json_data["name"] == "Test Key"

    def test_schema_validation_errors(self):
        """Test schema validation error messages"""
        try:
            UrlCreate(original_url="invalid-url")
        except ValueError as e:
            # Should contain helpful error message
            error_str = str(e)
            assert "url" in error_str.lower() or "valid" in error_str.lower()

    def test_datetime_handling(self):
        """Test datetime field handling in schemas"""
        now = datetime.utcnow()
        future = now + timedelta(days=30)

        url_data = {"original_url": "https://datetime.com", "expires_at": future}
        schema = UrlCreate(**url_data)

        assert isinstance(schema.expires_at, datetime)
        assert schema.expires_at > now
