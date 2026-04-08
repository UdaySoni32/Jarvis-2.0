"""
JARVIS 2.0 API Server

FastAPI-based REST API for remote access to JARVIS functionality.
Provides endpoints for chat, plugins, automation, and system management.

Features:
- JWT and API Key authentication
- Real-time chat with streaming responses
- Plugin management and execution
- WebSocket support for live updates
- Rate limiting and request validation
- Comprehensive error handling and logging
"""

from fastapi import FastAPI, Request, status, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from fastapi.security import HTTPBearer
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.openapi.utils import get_openapi
from contextlib import asynccontextmanager
import logging
from typing import AsyncGenerator, Dict, Any
import time

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
    """Enhanced application lifespan manager"""
    # Startup
    start_time = time.time()
    app.state.start_time = start_time
    
    logger.info("🚀 Starting JARVIS 2.0 API Server...")
    logger.info(f"Environment: {settings.environment}")
    logger.info(f"Debug mode: {settings.debug}")
    logger.info(f"Host: {settings.host}:{settings.port}")
    logger.info(f"CORS enabled: {settings.cors_enabled}")
    logger.info(f"CORS origins: {settings.cors_origins}")
    logger.info(f"Rate limiting: {settings.rate_limit_enabled}")
    
    # Initialize database
    try:
        from .database import init_database
        init_database()
        logger.info("✅ Database initialized successfully")
    except Exception as e:
        logger.error(f"❌ Database initialization failed: {e}")
        raise
    
    # Initialize plugins registry
    try:
        from ..plugins.registry import PluginRegistry
        plugin_registry = PluginRegistry()
        app.state.plugin_registry = plugin_registry
        logger.info(f"✅ Plugin registry initialized with {len(plugin_registry.get_available_plugins())} plugins")
    except Exception as e:
        logger.error(f"❌ Plugin registry initialization failed: {e}")
    
    # Initialize LLM manager
    try:
        from ..core.llm.manager import llm_manager
        app.state.llm_manager = llm_manager
        logger.info("✅ LLM manager initialized")
    except Exception as e:
        logger.error(f"❌ LLM manager initialization failed: {e}")
    
    logger.info(f"🎉 JARVIS 2.0 API Server started successfully in {time.time() - start_time:.2f}s")
    
    yield
    
    # Shutdown
    logger.info("👋 Shutting down JARVIS 2.0 API Server...")
    
    # Cleanup resources
    if hasattr(app.state, 'plugin_registry'):
        logger.info("🧹 Cleaning up plugin registry...")
    
    if hasattr(app.state, 'llm_manager'): 
        logger.info("🧹 Cleaning up LLM manager...")
    
    logger.info("✅ Shutdown complete")


# Create FastAPI application with enhanced metadata
def custom_openapi():
    """Custom OpenAPI schema generator"""
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title="JARVIS 2.0 API",
        version="2.0.0",
        description="""
## JARVIS 2.0 - AI-Powered Personal Assistant API

A comprehensive REST API for interacting with JARVIS 2.0, featuring:

### 🤖 AI Features
- **Multi-model LLM Support**: OpenAI, Claude, Gemini, Ollama
- **Streaming Responses**: Real-time conversation experience  
- **Context Memory**: Persistent conversation history
- **Smart Plugins**: 8 advanced automation plugins

### 🔐 Security
- **JWT Authentication**: Secure token-based access
- **API Key Support**: Long-lived programmatic access
- **Rate Limiting**: Configurable request throttling
- **Input Validation**: Comprehensive request validation

### 🚀 Real-time Features
- **WebSocket Support**: Live bidirectional communication
- **Server-Sent Events**: Streaming chat responses
- **Presence System**: User connection tracking
- **Live Updates**: Real-time notifications

### 🔌 Plugin System
- **GitHub Integration**: Repository management and search
- **Docker Operations**: Container lifecycle management
- **Database Access**: Multi-database query support
- **Calendar & Email**: Productivity automation
- **API Testing**: HTTP request automation
- **System Tools**: Screen capture, clipboard, file operations

### 📊 Monitoring
- **Health Checks**: System status monitoring
- **Performance Metrics**: Resource usage tracking
- **Audit Logging**: Complete request/response logging
- **Error Tracking**: Comprehensive error handling

### 🌐 Multi-Interface
- **Web Application**: Modern React-based UI
- **CLI Interface**: Rich terminal experience
- **Voice Interface**: Speech-to-text and text-to-speech
- **REST API**: Full programmatic access

### Authentication
All protected endpoints require authentication via:
1. **JWT Bearer Token**: For user sessions (Header: `Authorization: Bearer <token>`)
2. **API Key**: For programmatic access (Header: `X-API-Key: <key>`)

### Rate Limits
- **Default**: 100 requests per minute per user
- **Authenticated**: 1000 requests per minute per user  
- **Streaming**: 10 concurrent streams per user

### Error Handling
The API returns consistent error responses:
```json
{
    "error": "Error Type",
    "message": "Human-readable message",  
    "detail": "Technical details (debug mode only)",
    "timestamp": "2024-01-01T00:00:00Z"
}
```

### WebSocket Events
Real-time events via WebSocket at `/api/v1/ws/chat`:
- `message`: New chat message
- `typing`: User typing indicator
- `presence`: User online/offline status
- `system`: System notifications
        """,
        routes=app.routes,
        tags=[
            {
                "name": "Authentication", 
                "description": "User authentication and API key management"
            },
            {
                "name": "Chat", 
                "description": "AI conversation endpoints with streaming support"
            },
            {
                "name": "Plugins", 
                "description": "Plugin management and execution"
            },
            {
                "name": "System", 
                "description": "System monitoring and configuration"
            },
            {
                "name": "WebSocket", 
                "description": "Real-time bidirectional communication"
            }
        ]
    )
    
    # Add security schemes
    openapi_schema["components"]["securitySchemes"] = {
        "Bearer": {
            "type": "http",
            "scheme": "bearer", 
            "bearerFormat": "JWT"
        },
        "APIKey": {
            "type": "apiKey",
            "in": "header",
            "name": "X-API-Key"
        }
    }
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema


app = FastAPI(
    title="JARVIS 2.0 API",
    description="AI-Powered Personal Assistant API", 
    version="2.0.0",
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
    openapi_url="/openapi.json" if settings.debug else None,
    lifespan=lifespan,
    contact={
        "name": "JARVIS 2.0 Support",
        "url": "https://github.com/UdaySoni32/Jarvis-2.0",
    },
    license_info={
        "name": "MIT License",
        "url": "https://opensource.org/licenses/MIT",
    },
)

# Set custom OpenAPI schema
app.openapi = custom_openapi


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


# Enhanced Exception Handlers
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Enhanced validation error handler with detailed feedback"""
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": "Validation Error",
            "message": "The request data is invalid",
            "detail": exc.errors() if settings.debug else "Invalid input data",
            "timestamp": time.time(),
            "path": str(request.url.path),
        },
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Enhanced HTTP exception handler"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.__class__.__name__,
            "message": exc.detail,
            "timestamp": time.time(),
            "path": str(request.url.path),
        },
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Enhanced general exception handler with better logging"""
    logger.error(f"Unhandled exception on {request.method} {request.url.path}: {exc}", exc_info=True)
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Internal Server Error",
            "message": str(exc) if settings.debug else "An unexpected error occurred",
            "timestamp": time.time(),
            "path": str(request.url.path),
            "trace_id": id(request) if settings.debug else None,
        },
    )


# Security Configuration
@app.middleware("http")
async def security_headers_middleware(request: Request, call_next):
    """Add security headers to all responses"""
    response = await call_next(request)
    
    # Security headers
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
    
    if settings.environment == "production":
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    
    return response


# Enhanced Health Check and Metrics
@app.get("/health", 
         summary="Health Check",
         description="Check API server health and status",
         response_model=Dict[str, Any],
         tags=["System"])
async def health_check():
    """Comprehensive health check endpoint"""
    import psutil
    from .models.user import User
    from .database import SessionLocal
    
    # Database health
    db_healthy = True
    try:
        session = SessionLocal()
        session.query(User).count()
        session.close()
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        db_healthy = False
    
    # System metrics
    system_info = {
        "cpu_percent": psutil.cpu_percent(),
        "memory_percent": psutil.virtual_memory().percent,
        "disk_percent": psutil.disk_usage('/').percent,
    }
    
    return {
        "status": "healthy" if db_healthy else "unhealthy",
        "version": "2.0.0",
        "environment": settings.environment,
        "timestamp": time.time(),
        "uptime": time.time() - app.state.start_time if hasattr(app.state, 'start_time') else 0,
        "database": "connected" if db_healthy else "disconnected", 
        "system": system_info,
        "features": {
            "authentication": True,
            "rate_limiting": True,
            "websockets": True,
            "streaming": True,
            "plugins": True,
        },
    }


@app.get("/", 
         summary="API Information",
         description="Get API information and available endpoints",
         tags=["System"])
async def root():
    """Enhanced root endpoint with comprehensive API information"""
    return {
        "name": "JARVIS 2.0 API",
        "version": "2.0.0",
        "description": "AI-Powered Personal Assistant API",
        "author": "JARVIS 2.0 Team",
        "license": "MIT",
        "repository": "https://github.com/UdaySoni32/Jarvis-2.0",
        "documentation": {
            "swagger": "/docs" if settings.debug else "disabled",
            "redoc": "/redoc" if settings.debug else "disabled",
            "openapi": "/openapi.json" if settings.debug else "disabled",
        },
        "endpoints": {
            "health": "/health",
            "auth": "/api/v1/auth",
            "chat": "/api/v1/chat", 
            "plugins": "/api/v1/plugins",
            "system": "/api/v1/system",
            "websocket": "/api/v1/ws",
        },
        "features": [
            "Multi-model LLM support",
            "Real-time streaming chat",
            "Voice interface integration",
            "Advanced plugin system",
            "JWT and API key authentication",
            "WebSocket real-time communication",
            "Comprehensive rate limiting",
            "Production-ready security",
        ],
        "timestamp": time.time(),
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
