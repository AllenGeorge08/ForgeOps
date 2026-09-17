from pydantic import BaseModel,Field 
from typing import Any,Literal

class GuardrailDecision(BaseModel):
    decision: Literal["allow", "reject", "clarify"]
    category: Literal[
        "github",
        "slack",
        "ci_cd",
        "cross_source_investigation",
        "general_engineering",
        "out_of_scope",
        "unsupported_action",
        "ambiguous",
        "unsafe",
    ]

    reason: str


class QueryRequest(BaseModel):
    user_query: str = Field(gt=0,description="User query cannot be empty")
    thread_id : int = Field(gt=0,description="The thread id cannot be empty")

class Finding(BaseModel):
    summary: str= ""
    evidence: list[str] = Field(default_factory=list)
    source_refs: list[str] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)


class ProposedAction(BaseModel):
    action_type: str = ""
    target: str = ""
    reason: str = ""
    parameters: dict[str,Any] = Field(default_factory=dict)


class ForgeOpsState(BaseModel):
    user_query: str
    thread_id: str  

    guardrail_allowed: bool = False
    guardrail_reason: str = ""
    guardrail_category: str = ""

    selected_agents: list[str] = Field(default_factory=list)
    investigation_plan: str= ""

    github_findings: list[Finding] = Field(default_factory=list)
    slack_findings: list[Finding] = Field(default_factory=list)
    ci_cd_findings: list[Finding] = Field(default_factory=list)

    investigation: str = ""
    root_cause: str  = ""
    evidence: list[str] = Field(default_factory=list)


    proposed_action: ProposedAction | None = None
    human_approved: bool = False
    human_feedback: str = ""

    final_response: str = ""
    errors: list[str]  = Field(default_factory=list)
    memory_context: list[str] = Field(default_factory=list)




