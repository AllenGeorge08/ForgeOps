from app.config.state import ForgeOpsState,MemoryDecision
from app.config.config import MEMORY_MODEL
from app.agents.prompts import memory_agent_prompt
import asyncio

def memory_agent(state: ForgeOpsState):
    user_query = state.user_query
    investigation = state.investigation
    root_cause = state.root_cause
    evidence = state.evidence
    final_response= state.final_response
    errors = state.errors if state.errors else None 


    structured_model = MEMORY_MODEL.with_structured_output(MemoryDecision)

    query = f"User Query: {user_query}" + f"Investigation: {investigation}" + f"Root Cause: {root_cause}" + f"Evidence : {evidence}" + f"Final Response: {final_response}" + f"Errors: {errors}"

    messages=[
        ("system",f"{memory_agent_prompt}"),
        ("human",f"{query}")
    ]

    try:
        result = structured_model.invoke(
        messages
        )
    except  Exception as e:
        print(f"Error encountered while calling model :{e}")
        raise e 

    should_store = result.should_store

    if should_store:
        memory_strings = [f"Context: {memory.content} Category: {memory.category}"    for memory in result.memories]
        state.memory_context.append(memory_strings)
        
    # store the category in mem0
    return result 



# Working

# test_state = ForgeOpsState(
#     user_query="Why did deployment #821 fail after PR #482?",
#     thread_id="test-memory-001",

#     # Investigation
#     investigation=(
#         "Deployment #821 failed during dependency installation after "
#         "PR #482 changed the Docker base image from Node 20 to Node 18. "
#         "The production deployment environment expects Node 20. "
#         "The deploy-prod GitHub Actions workflow is used for production "
#         "deployments."
#     ),

#     root_cause=(
#         "PR #482 changed the Docker base image from Node 20 to Node 18, "
#         "creating a Node.js version mismatch with the production environment."
#     ),

#     evidence=[
#         "PR #482 changed the Docker base image from node:20 to node:18.",
#         "Deployment #821 failed during npm ci.",
#         "The failed build was running Node 18.",
#         "The production environment expects Node 20.",
#         "Production deployments use the deploy-prod GitHub Actions workflow.",
#     ],

#     final_response=(
#         "## Summary\n\n"
#         "Deployment #821 failed during dependency installation because "
#         "PR #482 changed the Docker base image to Node 18 while production "
#         "requires Node 20.\n\n"
#         "## Root Cause\n\n"
#         "The Node.js version mismatch caused the deployment failure.\n\n"
#         "## Evidence\n\n"
#         "- PR #482 changed node:20 to node:18.\n"
#         "- Deployment #821 failed during npm ci.\n"
#         "- Production expects Node 20.\n\n"
#         "## Recommended Action\n\n"
#         "Restore Node 20 and rerun the deployment."
#     ),

#     errors=[],

#     # Not relevant to extraction, but represents the complete state.
#     memory_context=[],
# )
# result = memory_agent(test_state)

# print(test_state.memory_context)