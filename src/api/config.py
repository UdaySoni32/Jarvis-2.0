"""
API Configuration for JARVIS 2.0

Manages all API server settings and environment variables.
"""

from pydantic_settings import BaseSettings
from pydantic import Field
from typing import List, Optional
import os


class APISettings(BaseSettings):
    """API Server Configuration"""
    
    # Server Settings
    host: str = Field(default="0.0.0.0", env="API_HOST")
    port: int = Field(default=8000, env="API_PORT")
    environment: str = Field(default="development", env="ENVIRONMENT")
    debug: bool = Field(default=True, env="DEBUG")
    
    # Security
    secret_key: str = Field(
        default="your-secret-key-change-in-production",
        env="API_SECRET_KEY"
    )
    access_token_expire_minutes: int = Field(default=60, env="ACCESS_TOKEN_EXPIRE")
    refresh_token_expire_days: int = Field(default=7, env="REFRESH_TOKEN_EXPIRE")
    api_key_header: str = Field(default="X-API-Key", env="API_KEY_HEADER")
    
    # CORS
    cors_enabled: bool = Field(default=True, env="CORS_ENABLED")
    cors_origins: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:5173"],
        env="CORS_ORIGINS"
    )
    
    # Rate Limiting
    rate_limit_enabled: bool = Field(default=True, env="RATE_LIMIT_ENABLED")
    rate_limit_requests: int = Field(default=100, env="RATE_LIMIT_REQUESTS")
    rate_limit_period: int = Field(default=60, env="RATE_LIMIT_PERIOD")  # seconds
    
    # Database
    database_url: str = Field(
        default="sqlite:///./jarvis_api.db",
        env="DATABASE_URL"
    )
    
    # Redis (for sessions and rate limiting)
    redis_url: Optional[str] = Field(default=None, env="REDIS_URL")
    redis_enabled: bool = Field(default=False, env="REDIS_ENABLED")
    
    # WebSocket
    websocket_heartbeat_interval: int = Field(default=30, env="WS_HEARTBEAT")
    websocket_max_connections: int = Field(default=100, env="WS_MAX_CONNECTIONS")
    
    # File Upload
    max_upload_size: int = Field(default=10 * 1024 * 1024, env="MAX_UPLOAD_SIZE")  # 10MB
    upload_dir: str = Field(default="./uploads", env="UPLOAD_DIR")
    
    # Logging
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    log_file: Optional[str] = Field(default=None, env="LOG_FILE")
    
    # LLM Integration (from core settings)
    default_llm: str = Field(default="ollama", env="DEFAULT_LLM")
    openai_api_key: Optional[str] = Field(default=None, env="OPENAI_API_KEY")
    anthropic_api_key: Optional[str] = Field(default=None, env="ANTHROPIC_API_KEY")
    gemini_api_key: Optional[str] = Field(default=None, env="GEMINI_API_KEY")
    
    # Features
    enable_memory: bool = Field(default=True, env="ENABLE_MEMORY")
    enable_plugins: bool = Field(default=True, env="ENABLE_PLUGINS")
    enable_voice: bool = Field(default=False, env="ENABLE_VOICE")
    
    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"  # Ignore extra fields from .env

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._apply_runtime_env_overrides()

    def _apply_runtime_env_overrides(self):
        """Apply shell environment overrides after dotenv loading."""
        overrides = {
            "API_HOST": ("host", str),
            "API_PORT": ("port", int),
            "DEBUG": ("debug", lambda value: value.lower() in {"1", "true", "yes", "on"}),
            "LOG_LEVEL": ("log_level", str),
            "DATABASE_URL": ("database_url", str),
            "DEFAULT_LLM": ("default_llm", str),
        }

        for env_name, (attr_name, parser) in overrides.items():
            raw_value = os.getenv(env_name)
            if raw_value is not None and raw_value != "":
                setattr(self, attr_name, parser(raw_value))


# Global settings instance
settings = APISettings()


# Ensure required directories exist
os.makedirs(settings.upload_dir, exist_ok=True)
