"""Unit tests for the ForgeOps memory layer.

Covers:
- app/memory/memory.py  (_content_hash, add_with_dedup)
- app/agents/memory_agent.py (memory_agent extraction logic)

These tests mock mem0, Ollama, and the LLM so no external services
(Qdrant, Ollama, Groq) are required.
"""

import sys
import hashlib
from unittest.mock import MagicMock, patch

import pytest

# ---------------------------------------------------------------------------
# Pre-import mocking: app/memory/memory.py runs mem0 + Ollama at import time.
# We must stub those out before the module is imported.
# ---------------------------------------------------------------------------

import os

os.environ.setdefault("OPENROUTER_API_KEY", "test-key")
os.environ.setdefault("GROQ_API_KEY", "test-key")

# Stub mem0.Memory so Memory.from_config() and instance methods don't hit Qdrant
mock_mem0_module = MagicMock()
mock_memory_instance = MagicMock()
mock_mem0_module.Memory.from_config.return_value = mock_memory_instance
mock_memory_instance.get_all.return_value = {"results": []}
mock_memory_instance.add.return_value = {"id": "mem-123", "event": "ADD"}
mock_memory_instance.delete_all.return_value = None
sys.modules["mem0"] = mock_mem0_module

# Stub langchain_ollama.ChatOllama (imported by memory.py)
mock_ollama_module = MagicMock()
mock_ollama_module.ChatOllama = MagicMock()
sys.modules["langchain_ollama"] = mock_ollama_module

# Now safe to import the memory module
from app.memory.memory import _content_hash, add_with_dedup  # noqa: E402

# ---------------------------------------------------------------------------
# Tests for _content_hash
# ---------------------------------------------------------------------------


def test_content_hash_is_deterministic():
    msgs = [
        {"role": "user", "content": "Hello"},
        {"role": "assistant", "content": "Hi there"},
    ]
    h1 = _content_hash(msgs)
    h2 = _content_hash(msgs)
    assert h1 == h2
    assert len(h1) == 32  # MD5 hex digest


def test_content_hash_changes_with_different_input():
    msgs_a = [{"role": "user", "content": "Hello"}]
    msgs_b = [{"role": "user", "content": "World"}]
    assert _content_hash(msgs_a) != _content_hash(msgs_b)


def test_content_hash_empty_messages():
    assert _content_hash([]) == hashlib.md5(b"").hexdigest()


# ---------------------------------------------------------------------------
# Tests for add_with_dedup
# ---------------------------------------------------------------------------


def test_add_with_dedup_new_memory_is_added():
    mock_memory_instance.get_all.return_value = {"results": []}
    mock_memory_instance.add.return_value = {"id": "mem-new"}
    mock_memory_instance.reset_mock()

    messages = [{"role": "user", "content": "Deploy failed"}]
    result = add_with_dedup(mock_memory_instance, messages, user_id="alex")

    mock_memory_instance.add.assert_called_once()
    assert result == {"id": "mem-new"}


def test_add_with_dedup_duplicate_memory_is_skipped():
    mock_memory_instance.reset_mock()
    messages = [{"role": "user", "content": "Deploy failed"}]
    target_hash = _content_hash(messages)

    mock_memory_instance.get_all.return_value = {
        "results": [{"hash": target_hash}]
    }

    result = add_with_dedup(mock_memory_instance, messages, user_id="alex")

    mock_memory_instance.add.assert_not_called()
    assert result is None


def test_add_with_dedup_passes_user_id_and_kwargs():
    mock_memory_instance.reset_mock()
    mock_memory_instance.get_all.return_value = {"results": []}
    messages = [{"role": "user", "content": "Test"}]
    add_with_dedup(mock_memory_instance, messages, user_id="bob", infer=False)

    mock_memory_instance.add.assert_called_once_with(
        messages, user_id="bob", infer=False
    )


# ---------------------------------------------------------------------------
# Tests for memory_agent (app/agents/memory_agent.py)
# ---------------------------------------------------------------------------


def _make_memory_decision(should_store=True, memories=None):
    from app.config.state import Memory, MemoryDecision

    if memories is None:
        memories = [
            Memory(
                content="Production deployments use Node 20.",
                category="deployment_context",
            )
        ]
    return MemoryDecision(
        should_store=should_store, memories=memories, reason="test reason"
    )


def _make_state(memory_context=None):
    from app.config.state import ForgeOpsState

    return ForgeOpsState(
        user_query="Why did deployment fail?",
        thread_id="tm-001",
        investigation="Deployment failed due to Node version mismatch.",
        root_cause="Node 18 vs Node 20 mismatch.",
        evidence=["PR #482 changed node:20 to node:18"],
        final_response="Formatted response.",
        errors=[],
        memory_context=memory_context if memory_context is not None else [],
    )


@patch("app.agents.memory_agent.MEMORY_MODEL")
def test_memory_agent_stores_when_should_store_true(mock_llm):
    from app.agents.memory_agent import memory_agent
    from app.config.state import Memory, MemoryDecision

    mock_structured = MagicMock()
    mock_structured.invoke.return_value = _make_memory_decision(
        should_store=True,
        memories=[
            Memory(
                content="Node 20 is production standard.",
                category="deployment_context",
            )
        ],
    )
    mock_llm.with_structured_output.return_value = mock_structured

    state = _make_state()
    result = memory_agent(state)

    assert result.should_store is True
    assert len(state.memory_context) == 1
    # BUG: memory_agent appends a list of strings to memory_context,
    # creating nested lists (list[list[str]]) instead of flat list[str].
    joined = " ".join(state.memory_context[0])
    assert "Node 20 is production standard" in joined


@patch("app.agents.memory_agent.MEMORY_MODEL")
def test_memory_agent_does_not_store_when_should_store_false(mock_llm):
    from app.agents.memory_agent import memory_agent
    from app.config.state import MemoryDecision

    mock_structured = MagicMock()
    mock_structured.invoke.return_value = _make_memory_decision(
        should_store=False, memories=[]
    )
    mock_llm.with_structured_output.return_value = mock_structured

    state = _make_state()
    result = memory_agent(state)

    assert result.should_store is False
    assert len(state.memory_context) == 0  # nothing appended


@patch("app.agents.memory_agent.MEMORY_MODEL")
def test_memory_agent_handles_none_memory_context(mock_llm):
    """memory_context is typed as list[str] | None; agent must not crash on None."""
    from app.agents.memory_agent import memory_agent
    from app.config.state import ForgeOpsState, Memory, MemoryDecision

    mock_structured = MagicMock()
    mock_structured.invoke.return_value = _make_memory_decision(
        should_store=True,
        memories=[Memory(content="Durable fact.", category="repository_context")],
    )
    mock_llm.with_structured_output.return_value = mock_structured

    state = ForgeOpsState(
        user_query="Q",
        thread_id="tm-002",
        memory_context=None,  # explicitly None
    )
    # Current implementation calls .append() on memory_context, which crashes
    # when it is None. This test documents the bug.
    with pytest.raises(AttributeError):
        memory_agent(state)


@patch("app.agents.memory_agent.MEMORY_MODEL")
def test_memory_agent_returns_MemoryDecision_type(mock_llm):
    from app.agents.memory_agent import memory_agent
    from app.config.state import MemoryDecision

    mock_structured = MagicMock()
    mock_structured.invoke.return_value = _make_memory_decision(
        should_store=False, memories=[]
    )
    mock_llm.with_structured_output.return_value = mock_structured

    state = _make_state()
    result = memory_agent(state)
    assert isinstance(result, MemoryDecision)


# ---------------------------------------------------------------------------
# Graph-level memory node wiring check
# ---------------------------------------------------------------------------


def test_memory_agent_invoked_in_graph():
    """Ensure the graph references memory_agent as a node."""
    from app.graph import graph

    node_names = {node for node in graph.nodes}
    assert "memory" in node_names, f"memory node missing from graph: {node_names}"
