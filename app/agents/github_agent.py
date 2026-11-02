from app.config.state import ForgeOpsState, Finding
from app.mcp.tools.github_tools import (
    get_commit,
    pull_request_read,
    list_commits,
    list_branches,
    search_code,
    get_file_contents,
    list_pull_requests,
    search_commits,
    search_issues,
    issue_read,
    search_pull_requests,
)
import re


async def github_agent(state: ForgeOpsState, supervisor_query: str):
    """Investigate GitHub repository evidence using direct MCP tool calls.

    Extracts owner/repo from the supervisor_query, then calls GitHub MCP tools
    directly with the extracted identifiers.
    """

    owner = None
    repo = None
    commit_sha = None
    pr_number = None

    # --- Extract owner/repo from supervisor_query ---
    repo_match = re.search(r'([A-Za-z0-9_.-]+)/([A-Za-z0-9_.-]+)', supervisor_query)
    if repo_match:
        owner = repo_match.group(1)
        repo = repo_match.group(2)

    # Extract commit SHA (40 hex chars or shortened 7+ hex)
    sha_match = re.search(r'\b([0-9a-f]{7,40})\b', supervisor_query, re.IGNORECASE)
    if sha_match:
        commit_sha = sha_match.group(1)

    # Extract PR number
    pr_match = re.search(r'PR\s*#?(\d+)', supervisor_query, re.IGNORECASE)
    if pr_match:
        pr_number = int(pr_match.group(1))

    # Extract run ID
    run_match = re.search(r'run\s*(?:#)?(\d+)', supervisor_query, re.IGNORECASE)
    run_id = None
    if run_match:
        run_id = int(run_match.group(1))

    if not owner or not repo:
        err = "GitHub Agent: No repository owner/repo found in query."
        state.errors.append(err)
        state.github_findings.append(Finding(
            summary="GitHub investigation failed - no repository specified",
            evidence=[],
            source_refs=[],
            errors=[err]
        ))
        return state.github_findings[-1]

    evidence = []
    errors = []

    # --- Step 1: Get latest commit if no SHA provided ---
    if not commit_sha:
        try:
            commits_result = await list_commits.ainvoke({
                "owner": owner,
                "repo_name": repo
            })
            if commits_result and isinstance(commits_result, dict):
                commits = commits_result.get("commits", [])
                if commits and len(commits) > 0:
                    commit_sha = commits[0].get("sha")
                    evidence.append(f"Latest commit: {commit_sha[:8]}...")
        except Exception as e:
            errors.append(f"list_commits failed: {str(e)}")

    # --- Step 2: Get commit details ---
    if commit_sha:
        try:
            commit_result = await get_commit.ainvoke({
                "owner": owner,
                "repo_name": repo,
                "sha": commit_sha
            })
            if commit_result:
                evidence.append(
                    f"Commit {commit_sha[:8]}: {commit_result.get('message', 'no message')}"
                )
                evidence.append(f"Author: {commit_result.get('author', {}).get('name', 'unknown')}")
                evidence.append(f"Files changed: {len(commit_result.get('files', []))}")
                for f in commit_result.get('files', []):
                    evidence.append(
                        f"  - {f.get('filename')}: {f.get('status')} "
                        f"({f.get('additions', 0)}+, {f.get('deletions', 0)}-)"
                    )
        except Exception as e:
            errors.append(f"get_commit failed: {str(e)}")

    # --- Step 3: Get PR details if PR number available ---
    if pr_number:
        try:
            pr_result = await pull_request_read.ainvoke({
                "action": "get",
                "owner": owner,
                "repo_name": repo,
                "pullNumber": pr_number
            })
            if pr_result:
                evidence.append(f"PR #{pr_number}: {pr_result.get('title', 'no title')}")
                evidence.append(f"PR state: {pr_result.get('state', 'unknown')}")
                evidence.append(f"PR body: {pr_result.get('body', 'no body')[:200]}")
                for f in pr_result.get('files', []):
                    evidence.append(
                        f"  File: {f.get('filename')}: {f.get('status')} "
                        f"({f.get('additions', 0)}+, {f.get('deletions', 0)}-)"
                    )
        except Exception as e:
            errors.append(f"pull_request_read failed: {str(e)}")

    finding = Finding(
        summary=f"GitHub investigation of {owner}/{repo}",
        evidence=evidence if evidence else ["No data retrieved from GitHub MCP"],
        source_refs=[f"{owner}/{repo}", f"commit {commit_sha}" if commit_sha else ""],
        errors=errors if errors else []
    )

    state.github_findings.append(finding)
    return {"github_findings": state.github_findings, "errors": state.errors}