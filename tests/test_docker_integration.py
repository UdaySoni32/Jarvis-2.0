"""Tests for Docker Integration Plugin"""

import pytest
from unittest.mock import AsyncMock, patch
from src.plugins.docker_integration import DockerIntegrationTool


class TestDockerIntegrationTool:
    """Test Docker integration tool"""
    
    def test_initialization(self):
        """Test tool initialization"""
        tool = DockerIntegrationTool()
        assert tool is not None
        assert tool.executor is not None
    
    def test_get_parameters(self):
        """Test get parameters"""
        tool = DockerIntegrationTool()
        params = tool.get_parameters()
        assert "action" in params
        assert params["action"].required is True
    
    @pytest.mark.asyncio
    async def test_list_containers(self):
        """Test listing containers"""
        tool = DockerIntegrationTool()
        with patch.object(tool.executor, 'run', new_callable=AsyncMock) as mock_run:
            mock_run.return_value = {
                "success": True,
                "stdout": "container1\ncontainer2"
            }
            
            result = await tool.execute(action="list_containers")
            assert result["success"] is True
            assert "container1" in result["containers"]
    
    @pytest.mark.asyncio
    async def test_pull_image(self):
        """Test pulling image"""
        tool = DockerIntegrationTool()
        with patch.object(tool.executor, 'run', new_callable=AsyncMock) as mock_run:
            mock_run.return_value = {"success": True, "stdout": ""}
            
            result = await tool.execute(
                action="pull_image",
                image="nginx:latest"
            )
            assert result["success"] is True
    
    @pytest.mark.asyncio
    async def test_get_docker_info(self):
        """Test getting Docker info"""
        tool = DockerIntegrationTool()
        with patch.object(tool.executor, 'run', new_callable=AsyncMock) as mock_run:
            mock_run.return_value = {
                "success": True,
                "stdout": "Containers: 5\nImages: 20"
            }
            
            result = await tool.execute(action="get_docker_info")
            assert result["success"] is True
    
    @pytest.mark.asyncio
    async def test_unknown_action(self):
        """Test unknown action"""
        tool = DockerIntegrationTool()
        result = await tool.execute(action="unknown")
        assert result["success"] is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
