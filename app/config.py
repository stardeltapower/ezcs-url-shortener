import os

from dotenv import load_dotenv

load_dotenv()


class Settings:
    BASE_URL: str = os.getenv("BASE_URL", "http://localhost:8000")
    REDIRECT_URL: str = os.getenv("REDIRECT_URL", "https://easycablesizing.com")
    SHORT_URL_LENGTH: int = int(os.getenv("SHORT_URL_LENGTH", "6"))
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL", "mysql+pymysql://username:password@localhost:3306/urlshortener"
    )
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-here")
    ADMIN_TOKEN: str = os.getenv("ADMIN_TOKEN", "admin-secret-token-change-this")
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")

    # Cache settings (in-memory cache)
    CACHE_TTL: int = int(os.getenv("CACHE_TTL", "3600"))  # 1 hour default
    CACHE_REFRESH_AHEAD: int = int(os.getenv("CACHE_REFRESH_AHEAD", "300"))  # 5 minutes
    CACHE_MAX_SIZE: int = int(os.getenv("CACHE_MAX_SIZE", "10000"))  # Max cached URLs
    ENABLE_CACHE: bool = os.getenv("ENABLE_CACHE", "true").lower() == "true"

    # Environment-specific settings
    @property
    def is_production(self) -> bool:
        """Check if running in production environment"""
        return self.ENVIRONMENT.lower() == "production"

    @property
    def is_development(self) -> bool:
        """Check if running in development environment"""
        return self.ENVIRONMENT.lower() == "development"

    @property
    def debug(self) -> bool:
        """Enable debug mode in development"""
        return self.is_development

    @property
    def log_level(self) -> str:
        """Set log level based on environment"""
        return "INFO" if self.is_production else "DEBUG"

    @property
    def docs_url(self) -> str | None:
        """API documentation URL - disabled in production for security"""
        return "/docs" if self.is_development else None

    @property
    def redoc_url(self) -> str | None:
        """ReDoc documentation URL - disabled in production for security"""
        return "/redoc" if self.is_development else None

    @property
    def openapi_url(self) -> str | None:
        """OpenAPI schema URL - disabled in production for security"""
        return "/openapi.json" if self.is_development else None

    @property
    def cors_origins(self) -> list[str]:
        """CORS origins - restrictive in production"""
        if self.is_development:
            return ["*"]  # Allow all origins in development
        else:
            # In production, only allow your domain
            return [self.BASE_URL, "https://localhost", "http://localhost"]


settings = Settings()
