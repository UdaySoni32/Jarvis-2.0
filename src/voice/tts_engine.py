"""
Text-to-Speech Engine for JARVIS

Supports multiple TTS providers:
- pyttsx3 (offline, basic)
- ElevenLabs (cloud, premium voices)
- Custom TTS providers
"""

import logging
from abc import ABC, abstractmethod
from typing import Optional, List, Dict
import tempfile
from pathlib import Path

logger = logging.getLogger(__name__)


class TTSEngine(ABC):
    """Abstract base class for Text-to-Speech engines"""
    
    @abstractmethod
    def speak(self, text: str, wait: bool = True):
        """
        Convert text to speech and play it
        
        Args:
            text: Text to speak
            wait: If True, wait for speech to complete
        """
        pass
    
    @abstractmethod
    def save_speech(self, text: str, filename: str):
        """
        Convert text to speech and save to file
        
        Args:
            text: Text to speak
            filename: Output file path
        """
        pass


class Pyttsx3TTS(TTSEngine):
    """pyttsx3 offline TTS engine"""
    
    def __init__(
        self,
        rate: int = 200,
        volume: float = 0.9,
        voice_id: Optional[str] = None,
    ):
        """
        Initialize pyttsx3 TTS
        
        Args:
            rate: Speech rate (words per minute)
            volume: Volume level (0.0 to 1.0)
            voice_id: Specific voice ID (None for default)
        """
        try:
            import pyttsx3
            self.engine = pyttsx3.init()
            
            # Set properties
            self.engine.setProperty('rate', rate)
            self.engine.setProperty('volume', volume)
            
            if voice_id:
                self.engine.setProperty('voice', voice_id)
            
            logger.info(f"pyttsx3 TTS initialized (rate={rate}, volume={volume})")
        
        except ImportError:
            raise ImportError("Install pyttsx3: pip install pyttsx3")
        
        except Exception as e:
            logger.error(f"Failed to initialize pyttsx3: {e}")
            raise
    
    def list_voices(self) -> List[Dict[str, str]]:
        """List available voices"""
        voices = self.engine.getProperty('voices')
        return [
            {
                "id": voice.id,
                "name": voice.name,
                "language": getattr(voice, 'languages', ['unknown'])[0]
            }
            for voice in voices
        ]
    
    def speak(self, text: str, wait: bool = True):
        """Speak text"""
        try:
            logger.info(f"Speaking: {text[:50]}...")
            self.engine.say(text)
            
            if wait:
                self.engine.runAndWait()
            
        except Exception as e:
            logger.error(f"TTS speak failed: {e}")
            raise
    
    def save_speech(self, text: str, filename: str):
        """Save speech to file"""
        try:
            logger.info(f"Saving speech to {filename}")
            self.engine.save_to_file(text, filename)
            self.engine.runAndWait()
        
        except Exception as e:
            logger.error(f"TTS save failed: {e}")
            raise
    
    def stop(self):
        """Stop current speech"""
        try:
            self.engine.stop()
        except Exception as e:
            logger.error(f"TTS stop failed: {e}")


class ElevenLabsTTS(TTSEngine):
    """ElevenLabs cloud TTS engine (premium voices)"""
    
    def __init__(
        self,
        api_key: str,
        voice_id: str = "21m00Tcm4TlvDq8ikWAM",  # Default voice (Rachel)
        model_id: str = "eleven_monolingual_v1",
    ):
        """
        Initialize ElevenLabs TTS
        
        Args:
            api_key: ElevenLabs API key
            voice_id: Voice ID to use
            model_id: Model ID to use
        """
        if not api_key:
            raise ValueError("API key required for ElevenLabs")
        
        try:
            from elevenlabs import generate, play, voices, save
            self.generate = generate
            self.play = play
            self.save = save
            self.voices_func = voices
            
            self.api_key = api_key
            self.voice_id = voice_id
            self.model_id = model_id
            
            # Set API key
            from elevenlabs import set_api_key
            set_api_key(api_key)
            
            logger.info(f"ElevenLabs TTS initialized (voice={voice_id})")
        
        except ImportError:
            raise ImportError("Install elevenlabs: pip install elevenlabs")
    
    def list_voices(self) -> List[Dict[str, str]]:
        """List available voices"""
        try:
            voice_list = self.voices_func()
            return [
                {
                    "id": voice.voice_id,
                    "name": voice.name,
                    "category": voice.category,
                }
                for voice in voice_list
            ]
        except Exception as e:
            logger.error(f"Failed to list voices: {e}")
            return []
    
    def speak(self, text: str, wait: bool = True):
        """Speak text using ElevenLabs"""
        try:
            logger.info(f"Speaking with ElevenLabs: {text[:50]}...")
            
            audio = self.generate(
                text=text,
                voice=self.voice_id,
                model=self.model_id,
            )
            
            if wait:
                self.play(audio)
            
        except Exception as e:
            logger.error(f"ElevenLabs TTS failed: {e}")
            raise
    
    def save_speech(self, text: str, filename: str):
        """Save speech to file"""
        try:
            logger.info(f"Saving speech to {filename}")
            
            audio = self.generate(
                text=text,
                voice=self.voice_id,
                model=self.model_id,
            )
            
            self.save(audio, filename)
        
        except Exception as e:
            logger.error(f"ElevenLabs save failed: {e}")
            raise


class GTTSEngine(TTSEngine):
    """Google Text-to-Speech (gTTS) engine"""
    
    def __init__(
        self,
        language: str = "en",
        slow: bool = False,
    ):
        """
        Initialize gTTS engine
        
        Args:
            language: Language code (e.g., 'en', 'es', 'fr')
            slow: Speak slowly
        """
        try:
            from gtts import gTTS
            import pygame
            
            self.gTTS = gTTS
            self.language = language
            self.slow = slow
            
            # Initialize pygame for audio playback
            pygame.mixer.init()
            
            logger.info(f"gTTS initialized (language={language})")
        
        except ImportError as e:
            raise ImportError(
                "Install gTTS and pygame: "
                "pip install gTTS pygame"
            )
    
    def speak(self, text: str, wait: bool = True):
        """Speak text using gTTS"""
        try:
            import pygame
            
            logger.info(f"Speaking with gTTS: {text[:50]}...")
            
            # Create temporary file
            with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
                temp_file = f.name
            
            # Generate speech
            tts = self.gTTS(text=text, lang=self.language, slow=self.slow)
            tts.save(temp_file)
            
            # Play audio
            pygame.mixer.music.load(temp_file)
            pygame.mixer.music.play()
            
            if wait:
                while pygame.mixer.music.get_busy():
                    pygame.time.Clock().tick(10)
            
            # Cleanup
            Path(temp_file).unlink(missing_ok=True)
        
        except Exception as e:
            logger.error(f"gTTS speak failed: {e}")
            raise
    
    def save_speech(self, text: str, filename: str):
        """Save speech to file"""
        try:
            logger.info(f"Saving speech to {filename}")
            
            tts = self.gTTS(text=text, lang=self.language, slow=self.slow)
            tts.save(filename)
        
        except Exception as e:
            logger.error(f"gTTS save failed: {e}")
            raise


def create_tts_engine(
    provider: str = "pyttsx3",
    **kwargs
) -> TTSEngine:
    """
    Create TTS engine
    
    Args:
        provider: TTS provider ('pyttsx3', 'elevenlabs', 'gtts')
        **kwargs: Provider-specific arguments
    
    Returns:
        Initialized TTS engine
    """
    providers = {
        "pyttsx3": Pyttsx3TTS,
        "elevenlabs": ElevenLabsTTS,
        "gtts": GTTSEngine,
    }
    
    if provider not in providers:
        raise ValueError(f"Unknown TTS provider: {provider}")
    
    return providers[provider](**kwargs)
