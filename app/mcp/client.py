from langchain_mcp_adapters.client import MultiServerMCPClient
import asyncio 
import os 
from dotenv import load_dotenv

load_dotenv()


GITHUB_ACCESS_TOKEN = os.getenv("GITHUB_ACCESS_TOKEN")

if not GITHUB_ACCESS_TOKEN:
        raise ValueError("Missing Github access token in user configuration context.")

SLACK_AUTH_TOKEN = os.getenv("SLACK_BOT_AUTH_TOKEN")
SLACK_TEAM_ID=os.getenv("SLACK_TEAM_ID")
if not SLACK_AUTH_TOKEN or not SLACK_TEAM_ID:
        raise ValueError("Missing slack team id or auth token")


client =  MultiServerMCPClient(
    {
        "github":{
            "transport": "stdio",
            "command": "docker",
            "args":[ 
                "run",
                "-i",
                "--rm",
                "-e","GITHUB_PERSONAL_ACCESS_TOKEN",
                "-e","GITHUB_TOOLSETS",
                "ghcr.io/github/github-mcp-server"
            ],
            "env": {
                "GITHUB_PERSONAL_ACCESS_TOKEN": GITHUB_ACCESS_TOKEN,
                "GITHUB_TOOLSETS": "repos,issues,pull_requests,users,actions",
                "PATH": os.getenv("PATH","")
            }
        },
        "slack":{
            "transport": "stdio",
            "command": "npx",
            "args": [
                "-y",
                "@modelcontextprotocol/server-slack"
            ],
            "env": {
                "SLACK_BOT_TOKEN": SLACK_AUTH_TOKEN,
                "SLACK_TEAM_ID": SLACK_TEAM_ID,
                "PATH": os.getenv("PATH","")
            }
        }
    })

def select_tools(all_tools,allowed_names):
    return [tool for tool in all_tools if tool.name in allowed_names]


# async def main():
#     tools = await client.get_tools()
#     # agent = GITHUB_MODEL.bind_tools(tools)
#     # response = agent.invoke(
#     #     "List the open Pull requests in my repository ForgeOps"
#     # )
#     # print(response.content)
#     tool_names = []
#     for tool in tools:
#         tool_names.append(tool.name)
#     # action_tools = [t.name for t in tools if "actions" in t.name]
#     # print(action_tools)
#     # regular_tools = [t.name for t in tools if "actions" not in t.name]
#     # print(regular_tools)
#     print(tool_names)


