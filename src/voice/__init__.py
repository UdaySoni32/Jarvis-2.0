"""
JARVIS 2.0 Voice Interface Module

Provides speech-to-text, text-to-speech, and voice control capabilities.
"""

from .audio_manager import AudioManager

try:
    from .stt_engine import STTEngine, WhisperSTT, GoogleSTT, create_stt_engine
    STT_AVAILABLE = True
except ImportError:
    STT_AVAILABLE = False
    STTEngine = None
    WhisperSTT = None
    GoogleSTT = None
    create_stt_engine = None

try:
    from .tts_engine import TTSEngine, Pyttsx3TTS, ElevenLabsTTS, GTTSEngine, create_tts_engine
    TTS_AVAILABLE = True
except ImportError:
    TTS_AVAILABLE = False
    TTSEngine = None
    Pyttsx3TTS = None
    ElevenLabsTTS = None
    GTTSEngine = None
    create_tts_engine = None

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

from .intent_router import AssistantMode, IntentRoute, IntentRouter
from .macro_engine import VoiceMacro, MacroEngine
from .followup_resolver import FollowupResolver, FollowupResolution

__all__ = [
    "AudioManager",
    "STTEngine",
    "WhisperSTT",
    "GoogleSTT",
    "create_stt_engine",
    "TTSEngine",
    "Pyttsx3TTS",
    "ElevenLabsTTS",
    "GTTSEngine",
    "create_tts_engine",
    "WakeWordDetector",
    "VoiceAssistant",
    "AssistantMode",
    "IntentRoute",
    "IntentRouter",
    "VoiceMacro",
    "MacroEngine",
    "FollowupResolver",
    "FollowupResolution",
]
