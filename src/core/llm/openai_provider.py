"""OpenAI LLM provider implementation."""

import json
from typing import Any, AsyncIterator, Dict, List, Optional

try:
    from openai import AsyncOpenAI
    import tiktoken
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

from ..config import settings
from ..logger import logger
from .base import BaseLLMProvider, Message


class OpenAIProvider(BaseLLMProvider):
    """OpenAI GPT provider."""

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        """
        Initialize OpenAI provider.

        Args:
            api_key: OpenAI API key (uses settings if not provided)
            model: Model name (uses settings if not provided)
        """
        if not OPENAI_AVAILABLE:
            raise ImportError(
                "OpenAI package not installed. Install with: pip install openai tiktoken"
            )

        api_key = api_key or settings.openai_api_key
        if not api_key:
            raise ValueError("OpenAI API key not configured")

        model = model or settings.openai_model
        super().__init__(model=model)

        self.client = AsyncOpenAI(api_key=api_key)
        
        # Initialize token encoder
        try:
            self.encoding = tiktoken.encoding_for_model(model)
        except KeyError:
            # Fallback to cl100k_base for unknown models
            self.encoding = tiktoken.get_encoding("cl100k_base")

        logger.info(f"OpenAI provider initialized with model: {model}")

    async def generate(
        self,
        messages: List[Message],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        stream: bool = False,
        **kwargs,
    ) -> str:
        """Generate response from OpenAI."""
        try:
            messages_dict = [msg.to_dict() for msg in messages]

            if stream:
                # Use streaming
                result = []
                async for chunk in self.generate_stream(
                    messages, temperature, max_tokens, **kwargs
                ):
                    result.append(chunk)
                return "".join(result)

            # Regular generation
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages_dict,
                temperature=temperature,
                max_tokens=max_tokens or settings.max_tokens,
                **kwargs,
            )

            content = response.choices[0].message.content
            return content or ""

        except Exception as e:
            logger.error(f"OpenAI generation error: {e}")
            raise

    async def generate_stream(
        self,
        messages: List[Message],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs,
    ) -> AsyncIterator[str]:
        """Generate streaming response from OpenAI."""
        try:
            messages_dict = [msg.to_dict() for msg in messages]

            stream = await self.client.chat.completions.create(
                model=self.model,
                messages=messages_dict,
                temperature=temperature,
                max_tokens=max_tokens or settings.max_tokens,
                stream=True,
                **kwargs,
            )

            async for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content

        except Exception as e:
            logger.error(f"OpenAI streaming error: {e}")
            raise

    async def generate_with_functions(
        self,
        messages: List[Message],
        functions: List[Dict[str, Any]],
        temperature: float = 0.7,
        **kwargs,
    ) -> Dict[str, Any]:
        """Generate response with function calling."""
        try:
            messages_dict = [msg.to_dict() for msg in messages]

            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages_dict,
                tools=[{"type": "function", "function": f} for f in functions],
                tool_choice="auto",
                temperature=temperature,
                **kwargs,
            )

            choice = response.choices[0]
            result = {
                "content": choice.message.content,
                "tool_calls": [],
            }

            if choice.message.tool_calls:
                for tool_call in choice.message.tool_calls:
                    result["tool_calls"].append({
                        "id": tool_call.id,
                        "name": tool_call.function.name,
                        "arguments": json.loads(tool_call.function.arguments),
                    })

            return result

        except Exception as e:
            logger.error(f"OpenAI function calling error: {e}")
            raise

    def count_tokens(self, text: str) -> int:
        """Count tokens in text."""
        try:
            return len(self.encoding.encode(text))
        except Exception:
            # Rough estimate if encoding fails
            return len(text) // 4

    async def is_available(self) -> bool:
        """Check if OpenAI is available."""
        try:
            # Simple API test
            await self.client.models.retrieve(self.model)
            return True
        except Exception as e:
            logger.warning(f"OpenAI not available: {e}")
            return False
