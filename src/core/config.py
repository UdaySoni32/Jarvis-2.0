"""Configuration management for JARVIS 2.0."""

import os
from pathlib import Path
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # OpenAI Configuration
    openai_api_key: Optional[str] = Field(default=None, alias="OPENAI_API_KEY")
    openai_model: str = Field(default="gpt-4-turbo-preview", alias="OPENAI_MODEL")

    # Anthropic Configuration
    anthropic_api_key: Optional[str] = Field(default=None, alias="ANTHROPIC_API_KEY")
    claude_model: str = Field(default="claude-3-opus-20240229", alias="CLAUDE_MODEL")

    # Ollama Configuration
    ollama_model: str = Field(default="llama3", alias="OLLAMA_MODEL")
    ollama_base_url: str = Field(
        default="http://localhost:11434", alias="OLLAMA_BASE_URL"
    )

    # LLM Configuration
    default_llm: str = Field(default="openai", alias="DEFAULT_LLM")
    max_tokens: int = Field(default=2000, alias="MAX_TOKENS")
    temperature: float = Field(default=0.7, alias="TEMPERATURE")

    # Database Configuration
    database_url: str = Field(
        default="sqlite:///./jarvis_data.db", alias="DATABASE_URL"
    )
    redis_url: Optional[str] = Field(default=None, alias="REDIS_URL")

    # Vector Database
    chroma_host: str = Field(default="localhost", alias="CHROMA_HOST")
    chroma_port: int = Field(default=8000, alias="CHROMA_PORT")

    # Application Settings
    debug: bool = Field(default=False, alias="DEBUG")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    log_file: str = Field(default="logs/jarvis.log", alias="LOG_FILE")

    # Features
    enable_memory: bool = Field(default=True, alias="ENABLE_MEMORY")
    enable_web_search: bool = Field(default=True, alias="ENABLE_WEB_SEARCH")
    enable_voice: bool = Field(default=False, alias="ENABLE_VOICE")
    enable_plugins: bool = Field(default=True, alias="ENABLE_PLUGINS")
    
    # Memory settings
    max_context_messages: int = Field(
        default=20, description="Maximum messages to keep in context"
    )

    # Voice Settings
    voice_enabled: bool = Field(default=False, alias="VOICE_ENABLED")
    tts_engine: str = Field(default="pyttsx3", alias="TTS_ENGINE")
    stt_engine: str = Field(default="whisper", alias="STT_ENGINE")

    # User Data
    user_data_dir: Path = Field(default=Path("./user_data"), alias="USER_DATA_DIR")
    conversation_history_dir: Path = Field(
        default=Path("./user_data/conversations"),
        alias="CONVERSATION_HISTORY_DIR",
    )
    memory_store_dir: Path = Field(
        default=Path("./user_data/memory"), alias="MEMORY_STORE_DIR"
    )

    # API Server (for future phases)
    api_host: str = Field(default="0.0.0.0", alias="API_HOST")
    api_port: int = Field(default=8000, alias="API_PORT")
    api_secret_key: str = Field(
        default="change_this_secret_key", alias="API_SECRET_KEY"
    )

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Create necessary directories
        self.user_data_dir.mkdir(parents=True, exist_ok=True)
        self.conversation_history_dir.mkdir(parents=True, exist_ok=True)
        self.memory_store_dir.mkdir(parents=True, exist_ok=True)
        Path("logs").mkdir(exist_ok=True)

    @property
    def has_openai_key(self) -> bool:
        """Check if OpenAI API key is configured."""
        return bool(self.openai_api_key)

    @property
    def has_anthropic_key(self) -> bool:
        """Check if Anthropic API key is configured."""
        return bool(self.anthropic_api_key)

    @property
    def can_use_cloud_llm(self) -> bool:
        """Check if any cloud LLM is available."""
        return self.has_openai_key or self.has_anthropic_key


# Global settings instance
settings = Settings()
