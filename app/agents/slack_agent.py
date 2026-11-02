from app.config.state import ForgeOpsState,Finding
from app.config.config import SLACK_MODEL
from app.mcp.tools.slack_tools import slack_list_channels,get_channel_history,get_thread_replies,get_users
from langchain.agents import create_agent
from app.agents.prompts import SLACK_AGENT_PROMPT
from langchain_core.prompts import PromptTemplate
import asyncio 

slack_tools = [
    slack_list_channels,
    get_channel_history,
    get_thread_replies,
    get_users
]

slack_llm = SLACK_MODEL.with_structured_output(Finding)

agent = create_agent(
        model=SLACK_MODEL,
        tools=slack_tools,
        system_prompt=SLACK_AGENT_PROMPT,
        ).with_retry(stop_after_attempt=3)


async def slack_agent(state: ForgeOpsState,supervisor_query: str) -> Finding:
   try:
       result = await agent.ainvoke({
        "messages": [{"role": "user","content": supervisor_query}]
        })
       final_text= result["messages"][-1].content

       final_answer =  await slack_llm.ainvoke(f"Convert this investigation output into the Finding schema. Add nothing new.\n\n{final_text}")
        #what if an error shows up and there's no structured repone
       state.slack_findings.append(final_answer)
       print(f"DEBUG slack_agent: final_answer.summary={final_answer.summary}")
       print(f"DEBUG slack_agent: final_answer.evidence={final_answer.evidence}")
       print(f"DEBUG slack_agent: final_answer.source_refs={final_answer.source_refs}")
       print(f"DEBUG slack_agent: final_answer.errors={final_answer.errors}")
       return {"slack_findings": state.slack_findings, "errors": state.errors}
   except Exception as e:
        print(f"Ran into an error : {e}")
        raise e 
