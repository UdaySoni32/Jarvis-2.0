"""Pytest-style unit tests for JARVIS 2.0 core systems."""

import asyncio
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


# ---------------------------------------------------------------------------
# Helper: run async in a fresh event loop (safe inside pytest)
# ---------------------------------------------------------------------------

def _run(coro):
    """Run a coroutine in an isolated event loop (avoids nested-loop issues)."""
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


# ---------------------------------------------------------------------------
# Configuration Tests
# ---------------------------------------------------------------------------

class TestConfig:
    """Tests for the settings/config system."""

    def test_settings_loads(self, settings):
        """Settings object must load without exceptions."""
        assert settings is not None

    def test_default_llm_is_set(self, settings):
        """A default LLM provider must be specified."""
        assert settings.default_llm in ("openai", "ollama", "claude", "anthropic")

    def test_user_data_dir_created(self, settings):
        """user_data_dir is created automatically on startup."""
        assert settings.user_data_dir.exists()

    def test_max_context_messages_positive(self, settings):
        """max_context_messages must be a positive integer."""
        assert isinstance(settings.max_context_messages, int)
        assert settings.max_context_messages > 0

    def test_has_openai_key_property(self, settings):
        """has_openai_key is bool-typed."""
        assert isinstance(settings.has_openai_key, bool)


# ---------------------------------------------------------------------------
# Memory System Tests
# ---------------------------------------------------------------------------

class TestMemorySystem:
    """Tests for the SQLite conversation memory system."""

    def test_session_created(self, memory_manager):
        """start_session() must return a session with an ID."""
        assert memory_manager.current_session is not None
        assert memory_manager.current_session.session_id != ""

    def test_add_and_retrieve_messages(self, memory_manager):
        """Messages added to the session must be retrievable."""
        memory_manager.add_message("user", "Hello JARVIS!")
        memory_manager.add_message("assistant", "Hello! How can I help?")
        ctx = memory_manager.get_context_messages()
        assert len(ctx) >= 2

    def test_context_roles(self, memory_manager):
        """Context messages must have role and content keys."""
        memory_manager.add_message("user", "Test message")
        ctx = memory_manager.get_context_messages()
        for msg in ctx:
            assert "role" in msg
            assert "content" in msg

    def test_max_context_limit(self, memory_manager, settings):
        """get_context_messages(max_messages=N) must honour the cap."""
        for i in range(5):
            memory_manager.add_message("user", f"msg {i}")
        ctx = memory_manager.get_context_messages(max_messages=3)
        assert len(ctx) <= 3

    def test_session_summary(self, memory_manager):
        """get_session_summary() returns a dict with expected keys."""
        summary = memory_manager.get_session_summary()
        assert isinstance(summary, dict)
        assert "active" in summary
        assert "message_count" in summary

    def test_search_messages(self, memory_manager):
        """search() returns results containing the query string."""
        memory_manager.add_message("user", "unique_search_term_xyz")
        results = memory_manager.search("unique_search_term_xyz")
        assert len(results) >= 1

    def test_list_sessions(self, memory_manager):
        """list_sessions() returns a non-empty list after creating a session."""
        sessions = memory_manager.list_sessions(limit=10)
        assert len(sessions) >= 1

    def test_persistence(self, settings):
        """A session saved and loaded must restore its messages."""
        from core.memory import memory_manager as mgr
        session = mgr.start_session(title="Persistence Test")
        session_id = session.session_id
        mgr.add_message("user", "persisted message")
        mgr.end_session()

        loaded = mgr.load_session(session_id)
        assert loaded
        assert any(
            m.content == "persisted message"
            for m in mgr.current_session.messages
        )
        mgr.delete_session(session_id)


# ---------------------------------------------------------------------------
# Tool Registry Tests
# ---------------------------------------------------------------------------

class TestToolRegistry:
    """Tests for the tool registration and lookup system."""

    def test_plugins_registered(self, tool_registry):
        """At least 10 plugins should be registered."""
        assert len(tool_registry) >= 10

    def test_calculator_present(self, tool_registry):
        """The calculator tool must be registered."""
        assert tool_registry.get("calculator") is not None

    def test_get_openai_functions(self, tool_registry):
        """get_openai_functions() returns a valid list of dicts."""
        funcs = tool_registry.get_openai_functions()
        assert isinstance(funcs, list)
        assert len(funcs) > 0
        for f in funcs:
            assert "name" in f
            assert "description" in f

    def test_all_tools_have_name(self, tool_registry):
        """Every registered tool must have a non-empty name."""
        for tool in tool_registry.get_all_tools():
            assert tool.name != ""

    def test_all_tools_have_description(self, tool_registry):
        """Every registered tool must have a non-empty description."""
        for tool in tool_registry.get_all_tools():
            assert tool.description != ""


# ---------------------------------------------------------------------------
# Tool Execution Tests
# ---------------------------------------------------------------------------

class TestToolExecution:
    """Tests for async tool execution (each uses a fresh event loop)."""

    def test_calculator(self, tool_executor):
        result = _run(tool_executor.execute("calculator", {"expression": "2 + 2"}))
        assert result["success"]
        assert result["result"]["result"] == 4

    def test_datetime(self, tool_executor):
        result = _run(tool_executor.execute("datetime", {"info_type": "current"}))
        assert result["success"]
        assert "date" in result["result"]

    def test_system_info(self, tool_executor):
        result = _run(tool_executor.execute("systeminfo", {"info_type": "cpu"}))
        assert result["success"]
        assert "cpu" in result["result"]

    def test_notes_create_and_delete(self, tool_executor):
        create_result = _run(tool_executor.execute("notes", {
            "action": "create",
            "title": "pytest note",
            "content": "temporary test note",
            "tags": "test",
        }))
        assert create_result["success"]
        note_id = create_result["result"]["note"]["id"]

        del_result = _run(
            tool_executor.execute("notes", {"action": "delete", "note_id": note_id})
        )
        assert del_result["success"]

    def test_timer_create_and_cancel(self, tool_executor):
        create_result = _run(tool_executor.execute("timer", {
            "action": "create",
            "duration": 60,
            "label": "pytest timer",
        }))
        assert create_result["success"]
        timer_id = create_result["result"]["timer_id"]

        cancel_result = _run(
            tool_executor.execute("timer", {"action": "cancel", "timer_id": timer_id})
        )
        assert cancel_result["success"]

    def test_process_manager(self, tool_executor):
        result = _run(tool_executor.execute("processmanager", {
            "action": "list",
            "limit": 5,
        }))
        assert result["success"]
        assert result["result"]["total_count"] > 0

    @pytest.mark.slow
    def test_web_search(self, tool_executor):
        """Network-dependent test. Run with: pytest -m slow"""
        result = _run(tool_executor.execute("websearch", {
            "query": "Python programming language",
            "max_results": 3,
        }))
        assert result["success"]
