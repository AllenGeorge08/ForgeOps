import asyncio
import json 
from app.mcp.client import select_tools,client
from app.config.config import CICD_TOOLS

# Internal functions
async def _get_tools():
    all_tools  = await client.get_tools()
    github_tools = select_tools(all_tools,CICD_TOOLS)
    return github_tools
    
    
results = asyncio.run(_get_tools())

class GithubActions:
    def __init__(self,github_actions_tools):
        if not github_actions_tools:
            raise ValueError("Enter the list of github tools. Call _get_tools()")

        self.github_tools  = github_actions_tools


    async def list_actions(self,method: str,owner: str,repo_name: str,perPage: int = 5):
        if not owner:
            raise ValueError("Missing owner name")
        
        if not repo_name:
            raise ValueError("Missing repo name")

        tool = [tool for tool in self.github_tools if tool.name == "actions_list"]
        results = await tool[0].ainvoke({
            "method": method,
            "owner": owner,
            "repo": repo_name,
            "perPage": perPage
        })
        content = json.loads(results[0]["text"])
        
        final_data = []
        for item in content.get("workflows",[]):
            return_data = {
                "id": item.get("id"),
                "name": item.get("name"),
                "path": item.get("path"),
                "state": item.get("state"),
                "created_at": item.get("created_at"),
                "updated_at": item.get("updated_at"),
            }

            final_data.append(return_data)

        return final_data

    async def actions_get(self, method: str, owner: str, repo: str, resource_id: str):
        if not owner:
            raise ValueError("Missing owner name")
        if not repo:
            raise ValueError("Missing repo name")
        if not resource_id:
            raise ValueError("Missing resource_id")

        payload = {
            "method": method,
            "owner": owner,
            "repo": repo,
            "resource_id": resource_id,
        }

        tool = [tool for tool in self.github_tools if tool.name == "actions_get"]
        results = await tool[0].ainvoke(payload)

        raw_text = results[0]["text"]
        contents = json.loads(raw_text)
        formatters = {
            "get_workflow": self._format_workflow,
            "get_workflow_run": self._format_workflow_run,
            "get_workflow_run_usage": self._format_run_usage,
        }
        formatter = formatters.get(method, lambda c: c)  # fallback: return raw if unmapped
        return formatter(contents)

    async def actions_list(self, method: str, owner: str, repo: str, **kwargs):
        payload = {
        "method": method,
        "owner": owner,
        "repo": repo,
        **kwargs,
        }
        tool = [tool for tool in self.github_tools if tool.name == "actions_list"]
        results = await tool[0].ainvoke(payload)
        raw_text = results[0]["text"]
        return json.loads(raw_text)


    async def get_job_logs(self, owner: str, repo: str, job_id: int = None, run_id: int = None,
                        failed_only: bool = False, return_content: bool = False, tail_lines: int = 500):
        if not owner:
            raise ValueError("Missing owner name")
        if not repo:
            raise ValueError("Missing repo name")
        if not job_id and not run_id:
            raise ValueError("Provide either job_id (single job) or run_id (with failed_only=True)")
        if failed_only and not run_id:
            raise ValueError("failed_only requires run_id")

        payload = {
            "owner": owner,
            "repo": repo,
            "return_content": return_content,
            "tail_lines": tail_lines,
        }

        if job_id:
            payload["job_id"] = job_id
        if run_id:
            payload["run_id"] = run_id
        if failed_only:
            payload["failed_only"] = failed_only

        tool = [tool for tool in self.github_tools if tool.name == "get_job_logs"]
        results = await tool[0].ainvoke(payload)

        raw_text = results[0]["text"]
        raw_text = results[0]["text"]
        try:
            contents = json.loads(raw_text)
        except json.JSONDecodeError:
            return {"error": raw_text}

        print(f"DEBUG raw: {raw_text!r}")  # inspect shape before formatting, per the pattern above
        contents = json.loads(raw_text)
        formatted_data = {
            "run_id": contents.get("run_id"),
            "failed_jobs": contents.get("failed_jobs"),
            "total_jobs": contents.get("total_jobs"),
            "message": contents.get("message"),
            }
        return formatted_data
    


    def _format_workflow_run(self,contents):
        formatted_data = {
            "id": contents.get("id"),
            "name": contents.get("name"),
            "display_title": contents.get("display_title"),
            "workflow_id": contents.get("workflow_id"),
            "run_number": contents.get("run_number"),
            "status": contents.get("status"),
            "conclusion": contents.get("conclusion"),
            "branch": contents.get("head_branch"),
            "sha": contents.get("head_sha"),
            "commit_message": contents.get("head_commit", {}).get("message"),
            "actor": contents.get("actor", {}).get("login"),
            "created_at": contents.get("created_at"),
        }
        return formatted_data

    def _format_run_usage(self, c):
        return {"run_duration_ms": c.get("run_duration_ms"), "billable": c.get("billable", {})}

    def _format_workflow(self, c):
        return {"id": c.get("id"), "name": c.get("name"), "state": c.get("state"), "path": c.get("path")}

    






github_actions = GithubActions(results)
# print(asyncio.run(github_actions.list_actions('list_workflows',owner="wassim249",repo_name="fastapi-langgraph-agent-production-ready-template")))
# print(asyncio.run(github_actions.actions_get("get_workflow",owner="wassim249",repo="fastapi-langgraph-agent-production-ready-template",resource_id="ci.yaml")))
# print(asyncio.run(github_actions.actions_get("get_workflow_run",owner="wassim249",repo="fastapi-langgraph-agent-production-ready-template",resource_id="33086051926")))
# the above can be called with get_workflow_run_usage, get_workflow_job,downlaod_workflow..

# print(asyncio.run(github_actions.actions_get("get_workflow_run_usage",owner="wassim249",repo="fastapi-langgraph-agent-production-ready-template",resource_id="33086051926")))

# get id from here
# print(asyncio.run(github_actions.actions_list("list_workflow_runs", "wassim249", "fastapi-langgraph-agent-production-ready-template", workflow_id="ci.yaml")))
# print(asyncio.run(github_actions.get_job_logs("wassim249", "fastapi-langgraph-agent-production-ready-template",job_id=62564480, return_content=True, tail_lines=200)))
# print(asyncio.run(github_actions.get_job_logs("wassim249", "fastapi-langgraph-agent-production-ready-template",run_id=33086051926, failed_only=True, return_content=True, tail_lines=500)))
# print(asyncio.run(github_actions.get_job_logs("wassim249", "fastapi-langgraph-agent-production-ready-template",
    # run_id=27279509987, failed_only=True, return_content=True, tail_lines=200
# )))

        

