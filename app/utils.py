import secrets
import string
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.config import settings
from app.models import Url


def generate_short_url(length: int = None) -> str:
    """Generate a random short URL code"""
    if length is None:
        length = settings.SHORT_URL_LENGTH

    # Use alphanumeric characters (avoiding confusing ones like 0, O, l, I)
    alphabet = string.ascii_letters + string.digits
    alphabet = alphabet.replace("0", "").replace("O", "").replace("l", "").replace("I", "")

    return "".join(secrets.choice(alphabet) for _ in range(length))


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
