"""
GitHub Integration Plugin for JARVIS 2.0

Comprehensive GitHub integration supporting:
- Repository management and operations
- Issue tracking and management
- Pull request workflow automation
- Workflow orchestration and CI/CD
- Code analysis and review assistance
- Collaboration and team features
"""

import asyncio
import json
from typing import Any, Dict, List, Optional, AsyncIterator, Union
from datetime import datetime, timedelta
from dataclasses import dataclass, field, asdict
from enum import Enum
import base64
import re
from functools import lru_cache
import aiohttp
from abc import ABC, abstractmethod


class PRState(Enum):
    """Pull request states"""
    OPEN = "open"
    CLOSED = "closed"
    MERGED = "merged"
    DRAFT = "draft"


class IssueState(Enum):
    """Issue states"""
    OPEN = "open"
    CLOSED = "closed"


class WorkflowConclusion(Enum):
    """Workflow run conclusions"""
    SUCCESS = "success"
    FAILURE = "failure"
    NEUTRAL = "neutral"
    CANCELLED = "cancelled"
    SKIPPED = "skipped"
    STALE = "stale"
    TIMED_OUT = "timed_out"


class WorkflowStatus(Enum):
    """Workflow run status"""
    QUEUED = "queued"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    REQUESTED = "requested"
    WAITING = "waiting"


@dataclass
class GitHubUser:
    """GitHub user information"""
    username: str
    user_id: int
    avatar_url: str
    profile_url: str
    name: Optional[str] = None
    bio: Optional[str] = None
    location: Optional[str] = None
    followers: int = 0
    following: int = 0
    public_repos: int = 0
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


@dataclass
class Repository:
    """GitHub repository information"""
    name: str
    owner: str
    url: str
    description: Optional[str] = None
    homepage: Optional[str] = None
    language: Optional[str] = None
    repo_id: int = 0
    private: bool = False
    fork: bool = False
    stars: int = 0
    watchers: int = 0
    forks: int = 0
    issues_count: int = 0
    open_issues: int = 0
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    pushed_at: Optional[str] = None
    default_branch: str = "main"
    topics: List[str] = field(default_factory=list)
    has_wiki: bool = False
    has_discussions: bool = False
    has_projects: bool = False


@dataclass
class Issue:
    """GitHub issue information"""
    number: int
    title: str
    description: str
    state: str
    issue_id: int = 0
    url: str = ""
    author: Optional[str] = None
    assignees: List[str] = field(default_factory=list)
    labels: List[str] = field(default_factory=list)
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    closed_at: Optional[str] = None
    comments_count: int = 0
    reactions: Dict[str, int] = field(default_factory=dict)
    is_pull_request: bool = False
    milestone: Optional[str] = None
    priority: str = "normal"  # normal, high, critical


@dataclass
class PullRequest:
    """GitHub pull request information"""
    number: int
    title: str
    description: str
    state: str
    pr_id: int = 0
    url: str = ""
    author: Optional[str] = None
    reviewers: List[str] = field(default_factory=list)
    assignees: List[str] = field(default_factory=list)
    labels: List[str] = field(default_factory=list)
    source_branch: str = ""
    target_branch: str = "main"
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    closed_at: Optional[str] = None
    merged_at: Optional[str] = None
    comments_count: int = 0
    review_comments_count: int = 0
    commits_count: int = 0
    additions: int = 0
    deletions: int = 0
    changed_files: int = 0
    mergeable: bool = True
    merged: bool = False
    draft: bool = False
    reactions: Dict[str, int] = field(default_factory=dict)


@dataclass
class Commit:
    """GitHub commit information"""
    sha: str
    message: str
    author: str
    timestamp: str
    url: str = ""
    tree_sha: str = ""
    parent_shas: List[str] = field(default_factory=list)
    additions: int = 0
    deletions: int = 0
    files_changed: int = 0
    comments_count: int = 0


@dataclass
class WorkflowRun:
    """GitHub Actions workflow run"""
    run_id: int
    run_number: int
    name: str
    workflow_file: str
    status: str
    conclusion: Optional[str]
    url: str = ""
    trigger_event: str = ""
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    run_started_at: Optional[str] = None
    duration_seconds: int = 0
    actor: Optional[str] = None
    branch: str = ""
    commit_sha: str = ""
    jobs: List[Dict[str, Any]] = field(default_factory=list)
    artifacts: List[Dict[str, Any]] = field(default_factory=list)
    logs_url: Optional[str] = None


@dataclass
class WorkflowJob:
    """GitHub Actions workflow job"""
    job_id: int
    name: str
    status: str
    conclusion: Optional[str]
    url: str = ""
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    duration_seconds: int = 0
    steps: List[Dict[str, Any]] = field(default_factory=list)
    runner_name: Optional[str] = None
    labels: List[str] = field(default_factory=list)


@dataclass
class CodeReview:
    """Code review analysis"""
    file_path: str
    comments: List[Dict[str, Any]] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)
    issues_found: List[Dict[str, Any]] = field(default_factory=list)
    overall_score: float = 0.0
    complexity_score: float = 0.0
    test_coverage: float = 0.0
    security_issues: List[str] = field(default_factory=list)


@dataclass
class PullRequestReview:
    """Pull request review"""
    review_id: int
    reviewer: str
    state: str  # APPROVED, CHANGES_REQUESTED, COMMENTED, DISMISSED, PENDING
    body: str = ""
    submitted_at: Optional[str] = None
    comments_count: int = 0
    commit_id: Optional[str] = None


@dataclass
class Branch:
    """Repository branch"""
    name: str
    commit_sha: str
    url: str = ""
    protected: bool = False
    latest_commit_author: Optional[str] = None
    latest_commit_date: Optional[str] = None


@dataclass
class Release:
    """GitHub release"""
    tag_name: str
    release_name: str
    draft: bool
    prerelease: bool
    body: str = ""
    url: str = ""
    author: Optional[str] = None
    created_at: Optional[str] = None
    published_at: Optional[str] = None
    assets: List[Dict[str, Any]] = field(default_factory=list)
    download_count: int = 0


@dataclass
class ProjectCard:
    """GitHub project card"""
    card_id: int
    note: Optional[str]
    content_url: str = ""
    content_id: int = 0
    content_type: str = "Issue"  # Issue or PullRequest
    archived: bool = False
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


@dataclass
class ProjectColumn:
    """GitHub project column"""
    column_id: int
    name: str
    url: str = ""
    cards_url: str = ""
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    cards: List[ProjectCard] = field(default_factory=list)


@dataclass
class Discussion:
    """GitHub discussion"""
    discussion_id: int
    title: str
    body: str
    category: str
    state: str  # OPEN or CLOSED
    author: str
    url: str = ""
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    answer_chosen_at: Optional[str] = None
    comments_count: int = 0
    upvote_count: int = 0


@dataclass
class RepositoryAnalysis:
    """Repository code analysis"""
    repo_name: str
    total_commits: int = 0
    total_branches: int = 0
    total_contributors: int = 0
    total_releases: int = 0
    total_issues: int = 0
    total_prs: int = 0
    open_issues: int = 0
    open_prs: int = 0
    languages: Dict[str, float] = field(default_factory=dict)
    topics: List[str] = field(default_factory=list)
    readme_exists: bool = False
    license: Optional[str] = None
    last_commit_date: Optional[str] = None
    last_release_date: Optional[str] = None
    maintainers: List[str] = field(default_factory=list)
    contributors: List[Dict[str, Any]] = field(default_factory=list)
    code_frequency: Dict[str, Dict[str, int]] = field(default_factory=dict)
    network_stats: Dict[str, Any] = field(default_factory=dict)


class GitHubAuthManager:
    """Manages GitHub API authentication"""
    
    def __init__(self):
        self.tokens: Dict[str, str] = {}
        self.authenticated_users: Dict[str, GitHubUser] = {}
    
    def add_token(self, token_name: str, token: str) -> bool:
        """Add GitHub API token"""
        if not token or not token_name:
            return False
        self.tokens[token_name] = token
        return True
    
    def get_token(self, token_name: str = "default") -> Optional[str]:
        """Get GitHub API token"""
        return self.tokens.get(token_name)
    
    def remove_token(self, token_name: str) -> bool:
        """Remove GitHub API token"""
        if token_name in self.tokens:
            del self.tokens[token_name]
            return True
        return False
    
    def list_tokens(self) -> List[str]:
        """List configured token names"""
        return list(self.tokens.keys())
    
    def get_headers(self, token_name: str = "default") -> Dict[str, str]:
        """Get authorization headers"""
        token = self.get_token(token_name)
        if not token:
            return {"Accept": "application/vnd.github.v3+json"}
        return {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3+json"
        }


class GitHubAPIClient:
    """GitHub REST API client"""
    
    BASE_URL = "https://api.github.com"
    
    def __init__(self, auth_manager: GitHubAuthManager):
        self.auth_manager = auth_manager
        self.session: Optional[aiohttp.ClientSession] = None
        self.rate_limit_remaining = 60
        self.rate_limit_reset = 0
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def _request(
        self,
        method: str,
        endpoint: str,
        token_name: str = "default",
        params: Optional[Dict[str, Any]] = None,
        json: Optional[Dict[str, Any]] = None,
        data: Optional[str] = None
    ) -> Dict[str, Any]:
        """Make API request"""
        if not self.session:
            self.session = aiohttp.ClientSession()
        
        url = f"{self.BASE_URL}{endpoint}"
        headers = self.auth_manager.get_headers(token_name)
        
        async with self.session.request(
            method, url, params=params, json=json, data=data, headers=headers
        ) as response:
            # Update rate limit info
            if "X-RateLimit-Remaining" in response.headers:
                self.rate_limit_remaining = int(response.headers["X-RateLimit-Remaining"])
                self.rate_limit_reset = int(response.headers["X-RateLimit-Reset"])
            
            if response.status == 200 or response.status == 201:
                return await response.json()
            elif response.status == 204:
                return {"success": True}
            elif response.status == 404:
                return {"error": "Not found", "status": 404}
            elif response.status == 401:
                return {"error": "Unauthorized - invalid token", "status": 401}
            elif response.status == 422:
                error_data = await response.json()
                return {"error": "Validation failed", "details": error_data, "status": 422}
            else:
                error_text = await response.text()
                return {"error": error_text, "status": response.status}
    
    async def get_user(self, username: str, token_name: str = "default") -> Optional[GitHubUser]:
        """Get user information"""
        result = await self._request("GET", f"/users/{username}", token_name)
        if "error" in result:
            return None
        
        return GitHubUser(
            username=result.get("login", username),
            user_id=result.get("id", 0),
            avatar_url=result.get("avatar_url", ""),
            profile_url=result.get("html_url", ""),
            name=result.get("name"),
            bio=result.get("bio"),
            location=result.get("location"),
            followers=result.get("followers", 0),
            following=result.get("following", 0),
            public_repos=result.get("public_repos", 0),
            created_at=result.get("created_at"),
            updated_at=result.get("updated_at")
        )
    
    async def get_authenticated_user(self, token_name: str = "default") -> Optional[GitHubUser]:
        """Get authenticated user information"""
        result = await self._request("GET", "/user", token_name)
        if "error" in result:
            return None
        
        return GitHubUser(
            username=result.get("login", ""),
            user_id=result.get("id", 0),
            avatar_url=result.get("avatar_url", ""),
            profile_url=result.get("html_url", ""),
            name=result.get("name"),
            bio=result.get("bio"),
            location=result.get("location"),
            followers=result.get("followers", 0),
            following=result.get("following", 0),
            public_repos=result.get("public_repos", 0),
            created_at=result.get("created_at"),
            updated_at=result.get("updated_at")
        )
    
    async def get_repository(
        self, owner: str, repo: str, token_name: str = "default"
    ) -> Optional[Repository]:
        """Get repository information"""
        result = await self._request("GET", f"/repos/{owner}/{repo}", token_name)
        if "error" in result:
            return None
        
        return Repository(
            name=result.get("name", repo),
            owner=result.get("owner", {}).get("login", owner),
            url=result.get("html_url", ""),
            description=result.get("description"),
            homepage=result.get("homepage"),
            language=result.get("language"),
            repo_id=result.get("id", 0),
            private=result.get("private", False),
            fork=result.get("fork", False),
            stars=result.get("stargazers_count", 0),
            watchers=result.get("watchers_count", 0),
            forks=result.get("forks_count", 0),
            issues_count=result.get("open_issues_count", 0),
            open_issues=result.get("open_issues_count", 0),
            created_at=result.get("created_at"),
            updated_at=result.get("updated_at"),
            pushed_at=result.get("pushed_at"),
            default_branch=result.get("default_branch", "main"),
            topics=result.get("topics", []),
            has_wiki=result.get("has_wiki", False),
            has_discussions=result.get("has_discussions", False),
            has_projects=result.get("has_projects", False)
        )
    
    async def list_repositories(
        self,
        username: str,
        token_name: str = "default",
        per_page: int = 30,
        page: int = 1
    ) -> List[Repository]:
        """List user repositories"""
        result = await self._request(
            "GET",
            f"/users/{username}/repos",
            token_name,
            params={"per_page": per_page, "page": page, "sort": "updated"}
        )
        
        if "error" in result or not isinstance(result, list):
            return []
        
        repositories = []
        for repo_data in result:
            repositories.append(Repository(
                name=repo_data.get("name", ""),
                owner=repo_data.get("owner", {}).get("login", username),
                url=repo_data.get("html_url", ""),
                description=repo_data.get("description"),
                homepage=repo_data.get("homepage"),
                language=repo_data.get("language"),
                repo_id=repo_data.get("id", 0),
                private=repo_data.get("private", False),
                fork=repo_data.get("fork", False),
                stars=repo_data.get("stargazers_count", 0),
                watchers=repo_data.get("watchers_count", 0),
                forks=repo_data.get("forks_count", 0),
                issues_count=repo_data.get("open_issues_count", 0),
                open_issues=repo_data.get("open_issues_count", 0),
                created_at=repo_data.get("created_at"),
                updated_at=repo_data.get("updated_at"),
                pushed_at=repo_data.get("pushed_at"),
                default_branch=repo_data.get("default_branch", "main"),
                topics=repo_data.get("topics", []),
                has_wiki=repo_data.get("has_wiki", False),
                has_discussions=repo_data.get("has_discussions", False),
                has_projects=repo_data.get("has_projects", False)
            ))
        
        return repositories
    
    async def get_issues(
        self,
        owner: str,
        repo: str,
        state: str = "open",
        token_name: str = "default",
        per_page: int = 30,
        page: int = 1,
        labels: Optional[str] = None,
        assignee: Optional[str] = None
    ) -> List[Issue]:
        """Get issues from repository"""
        params = {
            "state": state,
            "per_page": per_page,
            "page": page,
            "sort": "updated"
        }
        if labels:
            params["labels"] = labels
        if assignee:
            params["assignee"] = assignee
        
        result = await self._request(
            "GET",
            f"/repos/{owner}/{repo}/issues",
            token_name,
            params=params
        )
        
        if "error" in result or not isinstance(result, list):
            return []
        
        issues = []
        for issue_data in result:
            # Skip pull requests in issues list
            if "pull_request" in issue_data:
                continue
            
            issues.append(Issue(
                number=issue_data.get("number", 0),
                title=issue_data.get("title", ""),
                description=issue_data.get("body", ""),
                state=issue_data.get("state", "open"),
                issue_id=issue_data.get("id", 0),
                url=issue_data.get("html_url", ""),
                author=issue_data.get("user", {}).get("login"),
                assignees=[a.get("login", "") for a in issue_data.get("assignees", [])],
                labels=[l.get("name", "") for l in issue_data.get("labels", [])],
                created_at=issue_data.get("created_at"),
                updated_at=issue_data.get("updated_at"),
                closed_at=issue_data.get("closed_at"),
                comments_count=issue_data.get("comments", 0),
                is_pull_request="pull_request" in issue_data
            ))
        
        return issues
    
    async def create_issue(
        self,
        owner: str,
        repo: str,
        title: str,
        body: str,
        labels: Optional[List[str]] = None,
        assignees: Optional[List[str]] = None,
        token_name: str = "default"
    ) -> Optional[Issue]:
        """Create a new issue"""
        payload = {
            "title": title,
            "body": body
        }
        if labels:
            payload["labels"] = labels
        if assignees:
            payload["assignees"] = assignees
        
        result = await self._request(
            "POST",
            f"/repos/{owner}/{repo}/issues",
            token_name,
            json=payload
        )
        
        if "error" in result:
            return None
        
        return Issue(
            number=result.get("number", 0),
            title=result.get("title", ""),
            description=result.get("body", ""),
            state=result.get("state", "open"),
            issue_id=result.get("id", 0),
            url=result.get("html_url", ""),
            author=result.get("user", {}).get("login"),
            assignees=[a.get("login", "") for a in result.get("assignees", [])],
            labels=[l.get("name", "") for l in result.get("labels", [])],
            created_at=result.get("created_at"),
            updated_at=result.get("updated_at")
        )
    
    async def update_issue(
        self,
        owner: str,
        repo: str,
        issue_number: int,
        title: Optional[str] = None,
        body: Optional[str] = None,
        state: Optional[str] = None,
        labels: Optional[List[str]] = None,
        assignees: Optional[List[str]] = None,
        token_name: str = "default"
    ) -> Optional[Issue]:
        """Update an issue"""
        payload = {}
        if title:
            payload["title"] = title
        if body:
            payload["body"] = body
        if state:
            payload["state"] = state
        if labels is not None:
            payload["labels"] = labels
        if assignees is not None:
            payload["assignees"] = assignees
        
        result = await self._request(
            "PATCH",
            f"/repos/{owner}/{repo}/issues/{issue_number}",
            token_name,
            json=payload
        )
        
        if "error" in result:
            return None
        
        return Issue(
            number=result.get("number", 0),
            title=result.get("title", ""),
            description=result.get("body", ""),
            state=result.get("state", "open"),
            issue_id=result.get("id", 0),
            url=result.get("html_url", ""),
            author=result.get("user", {}).get("login"),
            assignees=[a.get("login", "") for a in result.get("assignees", [])],
            labels=[l.get("name", "") for l in result.get("labels", [])],
            created_at=result.get("created_at"),
            updated_at=result.get("updated_at")
        )
    
    async def get_pull_requests(
        self,
        owner: str,
        repo: str,
        state: str = "open",
        token_name: str = "default",
        per_page: int = 30,
        page: int = 1
    ) -> List[PullRequest]:
        """Get pull requests from repository"""
        result = await self._request(
            "GET",
            f"/repos/{owner}/{repo}/pulls",
            token_name,
            params={"state": state, "per_page": per_page, "page": page, "sort": "updated"}
        )
        
        if "error" in result or not isinstance(result, list):
            return []
        
        prs = []
        for pr_data in result:
            prs.append(PullRequest(
                number=pr_data.get("number", 0),
                title=pr_data.get("title", ""),
                description=pr_data.get("body", ""),
                state=pr_data.get("state", "open"),
                pr_id=pr_data.get("id", 0),
                url=pr_data.get("html_url", ""),
                author=pr_data.get("user", {}).get("login"),
                reviewers=[r.get("login", "") for r in pr_data.get("requested_reviewers", [])],
                assignees=[a.get("login", "") for a in pr_data.get("assignees", [])],
                labels=[l.get("name", "") for l in pr_data.get("labels", [])],
                source_branch=pr_data.get("head", {}).get("ref", ""),
                target_branch=pr_data.get("base", {}).get("ref", "main"),
                created_at=pr_data.get("created_at"),
                updated_at=pr_data.get("updated_at"),
                closed_at=pr_data.get("closed_at"),
                merged_at=pr_data.get("merged_at"),
                comments_count=pr_data.get("comments", 0),
                review_comments_count=pr_data.get("review_comments", 0),
                commits_count=pr_data.get("commits", 0),
                additions=pr_data.get("additions", 0),
                deletions=pr_data.get("deletions", 0),
                changed_files=pr_data.get("changed_files", 0),
                mergeable=pr_data.get("mergeable", True),
                merged=pr_data.get("merged", False),
                draft=pr_data.get("draft", False)
            ))
        
        return prs
    
    async def create_pull_request(
        self,
        owner: str,
        repo: str,
        title: str,
        body: str,
        source_branch: str,
        target_branch: str = "main",
        draft: bool = False,
        token_name: str = "default"
    ) -> Optional[PullRequest]:
        """Create a new pull request"""
        payload = {
            "title": title,
            "body": body,
            "head": source_branch,
            "base": target_branch,
            "draft": draft
        }
        
        result = await self._request(
            "POST",
            f"/repos/{owner}/{repo}/pulls",
            token_name,
            json=payload
        )
        
        if "error" in result:
            return None
        
        return PullRequest(
            number=result.get("number", 0),
            title=result.get("title", ""),
            description=result.get("body", ""),
            state=result.get("state", "open"),
            pr_id=result.get("id", 0),
            url=result.get("html_url", ""),
            author=result.get("user", {}).get("login"),
            reviewers=[r.get("login", "") for r in result.get("requested_reviewers", [])],
            assignees=[a.get("login", "") for a in result.get("assignees", [])],
            labels=[l.get("name", "") for l in result.get("labels", [])],
            source_branch=result.get("head", {}).get("ref", ""),
            target_branch=result.get("base", {}).get("ref", "main"),
            created_at=result.get("created_at"),
            merged=result.get("merged", False),
            draft=result.get("draft", False)
        )
    
    async def get_commits(
        self,
        owner: str,
        repo: str,
        token_name: str = "default",
        per_page: int = 30,
        page: int = 1,
        branch: Optional[str] = None
    ) -> List[Commit]:
        """Get commits from repository"""
        params = {"per_page": per_page, "page": page}
        endpoint = f"/repos/{owner}/{repo}/commits"
        if branch:
            params["sha"] = branch
        
        result = await self._request("GET", endpoint, token_name, params=params)
        
        if "error" in result or not isinstance(result, list):
            return []
        
        commits = []
        for commit_data in result:
            commit_obj = commit_data.get("commit", {})
            commits.append(Commit(
                sha=commit_data.get("sha", ""),
                message=commit_obj.get("message", ""),
                author=commit_obj.get("author", {}).get("name", ""),
                timestamp=commit_obj.get("author", {}).get("date", ""),
                url=commit_data.get("html_url", ""),
                tree_sha=commit_obj.get("tree", {}).get("sha", ""),
                parent_shas=[p.get("sha", "") for p in commit_obj.get("parents", [])]
            ))
        
        return commits
    
    async def get_workflows(
        self,
        owner: str,
        repo: str,
        token_name: str = "default",
        per_page: int = 30,
        page: int = 1
    ) -> List[Dict[str, Any]]:
        """Get GitHub Actions workflows"""
        result = await self._request(
            "GET",
            f"/repos/{owner}/{repo}/actions/workflows",
            token_name,
            params={"per_page": per_page, "page": page}
        )
        
        if "error" in result or "workflows" not in result:
            return []
        
        return result.get("workflows", [])
    
    async def get_workflow_runs(
        self,
        owner: str,
        repo: str,
        workflow_id: str,
        token_name: str = "default",
        per_page: int = 30,
        page: int = 1
    ) -> List[WorkflowRun]:
        """Get workflow runs"""
        result = await self._request(
            "GET",
            f"/repos/{owner}/{repo}/actions/workflows/{workflow_id}/runs",
            token_name,
            params={"per_page": per_page, "page": page}
        )
        
        if "error" in result or "workflow_runs" not in result:
            return []
        
        runs = []
        for run_data in result.get("workflow_runs", []):
            runs.append(WorkflowRun(
                run_id=run_data.get("id", 0),
                run_number=run_data.get("run_number", 0),
                name=run_data.get("name", ""),
                workflow_file=run_data.get("path", ""),
                status=run_data.get("status", ""),
                conclusion=run_data.get("conclusion"),
                url=run_data.get("html_url", ""),
                trigger_event=run_data.get("event", ""),
                created_at=run_data.get("created_at"),
                updated_at=run_data.get("updated_at"),
                run_started_at=run_data.get("run_started_at"),
                actor=run_data.get("actor", {}).get("login"),
                branch=run_data.get("head_branch", ""),
                commit_sha=run_data.get("head_commit", {}).get("id", "") if run_data.get("head_commit") else ""
            ))
        
        return runs
    
    async def get_workflow_jobs(
        self,
        owner: str,
        repo: str,
        run_id: int,
        token_name: str = "default"
    ) -> List[WorkflowJob]:
        """Get workflow jobs for a run"""
        result = await self._request(
            "GET",
            f"/repos/{owner}/{repo}/actions/runs/{run_id}/jobs",
            token_name
        )
        
        if "error" in result or "jobs" not in result:
            return []
        
        jobs = []
        for job_data in result.get("jobs", []):
            jobs.append(WorkflowJob(
                job_id=job_data.get("id", 0),
                name=job_data.get("name", ""),
                status=job_data.get("status", ""),
                conclusion=job_data.get("conclusion"),
                url=job_data.get("html_url", ""),
                started_at=job_data.get("started_at"),
                completed_at=job_data.get("completed_at"),
                runner_name=job_data.get("runner_name"),
                labels=job_data.get("labels", [])
            ))
        
        return jobs
    
    async def get_branches(
        self,
        owner: str,
        repo: str,
        token_name: str = "default",
        per_page: int = 30,
        page: int = 1
    ) -> List[Branch]:
        """Get repository branches"""
        result = await self._request(
            "GET",
            f"/repos/{owner}/{repo}/branches",
            token_name,
            params={"per_page": per_page, "page": page}
        )
        
        if "error" in result or not isinstance(result, list):
            return []
        
        branches = []
        for branch_data in result:
            commit_data = branch_data.get("commit", {})
            branches.append(Branch(
                name=branch_data.get("name", ""),
                commit_sha=commit_data.get("sha", ""),
                url=branch_data.get("commit", {}).get("url", ""),
                protected=branch_data.get("protected", False),
                latest_commit_author=commit_data.get("commit", {}).get("author", {}).get("name"),
                latest_commit_date=commit_data.get("commit", {}).get("author", {}).get("date")
            ))
        
        return branches
    
    async def get_releases(
        self,
        owner: str,
        repo: str,
        token_name: str = "default",
        per_page: int = 30,
        page: int = 1
    ) -> List[Release]:
        """Get repository releases"""
        result = await self._request(
            "GET",
            f"/repos/{owner}/{repo}/releases",
            token_name,
            params={"per_page": per_page, "page": page}
        )
        
        if "error" in result or not isinstance(result, list):
            return []
        
        releases = []
        for release_data in result:
            releases.append(Release(
                tag_name=release_data.get("tag_name", ""),
                release_name=release_data.get("name", ""),
                draft=release_data.get("draft", False),
                prerelease=release_data.get("prerelease", False),
                body=release_data.get("body", ""),
                url=release_data.get("html_url", ""),
                author=release_data.get("author", {}).get("login"),
                created_at=release_data.get("created_at"),
                published_at=release_data.get("published_at"),
                assets=release_data.get("assets", [])
            ))
        
        return releases
    
    async def create_release(
        self,
        owner: str,
        repo: str,
        tag_name: str,
        release_name: str,
        body: str,
        draft: bool = False,
        prerelease: bool = False,
        token_name: str = "default"
    ) -> Optional[Release]:
        """Create a release"""
        payload = {
            "tag_name": tag_name,
            "name": release_name,
            "body": body,
            "draft": draft,
            "prerelease": prerelease
        }
        
        result = await self._request(
            "POST",
            f"/repos/{owner}/{repo}/releases",
            token_name,
            json=payload
        )
        
        if "error" in result:
            return None
        
        return Release(
            tag_name=result.get("tag_name", ""),
            release_name=result.get("name", ""),
            draft=result.get("draft", False),
            prerelease=result.get("prerelease", False),
            body=result.get("body", ""),
            url=result.get("html_url", ""),
            author=result.get("author", {}).get("login"),
            created_at=result.get("created_at"),
            published_at=result.get("published_at")
        )
    
    async def get_file_content(
        self,
        owner: str,
        repo: str,
        path: str,
        token_name: str = "default",
        ref: Optional[str] = None
    ) -> Optional[str]:
        """Get file content from repository"""
        params = {}
        if ref:
            params["ref"] = ref
        
        result = await self._request(
            "GET",
            f"/repos/{owner}/{repo}/contents/{path}",
            token_name,
            params=params
        )
        
        if "error" in result or "content" not in result:
            return None
        
        try:
            return base64.b64decode(result["content"]).decode("utf-8")
        except Exception:
            return None
    
    async def get_pr_diff(
        self,
        owner: str,
        repo: str,
        pr_number: int,
        token_name: str = "default"
    ) -> Optional[str]:
        """Get pull request diff"""
        if not self.session:
            self.session = aiohttp.ClientSession()
        
        url = f"{self.BASE_URL}/repos/{owner}/{repo}/pulls/{pr_number}.diff"
        headers = self.auth_manager.get_headers(token_name)
        
        async with self.session.get(url, headers=headers) as response:
            if response.status == 200:
                return await response.text()
        
        return None


from src.core.tools.base import BaseTool

class GitHubIntegrationTool(BaseTool):
    """GitHub integration tool for repository management, issues, PRs, and CI/CD workflows"""
    
    def __init__(self):
        super().__init__()
        self.auth_manager = GitHubAuthManager()
        self.api_client: Optional[GitHubAPIClient] = None
        self.cache: Dict[str, Any] = {}
        self.cache_ttl = 3600  # 1 hour
        self.cache_timestamps: Dict[str, float] = {}
    

    def get_parameters(self):
        """Get tool parameters."""
        from src.core.tools.base import ToolParameter
        return {
            "action": ToolParameter(
                name="action",
                type="string",
                description="GitHub action to perform",
                required=True,
                enum=[
                    "add_token", "list_tokens", "remove_token",
                    "get_repo", "list_repos", "get_repo_analysis",
                    "get_issues", "create_issue", "update_issue",
                    "get_prs", "create_pr", "get_pr_diff",
                    "get_commits", "get_workflows", "get_workflow_runs",
                    "get_workflow_jobs", "get_branches", "get_releases",
                    "create_release", "get_file", "get_user",
                    "get_authenticated_user"
                ]
            ),
            "token_name": ToolParameter(
                name="token_name",
                type="string",
                description="GitHub token name",
                required=False
            ),
            "token": ToolParameter(
                name="token",
                type="string",
                description="GitHub personal access token",
                required=False
            ),
            "owner": ToolParameter(
                name="owner",
                type="string",
                description="Repository owner/organization",
                required=False
            ),
            "repo": ToolParameter(
                name="repo",
                type="string",
                description="Repository name",
                required=False
            ),
            "username": ToolParameter(
                name="username",
                type="string",
                description="GitHub username",
                required=False
            )
        }

    async def execute(self, action: str, **kwargs) -> Dict[str, Any]:
        """Execute GitHub integration action"""
        
        # Authentication actions
        if action == "add_token":
            return await self._add_token(**kwargs)
        elif action == "list_tokens":
            return self._list_tokens(**kwargs)
        elif action == "remove_token":
            return self._remove_token(**kwargs)
        
        # Repository actions
        elif action == "get_repo":
            return await self._get_repo(**kwargs)
        elif action == "list_repos":
            return await self._list_repos(**kwargs)
        elif action == "get_repo_analysis":
            return await self._get_repo_analysis(**kwargs)
        
        # Issue actions
        elif action == "get_issues":
            return await self._get_issues(**kwargs)
        elif action == "create_issue":
            return await self._create_issue(**kwargs)
        elif action == "update_issue":
            return await self._update_issue(**kwargs)
        
        # Pull request actions
        elif action == "get_prs":
            return await self._get_prs(**kwargs)
        elif action == "create_pr":
            return await self._create_pr(**kwargs)
        elif action == "get_pr_diff":
            return await self._get_pr_diff(**kwargs)
        
        # Commit actions
        elif action == "get_commits":
            return await self._get_commits(**kwargs)
        
        # Workflow actions
        elif action == "get_workflows":
            return await self._get_workflows(**kwargs)
        elif action == "get_workflow_runs":
            return await self._get_workflow_runs(**kwargs)
        elif action == "get_workflow_jobs":
            return await self._get_workflow_jobs(**kwargs)
        
        # Branch actions
        elif action == "get_branches":
            return await self._get_branches(**kwargs)
        
        # Release actions
        elif action == "get_releases":
            return await self._get_releases(**kwargs)
        elif action == "create_release":
            return await self._create_release(**kwargs)
        
        # File actions
        elif action == "get_file":
            return await self._get_file(**kwargs)
        
        # User actions
        elif action == "get_user":
            return await self._get_user(**kwargs)
        elif action == "get_authenticated_user":
            return await self._get_authenticated_user(**kwargs)
        
        else:
            return {
                "success": False,
                "error": f"Unknown action: {action}",
                "available_actions": [
                    "add_token", "list_tokens", "remove_token",
                    "get_repo", "list_repos", "get_repo_analysis",
                    "get_issues", "create_issue", "update_issue",
                    "get_prs", "create_pr", "get_pr_diff",
                    "get_commits", "get_workflows", "get_workflow_runs",
                    "get_workflow_jobs", "get_branches", "get_releases",
                    "create_release", "get_file", "get_user",
                    "get_authenticated_user"
                ]
            }
    
    async def _add_token(self, token_name: str, token: str, **kwargs) -> Dict[str, Any]:
        """Add GitHub API token"""
        if not token_name or not token:
            return {
                "success": False,
                "error": "token_name and token are required"
            }
        
        success = self.auth_manager.add_token(token_name, token)
        if success and not self.api_client:
            self.api_client = GitHubAPIClient(self.auth_manager)
        
        return {
            "success": success,
            "message": f"Token '{token_name}' added successfully" if success else "Failed to add token",
            "token_name": token_name
        }
    
    def _list_tokens(self, **kwargs) -> Dict[str, Any]:
        """List configured tokens"""
        tokens = self.auth_manager.list_tokens()
        return {
            "success": True,
            "tokens": tokens,
            "count": len(tokens)
        }
    
    def _remove_token(self, token_name: str, **kwargs) -> Dict[str, Any]:
        """Remove token"""
        success = self.auth_manager.remove_token(token_name)
        return {
            "success": success,
            "message": f"Token '{token_name}' removed" if success else f"Token '{token_name}' not found"
        }
    
    async def _get_repo(
        self,
        owner: str,
        repo: str,
        token_name: str = "default",
        **kwargs
    ) -> Dict[str, Any]:
        """Get repository information"""
        if not self.api_client:
            return {
                "success": False,
                "error": "No GitHub token configured. Use add_token action first."
            }
        
        async with self.api_client:
            repository = await self.api_client.get_repository(owner, repo, token_name)
            
            if not repository:
                return {
                    "success": False,
                    "error": f"Repository {owner}/{repo} not found"
                }
            
            return {
                "success": True,
                "repository": asdict(repository)
            }
    
    async def _list_repos(
        self,
        username: str,
        token_name: str = "default",
        page: int = 1,
        per_page: int = 30,
        **kwargs
    ) -> Dict[str, Any]:
        """List user repositories"""
        if not self.api_client:
            return {
                "success": False,
                "error": "No GitHub token configured"
            }
        
        async with self.api_client:
            repos = await self.api_client.list_repositories(
                username, token_name, per_page, page
            )
            
            return {
                "success": True,
                "repositories": [asdict(r) for r in repos],
                "count": len(repos)
            }
    
    async def _get_repo_analysis(
        self,
        owner: str,
        repo: str,
        token_name: str = "default",
        **kwargs
    ) -> Dict[str, Any]:
        """Analyze repository"""
        if not self.api_client:
            return {
                "success": False,
                "error": "No GitHub token configured"
            }
        
        async with self.api_client:
            # Get basic repo info
            repository = await self.api_client.get_repository(owner, repo, token_name)
            if not repository:
                return {
                    "success": False,
                    "error": f"Repository {owner}/{repo} not found"
                }
            
            # Get additional stats
            issues = await self.api_client.get_issues(
                owner, repo, state="all", token_name=token_name, per_page=1
            )
            prs = await self.api_client.get_pull_requests(
                owner, repo, state="all", token_name=token_name, per_page=1
            )
            releases = await self.api_client.get_releases(
                owner, repo, token_name=token_name, per_page=1
            )
            branches = await self.api_client.get_branches(
                owner, repo, token_name=token_name
            )
            commits = await self.api_client.get_commits(
                owner, repo, token_name=token_name, per_page=1
            )
            
            analysis = RepositoryAnalysis(
                repo_name=repository.name,
                total_branches=len(branches),
                total_releases=len(releases),
                open_issues=repository.open_issues,
                languages={repository.language: 100.0} if repository.language else {},
                topics=repository.topics,
                license=None,  # Would need additional API call
                last_commit_date=commits[0].timestamp if commits else None,
                last_release_date=releases[0].published_at if releases else None
            )
            
            return {
                "success": True,
                "analysis": asdict(analysis)
            }
    
    async def _get_issues(
        self,
        owner: str,
        repo: str,
        state: str = "open",
        token_name: str = "default",
        page: int = 1,
        per_page: int = 30,
        labels: Optional[str] = None,
        assignee: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Get issues"""
        if not self.api_client:
            return {"success": False, "error": "No GitHub token configured"}
        
        async with self.api_client:
            issues = await self.api_client.get_issues(
                owner, repo, state, token_name, per_page, page, labels, assignee
            )
            
            return {
                "success": True,
                "issues": [asdict(i) for i in issues],
                "count": len(issues)
            }
    
    async def _create_issue(
        self,
        owner: str,
        repo: str,
        title: str,
        body: str,
        labels: Optional[List[str]] = None,
        assignees: Optional[List[str]] = None,
        token_name: str = "default",
        **kwargs
    ) -> Dict[str, Any]:
        """Create issue"""
        if not self.api_client:
            return {"success": False, "error": "No GitHub token configured"}
        
        async with self.api_client:
            issue = await self.api_client.create_issue(
                owner, repo, title, body, labels, assignees, token_name
            )
            
            if not issue:
                return {"success": False, "error": "Failed to create issue"}
            
            return {
                "success": True,
                "issue": asdict(issue)
            }
    
    async def _update_issue(
        self,
        owner: str,
        repo: str,
        issue_number: int,
        title: Optional[str] = None,
        body: Optional[str] = None,
        state: Optional[str] = None,
        labels: Optional[List[str]] = None,
        assignees: Optional[List[str]] = None,
        token_name: str = "default",
        **kwargs
    ) -> Dict[str, Any]:
        """Update issue"""
        if not self.api_client:
            return {"success": False, "error": "No GitHub token configured"}
        
        async with self.api_client:
            issue = await self.api_client.update_issue(
                owner, repo, issue_number, title, body, state, labels, assignees, token_name
            )
            
            if not issue:
                return {"success": False, "error": "Failed to update issue"}
            
            return {
                "success": True,
                "issue": asdict(issue)
            }
    
    async def _get_prs(
        self,
        owner: str,
        repo: str,
        state: str = "open",
        token_name: str = "default",
        page: int = 1,
        per_page: int = 30,
        **kwargs
    ) -> Dict[str, Any]:
        """Get pull requests"""
        if not self.api_client:
            return {"success": False, "error": "No GitHub token configured"}
        
        async with self.api_client:
            prs = await self.api_client.get_pull_requests(
                owner, repo, state, token_name, per_page, page
            )
            
            return {
                "success": True,
                "pull_requests": [asdict(p) for p in prs],
                "count": len(prs)
            }
    
    async def _create_pr(
        self,
        owner: str,
        repo: str,
        title: str,
        body: str,
        source_branch: str,
        target_branch: str = "main",
        draft: bool = False,
        token_name: str = "default",
        **kwargs
    ) -> Dict[str, Any]:
        """Create pull request"""
        if not self.api_client:
            return {"success": False, "error": "No GitHub token configured"}
        
        async with self.api_client:
            pr = await self.api_client.create_pull_request(
                owner, repo, title, body, source_branch, target_branch, draft, token_name
            )
            
            if not pr:
                return {"success": False, "error": "Failed to create PR"}
            
            return {
                "success": True,
                "pull_request": asdict(pr)
            }
    
    async def _get_pr_diff(
        self,
        owner: str,
        repo: str,
        pr_number: int,
        token_name: str = "default",
        **kwargs
    ) -> Dict[str, Any]:
        """Get pull request diff"""
        if not self.api_client:
            return {"success": False, "error": "No GitHub token configured"}
        
        async with self.api_client:
            diff = await self.api_client.get_pr_diff(owner, repo, pr_number, token_name)
            
            if not diff:
                return {"success": False, "error": "Failed to get PR diff"}
            
            return {
                "success": True,
                "diff": diff,
                "pr_number": pr_number
            }
    
    async def _get_commits(
        self,
        owner: str,
        repo: str,
        token_name: str = "default",
        page: int = 1,
        per_page: int = 30,
        branch: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Get commits"""
        if not self.api_client:
            return {"success": False, "error": "No GitHub token configured"}
        
        async with self.api_client:
            commits = await self.api_client.get_commits(
                owner, repo, token_name, per_page, page, branch
            )
            
            return {
                "success": True,
                "commits": [asdict(c) for c in commits],
                "count": len(commits)
            }
    
    async def _get_workflows(
        self,
        owner: str,
        repo: str,
        token_name: str = "default",
        page: int = 1,
        per_page: int = 30,
        **kwargs
    ) -> Dict[str, Any]:
        """Get workflows"""
        if not self.api_client:
            return {"success": False, "error": "No GitHub token configured"}
        
        async with self.api_client:
            workflows = await self.api_client.get_workflows(
                owner, repo, token_name, per_page, page
            )
            
            return {
                "success": True,
                "workflows": workflows,
                "count": len(workflows)
            }
    
    async def _get_workflow_runs(
        self,
        owner: str,
        repo: str,
        workflow_id: str,
        token_name: str = "default",
        page: int = 1,
        per_page: int = 30,
        **kwargs
    ) -> Dict[str, Any]:
        """Get workflow runs"""
        if not self.api_client:
            return {"success": False, "error": "No GitHub token configured"}
        
        async with self.api_client:
            runs = await self.api_client.get_workflow_runs(
                owner, repo, workflow_id, token_name, per_page, page
            )
            
            return {
                "success": True,
                "workflow_runs": [asdict(r) for r in runs],
                "count": len(runs)
            }
    
    async def _get_workflow_jobs(
        self,
        owner: str,
        repo: str,
        run_id: int,
        token_name: str = "default",
        **kwargs
    ) -> Dict[str, Any]:
        """Get workflow jobs"""
        if not self.api_client:
            return {"success": False, "error": "No GitHub token configured"}
        
        async with self.api_client:
            jobs = await self.api_client.get_workflow_jobs(owner, repo, run_id, token_name)
            
            return {
                "success": True,
                "jobs": [asdict(j) for j in jobs],
                "count": len(jobs)
            }
    
    async def _get_branches(
        self,
        owner: str,
        repo: str,
        token_name: str = "default",
        page: int = 1,
        per_page: int = 30,
        **kwargs
    ) -> Dict[str, Any]:
        """Get branches"""
        if not self.api_client:
            return {"success": False, "error": "No GitHub token configured"}
        
        async with self.api_client:
            branches = await self.api_client.get_branches(
                owner, repo, token_name, per_page, page
            )
            
            return {
                "success": True,
                "branches": [asdict(b) for b in branches],
                "count": len(branches)
            }
    
    async def _get_releases(
        self,
        owner: str,
        repo: str,
        token_name: str = "default",
        page: int = 1,
        per_page: int = 30,
        **kwargs
    ) -> Dict[str, Any]:
        """Get releases"""
        if not self.api_client:
            return {"success": False, "error": "No GitHub token configured"}
        
        async with self.api_client:
            releases = await self.api_client.get_releases(
                owner, repo, token_name, per_page, page
            )
            
            return {
                "success": True,
                "releases": [asdict(r) for r in releases],
                "count": len(releases)
            }
    
    async def _create_release(
        self,
        owner: str,
        repo: str,
        tag_name: str,
        release_name: str,
        body: str,
        draft: bool = False,
        prerelease: bool = False,
        token_name: str = "default",
        **kwargs
    ) -> Dict[str, Any]:
        """Create release"""
        if not self.api_client:
            return {"success": False, "error": "No GitHub token configured"}
        
        async with self.api_client:
            release = await self.api_client.create_release(
                owner, repo, tag_name, release_name, body, draft, prerelease, token_name
            )
            
            if not release:
                return {"success": False, "error": "Failed to create release"}
            
            return {
                "success": True,
                "release": asdict(release)
            }
    
    async def _get_file(
        self,
        owner: str,
        repo: str,
        path: str,
        token_name: str = "default",
        ref: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Get file content"""
        if not self.api_client:
            return {"success": False, "error": "No GitHub token configured"}
        
        async with self.api_client:
            content = await self.api_client.get_file_content(
                owner, repo, path, token_name, ref
            )
            
            if content is None:
                return {"success": False, "error": f"File {path} not found"}
            
            return {
                "success": True,
                "file": path,
                "content": content
            }
    
    async def _get_user(
        self,
        username: str,
        token_name: str = "default",
        **kwargs
    ) -> Dict[str, Any]:
        """Get user information"""
        if not self.api_client:
            return {"success": False, "error": "No GitHub token configured"}
        
        async with self.api_client:
            user = await self.api_client.get_user(username, token_name)
            
            if not user:
                return {"success": False, "error": f"User {username} not found"}
            
            return {
                "success": True,
                "user": asdict(user)
            }
    
    async def _get_authenticated_user(
        self,
        token_name: str = "default",
        **kwargs
    ) -> Dict[str, Any]:
        """Get authenticated user information"""
        if not self.api_client:
            return {"success": False, "error": "No GitHub token configured"}
        
        async with self.api_client:
            user = await self.api_client.get_authenticated_user(token_name)
            
            if not user:
                return {"success": False, "error": "Failed to get authenticated user"}
            
            return {
                "success": True,
                "user": asdict(user)
            }
