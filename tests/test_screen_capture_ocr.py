"""Tests for Screen Capture and OCR Plugin"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from src.plugins.screen_capture_ocr import (
    ScreenCaptureOCRTool,
    ScreenCaptureManager,
    OCREngine,
    ScreenCapture,
    OCRResult
)


class TestScreenCaptureManager:
    """Test screen capture manager"""
    
    def test_initialization(self):
        """Test manager initialization"""
        manager = ScreenCaptureManager()
        assert manager.output_dir.exists()
        assert manager.capture_history == []


class TestOCREngine:
    """Test OCR engine"""
    
    def test_initialization(self):
        """Test OCR initialization"""
        engine = OCREngine()
        assert engine.default_language == "eng"


class TestScreenCaptureOCRTool:
    """Test screen capture OCR tool"""
    
    def test_initialization(self):
        """Test tool initialization"""
        tool = ScreenCaptureOCRTool()
        assert tool.capture_manager is not None
        assert tool.ocr_engine is not None
    
    def test_get_parameters(self):
        """Test get parameters"""
        tool = ScreenCaptureOCRTool()
        params = tool.get_parameters()
        assert "action" in params
        assert "image_path" in params
        assert "language" in params
    
    @pytest.mark.asyncio
    async def test_get_history(self):
        """Test getting history"""
        tool = ScreenCaptureOCRTool()
        
        result = await tool.execute(action="get_history")
        assert result["success"] is True
        assert result["count"] == 0
    
    @pytest.mark.asyncio
    async def test_clear_history(self):
        """Test clearing history"""
        tool = ScreenCaptureOCRTool()
        
        # Add fake capture
        fake_capture = ScreenCapture(
            filename="test.png",
            path="/tmp/test.png",
            timestamp="20240101_120000"
        )
        tool.capture_manager.capture_history.append(fake_capture)
        
        result = await tool.execute(action="clear_history")
        assert result["success"] is True
        assert result["cleared"] == 1
        assert len(tool.capture_manager.capture_history) == 0
    
    @pytest.mark.asyncio
    async def test_unknown_action(self):
        """Test unknown action"""
        tool = ScreenCaptureOCRTool()
        result = await tool.execute(action="unknown")
        assert result["success"] is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
