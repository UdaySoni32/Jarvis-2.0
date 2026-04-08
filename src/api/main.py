"""
JARVIS 2.0 API Server

FastAPI-based REST API for remote access to JARVIS functionality.
Provides endpoints for chat, plugins, automation, and system management.
"""

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from contextlib import asynccontextmanager
import logging
from typing import AsyncGenerator

from .config import settings
from .routes import (
    chat_router,
    auth_router,
    plugins_router,
    system_router,
    websocket_router,
)
from .middleware.auth import AuthMiddleware
from .middleware.rate_limit import RateLimitMiddleware
from .middleware.logging import LoggingMiddleware

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    """Application lifespan manager"""
    # Startup
    logger.info("🚀 Starting JARVIS API Server...")
    logger.info(f"Environment: {settings.environment}")
    logger.info(f"Debug mode: {settings.debug}")
    logger.info(f"CORS enabled: {settings.cors_enabled}")
    
    yield
    
    # Shutdown
    logger.info("👋 Shutting down JARVIS API Server...")


# Create FastAPI application
app = FastAPI(
    title="JARVIS 2.0 API",
    description="AI-Powered Personal Assistant API",
    version="2.0.0",
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
    lifespan=lifespan,
)


# CORS Middleware
if settings.cors_enabled:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


# Compression Middleware
app.add_middleware(GZipMiddleware, minimum_size=1000)


# Custom Middleware
app.add_middleware(LoggingMiddleware)
app.add_middleware(RateLimitMiddleware)
app.add_middleware(AuthMiddleware)


# Exception Handlers
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors"""
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": "Validation Error",
            "detail": exc.errors(),
            "body": exc.body,
        },
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Internal Server Error",
            "message": str(exc) if settings.debug else "An error occurred",
        },
    )


# Health Check
@app.get("/health", tags=["System"])
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "version": "2.0.0",
        "environment": settings.environment,
    }


@app.get("/", tags=["System"])
async def root():
    """Root endpoint"""
    return {
        "message": "JARVIS 2.0 API",
        "version": "2.0.0",
        "docs": "/docs" if settings.debug else "disabled",
        "health": "/health",
    }


# Include Routers
app.include_router(auth_router, prefix="/api/v1/auth", tags=["Authentication"])
app.include_router(chat_router, prefix="/api/v1/chat", tags=["Chat"])
app.include_router(plugins_router, prefix="/api/v1/plugins", tags=["Plugins"])
app.include_router(system_router, prefix="/api/v1/system", tags=["System"])
app.include_router(websocket_router, prefix="/api/v1/ws", tags=["WebSocket"])


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "src.api.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level="info" if settings.debug else "warning",
    )
