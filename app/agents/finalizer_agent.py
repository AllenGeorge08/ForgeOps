from app.config.state import ForgeOpsState,GuardrailDecision,Finding,ProposedAction,FinalizeAgentResponse
from app.config.config import FINAL_MODEL
from app.agents.prompts import finalizer_agent_prompt
import asyncio

async def finalize_agent(state: ForgeOpsState):
    investigation = state.investigation 
    root_cause= state.root_cause 
    evidence = state.evidence 
    proposed_action = state.proposed_action 
    user_query = state.user_query
    errors = state.errors

    query = f"User Query: {user_query}" + f"Investigation: {investigation}" + f"Root Cause: {root_cause}" + f"Evidence: {evidence}" + f"Proposed Action: {proposed_action}" + f"Errors: {errors}"
    
    structured_model = FINAL_MODEL.with_structured_output(FinalizeAgentResponse)

    messages = [
        ("system",f"{finalizer_agent_prompt}"),
        ("human",f"{query}")
    ]

    try:
         result = await structured_model.ainvoke(
             messages
        )
    except  Exception as e:
        print(f"Error encountered while calling model :{e}")
        raise e 

    query_formed = f"Summary : {result.summary} , Root Cause: {result.root_cause} , evidence: {result.evidence}, recommended_action: {result.recommended_action}"
    final_query = query_formed + f"Limitations: {result.limitations}" if result.limitations else query_formed
    state.final_response = final_query

    return result


# Working
# test_state = ForgeOpsState(
#     user_query="Why did deployment #821 fail after PR #482?",
#     thread_id="test-thread-001",

#     # Guardrail
#     guardrail_allowed=True,
#     guardrail_reason="The request concerns a CI/CD deployment failure.",
#     guardrail_category="cross_source_investigation",

#     # Planning
#     selected_agents=["github", "cicd", "slack"],
#     investigation_plan=(
#         "Inspect PR #482, examine deployment run #821 and its logs, "
#         "and check Slack for related deployment discussions."
#     ),

#     # Evidence
#     github_findings=[
#         Finding(
#             summary="PR #482 changed the Docker base image.",
#             evidence=[
#                 "Dockerfile changed from node:20 to node:18."
#             ],
#             source_refs=[
#                 "PR #482"
#             ],
#         )
#     ],

#     slack_findings=[
#         Finding(
#             summary="Engineers discussed Node version compatibility.",
#             evidence=[
#                 "A Slack thread reported Node 20 as the expected production version."
#             ],
#             source_refs=[
#                 "#backend thread 173921"
#             ],
#         )
#     ],

#     ci_cd_findings=[
#         Finding(
#             summary="Deployment #821 failed during dependency installation.",
#             evidence=[
#                 "GitHub Actions deployment #821 failed during npm ci.",
#                 "The build environment was using Node 18."
#             ],
#             source_refs=[
#                 "workflow run #821",
#                 "build job"
#             ],
#         )
#     ],

#     # Investigation
#     investigation=(
#         "The deployment failure is consistent with a Node.js version "
#         "mismatch introduced by PR #482. The PR changed the Docker image "
#         "from Node 20 to Node 18, while the production environment expects "
#         "Node 20. The deployment subsequently failed during dependency "
#         "installation."
#     ),

#     root_cause=(
#         "PR #482 changed the Docker base image from Node 20 to Node 18, "
#         "creating a Node.js version mismatch with the production "
#         "environment."
#     ),

#     evidence=[
#         "PR #482 changed the Docker base image from node:20 to node:18.",
#         "Deployment #821 failed during npm ci.",
#         "The failed build was running Node 18.",
#         "Slack discussion indicates that production expects Node 20.",
#     ],

#     # Proposed action
#     proposed_action=ProposedAction(
#         action_type="update_configuration",
#         target="Dockerfile",
#         reason="Restore the Node.js version expected by production.",
#         parameters={
#             "current_version": "18",
#             "expected_version": "20",
#         },
#     ),

#     # Output
#     final_response="",

#     # Execution
#     errors=[],

#     # Memory isn't particularly relevant to finalization,
#     # but included to represent the complete state.
#     memory_context=[
#         "Production deployments use the deploy-prod workflow.",
#         "The production environment currently expects Node 20."
#     ],
# )    

# result = asyncio.run(finalize_agent(test_state))
# print(result)