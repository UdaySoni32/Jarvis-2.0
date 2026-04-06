"""LLM manager for selecting and managing LLM providers."""

from typing import Optional

from ..config import settings
from ..logger import logger
from .base import BaseLLMProvider
from .openai_provider import OpenAIProvider, OPENAI_AVAILABLE
from .ollama_provider import OllamaProvider, HTTPX_AVAILABLE


class LLMManager:
    """Manages LLM provider selection and initialization."""

    def __init__(self):
        """Initialize LLM manager."""
        self._provider: Optional[BaseLLMProvider] = None
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
        if self._provider and not force_reload:
            return self._provider

        provider_name = settings.default_llm.lower()
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
                # TODO: Implement Claude provider
                raise NotImplementedError(
                    "Claude provider not yet implemented. Use OpenAI or Ollama for now."
                )

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
        provider = await self.get_provider()
        return await provider.generate(messages, **kwargs)

    async def stream_chat(self, messages: list, **kwargs):
        """
        Stream chat response from LLM.

        Args:
            messages: List of Message objects
            **kwargs: Additional generation parameters

        Yields:
            Response chunks
        """
        provider = await self.get_provider()
        async for chunk in provider.generate_stream(messages, **kwargs):
            yield chunk

    def count_tokens(self, text: str) -> int:
        """Count tokens in text using current provider."""
        if self._provider:
            return self._provider.count_tokens(text)
        # Rough estimate if no provider
        return len(text) // 4


# Global LLM manager instance
llm_manager = LLMManager()
