import asyncio
import re
from langchain.agents import create_agent
from app.config.state import Finding, ForgeOpsState, InvestigationResponse
from app.config.config import INVESTIGATION_MODEL
from app.agents.prompts import INVESTIGATION_PROMPT

structured_llm = INVESTIGATION_MODEL.with_structured_output(InvestigationResponse)

agent = create_agent(
    model=INVESTIGATION_MODEL,
    system_prompt=INVESTIGATION_PROMPT,
    tools=[]
).with_retry(stop_after_attempt=3)


def _finding_to_text(finding: Finding) -> str:
    """Convert a Finding object into clean evidence text."""
    lines = [f"Summary: {finding.summary}"]
    if finding.evidence:
        lines.append(f"Evidence: {'; '.join(finding.evidence)}")
    if finding.source_refs:
        lines.append(f"Sources: {', '.join(finding.source_refs)}")
    if finding.errors:
        lines.append(f"Errors: {'; '.join(finding.errors)}")
    return "\n".join(lines)


async def investigation_agent(state: ForgeOpsState):
    try:
        github_evidence = state.github_findings
        slack_findings = state.slack_findings
        pipeline_failures = state.ci_cd_findings

        print(f"DEBUG investigation: ci_cd_findings count={len(pipeline_failures)}")
        for i, f in enumerate(pipeline_failures):
            print(f"DEBUG investigation: finding[{i}].summary={f.summary}")
            print(f"DEBUG investigation: finding[{i}].evidence={f.evidence}")
            print(f"DEBUG investigation: finding[{i}].source_refs={f.source_refs}")
            print(f"DEBUG investigation: finding[{i}].errors={f.errors}")

        github_text = "\n".join([_finding_to_text(f) for f in github_evidence]) if github_evidence else "None"
        cicd_text = "\n".join([_finding_to_text(f) for f in pipeline_failures]) if pipeline_failures else "None"
        slack_text = "\n".join([_finding_to_text(f) for f in slack_findings]) if slack_findings else "None"

        print(f"DEBUG investigation: cicd_text length={len(cicd_text)}")
        print(f"DEBUG investigation: cicd_text={cicd_text[:500]}")

        query = (
            f"Evidence established from github logs :\n{github_text}\n"
            f"Evidence from investigating ci-cd pipeline :\n{cicd_text}\n"
            f"Evidence from slack channels:\n{slack_text}"
        )

        result = await agent.ainvoke({
            "messages": [{"role": "user", "content": query}]
        })
        response_content = result["messages"][-1].content
        print(f"DEBUG investigation: agent response={response_content[:500]}")
        final_answer = await structured_llm.ainvoke(
            f"Convert the given response into a InvestigationResponse Schema. {response_content}"
        )

        print(f"DEBUG investigation: final_answer.investigation={final_answer.investigation}")
        print(f"DEBUG investigation: final_answer.root_cause={final_answer.root_cause}")
        print(f"DEBUG investigation: final_answer.evidence={final_answer.evidence}")
        print(f"DEBUG investigation: final_answer.proposed_action={final_answer.proposed_action}")

        state.investigation = final_answer.investigation
        state.root_cause = final_answer.root_cause

        # Handle evidence: final_answer.evidence may be str or list[str]
        if isinstance(final_answer.evidence, list):
            state.evidence.extend(final_answer.evidence)
        elif isinstance(final_answer.evidence, str) and final_answer.evidence.strip():
            state.evidence.append(final_answer.evidence)

        state.proposed_action = final_answer.proposed_action
        return {
            "investigation": state.investigation,
            "root_cause": state.root_cause,
            "evidence": state.evidence,
            "proposed_action": state.proposed_action,
        }
    except Exception as e:
        print(f"Investigation Agent Ran Into an error : {e}")
        raise e
