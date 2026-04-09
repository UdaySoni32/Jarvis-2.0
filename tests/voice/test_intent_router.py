"""Tests for voice intent routing."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.voice.intent_router import AssistantMode, IntentRouter


def test_defaults_to_general_when_no_keywords():
    router = IntentRouter()
    route = router.classify("tell me a joke")
    assert route.mode == AssistantMode.GENERAL
    assert route.source == "auto"


def test_routes_to_coding_for_code_keywords():
    router = IntentRouter()
    route = router.classify("please debug this python stack trace")
    assert route.mode == AssistantMode.CODING
    assert route.confidence > 0.3
    assert "python" in route.matched_keywords or "debug" in route.matched_keywords


def test_routes_to_ops_for_infra_keywords():
    router = IntentRouter()
    route = router.classify("check server logs and restart docker service")
    assert route.mode == AssistantMode.OPS


def test_manual_mode_override():
    router = IntentRouter()
    routed_prompt, route = router.route_input(
        "plan my day",
        explicit_mode=AssistantMode.PRODUCTIVITY,
    )
    assert route.mode == AssistantMode.PRODUCTIVITY
    assert route.source == "manual"
    assert "Mode: productivity assistant." in routed_prompt
