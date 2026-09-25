from app.agents.github_agent import github_agent
from app.config.state import ForgeOpsState,Finding
import pytest
import pytest_asyncio


@pytest.mark.asyncio
async def test_github_agent():
    sample_state =  ForgeOpsState(
    user_query="I am not able to figure out the error by the latest commit in wassim249/fastapi-langgraph-agent-production-ready-template",thread_id="123")
    query = "What changes in commit db26373460a0f22b170051f5de7fc7dd0ec4f9d2"
    answers = await github_agent(sample_state,query)
    # print(answers)
    assert isinstance(answers,Finding)


# 62e59a49e5b50003523b11ed01929a661863c594