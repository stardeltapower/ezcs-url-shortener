from app.config import settings
from app.models import Url


class TestMainEndpoints:
    """Test main application endpoints"""

    def test_root_redirect(self, client):
        """Test root endpoint redirects to configured URL"""
        response = client.get("/", allow_redirects=False)
        assert response.status_code == 307
        assert response.headers["location"] == settings.REDIRECT_URL

    def test_docs_endpoint_environment_aware(self, client):
        """Test docs endpoint behavior based on environment"""
        response = client.get("/docs")

        if settings.is_development:
            # Development: docs should be available
            assert response.status_code == 200
            assert "swagger" in response.text.lower() or "fastapi" in response.text.lower()
        else:
            # Production: docs should be disabled (404)
            assert response.status_code == 404

    def test_redoc_endpoint_environment_aware(self, client):
        """Test ReDoc endpoint behavior based on environment"""
        response = client.get("/redoc")

        if settings.is_development:
            # Development: redoc should be available
            assert response.status_code == 200
        else:
            # Production: redoc should be disabled (404)
            assert response.status_code == 404

    def test_openapi_json_environment_aware(self, client):
        """Test OpenAPI JSON schema based on environment"""
        response = client.get("/openapi.json")

        if settings.is_development:
            # Development: OpenAPI schema should be available
            assert response.status_code == 200
            data = response.json()
            assert "openapi" in data
            assert "info" in data
            assert data["info"]["title"] == "URL Shortener API"
        else:
            # Production: OpenAPI schema should be disabled (404)
            assert response.status_code == 404

    def test_health_check_endpoint(self, client):
        """Test health check endpoint with environment information"""
        response = client.get("/api/health")
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "healthy"
        assert "environment" in data
        assert "debug" in data
        assert data["environment"] == settings.ENVIRONMENT
        assert data["debug"] == settings.debug

    def test_short_url_redirect_not_found(self, client):
        """Test redirect for non-existent short URL"""
        response = client.get("/nonexistent", allow_redirects=False)
        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"].lower()

    def test_short_url_redirect_success(self, client, db_session, api_key_data):
        """Test successful redirect for existing short URL"""
        # Create a URL in the database
        url = Url(
            short_url="testurl", original_url="https://example.com", api_key_id=api_key_data["id"]
        )
        db_session.add(url)
        db_session.commit()

        # Test redirect
        response = client.get("/testurl", allow_redirects=False)
        assert response.status_code == 307
        assert response.headers["location"] == "https://example.com"

    def test_short_url_redirect_expired(self, client, db_session, api_key_data):
        """Test redirect for expired short URL"""
        from datetime import datetime, timedelta

        # Create an expired URL
        expired_url = Url(
            short_url="expired",
            original_url="https://example.com",
            expires_at=datetime.utcnow() - timedelta(hours=1),
            api_key_id=api_key_data["id"],
        )
        db_session.add(expired_url)
        db_session.commit()

        # Test that expired URL returns 410 Gone
        response = client.get("/expired", allow_redirects=False)
        assert response.status_code == 410
        data = response.json()
        assert "expired" in data["detail"].lower()

    def test_invalid_short_url_format(self, client):
        """Test that invalid short URL formats are handled"""
        # Test with invalid characters
        response = client.get("/invalid-url-with-special-chars!", allow_redirects=False)
        assert response.status_code == 404

    def test_environment_specific_logging(self, client, caplog):
        """Test that logging behavior differs by environment"""
        import logging

        # Clear any existing logs
        caplog.clear()

        # Make a request that will trigger logging
        response = client.get("/nonexistent", allow_redirects=False)
        assert response.status_code == 404

        # Check logging behavior based on environment
        if settings.is_development:
            # Development should have debug logs
            assert any(record.levelno == logging.DEBUG for record in caplog.records)

        # Both environments should have warning/info logs
        assert any(record.levelno >= logging.WARNING for record in caplog.records)

    def test_environment_configuration(self, client):
        """Test that environment configuration is working properly"""
        # Test health endpoint shows correct environment
        response = client.get("/api/health")
        assert response.status_code == 200

        data = response.json()
        assert data["environment"] == settings.ENVIRONMENT
        assert data["debug"] == settings.debug

        # Test that configuration properties work
        assert settings.is_production or settings.is_development
        assert isinstance(settings.log_level, str)
        assert isinstance(settings.cors_origins, list)
