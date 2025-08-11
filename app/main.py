import logging

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.config import settings
from app.database import engine, get_db
from app.models import Base, Url
from app.routers import api_keys, urls
from app.utils import is_url_expired

# Configure logging based on environment
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Create database tables
Base.metadata.create_all(bind=engine)

# Create FastAPI app with environment-specific configuration
app = FastAPI(
    title="ezcs URL Shortener API",
    description="A simple URL shortener service for ezcs.to with API key authentication",
    version="0.1.0",
    debug=settings.debug,
    docs_url=settings.docs_url,
    redoc_url=settings.redoc_url,
    openapi_url=settings.openapi_url,
)

# Add CORS middleware with environment-specific origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
    allow_headers=["*"],
)

# Log startup information
logger.info(f"Starting URL Shortener API in {settings.ENVIRONMENT} mode")
logger.info(f"Debug mode: {settings.debug}")
if settings.is_development:
    logger.info(f"API Documentation available at: {settings.BASE_URL}{settings.docs_url}")
else:
    logger.info("API Documentation disabled in production mode")

# Include routers
app.include_router(api_keys.router)  # Admin API key management
app.include_router(api_keys.public_router)  # Public API key validation
app.include_router(urls.router)


@app.get("/")
def root():
    """Redirect to the configured redirect URL"""
    logger.debug(f"Root redirect to: {settings.REDIRECT_URL}")
    return RedirectResponse(url=settings.REDIRECT_URL)


@app.get("/{short_url}")
def redirect_short_url(short_url: str, db: Session = Depends(get_db)):
    """Redirect to the original URL using the short URL"""
    logger.debug(f"Looking up short URL: {short_url}")

    url = db.query(Url).filter(Url.short_url == short_url).first()

    if not url:
        logger.warning(f"Short URL not found: {short_url}")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Short URL not found")

    # Check if URL has expired
    if is_url_expired(url):
        logger.warning(f"Expired short URL accessed: {short_url}")
        raise HTTPException(status_code=status.HTTP_410_GONE, detail="Short URL has expired")

    logger.info(f"Redirecting {short_url} to {url.original_url}")
    return RedirectResponse(url=str(url.original_url), status_code=307)


@app.get("/api/health")
def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "message": "URL Shortener API is running",
        "environment": settings.ENVIRONMENT,
        "debug": settings.debug,
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level=settings.log_level.lower(),
        reload=settings.is_development,  # Auto-reload only in development
    )
