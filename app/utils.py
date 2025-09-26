import logging
import secrets
import string
import time
from datetime import datetime, timezone
from functools import wraps
from typing import Any, Callable

from sqlalchemy.exc import DisconnectionError, OperationalError
from sqlalchemy.orm import Session

from app.config import settings
from app.models import Url

logger = logging.getLogger(__name__)


def generate_short_url(length: int = None) -> str:
    """Generate a random short URL code"""
    if length is None:
        length = settings.SHORT_URL_LENGTH

    # Use alphanumeric characters (avoiding confusing ones like 0, O, l, I)
    alphabet = string.ascii_letters + string.digits
    alphabet = alphabet.replace("0", "").replace("O", "").replace("l", "").replace("I", "")

    return "".join(secrets.choice(alphabet) for _ in range(length))


def retry_db_operation(max_retries: int = 3, delay: float = 0.1, backoff: float = 2.0):
    """
    Retry decorator for database operations that may fail due to connection issues.

    Args:
        max_retries: Maximum number of retry attempts
        delay: Initial delay between retries in seconds
        backoff: Multiplier for delay after each retry
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            last_exception = None
            current_delay = delay

            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except (DisconnectionError, OperationalError) as e:
                    last_exception = e
                    error_msg = str(e).lower()

                    # Check if it's a connection-related error we should retry
                    retry_conditions = [
                        "mysql server has gone away",
                        "broken pipe",
                        "connection lost",
                        "lost connection",
                        "can't connect to mysql server",
                        "connection was killed",
                    ]

                    should_retry = any(condition in error_msg for condition in retry_conditions)

                    if not should_retry or attempt == max_retries:
                        logger.error(f"Database operation failed after {attempt + 1} attempts: {e}")
                        raise e

                    logger.warning(
                        f"Database connection error (attempt {attempt + 1}/{max_retries + 1}): {e}"
                    )
                    logger.info(f"Retrying in {current_delay:.2f} seconds...")

                    time.sleep(current_delay)
                    current_delay *= backoff

            # This should never be reached, but just in case
            raise last_exception

        return wrapper

    return decorator


@retry_db_operation(max_retries=3, delay=0.1, backoff=2.0)
def is_short_url_available(db: Session, short_url: str) -> bool:
    """Check if a short URL is available"""
    existing = db.query(Url).filter(Url.short_url == short_url).first()
    return existing is None


def generate_unique_short_url(db: Session, length: int = None) -> str:
    """Generate a unique short URL that doesn't exist in database"""
    max_attempts = 100
    attempts = 0

    while attempts < max_attempts:
        short_url = generate_short_url(length)
        if is_short_url_available(db, short_url):
            return short_url
        attempts += 1

    # If we can't find a unique URL after max_attempts, increase length
    return generate_unique_short_url(db, (length or settings.SHORT_URL_LENGTH) + 1)


def is_url_expired(url: Url) -> bool:
    """Check if a URL has expired"""
    if url.expires_at is None:
        return False

    # Handle both timezone-aware and naive datetimes
    now = datetime.now(timezone.utc)
    expires_at = url.expires_at

    # If expires_at is naive, assume it's UTC
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)

    # If now is naive (shouldn't happen but just in case)
    if now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)

    return now > expires_at
