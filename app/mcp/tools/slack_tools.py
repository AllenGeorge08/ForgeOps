from app.mcp.slack import SlackTools
from langchain.tools import tool


_slack = None


async def init_slack():
    """Initialize the Slack MCP client. Call this during app startup."""
    global _slack
    if _slack is None:
        _slack = await SlackTools().ainit()
    return _slack


def _ensure_slack():
    if _slack is None:
        raise RuntimeError(
            "Slack MCP client not initialized. Call init_slack() during app startup."
        )
    return _slack


@tool
async def slack_list_channels(types: str = None, exclude_archived: bool = False, limit: int = 100):
    """List Slack channels. types can be 'public_channel' or 'private_channel' (omit for both). Set exclude_archived to skip archived channels."""
    return await _ensure_slack().slack_list_channels(types, exclude_archived, limit)


@tool
async def get_channel_history(channel_id: str, limit: int = 20):
    """Get recent message history for a Slack channel, given its channel ID. The bot must be a member of the channel first."""
    return await _ensure_slack().get_channel_history(channel_id, limit)


@tool
async def get_users(limit: int = 100):
    """List Slack workspace members (id, username, real name, title, timezone, admin/owner flags). Excludes deleted users."""
    return await _ensure_slack().get_users(limit)


@tool
async def get_thread_replies(channel_id: str, thread_ts: str, limit: int = 20):
    """Get replies in a Slack thread, given the channel ID and the parent message's ts (e.g. '1789954543.416699')."""
    return await _ensure_slack().get_thread_replies(channel_id, thread_ts, limit)
