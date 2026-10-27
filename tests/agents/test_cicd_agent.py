from app.mcp.tools.github_actions_tools import init_github_actions
from app.agents.github_ci_agent import ci_cd_agent
from app.agents.github_agent import github_agent
from app.config.state import ForgeOpsState, Finding
import pytest


@pytest.mark.asyncio
async def test_ci_cd_agent():
    await init_github_actions()
    repo = "wassim249/fastapi-langgraph-agent-production-ready-template"
    commit = "62e59a49e5b50003523b11ed01929a661863c594"

    state = ForgeOpsState(
        user_query=(
            f"Investigate CI/CD execution associated with commit "
            f"{commit} in {repo}."
        ),
        thread_id="123",
    )

    # GitHub context
    github_query = (
        f"Inspect commit {commit} in {repo} and summarize the repository "
        "changes relevant to a CI/CD investigation."
    )

    github_finding = await github_agent(
        state,
        github_query,
    )

    assert isinstance(github_finding, Finding)

    # CI/CD context
    cicd_query = f"""
Supervisor task:

Investigate CI/CD execution for commit {commit} in {repo}.

GitHub Agent finding:
{github_finding.model_dump_json(indent=2)}

Determine:

1. Whether any GitHub Actions workflow run is associated with this commit.
2. If a run exists, determine whether it succeeded or failed.
3. If it failed, identify the failed job and step.
4. Retrieve the relevant logs.
5. State the concrete CI/CD failure.
6. Only provide a potential fix when the CI/CD evidence supports it.

STRICT RULES:

- Use only the CI/CD tools provided to you.
- Do not investigate the commit again.
- Do not invoke GitHub repository/PR tools.
- Do not assume a relationship between the commit and an unrelated run.
- If no workflow run is associated with this commit, report that explicitly.
"""

    cicd_finding = await ci_cd_agent(
        state,
        cicd_query,
    )

    assert isinstance(cicd_finding, Finding)

    print("\n===== GITHUB =====")
    print(github_finding.model_dump_json(indent=2))

    print("\n===== CI/CD =====")
    print(cicd_finding.model_dump_json(indent=2))

    assert (
        cicd_finding.evidence
        or cicd_finding.errors
    )


@pytest.mark.asyncio
async def test_ci_cd_agent_run_investigation():
    """Test CI/CD agent investigating a specific workflow run."""
    await init_github_actions()
    state = ForgeOpsState(
        user_query="Investigate GitHub Actions run 32956808292 failure",
        thread_id="cicd-test-001",
    )
    query = (
        "Investigate GitHub Actions workflow run 32956808292 "
        "in wassim249/fastapi-langgraph-agent-production-ready-template. "
        "Retrieve the run status, failed jobs, steps, and logs."
    )
    finding = await ci_cd_agent(state, query)
    assert isinstance(finding, Finding)
    assert finding.summary or finding.errors


# 62e59a49e5b50003523b11ed01929a661863c594
