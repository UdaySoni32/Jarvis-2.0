"""Custom model provider framework for JARVIS 2.0."""

from typing import AsyncGenerator, Optional, Callable, Any, Dict
import aiohttp
from ..logger import logger

from .base import BaseLLMProvider, Message


class CustomModelProvider(BaseLLMProvider):
    """Generic custom model provider for any HTTP-based API."""

    def __init__(
        self,
        name: str,
        api_url: str,
        api_key: Optional[str] = None,
        request_formatter: Optional[Callable] = None,
        response_parser: Optional[Callable] = None,
        headers: Optional[Dict[str, str]] = None,
    ):
        """
        Initialize custom model provider.
        
        Args:
            name: Name of the model/provider
            api_url: Base URL for the API endpoint
            api_key: API key (if required)
            request_formatter: Function to format request body
            response_parser: Function to parse response
            headers: Custom HTTP headers
        """
        self.name = name
        self.api_url = api_url
        self.api_key = api_key
        self.request_formatter = request_formatter
        self.response_parser = response_parser
        self.headers = headers or {}
        
        if api_key:
            self.headers["Authorization"] = f"Bearer {api_key}"
        
        logger.info(f"Custom provider initialized: {name} ({api_url})")

    async def is_available(self) -> bool:
        """Check if custom API is available."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.api_url,
                    headers=self.headers,
                    json={"test": True},
                    timeout=aiohttp.ClientTimeout(total=5)
                ) as response:
                    return response.status in [200, 201, 400]  # 400 is ok for test
        except Exception as e:
            logger.warning(f"Custom API availability check failed: {e}")
            return False

    async def chat(self, messages: list[Message], temperature: float = 0.7, **kwargs) -> str:
        """
        Get a chat response from custom model.
        
        Args:
            messages: List of Message objects
            temperature: Temperature for response generation
            **kwargs: Additional parameters
            
        Returns:
            Response text
        """
        # Format request
        if self.request_formatter:
            request_body = self.request_formatter(messages, temperature, **kwargs)
        else:
            request_body = self._default_format_request(messages, temperature, **kwargs)
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                self.api_url,
                headers=self.headers,
                json=request_body
            ) as response:
                data = await response.json()
                
                # Parse response
                if self.response_parser:
                    return self.response_parser(data)
                else:
                    return self._default_parse_response(data)

    async def stream_chat(self, messages: list[Message], temperature: float = 0.7, **kwargs) -> AsyncGenerator[str, None]:
        """
        Stream a chat response from custom model.
        
        Args:
            messages: List of Message objects
            temperature: Temperature for response generation
            **kwargs: Additional parameters
            
        Yields:
            Response chunks
        """
        # Format request
        if self.request_formatter:
            request_body = self.request_formatter(messages, temperature, **kwargs)
        else:
            request_body = self._default_format_request(messages, temperature, **kwargs)
        
        request_body["stream"] = True
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                self.api_url,
                headers=self.headers,
                json=request_body
            ) as response:
                async for line in response.content:
                    if line:
                        text = line.decode().strip()
                        if text:
                            yield text

    def _default_format_request(self, messages: list[Message], temperature: float, **kwargs) -> Dict:
        """Default request formatting (OpenAI-compatible format)."""
        return {
            "model": getattr(self, "model_name", self.name),
            "messages": [
                {"role": msg.role, "content": msg.content}
                for msg in messages
            ],
            "temperature": temperature,
            "max_tokens": kwargs.get("max_tokens", 2000),
        }

    def _default_parse_response(self, data: Dict) -> str:
        """Default response parsing (OpenAI-compatible format)."""
        # Try OpenAI format
        if "choices" in data and len(data["choices"]) > 0:
            choice = data["choices"][0]
            if "message" in choice:
                return choice["message"].get("content", "")
            elif "text" in choice:
                return choice["text"]
        
        # Try common alternatives
        if "response" in data:
            return data["response"]
        if "result" in data:
            return data["result"]
        if "text" in data:
            return data["text"]
        if "content" in data:
            return data["content"]
        
        # Fallback
        return str(data)

    def get_name(self) -> str:
        """Get provider name."""
        return self.name


class LocalModelProvider(BaseLLMProvider):
    """Provider for local models (llama.cpp, local servers, etc.)."""

    def __init__(self, base_url: str, model_name: str = "local"):
        """
        Initialize local model provider.
        
        Args:
            base_url: Base URL of local model server
            model_name: Name of the model
        """
        self.base_url = base_url.rstrip("/")
        self.model_name = model_name
        logger.info(f"Local model provider initialized: {model_name} ({base_url})")

    async def is_available(self) -> bool:
        """Check if local model is available."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.base_url}/api/tags",
                    timeout=aiohttp.ClientTimeout(total=5)
                ) as response:
                    return response.status == 200
        except Exception as e:
            logger.warning(f"Local model availability check failed: {e}")
            return False

    async def chat(self, messages: list[Message], temperature: float = 0.7, **kwargs) -> str:
        """Get response from local model."""
        formatted_messages = [
            {"role": msg.role, "content": msg.content}
            for msg in messages
        ]
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/api/chat",
                json={
                    "model": self.model_name,
                    "messages": formatted_messages,
                    "temperature": temperature,
                }
            ) as response:
                data = await response.json()
                return data.get("message", {}).get("content", "")

    async def stream_chat(self, messages: list[Message], temperature: float = 0.7, **kwargs) -> AsyncGenerator[str, None]:
        """Stream response from local model."""
        formatted_messages = [
            {"role": msg.role, "content": msg.content}
            for msg in messages
        ]
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/api/chat",
                json={
                    "model": self.model_name,
                    "messages": formatted_messages,
                    "temperature": temperature,
                    "stream": True,
                }
            ) as response:
                async for line in response.content:
                    if line:
                        text = line.decode().strip()
                        if text:
                            try:
                                import json
                                data = json.loads(text)
                                if "message" in data and "content" in data["message"]:
                                    yield data["message"]["content"]
                            except:
                                yield text

    def get_name(self) -> str:
        """Get provider name."""
        return f"Local-{self.model_name}"
