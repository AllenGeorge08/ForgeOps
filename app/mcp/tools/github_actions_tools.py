from app.mcp.github_actions import GithubActions
from langchain.tools import tool


_github_actions = None


async def init_github_actions():
    """Initialize the GitHub Actions MCP client. Call this during app startup."""
    global _github_actions
    if _github_actions is None:
        _github_actions = await GithubActions().ainit()
    return _github_actions


def _ensure_github_actions():
    if _github_actions is None:
        raise RuntimeError(
            "GitHub Actions MCP client not initialized. Call init_github_actions() during app startup."
        )
    return _github_actions


@tool
async def list_actions(method: str, owner: str, repo_name: str, perPage: int = 5):
    """List GitHub Actions workflows for a repo. Requires owner, repo name, and a method (check your MCP server for valid values, likely 'list_workflows')."""
    return await _ensure_github_actions().list_actions(method, owner, repo_name, perPage)


@tool
async def actions_get(method: str, owner: str, repo: str, resource_id: str):
    """Get a single Actions resource. method can be 'get_workflow', 'get_workflow_run', or 'get_workflow_run_usage'. resource_id is the workflow ID or run ID depending on method."""
    return await _ensure_github_actions().actions_get(method, owner, repo, resource_id)


@tool
async def actions_list(method: str, owner: str, repo: str, **kwargs):
    """List Actions resources (e.g. workflow runs, jobs for a run). method selects the resource type; pass extra filters like workflow_id or run_id as kwargs."""
    return await _ensure_github_actions().actions_list(method, owner, repo, **kwargs)


@tool
async def get_job_logs(
    owner: str,
    repo: str,
    job_id: int = None,
    run_id: int = None,
    failed_only: bool = False,
    return_content: bool = False,
    tail_lines: int = 500,
):
    """Get logs for a CI job or run. Pass job_id for a single job, or run_id with failed_only=True to get only failed jobs' logs from a run."""
    return await _ensure_github_actions().get_job_logs(owner, repo, job_id, run_id, failed_only, return_content, tail_lines)
