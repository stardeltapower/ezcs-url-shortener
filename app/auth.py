import secrets
import string
from typing import Optional

from fastapi import Depends, Header, HTTPException, status
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models import ApiKey

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def generate_api_key(length: int = 32) -> str:
    """Generate a random API key"""
    # Use alphanumeric characters (avoiding confusing ones like 0, O, l, I)
    alphabet = string.ascii_letters + string.digits
    alphabet = alphabet.replace("0", "").replace("O", "").replace("l", "").replace("I", "")

    return "".join(secrets.choice(alphabet) for _ in range(length))


def hash_api_key(api_key: str) -> str:
    """Hash an API key"""
    if not api_key:
        raise ValueError("API key cannot be empty")
    return pwd_context.hash(api_key)


def verify_api_key(plain_key: str, hashed_key: str) -> bool:
    """Verify an API key against its hash"""
    try:
        if not plain_key or not hashed_key:
            return False
        return pwd_context.verify(plain_key, hashed_key)
    except Exception:
        # Handle any password verification errors gracefully
        return False


def get_api_key_from_db(db: Session, api_key: str) -> Optional[ApiKey]:
    """Get API key from database and verify it"""
    if not api_key:
        return None

    # Get all active API keys and check each one
    api_keys = db.query(ApiKey).filter(ApiKey.is_active == True).all()

    for key_record in api_keys:
        if verify_api_key(api_key, key_record.key_hash):
            return key_record

    return None


def get_current_api_key(
    x_api_key: Optional[str] = Header(None, alias="X-API-Key"), db: Session = Depends(get_db)
) -> ApiKey:
    """Get current API key from header"""
    if not x_api_key:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="API key required")

    api_key = get_api_key_from_db(db, x_api_key)
    if not api_key:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API key")

    return api_key


def verify_admin_token(x_admin_token: Optional[str] = Header(None, alias="X-Admin-Token")) -> bool:
    """Verify admin token"""
    if not x_admin_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Admin token required")

    if x_admin_token != settings.ADMIN_TOKEN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid admin token")

    return True
