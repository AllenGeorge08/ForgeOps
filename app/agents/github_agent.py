from langchain.agents.structured_output import ToolStrategy
from app.config.state import ForgeOpsState ,Finding
from app.config.config import GITHUB_MODEL
from langchain.agents import create_agent
from app.mcp.tools.github_tools import get_commit,pull_request_read,list_commits,list_branches,search_code,get_file_contents,list_pull_requests,search_commits,search_issues,issue_read, search_pull_requests 
from app.agents.prompts import GITHUB_AGENT_PROMPT
import asyncio 

github_tools = [
    get_commit,
    pull_request_read,
    list_commits,
    list_branches,
    search_code,
    get_file_contents,
    list_pull_requests,
    search_commits,
    search_issues,
    issue_read,
    search_pull_requests,
]

github_llm = GITHUB_MODEL.with_structured_output(Finding)

agent = create_agent(
        model=GITHUB_MODEL,
        tools=github_tools,
        system_prompt=GITHUB_AGENT_PROMPT,
    )

async def github_agent(state: ForgeOpsState,supervisor_query: str):
    result = await agent.ainvoke({
        "messages": [{"role": "user","content": supervisor_query}]
    })
    final_text= result["messages"][-1].content

    final_answer =  await github_llm.ainvoke(f"Convert this investigation output into the Finding schema. Add nothing new.\n\n{final_text}")
    state.github_findings.append(final_answer)
    return final_answer
  
 
 