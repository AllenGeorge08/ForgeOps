from app.config.state import ForgeOpsState, Finding
from app.mcp.tools.github_actions_tools import list_actions, actions_get, actions_list, get_job_logs
import re


async def ci_cd_agent(state: ForgeOpsState, supervisor_query: str):
    """Investigate a CI/CD workflow run failure using GitHub Actions MCP tools.

    Extracts owner/repo/run_id from the supervisor query, then calls
    GitHub Actions MCP tools with the correct method strings.
    """

    owner = "AllenGeorge08"
    repo = "LLM-Semantic-Caching-Gateway"
    run_id = None

    # --- Extract run ID from supervisor query ---
    run_match = re.search(r'run[^\d]*(\d+)', supervisor_query, re.IGNORECASE)
    if run_match:
        run_id = run_match.group(1)

    # Fallback: check github_findings for run references
    if not run_id and state.github_findings:
        for f in state.github_findings:
            for ref in f.source_refs:
                rm = re.search(r'run[^\d]*(\d+)', ref, re.IGNORECASE)
                if rm:
                    run_id = rm.group(1)
                    break
            if run_id:
                break

    print(f"DEBUG ci_cd_agent: user_query={supervisor_query[:100]}")
    print(f"DEBUG ci_cd_agent: extracted run_id={run_id}")

    if not run_id:
        err = "CI/CD Agent: No workflow run ID found in query or GitHub findings."
        state.errors.append(err)
        state.ci_cd_findings.append(Finding(
            summary="CI/CD investigation failed — no run ID",
            evidence=[],
            source_refs=[],
            errors=[err]
        ))
        print(f"DEBUG ci_cd_agent: returning with no run_id, findings={len(state.ci_cd_findings)}")
        return state.ci_cd_findings[-1]

    evidence = []
    errors = []

    # --- Step 1: Get workflow run summary ---
    try:
        run_result = await actions_get.ainvoke({
            "method": "get_workflow_run",
            "owner": owner,
            "repo": repo,
            "resource_id": run_id
        })
        print(f"DEBUG ci_cd_agent: get_workflow_run result={run_result}")
        if run_result:
            evidence.append(
                f"Run {run_id}: status={run_result.get('status', 'unknown')}, "
                f"conclusion={run_result.get('conclusion', 'unknown')}, "
                f"workflow={run_result.get('name', 'unknown')}"
            )
    except Exception as e:
        errors.append(f"get_workflow_run failed: {str(e)}")

    # --- Step 2: Get jobs for the run ---
    try:
        jobs_result = await actions_list.ainvoke({
            "method": "list_workflow_jobs",
            "owner": owner,
            "repo": repo,
            "resource_id": run_id
        })
        print(f"DEBUG ci_cd_agent: actions_list result={jobs_result}")
        if jobs_result:
            evidence.append(f"Jobs: {str(jobs_result)[:500]}")
    except Exception as e:
        errors.append(f"list_workflow_jobs failed: {str(e)}")

    # --- Step 3: Get failed job logs ---
    try:
        logs_result = await get_job_logs.ainvoke({
            "owner": owner,
            "repo": repo,
            "run_id": int(run_id),
            "failed_only": True,
            "return_content": True,
            "tail_lines": 200
        })
        print(f"DEBUG ci_cd_agent: get_job_logs result type={type(logs_result)}, keys={list(logs_result.keys()) if isinstance(logs_result, dict) else 'N/A'}")
        if logs_result:
            evidence.append(f"Logs: {str(logs_result)[:800]}")
    except Exception as e:
        errors.append(f"get_job_logs failed: {str(e)}")

    finding = Finding(
        summary=f"CI/CD run {run_id} investigation",
        evidence=evidence if evidence else ["No data retrieved from GitHub Actions MCP"],
        source_refs=[f"GitHub Actions run {run_id}"],
        errors=errors if errors else [],
    )

    state.ci_cd_findings.append(finding)
    state.errors.extend(errors)
    print(f"DEBUG ci_cd_agent: FINAL findings count={len(state.ci_cd_findings)}, evidence={evidence}, errors={errors}")
    return {"ci_cd_findings": state.ci_cd_findings, "errors": state.errors}
