"""Base LLM provider interface."""

from abc import ABC, abstractmethod
from typing import AsyncIterator, Dict, List, Optional, Any


class Message:
    """Represents a chat message."""

    def __init__(self, role: str, content: str):
        """
        Initialize message.

        Args:
            role: Message role (system, user, assistant, function)
            content: Message content
        """
        self.role = role
        self.content = content

    def to_dict(self) -> Dict[str, str]:
        """Convert to dictionary."""
        return {"role": self.role, "content": self.content}

    def __repr__(self) -> str:
        return f"Message(role={self.role!r}, content={self.content[:50]!r}...)"


class BaseLLMProvider(ABC):
    """Abstract base class for LLM providers."""

    def __init__(self, model: str, **kwargs):
        """
        Initialize LLM provider.

        Args:
            model: Model name/identifier
            **kwargs: Additional provider-specific parameters
        """
        self.model = model
        self.kwargs = kwargs

    @abstractmethod
    async def generate(
        self,
        messages: List[Message],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        stream: bool = False,
        **kwargs,
    ) -> str:
        """
        Generate a response from the LLM.

        Args:
            messages: List of conversation messages
            temperature: Sampling temperature (0.0 to 2.0)
            max_tokens: Maximum tokens to generate
            stream: Whether to stream the response
            **kwargs: Additional provider-specific parameters

        Returns:
            Generated response text
        """
        pass

    @abstractmethod
    async def generate_stream(
        self,
        messages: List[Message],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs,
    ) -> AsyncIterator[str]:
        """
        Generate a streaming response from the LLM.

        Args:
            messages: List of conversation messages
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            **kwargs: Additional provider-specific parameters

        Yields:
            Chunks of generated text
        """
        pass

    @abstractmethod
    async def generate_with_functions(
        self,
        messages: List[Message],
        functions: List[Dict[str, Any]],
        temperature: float = 0.7,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Generate response with function calling support.

        Args:
            messages: List of conversation messages
            functions: List of available functions
            temperature: Sampling temperature
            **kwargs: Additional provider-specific parameters

        Returns:
            Response with potential function calls
        """
        pass

    @abstractmethod
    def count_tokens(self, text: str) -> int:
        """
        Count tokens in text.

        Args:
            text: Text to count tokens for

        Returns:
            Number of tokens
        """
        pass

    @abstractmethod
    async def is_available(self) -> bool:
        """
        Check if the provider is available.

        Returns:
            True if provider can be used
        """
        pass
