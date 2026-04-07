# JARVIS 2.0 - GitHub Integration Plugin Documentation

## Overview

The GitHub Integration Plugin provides comprehensive GitHub API integration supporting:
- Repository management and operations
- Issue tracking and automation
- Pull request workflow automation
- GitHub Actions CI/CD integration
- Code analysis and collaboration features
- User and organization management

## Features

### Repository Management
- **Repository Information**: Get detailed repository metadata
- **Repository Listing**: List user/organization repositories with filtering
- **Repository Analysis**: Comprehensive repository statistics and metrics
- **Branch Management**: Get, create, and manage branches
- **Release Management**: Create and manage releases with assets

### Issue Management
- **Issue Retrieval**: Get all issues with filtering and sorting
- **Issue Creation**: Create new issues with labels and assignees
- **Issue Updates**: Update issue state, title, description, and metadata
- **Issue Tracking**: Full issue lifecycle management
- **Issue Search**: Advanced issue filtering by state, labels, assignees

### Pull Request Workflow
- **PR Retrieval**: Get all pull requests with state filtering
- **PR Creation**: Create new PRs with draft and review support
- **PR Diff**: Get detailed PR diff and file changes
- **PR Review**: Review PR changes and suggest improvements
- **PR Merging**: Merge PRs with conflict detection
- **PR Statistics**: Track PR metrics (additions, deletions, changed files)

### GitHub Actions Integration
- **Workflow Management**: Get workflows and runs
- **Workflow Runs**: Retrieve run history with status and conclusions
- **Job Details**: Get individual job information and logs
- **CI/CD Status**: Monitor build and test status
- **Artifact Management**: Access workflow artifacts
- **Performance Monitoring**: Track workflow execution times

### Code & Collaboration
- **Commit History**: Get commit logs with detailed information
- **File Operations**: Read and analyze file content
- **User Management**: Retrieve user profiles and information
- **Team Management**: Manage repository teams and access
- **Code Review**: Facilitate code review workflows

### Authentication
- **Token Management**: Securely store and manage GitHub tokens
- **Multi-Token Support**: Support for multiple GitHub accounts
- **API Rate Limiting**: Handle GitHub API rate limits gracefully
- **OAuth Support**: Support for GitHub OAuth flows (extensible)

## Installation

### Requirements

```bash
pip install aiohttp requests
```

The plugin requires:
- Python 3.8+
- aiohttp for async HTTP requests
- GitHub API v3 access

### Configuration

#### GitHub Token Setup

1. **Generate Personal Access Token**:
   - Go to GitHub Settings → Developer settings → Personal access tokens
   - Create a new token with required scopes:
     - `repo`: Full control of private repositories
     - `admin:repo_hook`: Write access to hooks
     - `admin:org_hook`: Access to org hooks
     - `user`: Access to user data
     - `read:org`: Read org data
     - `admin:public_key`: Manage public keys

2. **Store Token Securely**:
   ```python
   from src.plugins.github_integration import GitHubIntegrationTool
   
   tool = GitHubIntegrationTool()
   tool.auth_manager.add_token("main", "ghp_your_token_here")
   ```

3. **Use Multiple Accounts**:
   ```python
   tool.auth_manager.add_token("work", "ghp_work_token")
   tool.auth_manager.add_token("personal", "ghp_personal_token")
   ```

## Usage Examples

### Authentication

```python
from src.plugins.github_integration import GitHubIntegrationTool

tool = GitHubIntegrationTool()

# Add GitHub token
result = await tool.execute(
    action="add_token",
    token_name="main",
    token="ghp_your_personal_access_token"
)

# List configured tokens
result = await tool.execute(action="list_tokens")
print(f"Tokens: {result['tokens']}")

# Remove token
result = await tool.execute(
    action="remove_token",
    token_name="main"
)
```

### Repository Operations

```python
# Get repository information
result = await tool.execute(
    action="get_repo",
    owner="python",
    repo="cpython",
    token_name="main"
)

repo = result['repository']
print(f"Stars: {repo['stars']}")
print(f"Language: {repo['language']}")
print(f"Description: {repo['description']}")

# List user repositories
result = await tool.execute(
    action="list_repos",
    username="torvalds",
    page=1,
    per_page=30,
    token_name="main"
)

for repo in result['repositories']:
    print(f"{repo['name']}: {repo['stars']} ⭐")

# Analyze repository
result = await tool.execute(
    action="get_repo_analysis",
    owner="kubernetes",
    repo="kubernetes",
    token_name="main"
)

analysis = result['analysis']
print(f"Total Commits: {analysis['total_commits']}")
print(f"Total Branches: {analysis['total_branches']}")
print(f"Open Issues: {analysis['open_issues']}")
print(f"Open PRs: {analysis['open_prs']}")
```

### Issue Management

```python
# Get all open issues
result = await tool.execute(
    action="get_issues",
    owner="django",
    repo="django",
    state="open",
    per_page=20,
    token_name="main"
)

print(f"Found {result['count']} open issues")
for issue in result['issues']:
    print(f"#{issue['number']}: {issue['title']}")
    print(f"  Assignees: {issue['assignees']}")
    print(f"  Labels: {issue['labels']}")

# Create new issue
result = await tool.execute(
    action="create_issue",
    owner="myorg",
    repo="myrepo",
    title="Bug: Feature not working",
    body="## Description\nThe feature is broken.\n## Steps\n1. Do this\n2. Then this",
    labels=["bug", "high-priority"],
    assignees=["username"],
    token_name="main"
)

new_issue = result['issue']
print(f"Created issue #{new_issue['number']}")

# Update issue
result = await tool.execute(
    action="update_issue",
    owner="myorg",
    repo="myrepo",
    issue_number=1,
    state="closed",
    title="Updated Title",
    labels=["bug", "fixed"],
    token_name="main"
)
```

### Pull Request Workflow

```python
# Get all open PRs
result = await tool.execute(
    action="get_prs",
    owner="facebook",
    repo="react",
    state="open",
    per_page=20,
    token_name="main"
)

print(f"Found {result['count']} open PRs")
for pr in result['pull_requests']:
    print(f"#{pr['number']}: {pr['title']}")
    print(f"  Author: {pr['author']}")
    print(f"  Status: {pr['state']}")
    print(f"  Changes: +{pr['additions']}/-{pr['deletions']}")

# Create pull request
result = await tool.execute(
    action="create_pr",
    owner="myorg",
    repo="myrepo",
    title="Add new feature",
    body="## Description\nAdds amazing feature\n## Type of Change\n- [ ] Bug fix\n- [x] New feature",
    source_branch="feature/awesome",
    target_branch="main",
    draft=False,
    token_name="main"
)

new_pr = result['pull_request']
print(f"Created PR #{new_pr['number']}: {new_pr['url']}")

# Get PR diff
result = await tool.execute(
    action="get_pr_diff",
    owner="myorg",
    repo="myrepo",
    pr_number=42,
    token_name="main"
)

print(result['diff'])  # Full unified diff format
```

### GitHub Actions

```python
# Get workflows
result = await tool.execute(
    action="get_workflows",
    owner="github",
    repo="docs",
    token_name="main"
)

for workflow in result['workflows']:
    print(f"Workflow: {workflow['name']}")
    print(f"  File: {workflow['path']}")
    print(f"  State: {workflow['state']}")

# Get workflow runs
result = await tool.execute(
    action="get_workflow_runs",
    owner="github",
    repo="docs",
    workflow_id="ci.yml",
    per_page=10,
    token_name="main"
)

for run in result['workflow_runs']:
    print(f"Run #{run['run_number']}: {run['name']}")
    print(f"  Status: {run['status']}")
    print(f"  Conclusion: {run['conclusion']}")
    print(f"  Branch: {run['branch']}")

# Get workflow jobs
result = await tool.execute(
    action="get_workflow_jobs",
    owner="github",
    repo="docs",
    run_id=123456,
    token_name="main"
)

for job in result['jobs']:
    print(f"Job: {job['name']}")
    print(f"  Status: {job['status']}")
    print(f"  Conclusion: {job['conclusion']}")
    print(f"  Duration: {job['duration_seconds']}s")
```

### Commits & History

```python
# Get commit history
result = await tool.execute(
    action="get_commits",
    owner="golang",
    repo="go",
    per_page=10,
    page=1,
    token_name="main"
)

for commit in result['commits']:
    print(f"Commit: {commit['sha'][:7]}")
    print(f"  Author: {commit['author']}")
    print(f"  Message: {commit['message']}")
    print(f"  Files Changed: {commit['files_changed']}")

# Get commits from specific branch
result = await tool.execute(
    action="get_commits",
    owner="myorg",
    repo="myrepo",
    branch="develop",
    token_name="main"
)
```

### Branches & Releases

```python
# Get repository branches
result = await tool.execute(
    action="get_branches",
    owner="torvalds",
    repo="linux",
    token_name="main"
)

for branch in result['branches']:
    print(f"Branch: {branch['name']}")
    print(f"  Latest commit: {branch['commit_sha'][:7]}")
    print(f"  Protected: {branch['protected']}")

# Get releases
result = await tool.execute(
    action="get_releases",
    owner="kubernetes",
    repo="kubernetes",
    per_page=10,
    token_name="main"
)

for release in result['releases']:
    print(f"Release: {release['tag_name']}")
    print(f"  Name: {release['release_name']}")
    print(f"  Draft: {release['draft']}")
    print(f"  Prerelease: {release['prerelease']}")
    print(f"  Assets: {len(release['assets'])}")

# Create release
result = await tool.execute(
    action="create_release",
    owner="myorg",
    repo="myrepo",
    tag_name="v1.0.0",
    release_name="Version 1.0.0",
    body="Release notes here",
    draft=False,
    prerelease=False,
    token_name="main"
)

release = result['release']
print(f"Created release: {release['tag_name']}")
```

### File Operations

```python
# Get file content
result = await tool.execute(
    action="get_file",
    owner="torvalds",
    repo="linux",
    path="README.md",
    token_name="main"
)

content = result['content']
print(f"File size: {len(content)} bytes")
print(content[:500])  # First 500 chars

# Get file from specific branch
result = await tool.execute(
    action="get_file",
    owner="myorg",
    repo="myrepo",
    path="src/main.py",
    ref="develop",
    token_name="main"
)
```

### User Information

```python
# Get user profile
result = await tool.execute(
    action="get_user",
    username="torvalds",
    token_name="main"
)

user = result['user']
print(f"User: {user['name']} (@{user['username']})")
print(f"Bio: {user['bio']}")
print(f"Location: {user['location']}")
print(f"Followers: {user['followers']}")
print(f"Public Repos: {user['public_repos']}")

# Get authenticated user
result = await tool.execute(
    action="get_authenticated_user",
    token_name="main"
)

user = result['user']
print(f"Authenticated as: {user['username']}")
print(f"Email: {user.get('email', 'N/A')}")
```

## Data Models

### Repository
```python
@dataclass
class Repository:
    name: str
    owner: str
    url: str
    description: Optional[str]
    language: Optional[str]
    stars: int
    forks: int
    open_issues: int
    private: bool
    fork: bool
    default_branch: str
    topics: List[str]
    created_at: Optional[str]
    updated_at: Optional[str]
    pushed_at: Optional[str]
```

### Issue
```python
@dataclass
class Issue:
    number: int
    title: str
    description: str
    state: str  # "open" or "closed"
    url: str
    author: Optional[str]
    assignees: List[str]
    labels: List[str]
    created_at: Optional[str]
    updated_at: Optional[str]
    closed_at: Optional[str]
    comments_count: int
```

### PullRequest
```python
@dataclass
class PullRequest:
    number: int
    title: str
    description: str
    state: str  # "open", "closed", "merged"
    url: str
    author: Optional[str]
    reviewers: List[str]
    assignees: List[str]
    labels: List[str]
    source_branch: str
    target_branch: str
    additions: int
    deletions: int
    changed_files: int
    created_at: Optional[str]
    merged_at: Optional[str]
```

### WorkflowRun
```python
@dataclass
class WorkflowRun:
    run_id: int
    run_number: int
    name: str
    workflow_file: str
    status: str  # "queued", "in_progress", "completed"
    conclusion: Optional[str]  # "success", "failure", etc
    branch: str
    created_at: Optional[str]
    run_started_at: Optional[str]
    duration_seconds: int
    actor: Optional[str]
```

## Available Actions

| Action | Description | Required Parameters |
|--------|-------------|-------------------|
| `add_token` | Add GitHub API token | `token_name`, `token` |
| `remove_token` | Remove token | `token_name` |
| `list_tokens` | List configured tokens | None |
| `get_repo` | Get repository info | `owner`, `repo` |
| `list_repos` | List user repositories | `username` |
| `get_repo_analysis` | Analyze repository | `owner`, `repo` |
| `get_issues` | Get issues | `owner`, `repo` |
| `create_issue` | Create issue | `owner`, `repo`, `title`, `body` |
| `update_issue` | Update issue | `owner`, `repo`, `issue_number` |
| `get_prs` | Get pull requests | `owner`, `repo` |
| `create_pr` | Create PR | `owner`, `repo`, `title`, `body`, `source_branch` |
| `get_pr_diff` | Get PR diff | `owner`, `repo`, `pr_number` |
| `get_commits` | Get commits | `owner`, `repo` |
| `get_workflows` | Get workflows | `owner`, `repo` |
| `get_workflow_runs` | Get workflow runs | `owner`, `repo`, `workflow_id` |
| `get_workflow_jobs` | Get workflow jobs | `owner`, `repo`, `run_id` |
| `get_branches` | Get branches | `owner`, `repo` |
| `get_releases` | Get releases | `owner`, `repo` |
| `create_release` | Create release | `owner`, `repo`, `tag_name`, `release_name`, `body` |
| `get_file` | Get file content | `owner`, `repo`, `path` |
| `get_user` | Get user info | `username` |
| `get_authenticated_user` | Get current user | None |

## Advanced Features

### Rate Limiting
The plugin handles GitHub API rate limits automatically:
- Tracks rate limit remaining and reset time
- Provides rate limit info in responses
- Implements exponential backoff for rate limit errors

### Caching
Responses are cached with configurable TTL:
- Default cache TTL: 1 hour
- Reduces API calls for repeated queries
- Can be disabled per request

### Error Handling
Comprehensive error handling with detailed messages:
- Connection errors
- Authentication failures
- Rate limiting
- Validation errors
- API errors

### Async/Await
All operations use async/await pattern:
- Non-blocking API calls
- Concurrent request support
- Better performance with many requests

## CLI Integration

```bash
# Add GitHub token
JARVIS> github add-token --token ghp_xxx

# Get repository info
JARVIS> github get-repo --owner python --repo cpython

# List repositories
JARVIS> github list-repos --username torvalds

# Get issues
JARVIS> github get-issues --owner django --repo django --state open

# Create issue
JARVIS> github create-issue --owner myorg --repo myrepo --title "Bug report" --body "Description"

# Get pull requests
JARVIS> github get-prs --owner facebook --repo react --state open

# Get workflow runs
JARVIS> github get-workflows --owner github --repo docs

# Analyze repository
JARVIS> github analyze --owner kubernetes --repo kubernetes
```

## Security Considerations

### Token Security
- Never commit tokens to repository
- Use environment variables for token storage
- Rotate tokens regularly
- Use fine-grained personal access tokens when possible

### Scope Management
- Request minimum required scopes
- Review token permissions regularly
- Revoke unused tokens

### API Security
- All requests use HTTPS
- SSL/TLS certificate verification enabled
- Token passed in Authorization header only

## Troubleshooting

### Common Issues

1. **"Unauthorized - invalid token"**
   - Verify token is valid and not expired
   - Check token has required scopes
   - Regenerate token if needed

2. **"API rate limit exceeded"**
   - Wait for rate limit reset
   - Reduce request frequency
   - Use caching to avoid repeated requests

3. **"Repository not found"**
   - Verify owner and repo names
   - Check repository is public or token has access
   - Ensure token has required permissions

4. **Connection timeout**
   - Check network connectivity
   - Verify GitHub API is accessible
   - Try request again

## Best Practices

1. **Token Management**
   - Use different tokens for different environments
   - Rotate tokens regularly
   - Monitor token usage

2. **API Usage**
   - Cache results when possible
   - Batch requests where applicable
   - Implement exponential backoff for retries

3. **Error Handling**
   - Handle rate limits gracefully
   - Log errors for debugging
   - Provide user-friendly error messages

4. **Performance**
   - Use pagination for large result sets
   - Filter results on GitHub side when possible
   - Minimize API calls with caching

## Future Enhancements

- [ ] GraphQL API support for more efficient queries
- [ ] Webhook integration for real-time events
- [ ] GitHub App authentication
- [ ] Advanced search and filtering
- [ ] Repository templates
- [ ] Team management
- [ ] Gist management
- [ ] Code scanning integration
- [ ] Dependency management features
- [ ] Advanced analytics and insights

## Support

For issues and feature requests:
- Check JARVIS 2.0 documentation
- Review GitHub API documentation
- Check plugin test cases for usage examples

---

**Version**: 2.6.0  
**Last Updated**: April 2026  
**Author**: JARVIS 2.0 Development Team
