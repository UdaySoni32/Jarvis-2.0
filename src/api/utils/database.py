"""
Database Utilities

Database connection, session management, and common queries.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator
import logging

from ..config import settings
from ..models.user import Base

logger = logging.getLogger(__name__)

# Create database engine
engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False} if "sqlite" in settings.database_url else {},
    echo=settings.debug,
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    """Initialize database - create all tables"""
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("✅ Database initialized successfully")
    except Exception as e:
        logger.error(f"❌ Failed to initialize database: {e}")
        raise


def get_db() -> Generator[Session, None, None]:
    """
    Get database session
    
    Yields:
        Database session
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_user_by_username(db: Session, username: str):
    """Get user by username"""
    from ..models.user import User
    return db.query(User).filter(User.username == username).first()


def get_user_by_email(db: Session, email: str):
    """Get user by email"""
    from ..models.user import User
    return db.query(User).filter(User.email == email).first()


def get_user_by_id(db: Session, user_id: str):
    """Get user by ID"""
    from ..models.user import User
    return db.query(User).filter(User.id == user_id).first()


def create_user(db: Session, username: str, email: str, hashed_password: str, full_name: str = None):
    """Create new user"""
    from ..models.user import User
    from datetime import datetime
    
    user = User(
        username=username,
        email=email,
        hashed_password=hashed_password,
        full_name=full_name,
        created_at=datetime.utcnow(),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def get_api_key(db: Session, key: str):
    """Get API key by key string"""
    from ..models.user import APIKey
    return db.query(APIKey).filter(APIKey.key == key, APIKey.is_active == True).first()


def create_api_key(db: Session, user_id: str, name: str, key: str, rate_limit: int = 100, expires_at=None):
    """Create new API key"""
    from ..models.user import APIKey
    from datetime import datetime
    
    api_key = APIKey(
        user_id=user_id,
        name=name,
        key=key,
        rate_limit=rate_limit,
        expires_at=expires_at,
        created_at=datetime.utcnow(),
    )
    db.add(api_key)
    db.commit()
    db.refresh(api_key)
    return api_key
