"""Multi-model support for JARVIS 2.0."""

from typing import Optional, List, AsyncGenerator
from dataclasses import dataclass
from ..logger import logger

from .base import BaseLLMProvider, Message
from .openai_provider import OpenAIProvider, OPENAI_AVAILABLE
from .ollama_provider import OllamaProvider, HTTPX_AVAILABLE
from .claude_provider import ClaudeProvider, ANTHROPIC_AVAILABLE


@dataclass
class ModelInfo:
    """Information about an available model."""
    name: str
    provider: str
    available: bool
    description: str


class MultiModelManager:
    """Manage multiple AI models and switch between them."""

    def __init__(self):
        """Initialize multi-model manager."""
        self._models: dict[str, BaseLLMProvider] = {}
        self._current_model: Optional[str] = None
        self._available_models: List[ModelInfo] = []
        logger.info("Multi-model manager initialized")

    async def initialize(self) -> None:
        """Initialize available models."""
        from ...core.config import settings
        
        # Try OpenAI
        if OPENAI_AVAILABLE and settings.has_openai_key:
            try:
                provider = OpenAIProvider()
                if await provider.is_available():
                    self._models["openai"] = provider
                    self._available_models.append(
                        ModelInfo("openai", "OpenAI", True, "GPT-4/3.5-turbo")
                    )
                    logger.info("✅ OpenAI model available")
            except Exception as e:
                logger.warning(f"OpenAI not available: {e}")
        
        # Try Ollama
        if HTTPX_AVAILABLE:
            try:
                provider = OllamaProvider()
                if await provider.is_available():
                    self._models["ollama"] = provider
                    self._available_models.append(
                        ModelInfo("ollama", "Ollama", True, f"Local: {settings.ollama_model}")
                    )
                    logger.info("✅ Ollama model available")
            except Exception as e:
                logger.warning(f"Ollama not available: {e}")
        
        # Try Claude
        if ANTHROPIC_AVAILABLE and settings.has_anthropic_key:
            try:
                provider = ClaudeProvider()
                if await provider.is_available():
                    self._models["claude"] = provider
                    self._available_models.append(
                        ModelInfo("claude", "Anthropic", True, "Claude 3.5 Sonnet")
                    )
                    logger.info("✅ Claude model available")
            except Exception as e:
                logger.warning(f"Claude not available: {e}")
        
        # Set default model
        self._current_model = settings.default_llm.lower()
        if self._current_model not in self._models:
            if self._models:
                self._current_model = list(self._models.keys())[0]
                logger.info(f"Default model not available, using {self._current_model}")
            else:
                raise ValueError("No LLM models available. Configure at least one provider.")

    def get_available_models(self) -> List[ModelInfo]:
        """Get list of available models."""
        return self._available_models

    def set_model(self, model_name: str) -> bool:
        """
        Switch to a different model.
        
        Args:
            model_name: Name of the model to switch to
            
        Returns:
            True if successful, False otherwise
        """
        if model_name not in self._models:
            logger.warning(f"Model {model_name} not available")
            return False
        
        self._current_model = model_name
        logger.info(f"Switched to model: {model_name}")
        return True

    def get_current_model(self) -> Optional[BaseLLMProvider]:
        """Get current active model."""
        if not self._current_model:
            return None
        return self._models.get(self._current_model)

    async def chat(self, messages: list[Message], model: Optional[str] = None, **kwargs) -> str:
        """
        Chat with specified or default model.
        
        Args:
            messages: List of messages
            model: Optional model to use (defaults to current)
            **kwargs: Additional arguments
            
        Returns:
            Response text
        """
        target_model = model or self._current_model
        provider = self._models.get(target_model)
        
        if not provider:
            raise ValueError(f"Model {target_model} not available")
        
        return await provider.chat(messages, **kwargs)

    async def stream_chat(self, messages: list[Message], model: Optional[str] = None, **kwargs) -> AsyncGenerator[str, None]:
        """
        Stream chat with specified or default model.
        
        Args:
            messages: List of messages
            model: Optional model to use (defaults to current)
            **kwargs: Additional arguments
            
        Yields:
            Response chunks
        """
        target_model = model or self._current_model
        provider = self._models.get(target_model)
        
        if not provider:
            raise ValueError(f"Model {target_model} not available")
        
        async for chunk in provider.stream_chat(messages, **kwargs):
            yield chunk


# Global instance
_multi_model_manager: Optional[MultiModelManager] = None


def get_multi_model_manager() -> MultiModelManager:
    """Get or create the multi-model manager."""
    global _multi_model_manager
    if _multi_model_manager is None:
        _multi_model_manager = MultiModelManager()
    return _multi_model_manager
