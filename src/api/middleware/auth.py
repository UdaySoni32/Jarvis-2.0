"""
Authentication Middleware

Validates JWT tokens and API keys for protected routes.
"""

from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Optional
import logging

from ..utils import decode_token, get_api_key
from ..utils.database import SessionLocal

logger = logging.getLogger(__name__)


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
                api_key = get_api_key(db, api_key_header)
                
                if not api_key:
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Invalid API key",
                    )
                
                # Add user ID to request state
                request.state.user_id = api_key.user_id
                request.state.auth_type = "api_key"
                request.state.api_key_id = api_key.id
            
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
