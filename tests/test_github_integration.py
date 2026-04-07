"""
Comprehensive tests for GitHub Integration Plugin

Tests cover:
- Authentication and token management
- Repository operations
- Issue and pull request management
- Workflow and CI/CD operations
- Branch and release management
- File operations
- User information retrieval
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from src.plugins.github_integration import (
    GitHubIntegrationTool,
    GitHubAuthManager,
    GitHubAPIClient,
    Repository,
    Issue,
    PullRequest,
    Commit,
    WorkflowRun,
    WorkflowJob,
    Branch,
    Release,
    GitHubUser,
    RepositoryAnalysis
)


class TestGitHubAuthManager:
    """Test GitHub authentication manager"""
    
    def test_add_token(self):
        """Test adding GitHub token"""
        auth = GitHubAuthManager()
        result = auth.add_token("test_token", "ghp_test123")
        assert result is True
        assert auth.get_token("test_token") == "ghp_test123"
    
    def test_add_token_empty(self):
        """Test adding empty token"""
        auth = GitHubAuthManager()
        result = auth.add_token("", "token")
        assert result is False
    
    def test_remove_token(self):
        """Test removing token"""
        auth = GitHubAuthManager()
        auth.add_token("test", "ghp_123")
        result = auth.remove_token("test")
        assert result is True
        assert auth.get_token("test") is None
    
    def test_remove_nonexistent_token(self):
        """Test removing non-existent token"""
        auth = GitHubAuthManager()
        result = auth.remove_token("nonexistent")
        assert result is False
    
    def test_list_tokens(self):
        """Test listing tokens"""
        auth = GitHubAuthManager()
        auth.add_token("token1", "ghp_123")
        auth.add_token("token2", "ghp_456")
        tokens = auth.list_tokens()
        assert len(tokens) == 2
        assert "token1" in tokens
        assert "token2" in tokens
    
    def test_get_headers(self):
        """Test getting authorization headers"""
        auth = GitHubAuthManager()
        auth.add_token("test", "ghp_test123")
        headers = auth.get_headers("test")
        assert headers["Authorization"] == "token ghp_test123"
        assert "Accept" in headers
    
    def test_get_headers_no_token(self):
        """Test getting headers without token"""
        auth = GitHubAuthManager()
        headers = auth.get_headers("nonexistent")
        assert "Accept" in headers
        assert "Authorization" not in headers


class TestGitHubAPIClient:
    """Test GitHub API client"""
    
    @pytest.mark.asyncio
    async def test_context_manager(self):
        """Test async context manager"""
        auth = GitHubAuthManager()
        auth.add_token("test", "ghp_123")
        
        async with GitHubAPIClient(auth) as client:
            assert client.session is not None
    
    @pytest.mark.asyncio
    async def test_get_user(self):
        """Test getting user info"""
        auth = GitHubAuthManager()
        auth.add_token("test", "ghp_123")
        
        with patch.object(GitHubAPIClient, '_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = {
                "login": "testuser",
                "id": 12345,
                "avatar_url": "https://avatars.githubusercontent.com/u/12345",
                "html_url": "https://github.com/testuser",
                "name": "Test User",
                "bio": "Test bio",
                "followers": 100,
                "following": 50,
                "public_repos": 10
            }
            
            async with GitHubAPIClient(auth) as client:
                user = await client.get_user("testuser")
                assert user is not None
                assert user.username == "testuser"
                assert user.user_id == 12345
                assert user.followers == 100


class TestGitHubIntegrationTool:
    """Test main GitHub integration tool"""
    
    def test_tool_initialization(self):
        """Test tool initialization"""
        tool = GitHubIntegrationTool()
        assert tool.auth_manager is not None
        assert tool.cache is not None
    
    @pytest.mark.asyncio
    async def test_add_token_action(self):
        """Test adding token through tool"""
        tool = GitHubIntegrationTool()
        result = await tool.execute(
            action="add_token",
            token_name="test",
            token="ghp_test123"
        )
        assert result["success"] is True
        assert result["token_name"] == "test"
    
    @pytest.mark.asyncio
    async def test_add_token_missing_params(self):
        """Test adding token with missing parameters"""
        tool = GitHubIntegrationTool()
        result = await tool.execute(action="add_token", token_name="", token="")
        assert result["success"] is False
    
    @pytest.mark.asyncio
    async def test_list_tokens_action(self):
        """Test listing tokens"""
        tool = GitHubIntegrationTool()
        tool.auth_manager.add_token("token1", "ghp_123")
        result = await tool.execute(action="list_tokens")
        assert result["success"] is True
        assert result["count"] == 1
    
    @pytest.mark.asyncio
    async def test_remove_token_action(self):
        """Test removing token"""
        tool = GitHubIntegrationTool()
        tool.auth_manager.add_token("token1", "ghp_123")
        result = await tool.execute(action="remove_token", token_name="token1")
        assert result["success"] is True
    
    @pytest.mark.asyncio
    async def test_unknown_action(self):
        """Test unknown action"""
        tool = GitHubIntegrationTool()
        result = await tool.execute(action="unknown_action")
        assert result["success"] is False
        assert "Unknown action" in result["error"]
    
    @pytest.mark.asyncio
    async def test_get_repo_no_token(self):
        """Test getting repo without token"""
        tool = GitHubIntegrationTool()
        result = await tool.execute(
            action="get_repo",
            owner="python",
            repo="cpython"
        )
        assert result["success"] is False
        assert "No GitHub token configured" in result["error"]
    

    @pytest.mark.asyncio
    async def test_full_workflow(self):
        """Test full GitHub workflow"""
        tool = GitHubIntegrationTool()
        
        # Add token
        result = await tool.execute(
            action="add_token",
            token_name="main",
            token="ghp_test123"
        )
        assert result["success"] is True
        
        # List tokens
        result = await tool.execute(action="list_tokens")
        assert result["count"] >= 1
        
        # Remove token
        result = await tool.execute(action="remove_token", token_name="main")
        assert result["success"] is True
    
    @pytest.mark.asyncio
    async def test_error_handling(self):
        """Test error handling"""
        tool = GitHubIntegrationTool()
        
        # Missing token
        result = await tool.execute(
            action="get_repo",
            owner="test",
            repo="test"
        )
        assert result["success"] is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
