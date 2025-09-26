import asyncio
import logging
import threading
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from cachetools import TTLCache
from sqlalchemy.orm import Session

from app.config import settings
from app.models import Url
from app.utils import is_url_expired, retry_db_operation

logger = logging.getLogger(__name__)


@dataclass
class CacheEntry:
    """Cache entry with metadata for background refresh"""

    data: Dict[str, Any]
    cached_at: float
    refreshing: bool = False


class InMemoryCache:
    """
    High-performance in-memory cache with background refresh.

    Features:
    - TTL-based eviction using cachetools
    - Background refresh for hot data (refresh-ahead pattern)
    - Thread-safe operations
    - URL expiration awareness
    - Zero external dependencies
    """

    def __init__(self):
        self.cache: TTLCache = TTLCache(maxsize=settings.CACHE_MAX_SIZE, ttl=settings.CACHE_TTL)
        self._lock = threading.RLock()
        self._background_tasks: Dict[str, asyncio.Task] = {}
        self.enabled = settings.ENABLE_CACHE

        if self.enabled:
            logger.info(
                f"In-memory cache initialized (max_size={settings.CACHE_MAX_SIZE}, ttl={settings.CACHE_TTL}s)"
            )
        else:
            logger.info("Caching disabled in configuration")

    def _serialize_url(self, url: Url) -> Dict[str, Any]:
        """Convert URL object to dict for caching"""
        return {
            "id": url.id,
            "short_url": url.short_url,
            "original_url": url.original_url,
            "expires_at": url.expires_at.isoformat() if url.expires_at else None,
            "api_key_id": url.api_key_id,
            "created_at": (
                url.created_at.isoformat()
                if hasattr(url, "created_at") and url.created_at
                else None
            ),
        }

    @retry_db_operation(max_retries=2, delay=0.05, backoff=2.0)
    def _fetch_from_db(self, db: Session, short_url: str) -> Optional[Url]:
        """Fetch URL from database with retry logic"""
        return db.query(Url).filter(Url.short_url == short_url).first()

    async def _background_refresh(self, db: Session, short_url: str):
        """Background task to refresh cache entry"""
        try:
            # Mark as refreshing to prevent multiple refresh tasks
            with self._lock:
                if short_url in self.cache:
                    entry = self.cache[short_url]
                    entry.refreshing = True

            url = self._fetch_from_db(db, short_url)

            with self._lock:
                if url and not is_url_expired(url):
                    # Update cache with fresh data
                    fresh_data = self._serialize_url(url)
                    self.cache[short_url] = CacheEntry(
                        data=fresh_data, cached_at=time.time(), refreshing=False
                    )
                    logger.debug(f"Background refreshed cache for {short_url}")
                elif short_url in self.cache:
                    # URL expired or deleted, remove from cache
                    del self.cache[short_url]
                    logger.debug(f"Removed expired/deleted URL {short_url} from cache")

        except Exception as e:
            logger.error(f"Background refresh failed for {short_url}: {e}")
            # Reset refreshing flag on error
            with self._lock:
                if short_url in self.cache:
                    self.cache[short_url].refreshing = False
        finally:
            # Remove task from tracking
            if short_url in self._background_tasks:
                del self._background_tasks[short_url]

    def _is_url_data_expired(self, url_data: Dict[str, Any]) -> bool:
        """Check if cached URL data represents an expired URL"""
        expires_at_str = url_data.get("expires_at")
        if not expires_at_str:
            return False

        expires_at = datetime.fromisoformat(expires_at_str.replace("Z", "+00:00"))
        return datetime.now(timezone.utc) > expires_at

    def get_url(self, db: Session, short_url: str) -> Optional[Dict[str, Any]]:
        """
        Get URL with cache-aside pattern and background refresh.

        Strategy:
        1. Try cache first
        2. If cache miss, fetch from DB and cache
        3. If cache hit but needs refresh, return cached data and refresh in background
        4. Handle URL expiration at both cache and DB level
        """
        if not self.enabled:
            # Cache disabled, go directly to database
            url = self._fetch_from_db(db, short_url)
            if url and not is_url_expired(url):
                return self._serialize_url(url)
            return None

        # Try cache first
        with self._lock:
            if short_url in self.cache:
                entry = self.cache[short_url]

                # Check if cached URL is expired
                if self._is_url_data_expired(entry.data):
                    del self.cache[short_url]
                    logger.debug(f"Removed expired URL {short_url} from cache")
                else:
                    # Cache hit - check if we should refresh in background
                    age = time.time() - entry.cached_at
                    refresh_threshold = settings.CACHE_TTL - settings.CACHE_REFRESH_AHEAD

                    if (
                        age >= refresh_threshold
                        and not entry.refreshing
                        and short_url not in self._background_tasks
                    ):

                        # Start background refresh
                        task = asyncio.create_task(self._background_refresh(db, short_url))
                        self._background_tasks[short_url] = task
                        logger.debug(f"Started background refresh for {short_url}")

                    logger.debug(f"Cache hit for {short_url}")
                    return entry.data

        # Cache miss - fetch from database
        logger.debug(f"Cache miss for {short_url}")
        url = self._fetch_from_db(db, short_url)

        if url and not is_url_expired(url):
            url_data = self._serialize_url(url)

            # Cache the result
            with self._lock:
                self.cache[short_url] = CacheEntry(data=url_data, cached_at=time.time())

            logger.debug(f"Cached URL {short_url}")
            return url_data

        return None

    def invalidate_url(self, short_url: str):
        """Invalidate cache entry (called when URL is updated/deleted)"""
        with self._lock:
            if short_url in self.cache:
                del self.cache[short_url]
                logger.debug(f"Invalidated cache for {short_url}")

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        if not self.enabled:
            return {"status": "disabled"}

        with self._lock:
            return {
                "status": "enabled",
                "size": len(self.cache),
                "max_size": self.cache.maxsize,
                "ttl": self.cache.ttl,
                "refresh_ahead_seconds": settings.CACHE_REFRESH_AHEAD,
                "active_refresh_tasks": len(self._background_tasks),
            }

    def clear(self):
        """Clear all cache entries"""
        with self._lock:
            self.cache.clear()
            logger.info("Cache cleared")


# Global cache instance
cache_service = InMemoryCache()


def get_cache_service() -> InMemoryCache:
    """Dependency to get cache service"""
    return cache_service
