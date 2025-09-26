from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.auth import get_current_api_key
from app.cache import get_cache_service
from app.database import get_db
from app.models import ApiKey, Url
from app.schemas import UrlCreate, UrlListResponse, UrlResponse, UrlUpdate
from app.utils import generate_unique_short_url, is_short_url_available

router = APIRouter(prefix="/api/urls", tags=["URLs"])


@router.post("/", response_model=UrlResponse, status_code=status.HTTP_201_CREATED)
def create_url(
    url_data: UrlCreate,
    db: Session = Depends(get_db),
    current_key: ApiKey = Depends(get_current_api_key),
):
    """Create a new short URL"""
    # Generate or validate short URL
    if url_data.short_url:
        # Check if custom short URL is available
        if not is_short_url_available(db, url_data.short_url):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Short URL already exists"
            )
        short_url = url_data.short_url
    else:
        # Generate unique short URL
        short_url = generate_unique_short_url(db)

    # Create URL record
    db_url = Url(
        short_url=short_url,
        original_url=str(url_data.original_url),
        expires_at=url_data.expires_at,
        api_key_id=current_key.id,
    )

    db.add(db_url)
    db.commit()
    db.refresh(db_url)

    return UrlResponse.model_validate(db_url)


@router.get("/", response_model=UrlListResponse)
def list_urls(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    current_key: ApiKey = Depends(get_current_api_key),
):
    """List URLs created by the current API key"""
    urls = db.query(Url).filter(Url.api_key_id == current_key.id).offset(skip).limit(limit).all()

    total = db.query(Url).filter(Url.api_key_id == current_key.id).count()

    return UrlListResponse(urls=[UrlResponse.model_validate(url) for url in urls], total=total)


@router.get("/{url_id}", response_model=UrlResponse)
def get_url(
    url_id: int,
    db: Session = Depends(get_db),
    current_key: ApiKey = Depends(get_current_api_key),
):
    """Get URL by ID"""
    url = db.query(Url).filter(Url.id == url_id, Url.api_key_id == current_key.id).first()

    if not url:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="URL not found")

    return UrlResponse.model_validate(url)


@router.get("/short/{short_url}", response_model=UrlResponse)
def get_url_by_short(
    short_url: str,
    db: Session = Depends(get_db),
    current_key: ApiKey = Depends(get_current_api_key),
):
    """Get URL by short URL code"""
    url = db.query(Url).filter(Url.short_url == short_url, Url.api_key_id == current_key.id).first()

    if not url:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Short URL not found")

    return UrlResponse.model_validate(url)


@router.put("/{url_id}", response_model=UrlResponse)
def update_url(
    url_id: int,
    url_data: UrlUpdate,
    db: Session = Depends(get_db),
    current_key: ApiKey = Depends(get_current_api_key),
    cache: get_cache_service = Depends(get_cache_service),
):
    """Update URL"""
    url = db.query(Url).filter(Url.id == url_id, Url.api_key_id == current_key.id).first()

    if not url:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="URL not found")

    # Invalidate cache for this URL
    cache.invalidate_url(url.short_url)

    # Update fields if provided
    if url_data.original_url is not None:
        url.original_url = str(url_data.original_url)
    if url_data.expires_at is not None:
        url.expires_at = url_data.expires_at

    db.commit()
    db.refresh(url)

    return UrlResponse.model_validate(url)


@router.delete("/{url_id}")
def delete_url(
    url_id: int,
    db: Session = Depends(get_db),
    current_key: ApiKey = Depends(get_current_api_key),
    cache: get_cache_service = Depends(get_cache_service),
):
    """Delete URL"""
    url = db.query(Url).filter(Url.id == url_id, Url.api_key_id == current_key.id).first()

    if not url:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="URL not found")

    # Invalidate cache for this URL
    cache.invalidate_url(url.short_url)

    db.delete(url)
    db.commit()

    return {"message": "URL deleted successfully"}


@router.get("/cache/stats")
def get_cache_stats(
    current_key: ApiKey = Depends(get_current_api_key),
    cache: get_cache_service = Depends(get_cache_service),
):
    """Get cache statistics (requires valid API key)"""
    return cache.get_stats()


@router.delete("/cache/clear")
def clear_cache(
    current_key: ApiKey = Depends(get_current_api_key),
    cache: get_cache_service = Depends(get_cache_service),
):
    """Clear all cache entries (requires valid API key)"""
    cache.clear()
    return {"message": "Cache cleared successfully"}
