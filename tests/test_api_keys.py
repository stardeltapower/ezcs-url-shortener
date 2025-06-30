from app.models import ApiKey


class TestApiKeyManagement:
    """Test API key management endpoints"""

    def test_create_api_key_success(self, client, admin_headers):
        """Test successful API key creation"""
        data = {"name": "Test API Key"}
        response = client.post("/api/admin/keys/", json=data, headers=admin_headers)

        assert response.status_code == 201
        response_data = response.json()
        assert response_data["name"] == "Test API Key"
        assert response_data["is_active"] is True
        assert "key" in response_data
        assert len(response_data["key"]) == 32  # Default key length
        assert "id" in response_data
        assert "created_at" in response_data

    def test_create_api_key_without_admin_token(self, client):
        """Test API key creation without admin token fails"""
        data = {"name": "Test API Key"}
        response = client.post("/api/admin/keys/", json=data)

        assert response.status_code == 401
        data = response.json()
        assert "admin token" in data["detail"].lower()

    def test_create_api_key_invalid_admin_token(self, client):
        """Test API key creation with invalid admin token fails"""
        headers = {"X-Admin-Token": "invalid-token"}
        data = {"name": "Test API Key"}
        response = client.post("/api/admin/keys/", json=data, headers=headers)

        assert response.status_code == 403
        data = response.json()
        assert "invalid" in data["detail"].lower()

    def test_create_api_key_missing_name(self, client, admin_headers):
        """Test API key creation with missing name fails"""
        data = {}
        response = client.post("/api/admin/keys/", json=data, headers=admin_headers)

        assert response.status_code == 422
        data = response.json()
        assert "name" in str(data["detail"]).lower()

    def test_list_api_keys(self, client, admin_headers):
        """Test listing API keys"""
        # Create a couple of API keys first
        for i in range(2):
            data = {"name": f"Test API Key {i+1}"}
            client.post("/api/admin/keys/", json=data, headers=admin_headers)

        response = client.get("/api/admin/keys/", headers=admin_headers)

        assert response.status_code == 200
        data = response.json()
        assert "keys" in data
        assert "total" in data
        assert len(data["keys"]) == 2
        assert data["total"] == 2

    def test_list_api_keys_without_admin_token(self, client):
        """Test listing API keys without admin token fails"""
        response = client.get("/api/admin/keys/")

        assert response.status_code == 401

    def test_get_api_key_details(self, client, admin_headers):
        """Test getting specific API key details"""
        # Create API key first
        create_data = {"name": "Test API Key"}
        create_response = client.post("/api/admin/keys/", json=create_data, headers=admin_headers)
        api_key_id = create_response.json()["id"]

        response = client.get(f"/api/admin/keys/{api_key_id}", headers=admin_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Test API Key"
        assert data["is_active"] is True
        assert "key" not in data  # Key should not be returned in details

    def test_get_nonexistent_api_key(self, client, admin_headers):
        """Test getting non-existent API key"""
        response = client.get("/api/admin/keys/999", headers=admin_headers)

        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"].lower()

    def test_revoke_api_key(self, client, admin_headers):
        """Test revoking an API key"""
        # Create API key first
        create_data = {"name": "Test API Key"}
        create_response = client.post("/api/admin/keys/", json=create_data, headers=admin_headers)
        api_key_id = create_response.json()["id"]

        response = client.patch(f"/api/admin/keys/{api_key_id}/revoke", headers=admin_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["is_active"] is False

    def test_activate_api_key(self, client, admin_headers):
        """Test activating a revoked API key"""
        # Create and revoke API key first
        create_data = {"name": "Test API Key"}
        create_response = client.post("/api/admin/keys/", json=create_data, headers=admin_headers)
        api_key_id = create_response.json()["id"]
        client.patch(f"/api/admin/keys/{api_key_id}/revoke", headers=admin_headers)

        response = client.patch(f"/api/admin/keys/{api_key_id}/activate", headers=admin_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["is_active"] is True

    def test_delete_api_key(self, client, admin_headers):
        """Test deleting an API key"""
        # Create API key first
        create_data = {"name": "Test API Key"}
        create_response = client.post("/api/admin/keys/", json=create_data, headers=admin_headers)
        api_key_id = create_response.json()["id"]

        response = client.delete(f"/api/admin/keys/{api_key_id}", headers=admin_headers)

        assert response.status_code == 200
        data = response.json()
        assert "deleted successfully" in data["message"]

        # Verify it's actually deleted
        response = client.get(f"/api/admin/keys/{api_key_id}", headers=admin_headers)
        assert response.status_code == 404

    def test_delete_nonexistent_api_key(self, client, admin_headers):
        """Test deleting non-existent API key"""
        response = client.delete("/api/admin/keys/999", headers=admin_headers)

        assert response.status_code == 404

    def test_validate_api_key_success(self, client, api_headers):
        """Test successful API key validation"""
        response = client.get("/api/keys/validate", headers=api_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is True
        assert "name" in data

    def test_validate_api_key_invalid(self, client):
        """Test API key validation with invalid key"""
        headers = {"X-API-Key": "invalid-key"}
        response = client.get("/api/keys/validate", headers=headers)
        assert response.status_code == 401

    def test_validate_api_key_inactive(self, client, admin_headers, db_session):
        """Test API key validation with inactive key"""
        from app.auth import hash_api_key

        # Create inactive API key
        inactive_key = "inactive-test-key"
        api_key = ApiKey(key_hash=hash_api_key(inactive_key), name="Inactive Key", is_active=False)
        db_session.add(api_key)
        db_session.commit()

        headers = {"X-API-Key": inactive_key}
        response = client.get("/api/keys/validate", headers=headers)
        assert response.status_code == 401

    def test_validate_api_key_missing_header(self, client):
        """Test API key validation without header"""
        response = client.get("/api/keys/validate")

        assert response.status_code == 401

    def test_validate_api_key_malformed_header(self, client):
        """Test API key validation with malformed header"""
        headers = {"X-API-Key": ""}
        response = client.get("/api/keys/validate", headers=headers)

        assert response.status_code == 401
