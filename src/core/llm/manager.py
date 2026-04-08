"""LLM manager for selecting and managing LLM providers."""

from typing import Any, Dict, List, Optional

from ..config import settings
from ..logger import logger
from .base import BaseLLMProvider
from .openai_provider import OpenAIProvider, OPENAI_AVAILABLE
from .ollama_provider import OllamaProvider, HTTPX_AVAILABLE

try:
    from .claude_provider import ClaudeProvider, ANTHROPIC_AVAILABLE
except ImportError:
    ClaudeProvider = None
    ANTHROPIC_AVAILABLE = False

try:
    from .gemini_provider import GeminiProvider, GEMINI_AVAILABLE
except ImportError:
    GeminiProvider = None
    GEMINI_AVAILABLE = False

from .custom_provider import CustomModelProvider, LocalModelProvider


class LLMManager:
    """Manages LLM provider selection and initialization."""

    def __init__(self):
        """Initialize LLM manager."""
        self._provider: Optional[BaseLLMProvider] = None
        self._provider_name: Optional[str] = None
        logger.info("LLM Manager initialized")

    async def get_provider(self, force_reload: bool = False) -> BaseLLMProvider:
        """
        Get the configured LLM provider.

        Args:
            force_reload: Force reload the provider

        Returns:
            Initialized LLM provider

        Raises:
            ValueError: If no valid provider is configured
        """
        if self._provider and not force_reload and self._provider_name == provider_name:
            return self._provider

        provider_name = self.current_model
        logger.info(f"Initializing LLM provider: {provider_name}")

        try:
            if provider_name == "openai":
                if not OPENAI_AVAILABLE:
                    raise ImportError(
                        "OpenAI not installed. Install with: pip install openai tiktoken"
                    )
                if not settings.has_openai_key:
                    raise ValueError(
                        "OpenAI API key not configured. Set OPENAI_API_KEY in .env"
                    )
                self._provider = OpenAIProvider()

            elif provider_name == "ollama":
                if not HTTPX_AVAILABLE:
                    raise ImportError(
                        "httpx not installed. Install with: pip install httpx"
                    )
                self._provider = OllamaProvider()

            elif provider_name == "claude" or provider_name == "anthropic":
                if not ANTHROPIC_AVAILABLE:
                    raise ImportError(
                        "Claude not installed. Install with: pip install anthropic"
                    )
                if not settings.has_anthropic_key:
                    raise ValueError(
                        "Anthropic API key not configured. Set ANTHROPIC_API_KEY in .env"
                    )
                self._provider = ClaudeProvider()

            elif provider_name == "gemini" or provider_name == "google":
                if not GEMINI_AVAILABLE:
                    raise ImportError(
                        "Gemini not installed. Install with: pip install google-generativeai"
                    )
                if not settings.has_gemini_key:
                    raise ValueError(
                        "Gemini API key not configured. Set GEMINI_API_KEY in .env"
                    )
                self._provider = GeminiProvider()

            else:
                raise ValueError(
                    f"Unknown LLM provider: {provider_name}. "
                    "Valid options: openai, ollama, claude"
                )

            # Test if provider is available
            is_available = await self._provider.is_available()
            if not is_available:
                raise ConnectionError(
                    f"{provider_name} provider initialized but not responding. "
                    "Check your configuration and connection."
                )

            logger.info(f"✅ {provider_name} provider ready")
            self._provider_name = provider_name
            return self._provider

        except Exception as e:
            logger.error(f"Failed to initialize {provider_name} provider: {e}")
            
            # Try fallback to Ollama if primary fails
            if provider_name != "ollama" and HTTPX_AVAILABLE:
                logger.info("Attempting fallback to Ollama...")
                try:
                    self._provider = OllamaProvider()
                    is_available = await self._provider.is_available()
                    if is_available:
                        logger.warning(
                            f"Using Ollama as fallback (primary {provider_name} failed)"
                        )
                        self._provider_name = "ollama"
                        return self._provider
                except Exception:
                    pass

            raise ValueError(
                f"Failed to initialize LLM provider: {e}\n\n"
                "Please check your configuration:\n"
                "- For OpenAI: Set OPENAI_API_KEY in .env\n"
                "- For Ollama: Install and run Ollama (https://ollama.ai/)\n"
                "- Run setup wizard: python -m src.cli"
            )

    async def generate(self, prompt: str, **kwargs) -> str:
        """
        Generate response from LLM (simple interface).

        Args:
            prompt: User prompt
            **kwargs: Additional generation parameters

        Returns:
            Generated response
        """
        from .base import Message

        model = kwargs.pop("model", None)
        if model:
            self.set_model(model)

        provider = await self.get_provider()
        messages = [Message("user", prompt)]
        return await provider.generate(messages, **kwargs)

    async def chat(self, messages: list, **kwargs) -> str:
        """
        Chat with LLM (message history interface).

        Args:
            messages: List of Message objects
            **kwargs: Additional generation parameters

        Returns:
            Generated response
        """
        model = kwargs.pop("model", None)
        if model:
            self.set_model(model)

        provider = await self.get_provider()
        return await provider.generate(self._normalize_messages(messages), **kwargs)

    async def stream_chat(self, messages: list, **kwargs):
        """
        Stream chat response from LLM.

        Args:
            messages: List of Message objects
            **kwargs: Additional generation parameters

        Yields:
            Response chunks
        """
        model = kwargs.pop("model", None)
        if model:
            self.set_model(model)

        provider = await self.get_provider()
        async for chunk in provider.generate_stream(self._normalize_messages(messages), **kwargs):
            yield chunk

    def count_tokens(self, text: str) -> int:
        """Count tokens in text using current provider."""
        if self._provider:
            return self._provider.count_tokens(text)
        # Rough estimate if no provider
        return len(text) // 4

    @property
    def current_model(self) -> str:
        """Return the active provider name."""
        return self._provider_name or settings.default_llm.lower()

    def set_model(self, model_name: str) -> bool:
        """Set the active provider name."""
        normalized = model_name.strip().lower()
        if not normalized:
            raise ValueError("Model name cannot be empty")

        self._provider_name = normalized
        self._provider = None
        logger.info(f"Switched to model: {normalized}")
        return True

    def check_provider_available(self, provider_name: str) -> bool:
        """Check whether a provider can be used with the current environment."""
        normalized = provider_name.strip().lower()

        if normalized == "openai":
            return OPENAI_AVAILABLE and settings.has_openai_key
        if normalized == "ollama":
            return HTTPX_AVAILABLE
        if normalized in {"claude", "anthropic"}:
            return bool(ClaudeProvider) and ANTHROPIC_AVAILABLE and settings.has_anthropic_key
        if normalized in {"gemini", "google"}:
            return bool(GeminiProvider) and GEMINI_AVAILABLE and settings.has_gemini_key
        return False

    def get_available_models(self) -> List[Dict[str, Any]]:
        """Return the configured model/providers and their availability."""
        return [
            {
                "name": "openai",
                "provider": "OpenAI",
                "available": self.check_provider_available("openai"),
                "description": settings.openai_model,
            },
            {
                "name": "ollama",
                "provider": "Ollama",
                "available": self.check_provider_available("ollama"),
                "description": f"Local: {settings.ollama_model}",
            },
            {
                "name": "claude",
                "provider": "Anthropic",
                "available": self.check_provider_available("claude"),
                "description": settings.claude_model,
            },
            {
                "name": "gemini",
                "provider": "Google",
                "available": self.check_provider_available("gemini"),
                "description": settings.gemini_model,
            },
        ]

    async def get_completion(self, messages: list, **kwargs) -> str:
        """Compatibility helper for chat routes."""
        return await self.chat(messages, **kwargs)

    async def stream_completion(self, messages: list, **kwargs):
        """Compatibility helper for streaming chat routes."""
        async for chunk in self.stream_chat(messages, **kwargs):
            yield chunk

    def _normalize_messages(self, messages: list) -> List["Message"]:
        """Coerce dicts and message-like objects into Message instances."""
        from .base import Message

        normalized: List[Message] = []
        for message in messages:
            if isinstance(message, Message):
                normalized.append(message)
            elif isinstance(message, dict):
                normalized.append(
                    Message(
                        role=message.get("role", "user"),
                        content=message.get("content", ""),
                    )
                )
            elif hasattr(message, "role") and hasattr(message, "content"):
                normalized.append(Message(str(message.role), str(message.content)))
            else:
                raise TypeError(f"Unsupported message type: {type(message)!r}")

        return normalized


# Global LLM manager instance
llm_manager = LLMManager()
