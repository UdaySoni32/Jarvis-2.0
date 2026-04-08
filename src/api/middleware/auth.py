"""
Authentication Middleware

Validates JWT tokens and API keys for protected routes.
"""

from fastapi import Request, HTTPException, status, Depends
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Optional
import logging

from ..utils.auth import decode_token
from ..utils.database import SessionLocal, get_user, get_api_key
from ..models.user import User

logger = logging.getLogger(__name__)


async def get_current_user_from_token(token: str) -> User:
    """Get current user from JWT token (for WebSocket auth)"""
    payload = decode_token(token)
    
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )
    
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload"
        )
    
    db = SessionLocal()
    try:
        user = get_user(db, user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found"
            )
        return user
    finally:
        db.close()


async def get_current_user(request: Request) -> User:
    """Get current user from request state"""
    if not hasattr(request.state, 'user_id'):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    
    user_id = request.state.user_id
    db = SessionLocal()
    try:
        user = get_user(db, user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        return user
    finally:
        db.close()


async def get_current_user_optional(request: Request) -> Optional[User]:
    """Get current user from request state (optional)"""
    if not hasattr(request.state, 'user_id'):
        return None
    
    user_id = request.state.user_id
    db = SessionLocal()
    try:
        user = get_user(db, user_id)
        return user
    finally:
        db.close()


class AuthMiddleware(BaseHTTPMiddleware):
    """Authentication middleware for validating requests"""
    
    # Public routes that don't require authentication
    PUBLIC_ROUTES = [
        "/",
        "/health",
        "/docs",
        "/redoc",
        "/openapi.json",
        "/api/v1/auth/register",
        "/api/v1/auth/login",
    ]
    
    async def dispatch(self, request: Request, call_next):
        """Process request and validate authentication"""
        
        # Skip auth for public routes
        if any(request.url.path.startswith(route) for route in self.PUBLIC_ROUTES):
            return await call_next(request)
        
        # Get authorization header
        auth_header = request.headers.get("Authorization")
        api_key_header = request.headers.get("X-API-Key")
        
        # Validate token or API key
        if auth_header:
            # JWT token authentication
            if not auth_header.startswith("Bearer "):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid authorization header",
                )
            
            token = auth_header.replace("Bearer ", "")
            payload = decode_token(token)
            
            if not payload:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid or expired token",
                )
            
            # Add user ID to request state
            request.state.user_id = payload.get("sub")
            request.state.auth_type = "jwt"
        
        elif api_key_header:
            # API key authentication
            db = SessionLocal()
            try:
                from ..models.user import APIKey
                api_key_obj = db.query(APIKey).filter(APIKey.key == api_key_header).first()
                
                if not api_key_obj or not api_key_obj.is_active:
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Invalid API key",
                    )
                
                # Add user ID to request state
                request.state.user_id = api_key_obj.user_id
                request.state.auth_type = "api_key"
                request.state.api_key_id = api_key_obj.id
            
            finally:
                db.close()
        
        else:
            # No authentication provided
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        response = await call_next(request)
        return response
