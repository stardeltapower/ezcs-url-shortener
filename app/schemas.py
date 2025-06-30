from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


# API Key schemas
class ApiKeyCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, description="Name for the API key")

    @field_validator("name")
    @classmethod
    def validate_name(cls, v):
        if not v or not v.strip():
            raise ValueError("Name cannot be empty")
        return v.strip()


class ApiKeyResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    key: str  # Only returned on creation
    is_active: bool
    created_at: datetime


class ApiKeyInfo(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    is_active: bool
    created_at: datetime


# URL schemas
class UrlCreate(BaseModel):
    original_url: str  # Changed from HttpUrl to str to preserve exact format
    short_url: Optional[str] = None
    expires_at: Optional[datetime] = None

    @field_validator("original_url")
    @classmethod
    def validate_url(cls, v):
        # Basic URL validation without reformatting
        if not isinstance(v, str):
            v = str(v)

        # Simple validation - must start with http:// or https://
        if not (v.startswith("http://") or v.startswith("https://")):
            raise ValueError("URL must start with http:// or https://")

        # Additional basic validation
        if len(v) < 10 or " " in v:
            raise ValueError("Invalid URL format")

        return v


class UrlResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    short_url: str
    original_url: str
    created_at: datetime
    expires_at: Optional[datetime] = None


class UrlUpdate(BaseModel):
    original_url: Optional[str] = None  # Changed from HttpUrl to str
    expires_at: Optional[datetime] = None

    @field_validator("original_url")
    @classmethod
    def validate_url(cls, v):
        if v is None:
            return v

        # Same validation as UrlCreate
        if not isinstance(v, str):
            v = str(v)

        if not (v.startswith("http://") or v.startswith("https://")):
            raise ValueError("URL must start with http:// or https://")

        if len(v) < 10 or " " in v:
            raise ValueError("Invalid URL format")

        return v


# List responses
class UrlListResponse(BaseModel):
    urls: List[UrlResponse]
    total: int


class ApiKeyListResponse(BaseModel):
    keys: List[ApiKeyInfo]  # Fixed field name to match router
    total: int
