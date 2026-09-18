# Meta-Muse later
from dotenv import load_dotenv
import os

from langchain_groq import ChatGroq
from langchain_nvidia_ai_endpoints import ChatNVIDIA
from langchain_core.rate_limiters import InMemoryRateLimiter


load_dotenv()


try:
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")
    print("Groq API Key Loaded")
except PermissionError:
    print("ERROR: GROQ API KEY NOT FOUND")


try:
    NVIDIA_API_KEY = os.getenv("NVIDIA_API_KEY")
    print("Nvidia API Key Loaded")
except PermissionError:
    print("ERROR: NVIDIA API KEY NOT FOUND")


guardrail_rate_limiter = InMemoryRateLimiter(
    requests_per_second=1.0,
    check_every_n_seconds=0.005,#pooll every 1 ms to reduce execution latency
    max_bucket_size=5 #tight burst 
)

# All working,tested
GUARDRAIL_MODEL = ChatGroq(model="qwen/qwen3.8-27b", max_retries=3, rate_limiter=guardrail_rate_limiter,max_tokens=300,reasoning_effort="low")

SUPERVISER_MODEL = ChatGroq(model="openai/gpt-oss-20b", max_retries=3)

FINAL_MODEL = ChatGroq(model="qwen/qwen3.8-27b", max_retries=3)
MEMORY_MODEL= ChatGroq(model="qwen/qwen3.8-27b", max_retries=3)

GITHUB_MODEL = ChatGroq(model="openai/gpt-oss-120b", max_retries=3)

CI_CD_MODEL = ChatNVIDIA(
    model="nvidia/nemotron-3-nano-omni-30b-a3b-reasoning",
    temperature=0.6,
    api_key=NVIDIA_API_KEY,
)

# MEMORY_MODEL = ChatNVIDIA(
#     model="nvidia/nemotron-3-nano-omni-30b-a3b-reasoning",
#     temperature=0.6,
#     api_key=NVIDIA_API_KEY,
# )



# Need a stronger model here
INVESTIGATION_MODEL = ChatNVIDIA(
    model="nvidia/nemotron-3-ultra-550b-a55b", temperature=0.2, top_p=0.95
)


GITHUB_READ_TOOLS = [
    "pull_request_read",
    "list_pull_requests",
    "get_commit",
    "list_commits",
    "get_file_contents",
    "search_code",
    "search_commits",
    "search_pull_requests",
    "search_issues",
    "issue_read",
    "list_branches",
]

SLACK_READ_TOOLS = [
    "slack_list_channels",
    "slack_get_channel_history",
    "slack_get_thread_replies",
    "slack_get_users",
    "slack_get_user_profile",
]

CICD_TOOLS = [
    "actions_get",
    "actions_list",
    "get_job_logs",
    "get_commit",
]
