from datasets import guardrail_dataset
from app.config.state import ForgeOpsState
import pytest 
from app.guardrails.guardrails import evaluate_user_query

@pytest.mark.parametrize("item",guardrail_dataset)
def test_guardrail_agent(item):
    query = item["user_query"]
    expected = item["expected"]

    state = ForgeOpsState(user_query=query,thread_id="Test Thread")

    response = evaluate_user_query(state)

    assert response.decision == expected["decision"], (
        f"Decision mismatch! Expected {expected['decision']}, got {response.decision}. "
        f"Reason given: {response.reason}"
    )
    assert response.category == expected["category"], (
        f"Category mismatch! Expected {expected['category']}, got {response.category}"
    )
    assert response.reason and len(response.reason) > 0


