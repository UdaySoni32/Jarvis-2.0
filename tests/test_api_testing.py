"""Tests for API Testing Plugin"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from src.plugins.api_testing import APITestingTool, APITester, APIRequest, APIResponse


class TestAPITester:
    """Test API tester"""
    
    def test_initialization(self):
        """Test tester initialization"""
        tester = APITester()
        assert tester.session is None
        assert tester.test_results == []
    


class TestAPITestingTool:
    """Test API testing tool"""
    
    def test_initialization(self):
        """Test tool initialization"""
        tool = APITestingTool()
        assert tool.tester is not None
    
    def test_get_parameters(self):
        """Test get parameters"""
        tool = APITestingTool()
        params = tool.get_parameters()
        assert "action" in params
        assert "url" in params
    
    @pytest.mark.asyncio
    async def test_get_results(self):
        """Test getting results"""
        tool = APITestingTool()
        tool.tester.test_results = [{"test": "data"}]
        
        result = await tool.execute(action="get_results")
        assert result["success"] is True
        assert result["count"] == 1
    
    @pytest.mark.asyncio
    async def test_clear_results(self):
        """Test clearing results"""
        tool = APITestingTool()
        tool.tester.test_results = [{"test": "data"}, {"test": "data2"}]
        
        result = await tool.execute(action="clear_results")
        assert result["success"] is True
        assert result["count"] == 2
        assert len(tool.tester.test_results) == 0
    
    def test_assert_status(self):
        """Test status assertion"""
        tool = APITestingTool()
        response = {"status_code": 200}
        
        result = tool._assert_status(response, expected_status=200)
        assert result["passed"] is True
        assert result["assertion"] == "status_code"
    
    def test_assert_time(self):
        """Test time assertion"""
        tool = APITestingTool()
        response = {"response_time": 0.5}
        
        result = tool._assert_time(response, max_time=1.0)
        assert result["passed"] is True
    
    def test_assert_contains(self):
        """Test contains assertion"""
        tool = APITestingTool()
        response = {"body": {"status": "ok", "data": "test"}}
        
        result = tool._assert_contains(response, field="status", value="ok")
        assert result["passed"] is True
    
    @pytest.mark.asyncio
    async def test_unknown_action(self):
        """Test unknown action"""
        tool = APITestingTool()
        result = await tool.execute(action="unknown")
        assert result["success"] is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
