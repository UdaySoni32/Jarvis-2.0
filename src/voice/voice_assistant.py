"""
Voice Assistant for JARVIS

Integrates STT, TTS, wake word detection, and conversation management
"""

import logging
import asyncio
from typing import Optional, Callable
import numpy as np

from .audio_manager import AudioManager
from .stt_engine import STTEngine, create_stt_engine
from .tts_engine import TTSEngine, create_tts_engine
from .wake_word import WakeWordDetector, VoiceActivityDetector

logger = logging.getLogger(__name__)


class VoiceAssistant:
    """Complete voice assistant with STT, TTS, and wake word detection"""
    
    def __init__(
        self,
        stt_engine: Optional[STTEngine] = None,
        tts_engine: Optional[TTSEngine] = None,
        audio_manager: Optional[AudioManager] = None,
        wake_word_detector: Optional[WakeWordDetector] = None,
        conversation_handler: Optional[Callable] = None,
    ):
        """
        Initialize voice assistant
        
        Args:
            stt_engine: Speech-to-text engine
            tts_engine: Text-to-speech engine  
            audio_manager: Audio input/output manager
            wake_word_detector: Wake word detector
            conversation_handler: Function to handle user input and generate response
        """
        self.stt_engine = stt_engine
        self.tts_engine = tts_engine
        self.audio_manager = audio_manager or AudioManager()
        self.wake_word_detector = wake_word_detector
        self.conversation_handler = conversation_handler
        
        self.is_active = False
        self.is_listening = False
        
        logger.info("Voice assistant initialized")
    
    def speak(self, text: str, wait: bool = True):
        """
        Speak text using TTS
        
        Args:
            text: Text to speak
            wait: Wait for speech to complete
        """
        if not self.tts_engine:
            logger.warning("No TTS engine available")
            return
        
        try:
            self.tts_engine.speak(text, wait=wait)
        except Exception as e:
            logger.error(f"Failed to speak: {e}")
    
    def listen(self, duration: float = 5.0, use_vad: bool = True) -> str:
        """
        Listen for speech and transcribe
        
        Args:
            duration: Maximum recording duration in seconds
            use_vad: Use voice activity detection to stop early
        
        Returns:
            Transcribed text
        """
        if not self.stt_engine:
            logger.warning("No STT engine available")
            return ""
        
        try:
            logger.info(f"Listening for {duration} seconds...")
            
            if use_vad:
                # Use VAD for smart recording
                audio_data = self._record_with_vad(max_duration=duration)
            else:
                # Simple fixed-duration recording
                audio_data = self.audio_manager.record_audio(duration)
            
            if audio_data is None or len(audio_data) == 0:
                logger.warning("No audio recorded")
                return ""
            
            logger.info("Transcribing...")
            text = self.stt_engine.transcribe(
                audio_data,
                self.audio_manager.sample_rate
            )
            
            return text
        
        except Exception as e:
            logger.error(f"Failed to listen: {e}")
            return ""
    
    def _record_with_vad(self, max_duration: float = 10.0) -> Optional[np.ndarray]:
        """
        Record audio using voice activity detection
        
        Args:
            max_duration: Maximum recording duration
        
        Returns:
            Recorded audio data
        """
        try:
            vad = VoiceActivityDetector(
                sample_rate=self.audio_manager.sample_rate
            )
            
            # Start recording
            self.audio_manager.start_recording()
            
            # Record until silence or max duration
            import time
            start_time = time.time()
            silence_duration = 0
            max_silence = 1.5  # Stop after 1.5s of silence
            
            while time.time() - start_time < max_duration:
                time.sleep(0.1)
                
                # Check if we have enough silence
                audio_data = self.audio_manager.stop_recording()
                if audio_data is not None and len(audio_data) > 0:
                    # Check last 0.5 seconds for silence
                    last_chunk_size = int(0.5 * self.audio_manager.sample_rate)
                    last_chunk = audio_data[-last_chunk_size:]
                    
                    if not vad.is_speech(last_chunk):
                        silence_duration += 0.1
                        if silence_duration >= max_silence:
                            logger.info("Silence detected, stopping recording")
                            break
                    else:
                        silence_duration = 0
                
                # Continue recording
                self.audio_manager.start_recording()
            
            # Get final audio
            audio_data = self.audio_manager.stop_recording()
            return audio_data
        
        except Exception as e:
            logger.error(f"VAD recording failed: {e}")
            # Fallback to simple recording
            return self.audio_manager.record_audio(max_duration)
    
    async def conversation_loop(self):
        """Run continuous conversation loop"""
        if not self.conversation_handler:
            logger.error("No conversation handler configured")
            return
        
        self.is_active = True
        
        while self.is_active:
            try:
                # Listen for input
                user_input = self.listen(duration=5.0)
                
                if not user_input or len(user_input.strip()) == 0:
                    continue
                
                logger.info(f"User said: {user_input}")
                
                # Process with conversation handler
                response = await self.conversation_handler(user_input)
                
                if response:
                    logger.info(f"Assistant: {response}")
                    self.speak(response)
                
            except KeyboardInterrupt:
                logger.info("Conversation interrupted by user")
                break
            
            except Exception as e:
                logger.error(f"Error in conversation loop: {e}")
                self.speak("Sorry, I encountered an error.")
        
        self.is_active = False
    
    def start_wake_word_mode(self, callback: Optional[Callable] = None):
        """
        Start wake word detection mode
        
        Args:
            callback: Function called when wake word detected
        """
        if not self.wake_word_detector:
            logger.error("No wake word detector configured")
            return
        
        def on_wake_word_detected(keyword_index: int):
            """Handle wake word detection"""
            logger.info(f"Wake word detected (index={keyword_index})")
            self.speak("Yes? How can I help?")
            
            if callback:
                callback(keyword_index)
            else:
                # Default: listen and respond
                user_input = self.listen()
                if user_input and self.conversation_handler:
                    response = asyncio.run(self.conversation_handler(user_input))
                    if response:
                        self.speak(response)
        
        # Start listening for wake word
        self.wake_word_detector.start_listening(
            self.audio_manager,
            callback=on_wake_word_detected
        )
        
        logger.info("Wake word mode started")
    
    def stop_wake_word_mode(self):
        """Stop wake word detection"""
        if self.wake_word_detector:
            self.wake_word_detector.stop_listening(self.audio_manager)
            logger.info("Wake word mode stopped")
    
    def cleanup(self):
        """Clean up resources"""
        self.is_active = False
        
        if self.audio_manager:
            self.audio_manager.cleanup()
        
        if self.wake_word_detector:
            self.wake_word_detector.cleanup()
        
        logger.info("Voice assistant cleaned up")
    
    def __enter__(self):
        """Context manager entry"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.cleanup()


# Convenience function to create a ready-to-use voice assistant
def create_voice_assistant(
    stt_provider: str = "whisper",
    tts_provider: str = "pyttsx3",
    enable_wake_word: bool = False,
    wake_word_access_key: Optional[str] = None,
    conversation_handler: Optional[Callable] = None,
    **kwargs
) -> VoiceAssistant:
    """
    Create a fully configured voice assistant
    
    Args:
        stt_provider: STT provider ('whisper', 'google')
        tts_provider: TTS provider ('pyttsx3', 'elevenlabs', 'gtts')
        enable_wake_word: Enable wake word detection
        wake_word_access_key: Porcupine access key (required if enable_wake_word)
        conversation_handler: Function to handle conversations
        **kwargs: Additional provider-specific arguments
    
    Returns:
        Configured VoiceAssistant instance
    """
    # Create engines
    stt_engine = create_stt_engine(stt_provider, **kwargs.get('stt_args', {}))
    tts_engine = create_tts_engine(tts_provider, **kwargs.get('tts_args', {}))
    audio_manager = AudioManager()
    
    # Create wake word detector if enabled
    wake_word_detector = None
    if enable_wake_word:
        if not wake_word_access_key:
            logger.warning(
                "Wake word enabled but no access key provided. "
                "Wake word detection will be disabled."
            )
        else:
            try:
                wake_word_detector = WakeWordDetector(
                    access_key=wake_word_access_key
                )
            except Exception as e:
                logger.error(f"Failed to initialize wake word detector: {e}")
    
    return VoiceAssistant(
        stt_engine=stt_engine,
        tts_engine=tts_engine,
        audio_manager=audio_manager,
        wake_word_detector=wake_word_detector,
        conversation_handler=conversation_handler,
    )
