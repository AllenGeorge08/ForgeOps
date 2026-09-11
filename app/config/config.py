# Meta-Muse later
from dotenv import load_dotenv
import os

from langchain_groq import ChatGroq 
from langchain_nvidia_ai_endpoints import ChatNVIDIA



load_dotenv()


try:
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")
    print("Groq API Key Loaded")
except PermissionError:
    print("ERROR: GROQ API KEY NOT FOUND")


try:
    NVIDIA_API_KEY=os.getenv("NVIDIA_API_KEY")
    print("Nvidia API Key Loaded")
except PermissionError:
    print("ERROR: NVIDIA API KEY NOT FOUND")


# All working,tested
GUARDRAIL_MODEL = ChatGroq(
    model="qwen/qwen3.8-27b",
    max_retries=3
)

SUPERVISER_MODEL = ChatGroq(
    model="openai/gpt-oss-20b",
    max_retries=3
)

FINAL_MODEL = ChatGroq(
    model="openai/gpt-oss-20b",
    max_retries=3
)

GITHUB_MODEL = ChatGroq(
    model="openai/gpt-oss-120b",
    max_retries=3
)

CI_CD_MODEL = ChatNVIDIA(
    model="nvidia/nemotron-3-nano-omni-30b-a3b-reasoning",
    temperature=0.6,
    api_key=NVIDIA_API_KEY
)

# Need a stronger model here
INVESTIGATION_MODEL = ChatNVIDIA(
    model="nvidia/nemotron-3-ultra-550b-a55b",
    temperature=0.2,
    top_p=0.95
)





