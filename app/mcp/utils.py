import json
from typing import Any


def safe_json_loads(raw: str, default: Any = None) -> Any:
    """Parse JSON safely, returning default on failure instead of crashing."""
    if not raw or not raw.strip():
        return default if default is not None else {}
    try:
        return json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        return default if default is not None else {}
