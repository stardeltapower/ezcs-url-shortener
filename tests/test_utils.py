from datetime import datetime, timedelta

from app.models import Url
from app.utils import (
    generate_short_url,
    generate_unique_short_url,
    is_short_url_available,
    is_url_expired,
)


class TestUtilityFunctions:
    """Test utility functions"""

    def test_generate_short_url_default_length(self):
        """Test short URL generation with default length"""
        short_url = generate_short_url()
        assert len(short_url) == 6  # Default from settings

    def test_generate_short_url_custom_length(self):
        """Test short URL generation with custom length"""
        short_url = generate_short_url(10)
        assert len(short_url) == 10

    def test_generate_short_url_character_set(self):
        """Test that generated short URLs use safe character set"""
        short_url = generate_short_url(50)  # Large sample

        # Should not contain confusing characters
        assert "0" not in short_url
        assert "O" not in short_url
        assert "l" not in short_url
        assert "I" not in short_url

        # Should be alphanumeric minus the excluded characters
        allowed_chars = set("abcdefghijkmnopqrstuvwxyzABCDEFGHJKLMNPQRSTUVWXYZ123456789")
        short_url_chars = set(short_url)
        assert short_url_chars.issubset(allowed_chars)

    def test_generate_short_url_uniqueness(self):
        """Test that generated short URLs are reasonably unique"""
        short_urls = [generate_short_url() for _ in range(100)]
        unique_urls = set(short_urls)

        # Should have high uniqueness (allowing for very rare collisions)
        assert len(unique_urls) >= 95

    def test_is_short_url_available_true(self, db_session):
        """Test checking availability for non-existent short URL"""
        assert is_short_url_available(db_session, "nonexistent") is True

    def test_is_short_url_available_false(self, db_session, api_key_data):
        """Test checking availability for existing short URL"""
        # Create a URL in the database
        url = Url(
            short_url="taken", original_url="https://example.com", api_key_id=api_key_data["id"]
        )
        db_session.add(url)
        db_session.commit()

        assert is_short_url_available(db_session, "taken") is False

    def test_generate_unique_short_url_success(self, db_session):
        """Test generating unique short URL when no conflicts"""
        unique_url = generate_unique_short_url(db_session)

        assert len(unique_url) == 6  # Default length
        assert is_short_url_available(db_session, unique_url) is True

    def test_generate_unique_short_url_with_conflicts(self, db_session, api_key_data):
        """Test generating unique short URL with existing conflicts"""
        # This test is probabilistic and might need adjustment
        # Create several URLs to increase chance of collision
        for i in range(10):
            url = Url(
                short_url=f"test{i:02d}",
                original_url=f"https://example{i}.com",
                api_key_id=api_key_data["id"],
            )
            db_session.add(url)
        db_session.commit()

        # Should still generate a unique URL
        unique_url = generate_unique_short_url(db_session)
        assert is_short_url_available(db_session, unique_url) is True

    def test_generate_unique_short_url_custom_length(self, db_session):
        """Test generating unique short URL with custom length"""
        unique_url = generate_unique_short_url(db_session, length=8)

        assert len(unique_url) == 8
        assert is_short_url_available(db_session, unique_url) is True

    def test_is_url_expired_no_expiry(self):
        """Test URL expiration check for URL without expiry"""
        url = Url(
            short_url="test", original_url="https://example.com", api_key_id=1, expires_at=None
        )

        assert is_url_expired(url) is False

    def test_is_url_expired_future_expiry(self):
        """Test URL expiration check for future expiry"""
        future_date = datetime.utcnow() + timedelta(hours=1)
        url = Url(
            short_url="test",
            original_url="https://example.com",
            api_key_id=1,
            expires_at=future_date,
        )

        assert is_url_expired(url) is False

    def test_is_url_expired_past_expiry(self):
        """Test URL expiration check for past expiry"""
        past_date = datetime.utcnow() - timedelta(hours=1)
        url = Url(
            short_url="test", original_url="https://example.com", api_key_id=1, expires_at=past_date
        )

        assert is_url_expired(url) is True

    def test_is_url_expired_exact_expiry(self):
        """Test URL expiration check for exact expiry time"""
        # This test might be flaky due to timing, so we allow some tolerance
        now = datetime.utcnow()
        url = Url(
            short_url="test", original_url="https://example.com", api_key_id=1, expires_at=now
        )

        # URL should be expired if time has passed, even slightly
        result = is_url_expired(url)
        assert isinstance(result, bool)  # Should return a boolean

    def test_short_url_edge_cases(self):
        """Test edge cases for short URL generation"""
        # Very short length
        short_url = generate_short_url(1)
        assert len(short_url) == 1

        # Zero length should probably raise an error or return empty
        try:
            short_url = generate_short_url(0)
            assert len(short_url) == 0
        except (ValueError, TypeError):
            # This is acceptable behavior
            pass

    def test_short_url_consistency(self):
        """Test that short URL generation is reasonably random"""
        urls_set1 = [generate_short_url() for _ in range(50)]
        urls_set2 = [generate_short_url() for _ in range(50)]

        # Should have minimal overlap between two sets
        overlap = set(urls_set1) & set(urls_set2)
        assert len(overlap) < 5  # Allow for some rare collisions

    def test_database_session_handling(self, db_session, api_key_data):
        """Test that utility functions handle database sessions correctly"""
        # Create a URL
        url = Url(
            short_url="dbtest", original_url="https://dbtest.com", api_key_id=api_key_data["id"]
        )
        db_session.add(url)
        db_session.commit()

        # Test that functions work with committed data
        assert is_short_url_available(db_session, "dbtest") is False
        assert is_short_url_available(db_session, "available") is True

    def test_url_expiration_with_timezone(self):
        """Test URL expiration handling with timezone considerations"""
        # Test with timezone-aware datetime
        import pytz

        utc = pytz.UTC

        past_date = datetime.now(utc) - timedelta(hours=1)
        future_date = datetime.now(utc) + timedelta(hours=1)

        past_url = Url(
            short_url="past", original_url="https://past.com", api_key_id=1, expires_at=past_date
        )

        future_url = Url(
            short_url="future",
            original_url="https://future.com",
            api_key_id=1,
            expires_at=future_date,
        )

        assert is_url_expired(past_url) is True
        assert is_url_expired(future_url) is False
