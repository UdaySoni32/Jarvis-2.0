"""
Logging Middleware

Logs all API requests and responses for monitoring and debugging.
"""

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
import time
import logging

logger = logging.getLogger(__name__)


class LoggingMiddleware(BaseHTTPMiddleware):
    """Request/response logging middleware"""
    
    async def dispatch(self, request: Request, call_next):
        """Log request and response"""
        
        # Start timer
        start_time = time.time()
        
        # Log request
        logger.info(
            f"→ {request.method} {request.url.path} "
            f"from {request.client.host}"
        )
        
        # Process request
        try:
            response = await call_next(request)
            
            # Calculate duration
            duration = time.time() - start_time
            
            # Log response
            logger.info(
                f"← {request.method} {request.url.path} "
                f"Status: {response.status_code} "
                f"Duration: {duration:.3f}s"
            )
            
            # Add custom headers
            response.headers["X-Process-Time"] = str(duration)
            
            return response
        
        except Exception as e:
            duration = time.time() - start_time
            logger.error(
                f"✗ {request.method} {request.url.path} "
                f"Error: {str(e)} "
                f"Duration: {duration:.3f}s"
            )
            raise
