from pydantic import BaseModel,Field 
from typing import Any,Literal

class Memory(BaseModel):
    content: str
    category: Literal[
        "engineering_environment",
        "repository_context",
        "deployment_context",
        "team_context",
        "user_preference",
    ]


class MemoryDecision(BaseModel):
    should_store: bool
    memories: list[Memory] = Field(default_factory=list)
    reason: str


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

#  Let's check format: Summary, Root Cause, Evidence, Recommended Action
class FinalizeAgentResponse(BaseModel):
    summary: str 
    root_cause: str 
    evidence: list[str]
    recommended_action: list[str]
    limitations: list[str] | None=None 


class QueryRequest(BaseModel):
    user_query: str = Field(gt=0,description="User query cannot be empty")
    thread_id : int = Field(gt=0,description="The thread id cannot be empty")

class Finding(BaseModel):
    summary: str= Field(description="Concise statement of what the evidence establishes")
    evidence: list[str] = Field(default_factory=list,description="Concrete observations retrieved from Github")
    source_refs: list[str] = Field(default_factory=list,description="e.g 'PR #482,commit b8eafed, Dockerfile")
    errors: list[str] | None = Field(default_factory=list,description="Tool failures or unavailable info")


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

    final_response: str = ""
    errors: list[str]  = Field(default_factory=list)
    memory_context: list[str]| None = None 




