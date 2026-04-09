"""Tests for natural follow-up resolution in voice mode."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.voice.followup_resolver import FollowupResolver


def test_same_for_rewrites_prior_request():
    resolver = FollowupResolver()
    result = resolver.resolve(
        user_input="do the same for tomorrow",
        last_user_input="summarize my priorities for today",
        last_response=None,
    )
    assert result.is_followup is True
    assert result.reason == "same_for"
    assert "for tomorrow" in result.resolved_input


def test_make_it_shorter_uses_last_response():
    resolver = FollowupResolver()
    result = resolver.resolve(
        user_input="make it shorter",
        last_user_input="explain deployment plan",
        last_response="Very long answer ...",
    )
    assert result.is_followup is True
    assert result.reason == "shorten_last_response"
    assert "Very long answer" in result.resolved_input


def test_non_followup_passes_through():
    resolver = FollowupResolver()
    result = resolver.resolve(
        user_input="what's the weather in tokyo",
        last_user_input="anything",
        last_response="anything",
    )
    assert result.is_followup is False
    assert result.resolved_input == "what's the weather in tokyo"
