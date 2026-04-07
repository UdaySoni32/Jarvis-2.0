"""
Wake Word Detection for JARVIS

Supports:
- Porcupine wake word detection
- Custom wake words
- Voice activity detection (VAD)
"""

import logging
import threading
from typing import Optional, Callable
import numpy as np

logger = logging.getLogger(__name__)


class WakeWordDetector:
    """Wake word detector using Porcupine"""
    
    def __init__(
        self,
        access_key: Optional[str] = None,
        keyword_paths: Optional[list] = None,
        sensitivities: Optional[list] = None,
    ):
        """
        Initialize wake word detector
        
        Args:
            access_key: Porcupine access key
            keyword_paths: List of custom keyword file paths
            sensitivities: List of sensitivities (0.0 to 1.0) for each keyword
        """
        try:
            import pvporcupine
            
            if not access_key:
                raise ValueError(
                    "Porcupine access key required. "
                    "Get free key at: https://console.picovoice.ai/"
                )
            
            # Use built-in keywords if no custom paths provided
            if not keyword_paths:
                keywords = ["jarvis"]  # Built-in Porcupine keyword
                self.porcupine = pvporcupine.create(
                    access_key=access_key,
                    keywords=keywords,
                    sensitivities=sensitivities or [0.5],
                )
            else:
                self.porcupine = pvporcupine.create(
                    access_key=access_key,
                    keyword_paths=keyword_paths,
                    sensitivities=sensitivities or [0.5] * len(keyword_paths),
                )
            
            self.sample_rate = self.porcupine.sample_rate
            self.frame_length = self.porcupine.frame_length
            self.is_listening = False
            self.detection_callback: Optional[Callable] = None
            
            logger.info(
                f"Wake word detector initialized "
                f"(sample_rate={self.sample_rate}Hz, "
                f"frame_length={self.frame_length})"
            )
        
        except ImportError:
            raise ImportError(
                "Install pvporcupine: pip install pvporcupine"
            )
        
        except Exception as e:
            logger.error(f"Failed to initialize wake word detector: {e}")
            raise
    
    def process_frame(self, audio_frame: np.ndarray) -> int:
        """
        Process audio frame for wake word detection
        
        Args:
            audio_frame: Audio frame (must be frame_length samples)
        
        Returns:
            Keyword index if detected, -1 otherwise
        """
        try:
            # Convert to int16 if needed
            if audio_frame.dtype != np.int16:
                audio_frame = (audio_frame * 32767).astype(np.int16)
            
            keyword_index = self.porcupine.process(audio_frame)
            
            if keyword_index >= 0:
                logger.info(f"Wake word detected! (index={keyword_index})")
            
            return keyword_index
        
        except Exception as e:
            logger.error(f"Wake word processing failed: {e}")
            return -1
    
    def start_listening(
        self,
        audio_manager,
        callback: Optional[Callable] = None
    ):
        """
        Start continuous wake word detection
        
        Args:
            audio_manager: AudioManager instance for recording
            callback: Function called when wake word detected
        """
        if self.is_listening:
            logger.warning("Already listening for wake word")
            return
        
        self.is_listening = True
        self.detection_callback = callback
        
        def audio_callback(audio_chunk):
            """Process each audio chunk"""
            if not self.is_listening:
                return
            
            # Process in frame_length chunks
            for i in range(0, len(audio_chunk), self.frame_length):
                if not self.is_listening:
                    break
                
                frame = audio_chunk[i:i + self.frame_length]
                
                if len(frame) == self.frame_length:
                    keyword_index = self.process_frame(frame.flatten())
                    
                    if keyword_index >= 0 and self.detection_callback:
                        self.detection_callback(keyword_index)
        
        # Start recording with callback
        audio_manager.start_recording(callback=audio_callback)
        logger.info("Started listening for wake word")
    
    def stop_listening(self, audio_manager):
        """Stop wake word detection"""
        if not self.is_listening:
            return
        
        self.is_listening = False
        audio_manager.stop_recording()
        logger.info("Stopped listening for wake word")
    
    def cleanup(self):
        """Clean up resources"""
        if hasattr(self, 'porcupine') and self.porcupine:
            self.porcupine.delete()
        
        logger.info("Wake word detector cleaned up")
    
    def __enter__(self):
        """Context manager entry"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.cleanup()


class VoiceActivityDetector:
    """Simple Voice Activity Detector (VAD)"""
    
    def __init__(
        self,
        sample_rate: int = 16000,
        frame_duration_ms: int = 30,
        padding_duration_ms: int = 300,
        energy_threshold: float = 0.01,
    ):
        """
        Initialize VAD
        
        Args:
            sample_rate: Audio sample rate
            frame_duration_ms: Frame duration in milliseconds
            padding_duration_ms: Padding duration for speech segments
            energy_threshold: Energy threshold for voice detection
        """
        try:
            import webrtcvad
            
            self.vad = webrtcvad.Vad(2)  # Aggressiveness: 0-3
            self.sample_rate = sample_rate
            self.frame_duration_ms = frame_duration_ms
            self.padding_duration_ms = padding_duration_ms
            self.energy_threshold = energy_threshold
            
            # Calculate frame size
            self.frame_size = int(
                sample_rate * frame_duration_ms / 1000
            )
            
            logger.info(f"VAD initialized (frame_size={self.frame_size})")
        
        except ImportError:
            raise ImportError("Install webrtcvad: pip install webrtcvad")
    
    def is_speech(self, audio_frame: np.ndarray) -> bool:
        """
        Check if audio frame contains speech
        
        Args:
            audio_frame: Audio frame
        
        Returns:
            True if speech detected, False otherwise
        """
        try:
            # Convert to int16
            if audio_frame.dtype != np.int16:
                audio_frame = (audio_frame * 32767).astype(np.int16)
            
            # Check energy threshold first (fast)
            rms = np.sqrt(np.mean(audio_frame ** 2))
            if rms < self.energy_threshold:
                return False
            
            # Use WebRTC VAD
            audio_bytes = audio_frame.tobytes()
            is_speech = self.vad.is_speech(
                audio_bytes,
                self.sample_rate
            )
            
            return is_speech
        
        except Exception as e:
            logger.error(f"VAD processing failed: {e}")
            return False
    
    def detect_speech_segments(
        self,
        audio_data: np.ndarray
    ) -> list:
        """
        Detect speech segments in audio
        
        Args:
            audio_data: Audio data
        
        Returns:
            List of (start_idx, end_idx) tuples for speech segments
        """
        segments = []
        speech_start = None
        padding_frames = int(
            self.padding_duration_ms / self.frame_duration_ms
        )
        num_padding_frames = 0
        
        for i in range(0, len(audio_data), self.frame_size):
            frame = audio_data[i:i + self.frame_size]
            
            if len(frame) < self.frame_size:
                break
            
            is_speech = self.is_speech(frame)
            
            if is_speech:
                if speech_start is None:
                    speech_start = max(0, i - num_padding_frames * self.frame_size)
                num_padding_frames = 0
            else:
                if speech_start is not None:
                    num_padding_frames += 1
                    
                    if num_padding_frames >= padding_frames:
                        # End of speech segment
                        segments.append((speech_start, i))
                        speech_start = None
                        num_padding_frames = 0
        
        # Add final segment if still in speech
        if speech_start is not None:
            segments.append((speech_start, len(audio_data)))
        
        logger.info(f"Detected {len(segments)} speech segments")
        return segments
