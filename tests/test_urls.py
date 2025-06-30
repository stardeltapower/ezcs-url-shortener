from datetime import datetime, timedelta, timezone


class TestUrlManagement:
    """Test URL management endpoints"""

    def test_create_url_success_auto_short(self, client, api_headers, sample_url_data):
        """Test successful URL creation with auto-generated short URL"""
        response = client.post("/api/urls/", json=sample_url_data, headers=api_headers)

        assert response.status_code == 201
        data = response.json()
        assert data["original_url"] == sample_url_data["original_url"]
        assert len(data["short_url"]) == 6  # Default length from settings
        assert "id" in data
        assert "created_at" in data
        assert data["expires_at"] is None

    def test_create_url_success_custom_short(self, client, api_headers, sample_custom_url_data):
        """Test successful URL creation with custom short URL"""
        response = client.post("/api/urls/", json=sample_custom_url_data, headers=api_headers)

        assert response.status_code == 201
        data = response.json()
        assert data["original_url"] == sample_custom_url_data["original_url"]
        assert data["short_url"] == sample_custom_url_data["short_url"]

    def test_create_url_duplicate_short(self, client, api_headers, sample_custom_url_data):
        """Test URL creation with duplicate custom short URL"""
        # Create first URL
        client.post("/api/urls/", json=sample_custom_url_data, headers=api_headers)

        # Try to create second URL with same short code
        response = client.post("/api/urls/", json=sample_custom_url_data, headers=api_headers)
        assert response.status_code == 400
        assert "already exists" in response.json()["detail"]

    def test_create_url_with_expiry(self, client, api_headers):
        """Test URL creation with expiry date"""
        future_date = datetime.now(timezone.utc) + timedelta(days=7)
        url_data = {
            "original_url": "https://example.com/expiry-test",
            "expires_at": future_date.isoformat(),
        }

        response = client.post("/api/urls/", json=url_data, headers=api_headers)
        assert response.status_code == 201
        data = response.json()
        assert data["expires_at"] is not None

    def test_create_url_without_api_key(self, client, sample_url_data):
        """Test URL creation without API key fails"""
        response = client.post("/api/urls/", json=sample_url_data)
        assert response.status_code == 401

    def test_create_url_invalid_api_key(self, client, sample_url_data):
        """Test URL creation with invalid API key fails"""
        headers = {"X-API-Key": "invalid-key"}
        response = client.post("/api/urls/", json=sample_url_data, headers=headers)
        assert response.status_code == 401

    def test_list_urls_success(self, client, api_headers, sample_url_data):
        """Test successful URL listing"""
        # Create a few URLs first
        for i in range(3):
            url_data = {"original_url": f"https://example.com/test-{i}"}
            client.post("/api/urls/", json=url_data, headers=api_headers)

        response = client.get("/api/urls/", headers=api_headers)
        assert response.status_code == 200
        data = response.json()
        assert "urls" in data
        assert "total" in data
        assert len(data["urls"]) == 3
        assert data["total"] == 3

    def test_list_urls_pagination(self, client, api_headers):
        """Test URL listing with pagination"""
        # Create 5 URLs
        for i in range(5):
            url_data = {"original_url": f"https://example.com/test-{i}"}
            client.post("/api/urls/", json=url_data, headers=api_headers)

        # Test pagination
        response = client.get("/api/urls/?skip=2&limit=2", headers=api_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data["urls"]) == 2
        assert data["total"] == 5

    def test_get_url_by_id_success(self, client, api_headers, sample_url_data):
        """Test successful URL retrieval by ID"""
        # Create URL first
        create_response = client.post("/api/urls/", json=sample_url_data, headers=api_headers)
        url_id = create_response.json()["id"]

        response = client.get(f"/api/urls/{url_id}", headers=api_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == url_id
        assert data["original_url"] == sample_url_data["original_url"]

    def test_get_url_by_id_not_found(self, client, api_headers):
        """Test URL retrieval with non-existent ID"""
        response = client.get("/api/urls/999", headers=api_headers)
        assert response.status_code == 404

    def test_get_url_by_short_code_success(self, client, api_headers, sample_custom_url_data):
        """Test successful URL retrieval by short code"""
        # Create URL first
        client.post("/api/urls/", json=sample_custom_url_data, headers=api_headers)

        response = client.get(
            f"/api/urls/short/{sample_custom_url_data['short_url']}", headers=api_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["short_url"] == sample_custom_url_data["short_url"]

    def test_get_url_by_short_code_not_found(self, client, api_headers):
        """Test URL retrieval with non-existent short code"""
        response = client.get("/api/urls/short/nonexistent", headers=api_headers)
        assert response.status_code == 404

    def test_update_url_success(self, client, api_headers, sample_url_data):
        """Test successful URL update"""
        # Create URL first
        create_response = client.post("/api/urls/", json=sample_url_data, headers=api_headers)
        url_id = create_response.json()["id"]

        # Update URL
        update_data = {"original_url": "https://updated.example.com"}
        response = client.put(f"/api/urls/{url_id}", json=update_data, headers=api_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["original_url"] == update_data["original_url"]

    def test_update_url_with_expiry(self, client, api_headers, sample_url_data):
        """Test URL update with expiry date"""
        # Create URL first
        create_response = client.post("/api/urls/", json=sample_url_data, headers=api_headers)
        url_id = create_response.json()["id"]

        # Update with expiry
        future_date = datetime.now(timezone.utc) + timedelta(days=7)
        update_data = {"expires_at": future_date.isoformat()}
        response = client.put(f"/api/urls/{url_id}", json=update_data, headers=api_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["expires_at"] is not None

    def test_update_url_not_found(self, client, api_headers):
        """Test updating non-existent URL"""
        update_data = {"original_url": "https://example.com"}
        response = client.put("/api/urls/999", json=update_data, headers=api_headers)
        assert response.status_code == 404

    def test_delete_url_success(self, client, api_headers, sample_url_data):
        """Test successful URL deletion"""
        # Create URL first
        create_response = client.post("/api/urls/", json=sample_url_data, headers=api_headers)
        url_id = create_response.json()["id"]

        response = client.delete(f"/api/urls/{url_id}", headers=api_headers)
        assert response.status_code == 200
        assert "deleted successfully" in response.json()["message"]

        # Verify URL is gone
        get_response = client.get(f"/api/urls/{url_id}", headers=api_headers)
        assert get_response.status_code == 404

    def test_delete_url_not_found(self, client, api_headers):
        """Test deleting non-existent URL"""
        response = client.delete("/api/urls/999", headers=api_headers)
        assert response.status_code == 404

    def test_url_isolation_between_api_keys(self, client, db_session):
        """Test that URLs are isolated between different API keys"""
        from app.auth import hash_api_key
        from app.models import ApiKey

        # Create two API keys
        key1 = "test-key-1"
        key2 = "test-key-2"

        api_key1 = ApiKey(key_hash=hash_api_key(key1), name="Key 1", is_active=True)
        api_key2 = ApiKey(key_hash=hash_api_key(key2), name="Key 2", is_active=True)

        db_session.add_all([api_key1, api_key2])
        db_session.commit()

        headers1 = {"X-API-Key": key1}
        headers2 = {"X-API-Key": key2}

        # Create URL with first key
        url_data = {"original_url": "https://example.com/key1"}
        response1 = client.post("/api/urls/", json=url_data, headers=headers1)
        url_id = response1.json()["id"]

        # Try to access with second key (should fail)
        response2 = client.get(f"/api/urls/{url_id}", headers=headers2)
        assert response2.status_code == 404

        # Verify first key can still access
        response3 = client.get(f"/api/urls/{url_id}", headers=headers1)
        assert response3.status_code == 200

    def test_expired_url_handling(self, client, api_headers):
        """Test handling of expired URLs"""
        # Create URL with past expiry date
        past_date = datetime.now(timezone.utc) - timedelta(days=1)
        url_data = {
            "original_url": "https://example.com/expired",
            "expires_at": past_date.isoformat(),
        }

        response = client.post("/api/urls/", json=url_data, headers=api_headers)
        assert response.status_code == 201

        # API should still return the URL (expiry check is for redirect)
        url_id = response.json()["id"]
        get_response = client.get(f"/api/urls/{url_id}", headers=api_headers)
        assert get_response.status_code == 200
