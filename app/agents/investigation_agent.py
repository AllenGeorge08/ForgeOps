import asyncio
from math import e
from langchain.agents import create_agent
from app.config.state import Finding, ForgeOpsState,InvestigationResponse
from app.config.config import INVESTIGATION_MODEL
from app.agents.prompts import INVESTIGATION_PROMPT

structured_llm = INVESTIGATION_MODEL.with_structured_output(InvestigationResponse)

agent = create_agent(
    model=INVESTIGATION_MODEL,
    system_prompt=INVESTIGATION_PROMPT,
    tools=[]
).with_retry(stop_after_attempt=3)


async def investigation_agent(state: ForgeOpsState):
   try:
     github_evidence  = state.github_findings
     slack_findings = state.slack_findings
     pipeline_failures = state.ci_cd_findings

     query = f"Evidence established from github logs : {github_evidence}\n" + f"Evidence from investigating ci-cd pipeline {pipeline_failures}\n" + f"Evidence from slack channels: {slack_findings}"

     result = await agent.ainvoke({
        "messages": [{"role": "user","content": query}]
     })
     final_answer = await structured_llm.ainvoke(f"Convert the given response into a InvestigationResponse Schema. {result["messages"][-1].content}")
     
     state.investigation = final_answer.investigation 
     state.root_cause = final_answer.root_cause 
     state.evidence.append(final_answer.evidence)
     state.proposed_action = final_answer.proposed_action
     return final_answer
   except Exception as e:
        print(f"Investigation Agent Ran Into an error : {e}")
        raise e 




# print(asyncio.run(investigation_agent(sample_state)))
# # investigation_agent(sample_state)
