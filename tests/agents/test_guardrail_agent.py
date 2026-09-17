from shlex import join
from datasets import guardrail_dataset

import json 
import time 
import pytest 
from app.guardrails.guardrails import evaluate_user_query

@pytest.mark.parametrize("item",guardrail_dataset)
def test_guardrail_agent(item):
    query = item["user_query"]
    expected = item["expected"]

    response = evaluate_user_query(query)

    assert response.decision == expected["decision"], (
        f"Decision mismatch! Expected {expected['decision']}, got {response.decision}. "
        f"Reason given: {response.reason}"
    )
    assert response.category == expected["category"], (
        f"Category mismatch! Expected {expected['category']}, got {response.category}"
    )
    assert response.reason and len(response.reason) > 0


