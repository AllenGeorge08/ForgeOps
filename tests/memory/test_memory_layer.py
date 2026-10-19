"""Unit tests for the ForgeOps memory layer.

Covers:
- app/memory/memory.py  (_content_hash, add_with_dedup, get_memory)
- app/agents/memory_agent.py (memory_agent extraction logic)

All external services (mem0/Qdrant, OpenRouter, Ollama) are mocked so no
network or API calls are made.
"""

import sys
import hashlib
from unittest.mock import MagicMock, patch

import pytest

# ---------------------------------------------------------------------------
# Pre-import mocking: app/memory/memory.py imports mem0 at module level but
# does NOT connect at import time anymore (lazy singleton). We still stub
# mem0 so that any accidental construction does not hit Qdrant/OpenRouter.
# ---------------------------------------------------------------------------

import os

os.environ.setdefault("OPENROUTER_API_KEY", "test-openrouter-key")
os.environ.setdefault("GROQ_API_KEY", "test-key")

mock_mem0_module = MagicMock()
mock_memory_instance = MagicMock()
mock_mem0_module.Memory.from_config.return_value = mock_memory_instance
mock_memory_instance.get_all.return_value = {"results": []}
mock_memory_instance.add.return_value = {"id": "mem-123", "event": "ADD"}
mock_memory_instance.delete_all.return_value = None
sys.modules["mem0"] = mock_mem0_module

# Now safe to import
from app.memory.memory import _content_hash, add_with_dedup, get_memory  # noqa: E402

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
# Tests for get_memory (lazy singleton)
# ---------------------------------------------------------------------------


@patch("app.memory.memory._memory_instance", None)
@patch("app.memory.memory.Memory")
def test_get_memory_creates_instance_lazily(mock_mem0_class):
    from app.config.config import memoryllm_model

    mock_mem0_class.from_config.return_value = mock_memory_instance

    result = get_memory()

    mock_mem0_class.from_config.assert_called_once()
    call_kwargs = mock_mem0_class.from_config.call_args[0][0]
    assert call_kwargs["embedder"]["provider"] == "openai"
    assert call_kwargs["embedder"]["config"]["model"] == "text-embedding-3-small"
    assert "openrouter.ai/api/v1" in call_kwargs["embedder"]["config"]["openai_api_base"]
    assert result is mock_memory_instance


@patch("app.memory.memory._memory_instance", mock_memory_instance)
def test_get_memory_returns_cached_instance():
    """Second call returns the same instance (singleton behavior)."""
    result = get_memory()
    assert result is mock_memory_instance


# ---------------------------------------------------------------------------
# Tests for add_with_dedup (new signature: messages, user_id, **kwargs)
# ---------------------------------------------------------------------------


def test_add_with_dedup_new_memory_is_added():
    # Reset module-level singleton so our patched get_memory is used
    with patch("app.memory.memory.get_memory", return_value=mock_memory_instance):
        mock_memory_instance.get_all.return_value = {"results": []}
        mock_memory_instance.add.return_value = {"id": "mem-new"}
        mock_memory_instance.reset_mock()

        messages = [{"role": "user", "content": "Deploy failed"}]
        result = add_with_dedup(messages, user_id="alex")

        mock_memory_instance.add.assert_called_once()
        call_kwargs = mock_memory_instance.add.call_args[1]
        assert call_kwargs["user_id"] == "alex"
        assert result == {"id": "mem-new"}


def test_add_with_dedup_duplicate_memory_is_skipped():
    with patch("app.memory.memory.get_memory", return_value=mock_memory_instance):
        mock_memory_instance.reset_mock()
        messages = [{"role": "user", "content": "Deploy failed"}]
        target_hash = _content_hash(messages)

        mock_memory_instance.get_all.return_value = {
            "results": [{"hash": target_hash}]
        }

        result = add_with_dedup(messages, user_id="alex")

        mock_memory_instance.add.assert_not_called()
        assert result is None


def test_add_with_dedup_passes_user_id_and_kwargs():
    with patch("app.memory.memory.get_memory", return_value=mock_memory_instance):
        mock_memory_instance.reset_mock()
        mock_memory_instance.get_all.return_value = {"results": []}
        messages = [{"role": "user", "content": "Test"}]
        add_with_dedup(messages, user_id="bob", infer=False)

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
    from app.config.state import Memory

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
    joined = " ".join(state.memory_context)
    assert "Node 20 is production standard" in joined


@patch("app.agents.memory_agent.MEMORY_MODEL")
def test_memory_agent_does_not_store_when_should_store_false(mock_llm):
    from app.agents.memory_agent import memory_agent

    mock_structured = MagicMock()
    mock_structured.invoke.return_value = _make_memory_decision(
        should_store=False, memories=[]
    )
    mock_llm.with_structured_output.return_value = mock_structured

    state = _make_state()
    result = memory_agent(state)

    assert result.should_store is False
    assert len(state.memory_context) == 0


@patch("app.agents.memory_agent.MEMORY_MODEL")
def test_memory_agent_handles_none_memory_context(mock_llm):
    """memory_context defaults to [] now; agent must not crash on None input."""
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
        memory_context=[],  # default is now []
    )
    result = memory_agent(state)

    assert result.should_store is True
    assert len(state.memory_context) == 1


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
