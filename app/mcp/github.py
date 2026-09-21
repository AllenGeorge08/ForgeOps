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


    async def pull_request_read(self,action: str,owner:str,repo_name: str,pullNumber: int):
        if not owner:
            raise ValueError("Missing owner name")
        
        if not repo_name:
            raise ValueError("Missing repo name")

        if not pullNumber:
            raise ValueError("Missing Pull Request Number")

        tool = [tool for tool in self.github_tools if tool.name == "pull_request_read"]
        result = await tool[0].ainvoke({
            "method": action,
            "owner": owner,
            "repo": repo_name,
            "pullNumber": pullNumber 
        })

        print(f"Diff : { result[0]['text']}\n")
        print(f"Id : {result[0]['id']}")


    async def list_commits(self,owner: str,repo_name: str):
        if not owner:
            raise ValueError("Missing owner name")

        if not repo_name:
            raise ValueError("Missing repo name")

        tool = [tool for tool in self.github_tools if tool.name =="list_commits"]
        results = await tool[0].ainvoke({
            "owner": owner,
            "repo": repo_name,
        })
        final_data = []
        raw_text = results[0]["text"]
        commits = json.loads(raw_text)

        for item in commits:
            commit_info = item.get("commit",{})
            commiter_info = commit_info.get("commiter",{})
            return_data  = {
                "sha": item.get("sha"),
                "commit": {
                    "message": commit_info.get("message"),
                    "commiter": {
                        "commiter": commiter_info.get("name"),
                        "commit_data": commiter_info.get("date"),
                    }
                },
            }
            final_data.append(return_data)
        
        return final_data


    async def list_pull_requests(self,owner: str,repo_name: str, state: str = None):
        if state:
            if state not in ['open','closed','all']:
                raise ValueError("Invalid pull request state")

        if not owner:
            raise ValueError("Missing owner name")

        if not repo_name:
            raise ValueError("Missing repo name")

        tool = [tool for tool in self.github_tools if tool.name =="list_pull_requests"]
        payload = {
            "owner": owner,
            "repo": repo_name
        }

        if state:
            payload["state"] = state 

        results = await tool[0].ainvoke(payload)
        raw_text = results[0]["text"]
        final_data = []
        pull_requests= json.loads(raw_text)
        for item in pull_requests:
            user_info = item.get("user") or {}
            head_info = item.get("head") or {}
            base_info = item.get("base") or {}

            return_data = {
                "number": item.get("number"),
                "title": item.get("title", ""),
                "body": item.get("body", ""),
                "state": item.get("state", ""),
                "merged": item.get("merged", False),
                "author": {
                    "login": user_info.get("login", ""),
                    "id": user_info.get("id"),
                },
                "head": {
                    "ref": head_info.get("ref", ""),
                    "sha": head_info.get("sha", ""),
                },
                "base": {
                    "ref": base_info.get("ref", ""),
                    "sha": base_info.get("sha", ""),
                },
                "created_at": item.get("created_at", ""),
                "updated_at": item.get("updated_at", ""),
            }
            final_data.append(return_data)
        return final_data


    async def get_file_contents(self,owner: str,repo_name: str):
        if not owner:
            raise ValueError("Missing owner name")

        if not repo_name:
            raise ValueError("Missing repo name")
        
        
        tool = [tool for tool in self.github_tools if tool.name =="get_file_contents"]
        results = await tool[0].ainvoke({
            "owner": owner,
            "repo": repo_name,
        })
        final_data = []
        raw_text  = results[0]["text"]
        contents = json.loads(raw_text)
        for item in contents:
            return_data = {
                "type": item.get("type"),
                "name": item.get("name"),
                "path": item.get("path"),
                "commit_hash": item.get("sha"),
                "git_url": item.get("git_url")
            }
            final_data.append(return_data)
        
        return final_data 

    
    async def list_branches(self,owner: str,repo_name: str) -> []:
        if not owner:
            raise ValueError("Missing owner name")

        if not repo_name:
            raise ValueError("Missing repo name")
        
           
        tool = [tool for tool in self.github_tools if tool.name =="list_branches"]
        results = await tool[0].ainvoke({
            "owner": owner,
            "repo": repo_name,
        })
        final_result = []
        raw_text  = results[0]["text"]
        contents = json.loads(raw_text)
        for item in contents:
            return_data = {
                "branch_name": item.get("name"),
                "sha_hash": item.get("sha"),
                "is_protected": item.get("protected")
            }
            final_result.append(return_data)
        return final_result

    async def search_code(
        self,
        search_term: str,
        owner: str = None,
        repo: str = None,
        language: str = None,
        path: str = None,
        extension: str = None,
        per_page: int = 2,
    ):
        if not search_term:
            raise ValueError("Missing Search Term")

        if not 1 <= per_page <= 100:
            raise ValueError("per_page must be between 1 and 100")

        query_parts = [search_term]

        if owner and repo:
            query_parts.append(f"repo:{owner}/{repo}")
        elif owner:
            query_parts.append(f"user:{owner}")

        if language:
            query_parts.append(f"language:{language}")
        if path:
            query_parts.append(f"path:{path}")
        if extension:
            query_parts.append(f"extension:{extension}")

        full_query = " ".join(query_parts)

        tool = [t for t in self.github_tools if t.name == "search_code"]
        if not tool:
            raise ValueError("search_code tool not found. Add it to GITHUB_READ_TOOLS")

        results = await tool[0].ainvoke({"query": full_query, "perPage": per_page})
        contents = json.loads(results[0]["text"])

        final_data = []
        for item in contents.get("items", []):
            text_matches = item.get("text_matches") or []

            # dedupe while keeping order, strip whitespace, cap length
            seen = set()
            fragments = []
            for m in text_matches:
                frag = (m.get("fragment") or "").strip()
                if frag and frag not in seen:
                    seen.add(frag)
                    fragments.append(frag[:300])

            # repository can be a plain string or a dict depending on the server
            repo_info = item.get("repository")
            repository = repo_info.get("full_name") if isinstance(repo_info, dict) else repo_info

            return_data = {
                "repository": repository,
                "path": item.get("path"),
                "name": item.get("name"),
                "url": item.get("html_url")
                       or (f"https://github.com/{repository}/blob/HEAD/{item.get('path')}" if repository else None),
                "blob_sha": item.get("sha"),
                "match_count": sum(len(m.get("matches") or []) for m in text_matches),
                "fragments": fragments,
            }
            final_data.append(return_data)

        return {
            "query": full_query,
            "total_count": contents.get("total_count"),
            "items": final_data,
        }
    async def search_pull_requests(self,search_term: str,owner: str=None,repo:str=None):
        
        payload = {
            "query": f"{search_term} is:pr repo:{owner}/{repo}" if owner and repo else f"{search_term} is:pr",
            "perPage": 10,
        }

        tool = [tool for tool in self.github_tools if tool.name =="search_pull_requests"]
        results = await tool[0].ainvoke(
            payload 
        )
        
        raw_text = results[0]["text"]
        contents = json.loads(raw_text)

        final_data =[]
        for item in contents.get("items",[]):
            return_data = {
                "number": item.get("number"),
                "title": item.get("title"),
                "state": item.get('state'),
                "author": item.get("user",{}).get("login"),
                "body": item.get("body"),
                "created_at": item.get("created_at"),
                "updated_at": item.get('updated_at'),
                "comments": item.get("comments"),
            }
            final_data.append(return_data)
        return final_data


    async def search_issues(self,search_term: str,owner: str=None,repo_name: str=None):
        payload = {"query": search_term,"perPage":10}
        if owner and repo_name:
            payload["owner"] = owner 
            payload["repo"] = repo_name

        tool = [tool for tool in self.github_tools if tool.name == "search_issues"]
        results = await tool[0].ainvoke(payload)
        raw_text = results[0]["text"]
        contents = json.loads(raw_text)
        final_data = []
        for item in contents.get("items",[]):
            return_data = {
                "number": item.get("number"),
                "title": item.get("title"),
                "state": item.get("state"),
                "author": item.get("user",{}).get("login"),
                "body": item.get("body"),
                "created_at": item.get("created_at"),
                "updated_at": item.get("updated_at"),
                "comments": item.get("comments")
            }
            final_data.append(return_data)

        return final_data


    async def issue_read(self,owner: str,repo: str,issue_number: int, method: str="get"):
        payload = {
            "owner": owner,
            "repo": repo,
            "issue_number": issue_number,
            "method": method 
        }

        tool = [tool for tool in self.github_tools if tool.name=="issue_read"]
        results = await tool[0].ainvoke(payload)
        raw_text = results[0]["text"]
        contents = json.loads(raw_text)

        final_data = []
        for item in contents:
            return_data = {
                "issue_id": item.get("id"),
                "body": item.get("body"),
                "issue_url": item.get("html_url"),
                "user": {
                    "login": item.get("user",{}).get("login"),
                    "user_id": item.get("user",{}).get("id"),
                    "user_profile": item.get('user',{}).get('profile_url'),
                },
                "created_at": item.get("created_at"),
                "updated_at": item.get("updated_at")
            }
            final_data.append(return_data)
        return final_data

    
    async def search_commits(self,search_term: str,owner: str = None,repo_name: str = None,sort: str = None,order: str = None,page: int = 1,per_page: int = 2):
        if not search_term:
            raise ValueError("Missing Search Term")

        if sort and sort not in ["author-date", "committer-date"]:
            raise ValueError("Invalid sort. Use 'author-date' or 'committer-date'")

        if order and order not in ["asc", "desc"]:
            raise ValueError("Invalid order. Use 'asc' or 'desc'")

        if page < 1:
            raise ValueError("page must be >= 1")

        if not 1 <= per_page <= 100:
            raise ValueError("per_page must be between 1 and 100")

        query_parts = [search_term]

        if owner and repo_name:
            query_parts.append(f"repo:{owner}/{repo_name}")
        elif owner:
            query_parts.append(f"user:{owner}")

        payload = {
            "query": " ".join(query_parts),
            "page": page,
            "perPage": per_page,
        }

        if sort:
            payload["sort"] = sort
        if order:
            payload["order"] = order

        tool = [tool for tool in self.github_tools if tool.name == "search_commits"]
        if not tool:
            raise ValueError("search_commits tool not found. Add it to GITHUB_READ_TOOLS")

        results = await tool[0].ainvoke(payload)
        raw_text = results[0]["text"]
        contents = json.loads(raw_text)
        final_data = []
        for item in contents.get("items", []):
            commit_info = item.get("commit") or {}
            author_info = commit_info.get("author") or {}
            committer_info = commit_info.get("committer") or {}
            author_user = item.get("author") or {}  # null if email isn't linked to a GitHub account
            repo_info = item.get("repository") or {}

            message = commit_info.get("message") or ""
            title, _, body = message.partition("\n")

            return_data = {
                "sha": item.get("sha"),
                "url": item.get("html_url"),
                "title": title,
                "body": body.strip(),
                "author": {
                    "name": author_info.get("name"),
                    "email": author_info.get("email"),
                    "username": author_user.get("login"),
                    "date": author_info.get("date"),
                },
                "committer": {
                    "name": committer_info.get("name"),
                    "date": committer_info.get("date"),
                },
                "repository": repo_info.get("full_name"),
            }
            final_data.append(return_data)

        return final_data

        
github = GithubTools(results)

# List
# print(asyncio.run(github.list_branches("AllenGeorge08","TestRepo")))
# print(asyncio.run(github.list_pull_requests("AllenGeorge08","TestRepo")))

# print(asyncio.run(github.get_commit("AllenGeorge08","ForgeOps","b8eafedb5408d4a557918ad4ad2868247cc876d4")))   #Working
# print(asyncio.run(github.pull_request_read("get_diff","AllenGeorge08","TestRepo","1")))   #Working
# print(asyncio.run(github.list_commits("AllenGeorge08","ForgeOps")))
# print(asyncio.run(github.get_file_contents("AllenGeorge08","ForgeOps")))
# print(asyncio.run(github.search_code("MultiServerMCPClient","AllenGeorge08","ForgeOps")))
# print(asyncio.run(github.search_pull_requests(" ","AllenGeorge08","TestRepo")))

# print(asyncio.run(github.search_issues("is:issue","alexeygrigorev","ai-engineering-field-guide"))) 

# get_sub_issues,get_parents,get_labels also supported
# print(asyncio.run(github.issue_read("AllenGeorge08","TestRepo",3,"get_comments"))) 
# print(asyncio.run(github.issue_read("AllenGeorge08","TestRepo",3))) #default = get,get_sub_issues,get_parent,get_label 

# print(asyncio.run(github.search_code('MultiServerMCP',owner="AllenGeorge08",repo="ForgeOps",language="python",path="app"))) #not indexd well
# print(asyncio.run(github.search_code("import",owner="wassim249",repo="fastapi-langgraph-agent-production-ready-template",language="python")))

# Search commits

# print(asyncio.run(github.search_commits("fix","langchain-ai","langchain")))
# print(asyncio.run(github.search_commits("mcp","langchain-ai","langchain",per_page=5)))
# print(asyncio.run(github.search_commits("author-date:>2026-08-01","langchain-ai","langchain",sort="author-date",order="desc",per_page=3)))
# print(asyncio.run(github.search_commits("merge:false","langchain-ai","langchain",per_page=5)))
# print(asyncio.run(github.search_commits("validator","anza-xyz","agave",per_page=5)))
# print(asyncio.run(github.search_commits("fix","anza-xyz")))  # whole org via user: qualifier