from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from app.config import settings

# Create engine with connection pool settings to handle MySQL connection issues
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,  # Validates connections before use, auto-reconnects if dropped
    pool_recycle=3600,  # Recycle connections every hour to prevent timeouts
    pool_size=20,  # Connection pool size for concurrent requests
    max_overflow=0,  # No overflow connections to maintain predictable behavior
    pool_timeout=30,  # Timeout when getting connection from pool
    echo=settings.debug,  # Log SQL queries in debug mode
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
