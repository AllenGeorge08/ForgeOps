import os
from mem0 import Memory
from langchain_ollama import ChatOllama
from app.config.config import memoryllm_model
import hashlib

import os
os.environ["MEM0_TELEMETRY"] = "False"

config = {
    "llm":{
        "provider": "langchain",
        "config": {
            "model": memoryllm_model
            # "ollama_base_url": "http://localhost:11434/"            
        }
    },
    "embedder": {
        "provider": "ollama",
        "config":{
            "model": "nomic-embed-text-v2-moe:latest",
            "ollama_base_url": "http://localhost:11434/"
        }
    },
    "vector_store": {
        "provider": "qdrant",
        "config": {
            "collection_name": "test",
            "host": "localhost",
            "port": 6333,
            "embedding_model_dims": 768
        }
    }
}


def _content_hash(messages)->str:
    content = "".join(
        f"{m.get('role','')}:{m.get('content','')}" for m in messages 
    )
    return hashlib.md5(content.encode('utf-8')).hexdigest()


def add_with_dedup(m: Memory, messages: list, user_id: str, **kwargs):
    target_hash = _content_hash(messages)

    existing = m.get_all(filters={"user_id": user_id})
    existing_hashes = {mem.get("hash") for mem in existing.get("results", [])}

    if target_hash in existing_hashes:
        print(f"Skipped duplicate memory (hash={target_hash})")
        return None

    return m.add(messages, user_id=user_id, **kwargs)

m = Memory.from_config(config)
m.delete_all(user_id="alex")
print("Deleted all memory")

# messages = [
#     {"role": "user", "content": "Hi, I'm Alex. I love basketball and gaming."},
#     {"role": "assistant", "content": "Hey Alex! I'll remember your interests."}
# ]

# add_with_dedup(m, messages, user_id="alex", infer=False) # infer (bool, optional): If True (default), an LLM is used to extract key facts from 'messages' and decide whether to add, update, or delete related memories. If False, 'messages' are added as raw memories directly.

# results = m.search("What do you know about me?",filters={"user_id": "alex"})
# print(results)