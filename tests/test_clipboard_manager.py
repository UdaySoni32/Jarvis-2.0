"""Tests for Clipboard Manager Plugin"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from src.plugins.clipboard_manager import ClipboardManagerTool, ClipboardManager


class TestClipboardManager:
    """Test clipboard manager"""
    
    def test_initialization(self):
        """Test manager initialization"""
        manager = ClipboardManager()
        assert manager.history == []
        assert manager.max_history == 100
    
    @pytest.mark.asyncio
    async def test_add_to_history(self):
        """Test adding to history"""
        manager = ClipboardManager()
        entry = await manager.add_to_history("test content", "text")
        
        assert entry.content == "test content"
        assert entry.content_type == "text"
        assert len(manager.history) == 1
    
    def test_search_history(self):
        """Test searching history"""
        manager = ClipboardManager()
        manager.history = [
            MagicMock(id="1", content="hello world", content_type="text"),
            MagicMock(id="2", content="goodbye world", content_type="text"),
            MagicMock(id="3", content="test content", content_type="text")
        ]
        
        results = manager.search_history("world")
        assert len(results) == 2
    
    def test_get_history(self):
        """Test getting history"""
        manager = ClipboardManager()
        manager.history = [MagicMock() for _ in range(20)]
        
        history = manager.get_history(limit=10)
        assert len(history) == 10
    
    def test_clear_history(self):
        """Test clearing history"""
        manager = ClipboardManager()
        manager.history = [MagicMock() for _ in range(5)]
        
        count = manager.clear_history()
        assert count == 5
        assert len(manager.history) == 0


class TestClipboardManagerTool:
    """Test clipboard manager tool"""
    
    def test_initialization(self):
        """Test tool initialization"""
        tool = ClipboardManagerTool()
        assert tool.manager is not None
    
    def test_get_parameters(self):
        """Test get parameters"""
        tool = ClipboardManagerTool()
        params = tool.get_parameters()
        assert "action" in params
        assert "content" in params
    
    @pytest.mark.asyncio
    async def test_get_history(self):
        """Test get history action"""
        tool = ClipboardManagerTool()
        await tool.manager.add_to_history("test content", "text")
        
        result = await tool.execute(action="get_history", limit=10)
        assert result["success"] is True
        assert result["count"] == 1
    
    @pytest.mark.asyncio
    async def test_search(self):
        """Test search action"""
        tool = ClipboardManagerTool()
        await tool.manager.add_to_history("hello world", "text")
        await tool.manager.add_to_history("goodbye world", "text")
        
        result = await tool.execute(action="search", query="hello")
        assert result["success"] is True
        assert result["count"] == 1
    
    @pytest.mark.asyncio
    async def test_clear_history(self):
        """Test clear history"""
        tool = ClipboardManagerTool()
        tool.manager.history = [MagicMock() for _ in range(5)]
        
        result = await tool.execute(action="clear_history")
        assert result["success"] is True
        assert result["count"] == 5
    
    @pytest.mark.asyncio
    async def test_get_stats(self):
        """Test get stats"""
        tool = ClipboardManagerTool()
        await tool.manager.add_to_history("test1", "text")
        await tool.manager.add_to_history("test2", "text")
        
        result = await tool.execute(action="get_stats")
        assert result["success"] is True
        assert "stats" in result
        assert result["stats"]["total_entries"] == 2
    
    @pytest.mark.asyncio
    async def test_unknown_action(self):
        """Test unknown action"""
        tool = ClipboardManagerTool()
        result = await tool.execute(action="unknown")
        assert result["success"] is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
