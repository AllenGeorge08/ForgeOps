import asyncio
import json 
from app.mcp.client import select_tools,client
from app.config.config import SLACK_READ_TOOLS

# Internal functions
async def _get_tools():
    all_tools  = await client.get_tools()
    slack_tools = select_tools(all_tools,SLACK_READ_TOOLS)
    return slack_tools


results = asyncio.run(_get_tools())

class SlackTools:
    def __init__(self,slack_tools):
        if not slack_tools:
            raise ValueError("Enter the list of slack tools. Call _get_tools()")

        self.slack_tools = slack_tools


    def slack_list_channels(self,types: str = None,exclude_archived: bool = False,limit: int = 2):
        if types:
            if types not in ['public_channel','private_channel']:
                raise ValueError("Types can be only public_channel or private_channel")
                
        pass
        