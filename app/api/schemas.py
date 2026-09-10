
from typing import TypedDict


class ForgeOps(TypedDict):
    user_query: str 
    thread_id: str 

    selected_agents: list[str]
    investigation_plan: str 

    github_findings: list[dict]
    slack_findings: list[dict]
    cicd_findings: list[dict]

    investigation: str 
    root_cause: str 

    proposed_action: dict 
    human_approved: bool 
    human_feedback: str 

    final_response: str 


    