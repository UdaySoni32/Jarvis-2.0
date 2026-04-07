"""
Tests for Audio Manager
"""

import pytest
import numpy as np
from unittest.mock import Mock, patch, MagicMock
from src.voice.audio_manager import AudioManager, quick_record


class TestAudioManager:
    """Test cases for AudioManager"""
    
    @patch('src.voice.audio_manager.AUDIO_AVAILABLE', True)
    @patch('src.voice.audio_manager.sd')
    def test_init(self, mock_sd):
        """Test AudioManager initialization"""
        manager = AudioManager(sample_rate=16000, channels=1)
        
        assert manager.sample_rate == 16000
        assert manager.channels == 1
        assert manager.is_recording == False
    
    @patch('src.voice.audio_manager.AUDIO_AVAILABLE', True)
    @patch('src.voice.audio_manager.sd')
    def test_list_devices(self, mock_sd):
        """Test listing audio devices"""
        mock_sd.query_devices.return_value = [
            {"name": "Mic 1", "max_input_channels": 2, "default_samplerate": 44100},
            {"name": "Mic 2", "max_input_channels": 1, "default_samplerate": 48000},
        ]
        
        devices = AudioManager.list_devices()
        
        assert len(devices) == 2
        assert devices[0]["name"] == "Mic 1"
    
    @patch('src.voice.audio_manager.AUDIO_AVAILABLE', True)
    @patch('src.voice.audio_manager.sd')
    def test_record_audio(self, mock_sd):
        """Test audio recording"""
        mock_audio = np.random.rand(16000, 1)
        mock_sd.rec.return_value = mock_audio
        
        manager = AudioManager()
        audio = manager.record_audio(duration=1.0)
        
        mock_sd.rec.assert_called_once()
        mock_sd.wait.assert_called_once()
        assert audio is not None
    
    @patch('src.voice.audio_manager.AUDIO_AVAILABLE', True)
    @patch('src.voice.audio_manager.sd')
    def test_play_audio(self, mock_sd):
        """Test audio playback"""
        manager = AudioManager()
        audio_data = np.random.rand(16000)
        
        manager.play_audio(audio_data, wait=True)
        
        mock_sd.play.assert_called_once()
        mock_sd.wait.assert_called_once()
    
    @patch('src.voice.audio_manager.AUDIO_AVAILABLE', True)
    @patch('src.voice.audio_manager.sf')
    @patch('src.voice.audio_manager.sd')
    def test_save_audio(self, mock_sd, mock_sf):
        """Test saving audio to file"""
        manager = AudioManager()
        audio_data = np.random.rand(16000)
        
        manager.save_audio(audio_data, "test.wav")
        
        mock_sf.write.assert_called_once_with("test.wav", audio_data, 16000)
    
    @patch('src.voice.audio_manager.AUDIO_AVAILABLE', True)
    @patch('src.voice.audio_manager.sf')
    @patch('src.voice.audio_manager.sd')
    def test_load_audio(self, mock_sd, mock_sf):
        """Test loading audio from file"""
        mock_audio = np.random.rand(16000)
        mock_sf.read.return_value = (mock_audio, 16000)
        
        manager = AudioManager()
        audio = manager.load_audio("test.wav")
        
        mock_sf.read.assert_called_once_with("test.wav")
        assert audio is not None
    
    @patch('src.voice.audio_manager.AUDIO_AVAILABLE', True)
    @patch('src.voice.audio_manager.sd')
    def test_normalize_audio(self, mock_sd):
        """Test audio normalization"""
        manager = AudioManager()
        audio_data = np.array([0.1, 0.5, 1.0, -0.5])
        
        normalized = manager.normalize_audio(audio_data.copy())
        
        assert np.max(np.abs(normalized)) <= 1.0
    
    @patch('src.voice.audio_manager.AUDIO_AVAILABLE', True)
    @patch('src.voice.audio_manager.sd')
    def test_detect_silence(self, mock_sd):
        """Test silence detection"""
        manager = AudioManager()
        
        # Silent audio (low amplitude)
        silent_audio = np.random.rand(1000) * 0.001
        assert manager.detect_silence(silent_audio, threshold=0.01)
        
        # Loud audio
        loud_audio = np.random.rand(1000) * 0.5
        assert not manager.detect_silence(loud_audio, threshold=0.01)
    
    @patch('src.voice.audio_manager.AUDIO_AVAILABLE', True)
    @patch('src.voice.audio_manager.sd')
    def test_context_manager(self, mock_sd):
        """Test AudioManager as context manager"""
        with AudioManager() as manager:
            assert manager is not None
        
        # Should be cleaned up after exiting context


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
