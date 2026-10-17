import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, patch

from app.config.state import ForgeOpsState, SupervisorDecision
from app.agents import supervisor_agent as supervisor_module


@pytest.fixture
def allowed_state():
    return ForgeOpsState(
        user_query="Why did deployment #821 fail after PR #482?",
        thread_id="test-1",
        guardrail_allowed=True,
        guardrail_reason="Valid GitHub and CI/CD investigation.",
        guardrail_category="cross_source_investigation",
    )


@pytest.fixture
def blocked_state():
    return ForgeOpsState(
        user_query="What's the weather in Delhi?",
        thread_id="test-2",
        guardrail_allowed=False,
        guardrail_reason="Unrelated to ForgeOps capabilities.",
        guardrail_category="out_of_scope",
    )


@pytest.mark.asyncio
async def test_supervisor_blocks_when_guardrail_rejects(blocked_state):
    result = await supervisor_module.supervisor_agent(blocked_state)

    assert result["selected_agents"] == []
    assert result["agent_queries"] == {}
    assert "Blocked by input guardrail" in result["investigation_plan"]


@pytest.mark.asyncio
async def test_supervisor_routes_cross_source(allowed_state):
    expected = SupervisorDecision(
        selected_agents=["github", "cicd", "slack"],
        investigation_plan="Inspect PR #482, deployment run #821, and Slack discussion.",
        agent_queries={
            "github": "Inspect PR #482 diff and changed files.",
            "cicd": "Investigate deployment run #821 failure and job logs.",
            "slack": "Search Slack for deployment #821 discussion.",
        },
        reasoning="Cross-source investigation requires GitHub, CI/CD, and Slack evidence.",
    )

    with patch.object(
        supervisor_module, "structured_llm"
    ) as mock_llm:
        mock_llm.ainvoke = AsyncMock(return_value=expected)
        result = await supervisor_module.supervisor_agent(allowed_state)

    assert result["selected_agents"] == ["github", "cicd", "slack"]
    assert result["agent_queries"]["github"] == "Inspect PR #482 diff and changed files."
    assert result["agent_queries"]["cicd"] == "Investigate deployment run #821 failure and job logs."
    assert result["agent_queries"]["slack"] == "Search Slack for deployment #821 discussion."
    assert "Inspect PR #482" in result["investigation_plan"]


@pytest.mark.asyncio
async def test_supervisor_routes_github_only():
    state = ForgeOpsState(
        user_query="Summarize PR #482.",
        thread_id="test-3",
        guardrail_allowed=True,
        guardrail_reason="Valid GitHub investigation.",
        guardrail_category="github",
    )

    expected = SupervisorDecision(
        selected_agents=["github"],
        investigation_plan="Inspect PR #482 metadata and diff.",
        agent_queries={"github": "Inspect PR #482 metadata and changed files."},
        reasoning="Single-source GitHub investigation.",
    )

    with patch.object(supervisor_module, "structured_llm") as mock_llm:
        mock_llm.ainvoke = AsyncMock(return_value=expected)
        result = await supervisor_module.supervisor_agent(state)

    assert result["selected_agents"] == ["github"]
    assert len(result["selected_agents"]) == 1


@pytest.mark.asyncio
async def test_supervisor_routes_ci_cd_only():
    state = ForgeOpsState(
        user_query="Why did GitHub Actions run #821 fail?",
        thread_id="test-4",
        guardrail_allowed=True,
        guardrail_reason="Valid CI/CD investigation.",
        guardrail_category="ci_cd",
    )

    expected = SupervisorDecision(
        selected_agents=["cicd"],
        investigation_plan="Inspect deployment run #821 logs and failed job.",
        agent_queries={"cicd": "Retrieve job logs for run #821."},
        reasoning="Single-source CI/CD investigation.",
    )

    with patch.object(supervisor_module, "structured_llm") as mock_llm:
        mock_llm.ainvoke = AsyncMock(return_value=expected)
        result = await supervisor_module.supervisor_agent(state)

    assert result["selected_agents"] == ["cicd"]
    assert result["agent_queries"]["cicd"] == "Retrieve job logs for run #821."


@pytest.mark.asyncio
async def test_supervisor_routes_slack_only():
    state = ForgeOpsState(
        user_query="Find Slack discussion about the production outage.",
        thread_id="test-5",
        guardrail_allowed=True,
        guardrail_reason="Valid Slack investigation.",
        guardrail_category="slack",
    )

    expected = SupervisorDecision(
        selected_agents=["slack"],
        investigation_plan="Search Slack channels for outage discussion.",
        agent_queries={"slack": "Inspect #incident-response channel history."},
        reasoning="Single-source Slack investigation.",
    )

    with patch.object(supervisor_module, "structured_llm") as mock_llm:
        mock_llm.ainvoke = AsyncMock(return_value=expected)
        result = await supervisor_module.supervisor_agent(state)

    assert result["selected_agents"] == ["slack"]
    assert result["agent_queries"]["slack"] == "Inspect #incident-response channel history."


def test_graph_compiles():
    from app.graph import graph

    node_names = {node for node in graph.nodes}
    expected_nodes = {
        "__start__",
        "guardrail",
        "supervisor",
        "dispatch",
        "investigation",
        "finalizer",
        "memory",
    }
    assert expected_nodes.issubset(node_names), f"Missing nodes: {expected_nodes - node_names}"
