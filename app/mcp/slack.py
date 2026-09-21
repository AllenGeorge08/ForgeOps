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


    async def slack_list_channels(self,types: str = None,exclude_archived: bool = False,limit: int = 2):
        if types:
            if types not in ['public_channel','private_channel']:
                raise ValueError("Types can be only public_channel or private_channel")
        

        tool = [tool for tool in self.slack_tools if tool.name == "slack_list_channels"]
        payload = {
            "types": types if types else None,
            "exclude_archived": exclude_archived,
            "limit": limit 
        }

        result = await tool[0].ainvoke(payload)
                
        raw_data = result[0]['text']
        contents = json.loads(raw_data)
        channels = contents.get("channels",[]) if isinstance(contents,dict) else contents
        final_data = []
        for ch in channels:
            return_data = {
                "id": ch.get("id"),
                "name": ch.get("name"),
                "is_private": ch.get("is_private", False),
                "is_archived": ch.get("is_archived", False),
                "is_general": ch.get("is_general", False),
                "is_member": ch.get("is_member", False),
                "num_members": ch.get("num_members"),
                "purpose": (ch.get("purpose") or {}).get("value", ""),
                "topic": (ch.get("topic") or {}).get("value", ""),
                "created_at": ch.get("created"),  # epoch seconds
            }
            final_data.append(return_data)

        return final_data

    
    async def get_channel_history(self,channel_id: str,limit: int=2):
        if not channel_id:
            raise ValueError("Enter a valid channel_id")

        
        tool = [tool for tool in self.slack_tools if tool.name == "slack_get_channel_history"]
        payload = {
            "channel_id": channel_id,
            "limit": limit
        }
        result = await tool[0].ainvoke(payload)
        raw_data = result[0]['text']
        contents = json.loads(raw_data)
        if contents.get("ok") == False:
            raise ValueError("Your bot is not added to the channel yet. Add by /invite @your-bot-name")

        messages = contents.get("messages",[])
        # return messages
        final_data = []
        for message in messages:
            return_data = {
                "type": message.get("subtype",""),
                "user_id": message.get('user',''),
                "text": message.get("text",""),
                "inviter": message.get("inviter"),                
            }
            final_data.append(return_data)

        return final_data

    async def get_users(self,limit:int = 2):
        tool = [tool for tool in self.slack_tools if tool.name == "slack_get_users"]
        payload={
            "limit": limit 
        }
        result = await tool[0].ainvoke(payload)
        raw_data = result[0]['text']
        contents = json.loads(raw_data)
        final_data=[]
        for member in contents.get("members", []):
            if member.get("deleted"):
                continue

            profile = member.get("profile") or {}
            return_data = {
                "id": member.get("id"),
                "username": member.get("name"),
                "real_name": member.get("real_name"),
                "display_name": profile.get("display_name") or None,
                "email": profile.get("email"),  # None unless users:read.email scope is granted
                "title": profile.get("title") or None,
                "timezone": member.get("tz"),
                "is_bot": member.get("is_bot", False),
                "is_admin": member.get("is_admin", False),
                "is_owner": member.get("is_owner", False),
            }
            final_data.append(return_data)

        return {
            "users": final_data,
            "next_cursor": (contents.get("response_metadata") or {}).get("next_cursor") or None,
        }

    async def get_thread_replies(self,channel_id: str, thread_ts: str,limit: int=5):

        if not channel_id:
            raise ValueError("Missing channel ID")
        if not thread_ts:
            raise ValueError("Missing thread_ts (the parent message's ts)")

        payload = {"channel_id": channel_id, "thread_ts": str(thread_ts), "limit": limit}
        tool = [t for t in self.slack_tools if t.name == "slack_get_thread_replies"]  # check real name
        if not tool:
            raise ValueError("get thread replies tool not found")

        results = await tool[0].ainvoke(payload)
        contents = json.loads(results[0]["text"])

        if not contents.get("ok", True):
            raise RuntimeError(f"Slack error: {contents.get('error')}")

        final_data =[]
        messages = contents.get("messages",[])
        for message in messages:
            return_data = {
                "user": message.get('user',''),
                "message_type": message.get("message",''),
                "message_timestamp":message.get('timestamp',''),
                "client_message_id":message.get("client_msg_id"),
                "text":message.get("text",""),
                "team":message.get("team",""),
                "thread_timestamp":message.get("thread_ts",""),
                "reply_users":message.get("reply_users","")
            }

            final_data.append(return_data)
        
        return final_data




slack = SlackTools(results)

# print(asyncio.run(slack.slack_list_channels(limit=10)))
# print(asyncio.run(slack.get_users()))
print(asyncio.run(slack.get_thread_replies("C0C16F2L62D","1789954543.416699")))

# print(asyncio.run(slack.get_channel_history(channel_id="C0C16F2L62D")))
# print(asyncio.run(slack.slack_list_channels(limit=10,types='public_channel')))

