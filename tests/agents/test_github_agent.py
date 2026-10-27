from app.mcp.tools.github_tools import init_github
from app.agents.github_agent import github_agent
from app.config.state import ForgeOpsState, Finding
import pytest
import pytest_asyncio


@pytest.mark.asyncio
async def test_github_agent():
    await init_github()
    sample_state = ForgeOpsState(
        user_query="I am not able to figure out the error by the latest commit in wassim249/fastapi-langgraph-agent-production-ready-template",
        thread_id="123",
    )
    query = "What changes in commit db26373460a0f22b170051f5de7fc7dd0ec4f9d2"
    answers = await github_agent(sample_state, query)
    assert isinstance(answers, Finding)


@pytest.mark.asyncio
async def test_github_agent_commit_inspection():
    """Test GitHub agent inspecting a specific commit diff."""
    await init_github()
    state = ForgeOpsState(
        user_query="Inspect commit 62e59a49e5b50003523b11ed01929a661863c594 for changes",
        thread_id="gh-test-001",
    )
    query = (
        "Inspect commit 62e59a49e5b50003523b11ed01929a661863c594 "
        "in wassim249/fastapi-langgraph-agent-production-ready-template. "
        "Summarize changed files and the commit message."
    )
    finding = await github_agent(state, query)
    assert isinstance(finding, Finding)
    assert finding.summary or finding.errors


@pytest.mark.asyncio
async def test_github_agent_pr_inspection():
    """Test GitHub agent reading a pull request."""
    await init_github()
    state = ForgeOpsState(
        user_query="Read PR #1 details in the repo",
        thread_id="gh-test-002",
    )
    query = "Read pull request #1 in wassim249/fastapi-langgraph-agent-production-ready-template including diff and files changed"
    finding = await github_agent(state, query)
    assert isinstance(finding, Finding)
    assert finding.summary or finding.errors


# 62e59a49e5b50003523b11ed01929a661863c594
