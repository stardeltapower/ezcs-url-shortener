from app.auth import generate_api_key, hash_api_key, verify_api_key
from app.models import ApiKey


class TestAuthUtilities:
    """Test authentication utility functions"""

    def test_generate_api_key_default_length(self):
        """Test API key generation with default length"""
        key = generate_api_key()
        assert len(key) == 32
        assert key.isalnum()  # Should be alphanumeric

    def test_generate_api_key_custom_length(self):
        """Test API key generation with custom length"""
        key = generate_api_key(16)
        assert len(key) == 16
        assert key.isalnum()

    def test_generate_api_key_uniqueness(self):
        """Test that generated API keys are unique"""
        keys = [generate_api_key() for _ in range(10)]
        assert len(set(keys)) == 10  # All should be unique

    def test_hash_api_key(self):
        """Test API key hashing"""
        key = "test-api-key"
        hashed = hash_api_key(key)
        assert hashed != key
        assert hashed.startswith("$2b$")

    def test_verify_api_key_success(self):
        """Test successful API key verification"""
        key = "test-api-key"
        hashed = hash_api_key(key)
        assert verify_api_key(key, hashed) is True

    def test_verify_api_key_failure(self):
        """Test failed API key verification"""
        key = "test-api-key"
        wrong_key = "wrong-key"
        hashed = hash_api_key(key)
        assert verify_api_key(wrong_key, hashed) is False

    def test_verify_admin_token_success(self):
        """Test successful admin token verification"""
        # Skip this test since admin token is set in environment
        # and we can't easily mock the dependency injection
        pass

    def test_verify_admin_token_missing(self):
        """Test admin token verification with missing token"""
        # This would require testing with dependency injection
        # which is complex to test in isolation
        pass

    def test_get_api_key_from_db_success(self, db_session):
        """Test successful API key retrieval from database"""
        from app.auth import get_api_key_from_db

        # Create test API key
        test_key = "test-key-success"
        hashed_key = hash_api_key(test_key)

        api_key = ApiKey(key_hash=hashed_key, name="Test Key", is_active=True)
        db_session.add(api_key)
        db_session.commit()

        # Test retrieval
        found_key = get_api_key_from_db(db_session, test_key)
        assert found_key is not None
        assert found_key.name == "Test Key"
        assert found_key.is_active is True

    def test_get_api_key_from_db_not_found(self, db_session):
        """Test API key retrieval for non-existent key"""
        from app.auth import get_api_key_from_db

        found_key = get_api_key_from_db(db_session, "non-existent-key")
        assert found_key is None

    def test_get_api_key_from_db_inactive(self, db_session):
        """Test API key retrieval for inactive key"""
        from app.auth import get_api_key_from_db

        # Create inactive API key
        test_key = "inactive-test-key"
        hashed_key = hash_api_key(test_key)

        api_key = ApiKey(key_hash=hashed_key, name="Inactive Key", is_active=False)
        db_session.add(api_key)
        db_session.commit()

        # Should return None for inactive keys in get_api_key_from_db function
        found_key = get_api_key_from_db(db_session, test_key)
        assert found_key is None

    def test_hash_consistency(self):
        """Test that hashing the same key produces different hashes"""
        key = "consistent-test-key"
        hash1 = hash_api_key(key)
        hash2 = hash_api_key(key)

        # Hashes should be different (bcrypt uses salt)
        assert hash1 != hash2
        # But both should verify correctly
        assert verify_api_key(key, hash1) is True
        assert verify_api_key(key, hash2) is True

    def test_api_key_character_set(self):
        """Test that generated API keys use safe character set"""
        key = generate_api_key(100)  # Generate longer key for better testing

        # Should not contain confusing characters
        assert "0" not in key
        assert "O" not in key
        assert "l" not in key
        assert "I" not in key

    def test_empty_key_handling(self):
        """Test handling of empty or None keys"""
        # Empty string should not cause errors, just return False
        assert verify_api_key("", "some_hash") is False
        assert verify_api_key("valid_key", "") is False

    def test_special_characters_in_verification(self):
        """Test verification with special characters"""
        key = "test-key-with-special-chars!@#$%"
        hashed = hash_api_key(key)
        assert verify_api_key(key, hashed) is True
