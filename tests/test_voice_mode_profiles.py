"""Tests for voice profile selection and fallback behavior."""

import asyncio
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.cli.voice_mode import VoiceMode
from src.core.config import settings


async def _dummy_handler(user_input: str, **kwargs) -> str:
    return f"ok:{user_input}"


def test_voice_mode_cloud_profile_uses_cloud_providers(monkeypatch):
    created = {"stt": None, "tts": None}

    class FakeAudioManager:
        def __init__(self):
            self.sample_rate = 16000

        @staticmethod
        def list_devices():
            return [{"index": 0}]

    monkeypatch.setattr("src.cli.voice_mode.AudioManager", FakeAudioManager)
    monkeypatch.setattr(
        "src.cli.voice_mode.create_stt_engine",
        lambda provider, **kwargs: created.update({"stt": provider}) or object(),
    )
    monkeypatch.setattr(
        "src.cli.voice_mode.create_tts_engine",
        lambda provider, **kwargs: created.update({"tts": provider}) or object(),
    )
    monkeypatch.setattr("src.cli.voice_mode.WakeWordDetector", lambda *args, **kwargs: object())
    monkeypatch.setattr(
        "src.cli.voice_mode.VoiceAssistant",
        lambda **kwargs: object(),
    )

    settings.voice_profile = "cloud"
    settings.voice_cloud_stt_provider = "whisper"
    settings.voice_cloud_tts_provider = "gtts"
    settings.enable_wake_word = False
    settings.openai_api_key = "test-key"

    vm = VoiceMode(_dummy_handler)
    initialized = asyncio.run(vm.initialize())
    assert initialized is True
    assert created["stt"] == "whisper"
    assert created["tts"] == "gtts"


def test_voice_mode_cloud_falls_back_to_local(monkeypatch):
    created = {"stt": [], "tts": []}

    class FakeAudioManager:
        def __init__(self):
            self.sample_rate = 16000

        @staticmethod
        def list_devices():
            return [{"index": 0}]

    monkeypatch.setattr("src.cli.voice_mode.AudioManager", FakeAudioManager)

    def fake_stt(provider, **kwargs):
        created["stt"].append(provider)
        if provider == "google":
            raise ValueError("cloud stt failed")
        return object()

    def fake_tts(provider, **kwargs):
        created["tts"].append(provider)
        return object()

    monkeypatch.setattr("src.cli.voice_mode.create_stt_engine", fake_stt)
    monkeypatch.setattr("src.cli.voice_mode.create_tts_engine", fake_tts)
    monkeypatch.setattr("src.cli.voice_mode.WakeWordDetector", lambda *args, **kwargs: object())
    monkeypatch.setattr(
        "src.cli.voice_mode.VoiceAssistant",
        lambda **kwargs: object(),
    )

    settings.voice_profile = "cloud"
    settings.voice_cloud_stt_provider = "google"
    settings.voice_cloud_tts_provider = "gtts"
    settings.voice_fallback_to_local = True
    settings.enable_wake_word = False

    vm = VoiceMode(_dummy_handler)
    initialized = asyncio.run(vm.initialize())
    assert initialized is True
    assert created["stt"] == ["google", "whisper"]
    assert created["tts"][-1] == "pyttsx3"
