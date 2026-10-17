from app.config.state import ForgeOpsState, SupervisorDecision
from app.config.config import SUPERVISOR_MODEL
from app.agents.prompts import SUPERVISOR_PROMPT

structured_llm = SUPERVISOR_MODEL.with_structured_output(SupervisorDecision)


async def supervisor_agent(state: ForgeOpsState) -> dict:
    """Triage the guardrail-vetted query and route to specialist agents.

    Reads the guardrail verdict from state, decides which agents to invoke,
    writes per-agent queries, and returns a state update dict.
    """

    # Guardrail blocked the request: do not route to any agent.
    if not state.guardrail_allowed:
        return {
            "selected_agents": [],
            "agent_queries": {},
            "investigation_plan": (
                f"Blocked by input guardrail: {state.guardrail_reason}"
            ),
        }

    query = (
        f"User Query: {state.user_query}\n"
        f"Guardrail Category: {state.guardrail_category}\n"
        f"Guardrail Reason: {state.guardrail_reason}\n"
        f"Memory Context: {state.memory_context}"
    )

    result: SupervisorDecision = await structured_llm.ainvoke(
        [
            ("system", SUPERVISOR_PROMPT),
            ("human", query),
        ]
    )

    return {
        "selected_agents": result.selected_agents,
        "agent_queries": result.agent_queries,
        "investigation_plan": result.investigation_plan,
    }
