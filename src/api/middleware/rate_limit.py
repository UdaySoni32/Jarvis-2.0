"""
Rate Limiting Middleware

Limits request rate per user/API key to prevent abuse.
"""

from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
import time
from collections import defaultdict
import logging

from ..config import settings

logger = logging.getLogger(__name__)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limiting middleware"""
    
    def __init__(self, app):
        super().__init__(app)
        # Store request counts: {user_id: [(timestamp, count), ...]}
        self.request_counts = defaultdict(list)
        self.cleanup_interval = 60  # seconds
        self.last_cleanup = time.time()
    
    async def dispatch(self, request: Request, call_next):
        """Process request and check rate limits"""
        
        if not settings.rate_limit_enabled:
            return await call_next(request)
        
        # Skip rate limiting for public routes
        public_routes = ["/", "/health", "/docs", "/redoc", "/openapi.json"]
        if any(request.url.path.startswith(route) for route in public_routes):
            return await call_next(request)
        
        # Get user identifier (from auth middleware)
        user_id = getattr(request.state, "user_id", None)
        if not user_id:
            # Use IP address as fallback
            user_id = request.client.host
        
        # Check rate limit
        current_time = time.time()
        period_start = current_time - settings.rate_limit_period
        
        # Get requests in current period
        user_requests = self.request_counts[user_id]
        recent_requests = [t for t in user_requests if t > period_start]
        
        # Check if limit exceeded
        if len(recent_requests) >= settings.rate_limit_requests:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Rate limit exceeded. Max {settings.rate_limit_requests} requests per {settings.rate_limit_period} seconds.",
                headers={
                    "X-RateLimit-Limit": str(settings.rate_limit_requests),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(int(period_start + settings.rate_limit_period)),
                },
            )
        
        # Add current request
        recent_requests.append(current_time)
        self.request_counts[user_id] = recent_requests
        
        # Cleanup old entries periodically
        if current_time - self.last_cleanup > self.cleanup_interval:
            self._cleanup_old_entries(period_start)
            self.last_cleanup = current_time
        
        # Add rate limit headers to response
        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(settings.rate_limit_requests)
        response.headers["X-RateLimit-Remaining"] = str(settings.rate_limit_requests - len(recent_requests))
        response.headers["X-RateLimit-Reset"] = str(int(period_start + settings.rate_limit_period))
        
        return response
    
    def _cleanup_old_entries(self, period_start: float):
        """Remove old request entries"""
        for user_id in list(self.request_counts.keys()):
            self.request_counts[user_id] = [
                t for t in self.request_counts[user_id] if t > period_start
            ]
            
            # Remove empty entries
            if not self.request_counts[user_id]:
                del self.request_counts[user_id]
