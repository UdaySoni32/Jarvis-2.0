"""
Audio Input/Output Manager for JARVIS Voice Interface

Handles microphone input, audio recording, playback, and preprocessing.
"""

import logging
import queue
import threading
from typing import Optional, Callable, List
import numpy as np

try:
    import sounddevice as sd
    import soundfile as sf
    AUDIO_AVAILABLE = True
except ImportError:
    AUDIO_AVAILABLE = False
    sd = None
    sf = None

logger = logging.getLogger(__name__)


class AudioManager:
    """Manages audio input/output for voice interface"""

    def __init__(
        self,
        sample_rate: int = 16000,
        channels: int = 1,
        dtype: str = "int16",
        block_size: int = 1024,
        device: Optional[int] = None,
    ):
        """
        Initialize audio manager
        
        Args:
            sample_rate: Audio sample rate in Hz (default: 16000 for speech)
            channels: Number of audio channels (1=mono, 2=stereo)
            dtype: Audio data type
            block_size: Number of frames per buffer
            device: Audio device index (None = default device)
        """
        if not AUDIO_AVAILABLE:
            raise ImportError(
                "Audio dependencies not installed. "
                "Run: pip install sounddevice soundfile"
            )
        
        self.sample_rate = sample_rate
        self.channels = channels
        self.dtype = dtype
        self.block_size = block_size
        self.device = device
        
        self.is_recording = False
        self.audio_queue: queue.Queue = queue.Queue()
        self.recording_thread: Optional[threading.Thread] = None
        self.stream: Optional[sd.InputStream] = None
        
        logger.info(
            f"AudioManager initialized: {sample_rate}Hz, "
            f"{channels} channel(s), device={device}"
        )
    
    @staticmethod
    def list_devices() -> List[dict]:
        """List all available audio devices"""
        if not AUDIO_AVAILABLE:
            return []
        
        devices = sd.query_devices()
        device_list = []
        
        for idx, device in enumerate(devices):
            device_list.append({
                "index": idx,
                "name": device["name"],
                "channels": device["max_input_channels"],
                "sample_rate": device["default_samplerate"],
            })
        
        return device_list
    
    def get_default_device(self) -> dict:
        """Get default input device info"""
        if not AUDIO_AVAILABLE:
            return {}
        
        device = sd.query_devices(kind="input")
        return {
            "name": device["name"],
            "channels": device["max_input_channels"],
            "sample_rate": device["default_samplerate"],
        }
    
    def start_recording(self, callback: Optional[Callable] = None):
        """
        Start recording audio from microphone
        
        Args:
            callback: Optional callback function(audio_chunk) called for each chunk
        """
        if self.is_recording:
            logger.warning("Already recording")
            return
        
        self.is_recording = True
        self.audio_queue = queue.Queue()
        
        def audio_callback(indata, frames, time, status):
            """Called for each audio block"""
            if status:
                logger.warning(f"Audio callback status: {status}")
            
            # Convert to numpy array and add to queue
            audio_data = indata.copy()
            self.audio_queue.put(audio_data)
            
            if callback:
                callback(audio_data)
        
        try:
            self.stream = sd.InputStream(
                samplerate=self.sample_rate,
                channels=self.channels,
                dtype=self.dtype,
                blocksize=self.block_size,
                device=self.device,
                callback=audio_callback,
            )
            self.stream.start()
            logger.info("Recording started")
        
        except Exception as e:
            logger.error(f"Failed to start recording: {e}")
            self.is_recording = False
            raise
    
    def stop_recording(self) -> Optional[np.ndarray]:
        """
        Stop recording and return all recorded audio
        
        Returns:
            Numpy array of recorded audio data, or None if no data
        """
        if not self.is_recording:
            logger.warning("Not currently recording")
            return None
        
        self.is_recording = False
        
        if self.stream:
            self.stream.stop()
            self.stream.close()
            self.stream = None
        
        # Collect all audio chunks
        audio_chunks = []
        while not self.audio_queue.empty():
            try:
                chunk = self.audio_queue.get_nowait()
                audio_chunks.append(chunk)
            except queue.Empty:
                break
        
        logger.info(f"Recording stopped, collected {len(audio_chunks)} chunks")
        
        if audio_chunks:
            # Concatenate all chunks
            return np.concatenate(audio_chunks, axis=0)
        
        return None
    
    def record_audio(self, duration: float) -> np.ndarray:
        """
        Record audio for a specified duration
        
        Args:
            duration: Recording duration in seconds
        
        Returns:
            Numpy array of recorded audio
        """
        logger.info(f"Recording for {duration} seconds...")
        
        frames = int(self.sample_rate * duration)
        audio = sd.rec(
            frames,
            samplerate=self.sample_rate,
            channels=self.channels,
            dtype=self.dtype,
            device=self.device,
        )
        sd.wait()  # Wait for recording to complete
        
        logger.info("Recording complete")
        return audio
    
    def play_audio(self, audio_data: np.ndarray, wait: bool = True):
        """
        Play audio through speakers
        
        Args:
            audio_data: Numpy array of audio data
            wait: If True, wait for playback to complete
        """
        try:
            sd.play(audio_data, self.sample_rate)
            if wait:
                sd.wait()
            logger.debug("Audio playback started")
        
        except Exception as e:
            logger.error(f"Failed to play audio: {e}")
            raise
    
    def save_audio(self, audio_data: np.ndarray, filename: str):
        """
        Save audio to file
        
        Args:
            audio_data: Numpy array of audio data
            filename: Output file path (supports .wav, .flac, .ogg, etc.)
        """
        try:
            sf.write(filename, audio_data, self.sample_rate)
            logger.info(f"Audio saved to {filename}")
        
        except Exception as e:
            logger.error(f"Failed to save audio: {e}")
            raise
    
    def load_audio(self, filename: str) -> np.ndarray:
        """
        Load audio from file
        
        Args:
            filename: Audio file path
        
        Returns:
            Numpy array of audio data
        """
        try:
            audio_data, sample_rate = sf.read(filename)
            
            # Resample if needed (basic implementation)
            if sample_rate != self.sample_rate:
                logger.warning(
                    f"Audio file sample rate ({sample_rate}Hz) differs from "
                    f"manager sample rate ({self.sample_rate}Hz)"
                )
            
            logger.info(f"Audio loaded from {filename}")
            return audio_data
        
        except Exception as e:
            logger.error(f"Failed to load audio: {e}")
            raise
    
    def apply_noise_reduction(self, audio_data: np.ndarray) -> np.ndarray:
        """
        Apply basic noise reduction to audio
        
        Args:
            audio_data: Input audio data
        
        Returns:
            Processed audio data
        """
        # Simple noise gate implementation
        # For production, use noisereduce library or more advanced methods
        
        threshold = np.percentile(np.abs(audio_data), 10)  # 10th percentile
        audio_data[np.abs(audio_data) < threshold] = 0
        
        logger.debug("Applied basic noise reduction")
        return audio_data
    
    def normalize_audio(self, audio_data: np.ndarray) -> np.ndarray:
        """
        Normalize audio to -1 to 1 range
        
        Args:
            audio_data: Input audio data
        
        Returns:
            Normalized audio data
        """
        max_val = np.max(np.abs(audio_data))
        if max_val > 0:
            audio_data = audio_data / max_val
        
        logger.debug("Audio normalized")
        return audio_data
    
    def detect_silence(
        self,
        audio_data: np.ndarray,
        threshold: float = 0.01,
        min_duration: float = 0.5
    ) -> bool:
        """
        Detect if audio contains significant silence
        
        Args:
            audio_data: Audio data to check
            threshold: Amplitude threshold for silence
            min_duration: Minimum duration of silence in seconds
        
        Returns:
            True if silence detected, False otherwise
        """
        # Calculate RMS energy
        rms = np.sqrt(np.mean(audio_data ** 2))
        
        # Check if below threshold
        is_silent = rms < threshold
        
        logger.debug(f"Silence detection: RMS={rms:.4f}, silent={is_silent}")
        return is_silent
    
    def cleanup(self):
        """Clean up resources"""
        if self.is_recording:
            self.stop_recording()
        
        if self.stream:
            self.stream.close()
        
        logger.info("AudioManager cleaned up")
    
    def __enter__(self):
        """Context manager entry"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.cleanup()


# Convenience function for quick audio recording
def quick_record(duration: float = 3.0, sample_rate: int = 16000) -> np.ndarray:
    """
    Quick audio recording utility
    
    Args:
        duration: Recording duration in seconds
        sample_rate: Audio sample rate
    
    Returns:
        Recorded audio as numpy array
    """
    with AudioManager(sample_rate=sample_rate) as manager:
        return manager.record_audio(duration)
