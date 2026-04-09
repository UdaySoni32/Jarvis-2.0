"""Tests for voice macro registry and lookup."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.voice.intent_router import AssistantMode
from src.voice.macro_engine import MacroEngine, VoiceMacro


def test_builtin_macros_exist():
    engine = MacroEngine()
    names = [macro.name for macro in engine.list_macros()]
    assert "start-work-mode" in names
    assert "incident-triage" in names
    assert "code-debug-sprint" in names


def test_macro_lookup_is_name_normalized():
    engine = MacroEngine()
    assert engine.get_macro("start work mode") is not None
    assert engine.get_macro("START_WORK_MODE") is not None


def test_can_register_custom_macro():
    engine = MacroEngine()
    custom = VoiceMacro(
        name="daily-summary",
        description="Summarize day progress",
        steps=["Summarize completed work in 5 bullets."],
        mode=AssistantMode.PRODUCTIVITY,
    )
    engine.register_macro(custom)
    loaded = engine.get_macro("daily summary")
    assert loaded is not None
    assert loaded.steps == custom.steps
