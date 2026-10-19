from uuid import uuid4
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, List

from app.config.state import ForgeOpsState, FinalizeAgentResponse
from app.graph import graph

application = FastAPI(title="ForgeOps API", version="1.0.0")


class QueryRequest(BaseModel):
    user_query: str = Field(..., min_length=1, description="User query cannot be empty")
    thread_id: Optional[str] = Field(
        None, description="Optional thread id for conversation continuity"
    )


class GuardrailOutput(BaseModel):
    decision: str
    category: str
    reason: str


class QueryResponse(BaseModel):
    thread_id: str
    status: str
    guardrail: GuardrailOutput
    investigation_plan: str
    selected_agents: List[str]
    final_response: Optional[FinalizeAgentResponse] = None
    errors: List[str] = Field(default_factory=list)


@application.get("/")
def health_check():
    return {"status": "healthy", "service": "forgeops"}


@application.post("/query", response_model=QueryResponse)
async def run_investigation(request: QueryRequest):
    """Accept a user query, run it through the ForgeOps investigation graph,
    and return the finalizer's structured response."""
    thread_id = request.thread_id or str(uuid4())

    initial_state = ForgeOpsState(
        user_query=request.user_query,
        thread_id=thread_id,
    )

    try:
        final_state = await graph.ainvoke(initial_state)
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Investigation failed: {str(e)}"
        )

    # Determine overall status
    if not final_state.guardrail_allowed:
        if final_state.guardrail_category in (
            "out_of_scope",
            "unsupported_action",
            "unsafe",
        ):
            status = "blocked"
        else:
            status = "clarify_needed"
    elif final_state.errors:
        status = "completed_with_errors"
    else:
        status = "completed"

    # Build FinalizeAgentResponse from state fields populated by the graph.
    # Only populated when the investigation actually ran (guardrail allowed).
    final_response = None
    if final_state.guardrail_allowed and (
        final_state.root_cause or final_state.evidence or final_state.investigation
    ):
        recommended_action: List[str] = []
        if final_state.proposed_action:
            pa = final_state.proposed_action
            recommended_action.append(
                f"{pa.action_type}: {pa.reason} (target: {pa.target})"
            )

        final_response = FinalizeAgentResponse(
            summary=final_state.investigation or final_state.final_response or "",
            root_cause=final_state.root_cause,
            evidence=final_state.evidence,
            recommended_action=recommended_action,
            limitations=final_state.errors if final_state.errors else None,
        )

    return QueryResponse(
        thread_id=thread_id,
        status=status,
        guardrail=GuardrailOutput(
            decision="allow" if final_state.guardrail_allowed else "reject",
            category=final_state.guardrail_category,
            reason=final_state.guardrail_reason,
        ),
        investigation_plan=final_state.investigation_plan,
        selected_agents=final_state.selected_agents,
        final_response=final_response,
        errors=final_state.errors,
    )


def main():
    import uvicorn

    uvicorn.run(application, port=8000, host="0.0.0.0")


if __name__ == "__main__":
    main()
