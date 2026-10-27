"""ForgeOps LangGraph wiring.

Wires the guardrail, supervisor, specialist agents, investigation,
finalizer, and memory into a single StateGraph over ForgeOpsState.

Usage:
    from app.graph import graph
    result = await graph.ainitial_state(...)   # or astream / invoke
"""

from typing import Literal

from langgraph.graph import StateGraph, END

from app.config.state import ForgeOpsState
from app.guardrails.guardrails import evaluate_user_query
from app.agents.supervisor_agent import supervisor_agent
from app.agents.github_agent import github_agent
from app.agents.github_ci_agent import ci_cd_agent
from app.agents.slack_agent import slack_agent
from app.agents.investigation_agent import investigation_agent
from app.agents.finalizer_agent import finalize_agent
from app.agents.memory_agent import memory_agent


def guardrail_node(state: ForgeOpsState) -> dict:
    """Run the input guardrail and map its verdict onto ForgeOpsState."""
    decision = evaluate_user_query(state)
    return {
        "guardrail_allowed": decision.decision == "allow",
        "guardrail_reason": decision.reason,
        "guardrail_category": decision.category,
    }


async def dispatch_node(state: ForgeOpsState) -> dict:
    """Invoke the specialist agents selected by the supervisor.

    Agents run sequentially (github -> cicd -> slack). If one agent fails,
    the error is recorded in state.errors and the next agent still runs.
    """
    for agent_name in state.selected_agents:
        query = state.agent_queries.get(agent_name, state.user_query)
        try:
            if agent_name == "github":
                await github_agent(state, query)
            elif agent_name == "cicd":
                await ci_cd_agent(state, query)
            elif agent_name == "slack":
                await slack_agent(state, query)
        except Exception as e:
            state.errors.append(f"{agent_name} agent failed: {str(e)}")
    return {}


def after_guardrail(state: ForgeOpsState) -> Literal["supervisor", END]:
    if state.guardrail_allowed:
        return "supervisor"
    return END


workflow = StateGraph(ForgeOpsState)

# Nodes
workflow.add_node("guardrail", guardrail_node)
workflow.add_node("supervisor", supervisor_agent)
workflow.add_node("dispatch", dispatch_node)
workflow.add_node("investigation", investigation_agent)
workflow.add_node("finalizer", finalize_agent)
workflow.add_node("memory", memory_agent)

# Entry point
workflow.set_entry_point("guardrail")

# Guardrail branches: allowed -> supervisor, otherwise halt
workflow.add_conditional_edges(
    "guardrail",
    after_guardrail,
    {"supervisor": "supervisor", END: END},
)

# Supervisor dispatches to selected specialists
workflow.add_edge("supervisor", "dispatch")

# Specialists -> correlation -> presentation -> memory -> end
workflow.add_edge("dispatch", "investigation")
workflow.add_edge("investigation", "finalizer")
workflow.add_edge("finalizer", "memory")
workflow.add_edge("memory", END)

graph = workflow.compile()

__all__ = ["graph"]
