"""Ollama LLM provider implementation for local models."""

import json
from typing import Any, AsyncIterator, Dict, List, Optional

try:
    import httpx
    HTTPX_AVAILABLE = True
except ImportError:
    HTTPX_AVAILABLE = False

from ..config import settings
from ..logger import logger
from .base import BaseLLMProvider, Message


class OllamaProvider(BaseLLMProvider):
    """Ollama local LLM provider."""

    def __init__(self, base_url: Optional[str] = None, model: Optional[str] = None):
        """
        Initialize Ollama provider.

        Args:
            base_url: Ollama API base URL
            model: Model name (e.g., llama3, mistral)
        """
        if not HTTPX_AVAILABLE:
            raise ImportError(
                "httpx not installed. Install with: pip install httpx"
            )

        self.base_url = base_url or settings.ollama_base_url
        model = model or settings.ollama_model
        super().__init__(model=model)

        self.client = httpx.AsyncClient(timeout=120.0)
        logger.info(f"Ollama provider initialized: {self.base_url} with model: {model}")

    async def generate(
        self,
        messages: List[Message],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        stream: bool = False,
        **kwargs,
    ) -> str:
        """Generate response from Ollama."""
        try:
            if stream:
                # Use streaming
                result = []
                async for chunk in self.generate_stream(
                    messages, temperature, max_tokens, **kwargs
                ):
                    result.append(chunk)
                return "".join(result)

            # Convert messages to Ollama format
            messages_dict = [msg.to_dict() for msg in messages]

            # Regular generation
            payload = {
                "model": self.model,
                "messages": messages_dict,
                "stream": False,
                "options": {
                    "temperature": temperature,
                },
            }

            if max_tokens:
                payload["options"]["num_predict"] = max_tokens

            response = await self.client.post(
                f"{self.base_url}/api/chat",
                json=payload,
            )
            response.raise_for_status()

            data = response.json()
            return data.get("message", {}).get("content", "")

        except Exception as e:
            logger.error(f"Ollama generation error: {e}")
            raise

    async def generate_stream(
        self,
        messages: List[Message],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs,
    ) -> AsyncIterator[str]:
        """Generate streaming response from Ollama."""
        try:
            messages_dict = [msg.to_dict() for msg in messages]

            payload = {
                "model": self.model,
                "messages": messages_dict,
                "stream": True,
                "options": {
                    "temperature": temperature,
                },
            }

            if max_tokens:
                payload["options"]["num_predict"] = max_tokens

            async with self.client.stream(
                "POST",
                f"{self.base_url}/api/chat",
                json=payload,
            ) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if line.strip():
                        try:
                            data = json.loads(line)
                            if "message" in data and "content" in data["message"]:
                                yield data["message"]["content"]
                        except json.JSONDecodeError:
                            continue

        except Exception as e:
            logger.error(f"Ollama streaming error: {e}")
            raise

    async def generate_with_functions(
        self,
        messages: List[Message],
        functions: List[Dict[str, Any]],
        temperature: float = 0.7,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Generate response with function calling.
        
        Note: Ollama doesn't natively support function calling like OpenAI,
        but we can simulate it by adding functions to the system prompt.
        """
        try:
            # Add function descriptions to system message
            function_descriptions = "\n\nAvailable functions:\n"
            for func in functions:
                function_descriptions += f"- {func['name']}: {func['description']}\n"
                if func.get('parameters'):
                    function_descriptions += f"  Parameters: {json.dumps(func['parameters'])}\n"

            # Add to first message or create system message
            enhanced_messages = list(messages)
            if enhanced_messages and enhanced_messages[0].role == "system":
                enhanced_messages[0].content += function_descriptions
            else:
                enhanced_messages.insert(0, Message("system", 
                    "You are a helpful assistant. When you need to use a function, "
                    "respond with FUNCTION_CALL followed by the function name and arguments in JSON format."
                    + function_descriptions
                ))

            # Generate response
            response_text = await self.generate(enhanced_messages, temperature, **kwargs)

            # Parse for function calls
            result = {
                "content": response_text,
                "tool_calls": [],
            }

            # Simple function call detection
            if "FUNCTION_CALL" in response_text:
                # Extract function call (basic implementation)
                # In production, use more robust parsing
                logger.warning("Function calling with Ollama is experimental")

            return result

        except Exception as e:
            logger.error(f"Ollama function calling error: {e}")
            raise

    def count_tokens(self, text: str) -> int:
        """
        Count tokens in text.
        
        Note: Ollama doesn't provide exact token counting,
        this is a rough estimate.
        """
        # Rough estimate: ~4 characters per token
        return len(text) // 4

    async def is_available(self) -> bool:
        """Check if Ollama is available (short timeout to avoid hanging)."""
        try:
            async with httpx.AsyncClient(timeout=5.0) as check_client:
                response = await check_client.get(f"{self.base_url}/api/tags")
                return response.status_code == 200
        except Exception as e:
            logger.warning(f"Ollama not available: {e}")
            return False

    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()
