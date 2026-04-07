"""Claude AI provider for JARVIS 2.0."""

from typing import AsyncGenerator, Optional
from ..logger import logger

try:
    from anthropic import AsyncAnthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False

from .base import BaseLLMProvider, Message


class ClaudeProvider(BaseLLMProvider):
    """Claude AI provider using Anthropic API."""

    def __init__(self):
        """Initialize Claude provider."""
        from ...core.config import settings
        
        if not settings.has_anthropic_key:
            raise ValueError("ANTHROPIC_API_KEY not set")
        
        self.client = AsyncAnthropic(api_key=settings.anthropic_api_key)
        self.model = "claude-3-5-sonnet-20241022"
        logger.info(f"Claude provider initialized with model: {self.model}")

    async def is_available(self) -> bool:
        """Check if Claude API is available."""
        try:
            # Test with a simple message
            response = await self.client.messages.create(
                model=self.model,
                max_tokens=50,
                messages=[{"role": "user", "content": "ping"}]
            )
            return response.content[0].text == "pong" or len(response.content) > 0
        except Exception as e:
            logger.warning(f"Claude availability check failed: {e}")
            return False

    async def chat(self, messages: list[Message], temperature: float = 0.7, **kwargs) -> str:
        """
        Get a chat response from Claude.
        
        Args:
            messages: List of Message objects
            temperature: Temperature for response generation
            **kwargs: Additional parameters
            
        Returns:
            Response text
        """
        formatted_messages = [
            {"role": msg.role, "content": msg.content}
            for msg in messages
        ]
        
        response = await self.client.messages.create(
            model=self.model,
            max_tokens=kwargs.get("max_tokens", 2000),
            temperature=temperature,
            messages=formatted_messages
        )
        
        return response.content[0].text

    async def stream_chat(self, messages: list[Message], temperature: float = 0.7, **kwargs) -> AsyncGenerator[str, None]:
        """
        Stream a chat response from Claude.
        
        Args:
            messages: List of Message objects
            temperature: Temperature for response generation
            **kwargs: Additional parameters
            
        Yields:
            Response chunks
        """
        formatted_messages = [
            {"role": msg.role, "content": msg.content}
            for msg in messages
        ]
        
        async with self.client.messages.stream(
            model=self.model,
            max_tokens=kwargs.get("max_tokens", 2000),
            temperature=temperature,
            messages=formatted_messages
        ) as stream:
            async for text in stream.text_stream:
                yield text

    def get_name(self) -> str:
        """Get provider name."""
        return "Claude"
