"""
Authentication Routes

User registration, login, token refresh, and API key management.
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import Optional

from . import auth_router
from ..schemas import (
    UserCreate,
    UserResponse,
    LoginRequest,
    Token,
)
from ..utils import (
    get_db,
    verify_password,
    get_password_hash,
    create_access_token,
    create_refresh_token,
    decode_token,
    generate_api_key,
    get_user_by_username,
    get_user_by_email,
    get_user_by_id,
    create_user,
    create_api_key,
)
from ..config import settings

security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """Get current authenticated user from JWT token"""
    token = credentials.credentials
    
    payload = decode_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type",
        )
    
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
        )
    
    user = get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive",
        )
    
    return user


@auth_router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserCreate, db: Session = Depends(get_db)):
    """
    Register a new user
    
    Creates a new user account with the provided credentials.
    """
    # Check if username already exists
    existing_user = get_user_by_username(db, user_data.username)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered",
        )
    
    # Check if email already exists
    existing_email = get_user_by_email(db, user_data.email)
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )
    
    # Create user
    hashed_password = get_password_hash(user_data.password)
    user = create_user(
        db,
        username=user_data.username,
        email=user_data.email,
        hashed_password=hashed_password,
        full_name=user_data.full_name,
    )
    
    return user


@auth_router.post("/login", response_model=Token)
async def login(login_data: LoginRequest, db: Session = Depends(get_db)):
    """
    User login
    
    Authenticate user and return JWT tokens.
    """
    # Get user
    user = get_user_by_username(db, login_data.username)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
        )
    
    # Verify password
    if not verify_password(login_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
        )
    
    # Check if user is active
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive",
        )
    
    # Update last login
    user.last_login = datetime.utcnow()
    db.commit()
    
    # Create tokens
    access_token = create_access_token({"sub": user.id})
    refresh_token = create_refresh_token({"sub": user.id})
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "expires_in": settings.access_token_expire_minutes * 60,
    }


@auth_router.post("/refresh", response_model=Token)
async def refresh_token(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """
    Refresh access token
    
    Use refresh token to get a new access token.
    """
    token = credentials.credentials
    
    payload = decode_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )
    
    if payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type",
        )
    
    user_id = payload.get("sub")
    user = get_user_by_id(db, user_id)
    
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid user",
        )
    
    # Create new tokens
    access_token = create_access_token({"sub": user.id})
    refresh_token_new = create_refresh_token({"sub": user.id})
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token_new,
        "token_type": "bearer",
        "expires_in": settings.access_token_expire_minutes * 60,
    }


@auth_router.get("/me", response_model=UserResponse)
async def get_me(current_user = Depends(get_current_user)):
    """
    Get current user information
    
    Returns the authenticated user's profile.
    """
    return current_user


@auth_router.post("/api-key")
async def create_user_api_key(
    name: str,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create API key for current user
    
    Generate a new API key for programmatic access.
    """
    # Generate API key
    api_key = generate_api_key()
    
    # Save to database
    db_api_key = create_api_key(
        db,
        user_id=current_user.id,
        name=name,
        key=api_key,
        rate_limit=100,
    )
    
    return {
        "id": db_api_key.id,
        "name": db_api_key.name,
        "key": api_key,  # Only shown once
        "rate_limit": db_api_key.rate_limit,
        "created_at": db_api_key.created_at,
    }
