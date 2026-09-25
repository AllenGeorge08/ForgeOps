from app.config.state import ForgeOpsState,Finding
from app.config.config import CI_CD_MODEL
from app.mcp.tools.github_actions_tools import list_actions,actions_get,actions_list,get_job_logs
from langchain.agents import create_agent
from app.agents.prompts import CICD_AGENT_PROMPT
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import PydanticOutputParser

# bz lgchain huggingfacce doesn't support native pydantic obj handling
parser = PydanticOutputParser(pydantic_object=Finding)

ci_cd_tools = [
    list_actions,
    actions_get,
    get_job_logs,
    actions_list
]

prompt = PromptTemplate(
    template=(
        "Convert this investigation output into the Finding schema. "
        "Add nothing new.\n\n{format_instructions}\n\n{text}"
    ),
    input_variables=["text"],
    partial_variables={"format_instructions": parser.get_format_instructions()},
)

ci_cd_llm = (prompt | CI_CD_MODEL | parser).with_retry(stop_after_attempt=2)
agent = create_agent(
    model=CI_CD_MODEL,
    tools=ci_cd_tools,
    system_prompt=CICD_AGENT_PROMPT
)

async def ci_cd_agent(state: ForgeOpsState,supervisor_query: str):
    github_findings = state.github_findings
  
    cicd_query = f"""

    Supervisor Task: {supervisor_query}

    Github Agent Finding: {github_findings}
    """

    result = await agent.ainvoke({
        "messages": [{"role": "user","content": cicd_query}]
    })

    final_text= result["messages"][-1].content

    final_answer =  await ci_cd_llm.ainvoke(f"Convert this investigation output into the Finding schema. Add nothing new.\n\n{final_text}")
    state.ci_cd_findings.append(final_answer)
    return final_answer









    