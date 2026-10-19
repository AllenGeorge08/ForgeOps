import os
from mem0 import Memory
import hashlib

import os
os.environ["MEM0_TELEMETRY"] = "False"

config = {
    "llm":{
        "provider": "langchain",
        "config": {
            "model": None,  # set lazily in get_memory()
        }
    },
    "embedder": {
        "provider": "openai",
        "config":{
            "model": "text-embedding-3-small",
            "openai_api_base": "https://openrouter.ai/api/v1",
            "openai_api_key": os.getenv("OPENROUTER_API_KEY"),
        }
    },
    "vector_store": {
        "provider": "qdrant",
        "config": {
            "collection_name": "test",
            "host": "localhost",
            "port": 6333,
            "embedding_model_dims": 1536
        }
    }
}


# Lazy singleton: mem0 instance is created on first use, not at import time.
_memory_instance = None


def _content_hash(messages) -> str:
    content = "".join(
        f"{m.get('role','')}:{m.get('content','')}" for m in messages
    )
    return hashlib.md5(content.encode('utf-8')).hexdigest()


def get_memory() -> Memory:
    """Return a lazily-initialized mem0 Memory instance.

    Deferred so importing this module does not require Qdrant or Ollama to be
    running, and so we do not wipe previous memory on every import.
    """
    global _memory_instance
    if _memory_instance is None:
        from app.config.config import memoryllm_model

        config["llm"]["config"]["model"] = memoryllm_model
        _memory_instance = Memory.from_config(config)
    return _memory_instance


def add_with_dedup(messages: list, user_id: str, **kwargs):
    """Add messages to mem0 with content-hash deduplication.

    Returns the result of m.add() if a new memory was stored, or None if a
    duplicate was skipped.
    """
    m = get_memory()
    target_hash = _content_hash(messages)

    existing = m.get_all(filters={"user_id": user_id})
    existing_hashes = {mem.get("hash") for mem in existing.get("results", [])}

    if target_hash in existing_hashes:
        print(f"Skipped duplicate memory (hash={target_hash})")
        return None

    return m.add(messages, user_id=user_id, **kwargs)
