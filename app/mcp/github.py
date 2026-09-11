import asyncio
import json 
from app.mcp.client import select_tools,client
from app.config.config import GITHUB_READ_TOOLS

# Internal functions
async def _get_tools():
    all_tools  = await client.get_tools()
    github_tools = select_tools(all_tools,GITHUB_READ_TOOLS)
    return github_tools
    
    

results = asyncio.run(_get_tools())

# def get_commit()

class GithubTools:
    def __init__(self,github_tools):
        if not github_tools:
            raise ValueError("Enter the list of github tools. Call _get_tools()")

        self.github_tools  = github_tools 

    
    async def get_commit(self,owner: str,repo_name: str,sha: str):
        if not owner:
            raise ValueError("Missing owner name")
        
        if not repo_name:
            raise ValueError("Missing repo name")

        if not sha:
            raise ValueError("Missing commit SHA,branch name or tag name")

        
        tool = [tool for tool in self.github_tools if tool.name == "get_commit"]
        # return tool[0](owner,repo_name,sha)
        result = await tool[0].ainvoke({
            "owner": owner,
            "repo": repo_name,
            "sha": sha
        })
        
        raw_data = result[0]['text']
        commit_data = json.loads(raw_data)

        formatted_data = {
            "commit_id": commit_data["sha"],
            "url": commit_data["html_url"],
            "message": commit_data["commit"]["message"],
            "author": {
                "name": commit_data["commit"]["author"]["name"],
                "email": commit_data["commit"]["author"]["email"],
                "username": commit_data["author"]["login"],
                "data": commit_data["commit"]["author"]["date"]
            },
            "stats": commit_data["stats"],
            "files": [
                {
                    "filename": f["filename"],
                    "status": f["status"],
                    "additions": f.get("additions",0),
                    "deletions": f.get("deletions",0),
                    "changes": f.get("changes",0)
                }
                for f in commit_data["files"]
            ]
           
            
        }

        return formatted_data





github = GithubTools(results)
print(asyncio.run(github.get_commit("AllenGeorge08","ForgeOps","b8eafedb5408d4a557918ad4ad2868247cc876d4")))

        
        
