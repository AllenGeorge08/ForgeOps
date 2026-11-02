from app.config.state import ForgeOpsState, Finding, Memory, MemoryDecision
from app.config.config import MEMORY_MODEL
from app.agents.prompts import memory_agent_prompt
import re
import asyncio


async def memory_agent(state: ForgeOpsState):
    user_query = state.user_query
    investigation = state.investigation
    root_cause = state.root_cause
    evidence = state.evidence
    final_response = state.final_response
    errors = state.errors if state.errors else None

    model = MEMORY_MODEL  # Call directly without with_structured_output

    query = (
        f"User Query: {user_query}\n"
        f"Investigation: {investigation}\n"
        f"Root Cause: {root_cause}\n"
        f"Evidence: {evidence}\n"
        f"Final Response: {final_response}\n"
        f"Errors: {errors}"
    )

    messages = [
        ("system", f"{memory_agent_prompt}"),
        ("human", f"{query}")
    ]

    try:
        response = await model.ainvoke(messages)
        result_text = response.content if hasattr(response, 'content') else str(response)
    except Exception as e:
        print(f"Error encountered while calling model: {e}")
        raise e

    # Parse the text response
    should_store = False
    memories = []
    reason = ""

    result_lower = result_text.lower()

    # Check if should_store is true
    if "should_store: true" in result_lower or "should_store:true" in result_lower:
        should_store = True

    # Extract memories - look for content and category pairs
    content_matches = re.findall(
        r'content["\']?\s*:\s*["\']([^"\']+)["\']', result_text
    )
    category_matches = re.findall(
        r'category["\']?\s*:\s*["\']([^"\']+)["\']', result_text
    )

    for i, content in enumerate(content_matches):
        category = category_matches[i] if i < len(category_matches) else "deployment_context"
        memories.append(Memory(content=content, category=category))

    # Extract reason
    reason_match = re.search(
        r'reason["\']?\s*:\s*["\']([^"\']+)["\']', result_text
    )
    if reason_match:
        reason = reason_match.group(1)
    elif should_store:
        reason = "Memory extraction completed."
    else:
        reason = "No memories to store."

    memory_decision = MemoryDecision(
        should_store=should_store,
        memories=memories,
        reason=reason
    )

    return memory_decision