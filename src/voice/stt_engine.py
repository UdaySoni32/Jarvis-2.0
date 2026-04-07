"""
Speech-to-Text Engine for JARVIS

Supports multiple STT providers:
- OpenAI Whisper (local or API)
- Google Speech Recognition
- Custom STT providers
"""

import logging
import tempfile
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
from pathlib import Path
import numpy as np

logger = logging.getLogger(__name__)


class STTEngine(ABC):
    """Abstract base class for Speech-to-Text engines"""
    
    @abstractmethod
    def transcribe(self, audio_data: np.ndarray, sample_rate: int = 16000) -> str:
        """
        Transcribe audio to text
        
        Args:
            audio_data: Audio data as numpy array
            sample_rate: Audio sample rate in Hz
        
        Returns:
            Transcribed text
        """
        pass
    
    @abstractmethod
    def transcribe_file(self, audio_file: str) -> str:
        """
        Transcribe audio file to text
        
        Args:
            audio_file: Path to audio file
        
        Returns:
            Transcribed text
        """
        pass


class WhisperSTT(STTEngine):
    """OpenAI Whisper Speech-to-Text Engine"""
    
    def __init__(
        self,
        model_size: str = "base",
        device: str = "cpu",
        language: Optional[str] = None,
        use_api: bool = False,
        api_key: Optional[str] = None,
    ):
        """
        Initialize Whisper STT
        
        Args:
            model_size: Whisper model size (tiny, base, small, medium, large)
            device: Device to run on (cpu, cuda)
            language: Language code (None for auto-detect)
            use_api: Use OpenAI API instead of local model
            api_key: OpenAI API key (required if use_api=True)
        """
        self.model_size = model_size
        self.device = device
        self.language = language
        self.use_api = use_api
        self.api_key = api_key
        
        if use_api:
            if not api_key:
                raise ValueError("API key required for OpenAI Whisper API")
            
            try:
                from openai import OpenAI
                self.client = OpenAI(api_key=api_key)
                self.model = None
                logger.info("Whisper API initialized")
            except ImportError:
                raise ImportError("Install openai: pip install openai")
        
        else:
            try:
                import whisper
                self.model = whisper.load_model(model_size, device=device)
                self.client = None
                logger.info(f"Whisper model '{model_size}' loaded on {device}")
            except ImportError:
                raise ImportError(
                    "Install whisper: pip install openai-whisper"
                )
    
    def transcribe(self, audio_data: np.ndarray, sample_rate: int = 16000) -> str:
        """Transcribe audio data to text"""
        # Save to temporary file and transcribe
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            temp_file = f.name
        
        try:
            import soundfile as sf
            sf.write(temp_file, audio_data, sample_rate)
            return self.transcribe_file(temp_file)
        
        finally:
            Path(temp_file).unlink(missing_ok=True)
    
    def transcribe_file(self, audio_file: str) -> str:
        """Transcribe audio file to text"""
        try:
            if self.use_api:
                # Use OpenAI API
                with open(audio_file, "rb") as f:
                    response = self.client.audio.transcriptions.create(
                        model="whisper-1",
                        file=f,
                        language=self.language,
                    )
                text = response.text
            
            else:
                # Use local model
                options = {}
                if self.language:
                    options["language"] = self.language
                
                result = self.model.transcribe(audio_file, **options)
                text = result["text"]
            
            logger.info(f"Transcribed: {text[:100]}...")
            return text.strip()
        
        except Exception as e:
            logger.error(f"Whisper transcription failed: {e}")
            raise


class GoogleSTT(STTEngine):
    """Google Speech Recognition STT Engine"""
    
    def __init__(
        self,
        language: str = "en-US",
        use_cloud: bool = False,
        credentials_file: Optional[str] = None,
    ):
        """
        Initialize Google STT
        
        Args:
            language: Language code (e.g., 'en-US', 'es-ES')
            use_cloud: Use Google Cloud Speech API (requires credentials)
            credentials_file: Path to Google Cloud credentials JSON
        """
        self.language = language
        self.use_cloud = use_cloud
        
        if use_cloud:
            if not credentials_file:
                raise ValueError(
                    "Credentials file required for Google Cloud Speech API"
                )
            
            try:
                from google.cloud import speech
                import os
                os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = credentials_file
                self.client = speech.SpeechClient()
                logger.info("Google Cloud Speech API initialized")
            except ImportError:
                raise ImportError(
                    "Install google-cloud-speech: "
                    "pip install google-cloud-speech"
                )
        
        else:
            try:
                import speech_recognition as sr
                self.recognizer = sr.Recognizer()
                self.client = None
                logger.info("Google Speech Recognition initialized (free)")
            except ImportError:
                raise ImportError(
                    "Install SpeechRecognition: "
                    "pip install SpeechRecognition"
                )
    
    def transcribe(self, audio_data: np.ndarray, sample_rate: int = 16000) -> str:
        """Transcribe audio data to text"""
        if self.use_cloud:
            return self._transcribe_cloud(audio_data, sample_rate)
        else:
            return self._transcribe_free(audio_data, sample_rate)
    
    def _transcribe_free(
        self,
        audio_data: np.ndarray,
        sample_rate: int = 16000
    ) -> str:
        """Transcribe using free Google Speech Recognition"""
        import speech_recognition as sr
        
        # Save to temporary WAV file
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            temp_file = f.name
        
        try:
            import soundfile as sf
            sf.write(temp_file, audio_data, sample_rate)
            
            with sr.AudioFile(temp_file) as source:
                audio = self.recognizer.record(source)
            
            text = self.recognizer.recognize_google(
                audio,
                language=self.language
            )
            
            logger.info(f"Transcribed: {text[:100]}...")
            return text.strip()
        
        except sr.UnknownValueError:
            logger.warning("Google STT could not understand audio")
            return ""
        
        except sr.RequestError as e:
            logger.error(f"Google STT request failed: {e}")
            raise
        
        finally:
            Path(temp_file).unlink(missing_ok=True)
    
    def _transcribe_cloud(
        self,
        audio_data: np.ndarray,
        sample_rate: int = 16000
    ) -> str:
        """Transcribe using Google Cloud Speech API"""
        from google.cloud import speech
        
        # Convert audio to bytes
        audio_bytes = audio_data.tobytes()
        
        audio = speech.RecognitionAudio(content=audio_bytes)
        config = speech.RecognitionConfig(
            encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
            sample_rate_hertz=sample_rate,
            language_code=self.language,
        )
        
        response = self.client.recognize(config=config, audio=audio)
        
        if response.results:
            text = response.results[0].alternatives[0].transcript
            logger.info(f"Transcribed: {text[:100]}...")
            return text.strip()
        
        logger.warning("No speech recognized")
        return ""
    
    def transcribe_file(self, audio_file: str) -> str:
        """Transcribe audio file to text"""
        import soundfile as sf
        audio_data, sample_rate = sf.read(audio_file)
        return self.transcribe(audio_data, sample_rate)


def create_stt_engine(
    provider: str = "whisper",
    **kwargs
) -> STTEngine:
    """
    Create STT engine
    
    Args:
        provider: STT provider ('whisper', 'google')
        **kwargs: Provider-specific arguments
    
    Returns:
        Initialized STT engine
    """
    providers = {
        "whisper": WhisperSTT,
        "google": GoogleSTT,
    }
    
    if provider not in providers:
        raise ValueError(f"Unknown STT provider: {provider}")
    
    return providers[provider](**kwargs)
