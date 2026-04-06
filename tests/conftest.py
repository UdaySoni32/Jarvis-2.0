"""pytest configuration and shared fixtures for JARVIS 2.0 test suite."""

import asyncio
import sys
from pathlib import Path

import pytest

# Ensure src/ is importable
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


# ---------------------------------------------------------------------------
# Pytest markers
# ---------------------------------------------------------------------------

def pytest_configure(config):
    """Register custom pytest markers."""
    config.addinivalue_line(
        "markers", "llm: mark test as requiring a live LLM API (openai/ollama)"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow-running"
    )


# ---------------------------------------------------------------------------
# Event-loop fixture (for async tests)
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
def event_loop():
    """Provide a single event loop for the entire test session."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


# ---------------------------------------------------------------------------
# Core fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
def settings():
    """Provide the global settings instance."""
    from core.config import settings as _settings
    return _settings


@pytest.fixture
def memory_manager():
    """Provide a fresh memory manager with a clean test session."""
    from core.memory import memory_manager as mgr
    session = mgr.start_session(title="Pytest Session")
    yield mgr
    # Cleanup: delete the test session
    try:
        mgr.delete_session(session.session_id)
    except Exception:
        pass


@pytest.fixture
def tool_registry():
    """Provide the tool registry with all plugins registered."""
    from core.tools.registry import tool_registry as registry
    from plugins import register_all_plugins  # noqa: F401 (auto-registers)
    return registry


@pytest.fixture
def tool_executor(tool_registry):
    """Provide the tool executor."""
    from core.tools.executor import tool_executor as executor
    return executor
