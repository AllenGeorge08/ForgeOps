import asyncio
from app.mcp.github import GithubTools
from langchain.tools import tool 


github = asyncio.run(GithubTools().ainit())



@tool
async def get_commit(owner: str, repo_name: str, sha: str):
    """Get a single commit's details (message, author, stats, changed files) given the owner, repo name, and commit SHA/branch/tag."""
    return await github.get_commit(owner, repo_name, sha)


@tool
async def pull_request_read(action: str, owner: str, repo_name: str, pullNumber: int):
    """Read a pull request. action can be 'get', 'get_diff', 'get_files', 'get_comments', 'get_reviews', or similar PR sub-resources. Requires owner, repo name, and PR number."""
    return await github.pull_request_read(action, owner, repo_name, pullNumber)


@tool
async def list_commits(owner: str, repo_name: str):
    """List recent commits (sha and message) for a given owner and repo."""
    return await github.list_commits(owner, repo_name)


@tool
async def list_pull_requests(owner: str, repo_name: str, state: str = None):
    """List pull requests for a repo. state can be 'open', 'closed', or 'all'; defaults to open if not provided."""
    return await github.list_pull_requests(owner, repo_name, state)


@tool
async def get_file_contents(owner: str, repo_name: str):
    """Get the file contents given the owner and the repo name"""
    return await github.get_file_contents(owner, repo_name)


@tool
async def list_branches(owner: str, repo_name: str):
    """List branches for a repo, including whether each is protected."""
    return await github.list_branches(owner, repo_name)


@tool
async def search_code(
    search_term: str,
    owner: str = None,
    repo: str = None,
    language: str = None,
    path: str = None,
    extension: str = None,
    per_page: int = 10,
):
    """Search code across GitHub. Narrow with owner (and repo for a single repo), language, path, or file extension. Returns matching files with fragments showing the match context."""
    return await github.search_code(search_term, owner, repo, language, path, extension, per_page)


@tool
async def search_pull_requests(search_term: str, owner: str = None, repo: str = None):
    """Search pull requests by keyword. Optionally scope to a specific owner/repo."""
    return await github.search_pull_requests(search_term, owner, repo)


@tool
async def search_issues(search_term: str, owner: str = None, repo_name: str = None):
    """Search issues by keyword. Optionally scope to a specific owner/repo."""
    return await github.search_issues(search_term, owner, repo_name)


@tool
async def issue_read(owner: str, repo: str, issue_number: int, method: str = "get"):
    """Read an issue. method can be 'get', 'get_comments', 'get_sub_issues', 'get_parent', or 'get_labels'. Requires owner, repo, and issue number."""
    return await github.issue_read(owner, repo, issue_number, method)


@tool
async def search_commits(
    search_term: str,
    owner: str = None,
    repo_name: str = None,
    sort: str = None,
    order: str = None,
    page: int = 1,
    per_page: int = 10,
):
    """Search commits using GitHub commit search syntax (e.g. 'author:x', 'author-date:>2026-01-01'). Optionally scope to owner/repo, sort by 'author-date' or 'committer-date', and paginate."""
    return await github.search_commits(search_term, owner, repo_name, sort, order, page, per_page)