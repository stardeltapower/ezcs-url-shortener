import logging
import time

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from sqlalchemy.exc import DisconnectionError, OperationalError
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


def _lookup_url_with_retry(db: Session, short_url: str, max_retries: int = 3) -> Url:
    """Lookup URL with retry logic for connection issues"""
    for attempt in range(max_retries):
        try:
            return db.query(Url).filter(Url.short_url == short_url).first()
        except (DisconnectionError, OperationalError) as e:
            error_msg = str(e).lower()
            # Check if it's a connection-related error we should retry
            retry_conditions = [
                "mysql server has gone away",
                "broken pipe",
                "connection lost",
                "lost connection"
            ]

            should_retry = any(condition in error_msg for condition in retry_conditions)

            if should_retry and attempt < max_retries - 1:
                logger.warning(f"Database connection error (attempt {attempt + 1}): {e}")
                time.sleep(0.1 * (2 ** attempt))  # Exponential backoff
                continue
            else:
                logger.error(f"Database lookup failed after {attempt + 1} attempts: {e}")
                raise


@app.get("/{short_url}")
def redirect_short_url(short_url: str, db: Session = Depends(get_db)):
    """Redirect to the original URL using the short URL"""
    logger.debug(f"Looking up short URL: {short_url}")

    try:
        url = _lookup_url_with_retry(db, short_url)
    except Exception as e:
        logger.error(f"Failed to lookup {short_url}: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service temporarily unavailable"
        ) from e

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
def health_check(db: Session = Depends(get_db)):
    """Health check endpoint with database connectivity test"""
    health_status = {
        "status": "healthy",
        "message": "URL Shortener API is running",
        "environment": settings.ENVIRONMENT,
        "debug": settings.debug,
        "database": {"status": "unknown"}
    }

    # Test database connectivity
    try:
        # Simple query to test database connection
        db.execute("SELECT 1")
        health_status["database"]["status"] = "connected"
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        health_status["status"] = "unhealthy"
        health_status["database"]["status"] = "disconnected"
        health_status["database"]["error"] = str(e)

        # Return 503 Service Unavailable if database is down
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=health_status
        ) from e

    return health_status


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level=settings.log_level.lower(),
        reload=settings.is_development,  # Auto-reload only in development
    )
