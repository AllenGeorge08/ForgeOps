from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient

from app.api.app import application
from app.config.state import ForgeOpsState, FinalizeAgentResponse, ProposedAction


def _fake_state(guardrail_allowed: bool = True) -> ForgeOpsState:
    state = ForgeOpsState(
        user_query="Why did deployment #821 fail?",
        thread_id="test-thread-001",
        guardrail_allowed=guardrail_allowed,
        guardrail_reason="Valid CI/CD investigation.",
        guardrail_category="ci_cd",
        selected_agents=["cicd"],
        agent_queries={"cicd": "Retrieve job logs for run #821."},
        investigation_plan="Inspect deployment run #821 logs.",
        ci_cd_findings=[],
        investigation="Deployment #821 failed during npm ci.",
        root_cause="Node version mismatch between Dockerfile and CI config.",
        evidence=["Run #821 failed during npm ci", "Dockerfile uses node:18"],
        proposed_action=ProposedAction(
            action_type="update_configuration",
            target="Dockerfile",
            reason="Restore Node 20 compatibility.",
            parameters={"current_version": "18", "expected_version": "20"},
        ),
        final_response="Formatted final response string.",
        errors=[],
    )
    return state


def test_health_check():
    client = TestClient(application)
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "forgeops"


def test_query_endpoint_success():
    fake_state = _fake_state(guardrail_allowed=True)

    with patch("app.api.app.graph.ainvoke", new=AsyncMock(return_value=fake_state)):
        client = TestClient(application)
        response = client.post(
            "/query",
            json={"user_query": "Why did deployment #821 fail?", "thread_id": "test-thread-001"},
        )

    assert response.status_code == 200
    data = response.json()
    assert data["thread_id"] == "test-thread-001"
    assert data["status"] == "completed"
    assert data["guardrail"]["decision"] == "allow"
    assert data["guardrail"]["category"] == "ci_cd"
    assert data["guardrail"]["reason"] == "Valid CI/CD investigation."
    assert data["investigation_plan"] == "Inspect deployment run #821 logs."
    assert data["selected_agents"] == ["cicd"]
    assert data["errors"] == []

    fr = data["final_response"]
    assert fr is not None
    assert fr["root_cause"] == "Node version mismatch between Dockerfile and CI config."
    assert fr["evidence"] == ["Run #821 failed during npm ci", "Dockerfile uses node:18"]
    assert "update_configuration" in fr["recommended_action"][0]
    assert fr["limitations"] is None


def test_query_endpoint_blocked():
    fake_state = _fake_state(guardrail_allowed=False)
    fake_state.guardrail_category = "out_of_scope"
    fake_state.guardrail_reason = "Unrelated request."

    with patch("app.api.app.graph.ainvoke", new=AsyncMock(return_value=fake_state)):
        client = TestClient(application)
        response = client.post("/query", json={"user_query": "What's the weather?"})

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "blocked"
    assert data["guardrail"]["decision"] == "reject"
    assert data["final_response"] is None


def test_query_endpoint_missing_thread_id_generates_one():
    fake_state = _fake_state(guardrail_allowed=True)

    with patch("app.api.app.graph.ainvoke", new=AsyncMock(return_value=fake_state)):
        client = TestClient(application)
        response = client.post("/query", json={"user_query": "Hello"})

    assert response.status_code == 200
    data = response.json()
    assert data["thread_id"] is not None
    assert len(data["thread_id"]) > 0


def test_query_endpoint_graph_error():
    with patch(
        "app.api.app.graph.ainvoke",
        new=AsyncMock(side_effect=Exception("boom")),
    ):
        client = TestClient(application)
        response = client.post("/query", json={"user_query": "Hello"})

    assert response.status_code == 500
