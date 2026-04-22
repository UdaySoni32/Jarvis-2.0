"""Voice-mode conversation runtime for JARVIS."""

from __future__ import annotations

from typing import Optional

from ..core.config import settings
from ..core.logger import logger
from ..core.llm import Message, llm_manager
from ..core.tools import tool_executor, tool_registry


class VoiceConversationRuntime:
    """Shared conversation handler used by voice mode."""

    def __init__(self):
        self.memory_manager = None
        if settings.enable_memory:
            try:
                from ..core.memory.semantic import semantic_memory

                semantic_memory.start_session(title="Voice Session")
                self.memory_manager = semantic_memory
            except Exception:
                from ..core.memory import memory_manager

                memory_manager.start_session(title="Voice Session")
                self.memory_manager = memory_manager

    async def handle(
        self,
        user_input: str,
        mode: Optional[str] = None,
        original_input: Optional[str] = None,
    ) -> str:
        """Handle one user utterance and return assistant text."""
        try:
            routed_mode = mode or "general"
            system_prompt = (
                "You are JARVIS, a concise, reliable voice assistant. "
                f"Current assistant mode: {routed_mode}. "
                "Keep spoken responses practical and brief."
            )

            if settings.enable_memory and self.memory_manager:
                self.memory_manager.add_message("user", original_input or user_input)
                context_messages = self.memory_manager.get_context_messages()
                messages = [Message("system", system_prompt)] + [
                    Message(msg["role"], msg["content"]) for msg in context_messages
                ]
            else:
                messages = [
                    Message("system", system_prompt),
                    Message("user", user_input),
                ]

            provider = await llm_manager.get_provider()
            tools_available = settings.enable_plugins and len(tool_registry) > 0
            final_response = ""

            if tools_available:
                response = await provider.generate_with_functions(
                    messages,
                    tool_registry.get_openai_functions(),
                    temperature=0.6,
                )

                if response.get("tool_calls"):
                    for tool_call in response["tool_calls"]:
                        tool_result = await tool_executor.execute_from_llm(tool_call)
                        messages.append(
                            Message("assistant", f"[Calling {tool_call.get('name', 'tool')}]")
                        )
                        messages.append(
                            Message("function", tool_executor.format_result_for_llm(tool_result))
                        )
                    final_response = await provider.generate(messages, temperature=0.6)
                else:
                    final_response = response.get("content", "")
            else:
                final_response = await provider.generate(messages, temperature=0.6)

            final_response = (final_response or "").strip()
            if settings.enable_memory and self.memory_manager and final_response:
                self.memory_manager.add_message("assistant", final_response)

            return final_response or "I didn't catch enough context to answer that."

        except Exception as exc:
            logger.error(f"Voice conversation failed: {exc}", exc_info=True)
            return (
                "I hit an issue while processing that request. "
                "Please retry or run jarvis configure to verify settings."
            )
