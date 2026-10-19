from langchain_mcp_adapters.client import MultiServerMCPClient
import asyncio
import os
from dotenv import load_dotenv

load_dotenv()


GITHUB_ACCESS_TOKEN = os.getenv("GITHUB_ACCESS_TOKEN")
SLACK_AUTH_TOKEN = os.getenv("SLACK_BOT_AUTH_TOKEN")
SLACK_TEAM_ID = os.getenv("SLACK_TEAM_ID")

# Validate tokens but don't crash at import time — allow container to start
# and fail gracefully at runtime if tokens are truly missing.
_missing = []
if not GITHUB_ACCESS_TOKEN:
    _missing.append("GITHUB_ACCESS_TOKEN")
if not SLACK_AUTH_TOKEN:
    _missing.append("SLACK_BOT_AUTH_TOKEN")
if not SLACK_TEAM_ID:
    _missing.append("SLACK_TEAM_ID")

if _missing:
    import warnings

    warnings.warn(
        f"Missing MCP env vars: {', '.join(_missing)}. "
        "MCP tools will fail at runtime. Pass --env-file .env to docker run.",
        stacklevel=2,
    )


client = MultiServerMCPClient(
    {
        "github": {
            "transport": "stdio",
            "command": "docker",
            "args": [
                "run",
                "-i",
                "--rm",
                "-e", "GITHUB_PERSONAL_ACCESS_TOKEN",
                "-e", "GITHUB_TOOLSETS",
                "ghcr.io/github/github-mcp-server",
            ],
            "env": {
                "GITHUB_PERSONAL_ACCESS_TOKEN": GITHUB_ACCESS_TOKEN or "",
                "GITHUB_TOOLSETS": "repos,issues,pull_requests,users,actions",
                "PATH": os.getenv("PATH", ""),
            },
        },
        "slack": {
            "transport": "stdio",
            "command": "npx",
            "args": [
                "-y",
                "@modelcontextprotocol/server-slack",
            ],
            "env": {
                "SLACK_BOT_TOKEN": SLACK_AUTH_TOKEN or "",
                "SLACK_TEAM_ID": SLACK_TEAM_ID or "",
                "PATH": os.getenv("PATH", ""),
            },
        },
    }
)


def select_tools(all_tools, allowed_names):
    return [tool for tool in all_tools if tool.name in allowed_names]


async def main():
    tools = await client.get_tools()
    tool_names = []
    for tool in tools:
        payload = {
            "tool_name": tool.name,
            "tool_args": [t for t in tool.args],
        }
        tool_names.append(payload)
    for tool in tools:
        print("-" * 10)
        print(tool)


# asyncio.run(main())
