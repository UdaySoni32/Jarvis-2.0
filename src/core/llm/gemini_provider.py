"""Google Gemini provider for JARVIS 2.0."""

from typing import AsyncGenerator, Optional
from ..logger import logger

try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False

from .base import BaseLLMProvider, Message


class GeminiProvider(BaseLLMProvider):
    """Google Gemini provider using Google AI API."""

    def __init__(self):
        """Initialize Gemini provider."""
        from ...core.config import settings
        
        if not settings.has_gemini_key:
            raise ValueError("GEMINI_API_KEY not set")
        
        genai.configure(api_key=settings.gemini_api_key)
        self.model = "gemini-1.5-pro"
        self.client = genai.GenerativeModel(self.model)
        logger.info(f"Gemini provider initialized with model: {self.model}")

    async def is_available(self) -> bool:
        """Check if Gemini API is available."""
        try:
            response = await self.client.generate_content_async("ping")
            return response and len(response.text) > 0
        except Exception as e:
            logger.warning(f"Gemini availability check failed: {e}")
            return False

    async def chat(self, messages: list[Message], temperature: float = 0.7, **kwargs) -> str:
        """
        Get a chat response from Gemini.
        
        Args:
            messages: List of Message objects
            temperature: Temperature for response generation
            **kwargs: Additional parameters
            
        Returns:
            Response text
        """
        # Format messages for Gemini
        chat_history = []
        user_message = None
        
        for msg in messages:
            if msg.role == "system":
                # System messages become part of the initial prompt
                continue
            elif msg.role == "user":
                user_message = msg.content
            elif msg.role == "assistant":
                chat_history.append({
                    "role": "model",
                    "parts": msg.content
                })
        
        # Create chat session
        chat = self.client.start_chat(history=chat_history)
        
        response = await chat.send_message_async(
            user_message,
            generation_config={
                "temperature": temperature,
                "max_output_tokens": kwargs.get("max_tokens", 2000),
            }
        )
        
        return response.text

    async def stream_chat(self, messages: list[Message], temperature: float = 0.7, **kwargs) -> AsyncGenerator[str, None]:
        """
        Stream a chat response from Gemini.
        
        Args:
            messages: List of Message objects
            temperature: Temperature for response generation
            **kwargs: Additional parameters
            
        Yields:
            Response chunks
        """
        # Format messages for Gemini
        chat_history = []
        user_message = None
        
        for msg in messages:
            if msg.role == "system":
                continue
            elif msg.role == "user":
                user_message = msg.content
            elif msg.role == "assistant":
                chat_history.append({
                    "role": "model",
                    "parts": msg.content
                })
        
        # Create chat session
        chat = self.client.start_chat(history=chat_history)
        
        response = await chat.send_message_async(
            user_message,
            generation_config={
                "temperature": temperature,
                "max_output_tokens": kwargs.get("max_tokens", 2000),
            },
            stream=True
        )
        
        async for chunk in response:
            if chunk.text:
                yield chunk.text

    def get_name(self) -> str:
        """Get provider name."""
        return "Gemini"
