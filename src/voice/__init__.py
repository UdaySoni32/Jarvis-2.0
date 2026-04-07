"""
JARVIS 2.0 Voice Interface Module

Provides speech-to-text, text-to-speech, and voice control capabilities.
"""

from .audio_manager import AudioManager

try:
    from .stt_engine import STTEngine, WhisperSTT, GoogleSTT
    STT_AVAILABLE = True
except ImportError:
    STT_AVAILABLE = False
    STTEngine = None
    WhisperSTT = None
    GoogleSTT = None

try:
    from .tts_engine import TTSEngine, Pyttsx3TTS, ElevenLabsTTS
    TTS_AVAILABLE = True
except ImportError:
    TTS_AVAILABLE = False
    TTSEngine = None
    Pyttsx3TTS = None
    ElevenLabsTTS = None

try:
    from .wake_word import WakeWordDetector
    WAKE_WORD_AVAILABLE = True
except ImportError:
    WAKE_WORD_AVAILABLE = False
    WakeWordDetector = None

try:
    from .voice_assistant import VoiceAssistant
    VOICE_ASSISTANT_AVAILABLE = True
except ImportError:
    VOICE_ASSISTANT_AVAILABLE = False
    VoiceAssistant = None

__all__ = [
    "AudioManager",
    "STTEngine",
    "WhisperSTT",
    "GoogleSTT",
    "TTSEngine",
    "Pyttsx3TTS",
    "ElevenLabsTTS",
    "WakeWordDetector",
    "VoiceAssistant",
]
