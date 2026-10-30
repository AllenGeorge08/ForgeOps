# Meta-Muse later
from dotenv import load_dotenv
import os
from langchain_groq import ChatGroq
from langchain_core.rate_limiters import InMemoryRateLimiter
from langchain_openrouter import ChatOpenRouter
import getpass 
import os 

load_dotenv()


if not os.getenv("OPENROUTER_API_KEY"):
    os.environ["OPENROUTER_API_KEY"] = getpass.getpass("Enter your OpenRouter API key: ")

if not os.getenv("GROQ_API_KEY"):
    os.environ["GROQ_API_KEY"] = getpass.getpass("Enter your OpenRouter API key: ")


guardrail_rate_limiter = InMemoryRateLimiter(
    requests_per_second=1.0,
    check_every_n_seconds=0.005,#pooll every 1 ms to reduce execution latency
    max_bucket_size=5 #tight burst 
)

SUPERVISOR_MODEL = ChatOpenRouter(
    model="deepseek/deepseek-v4.1-flash-1017",
    max_retries=3,
    temperature=0.1,
)

FINAL_MODEL = ChatGroq(model="qwen/qwen3.8-27b", max_retries=3)
MEMORY_MODEL= ChatGroq(model="qwen/qwen3.8-27b", max_retries=3)

GITHUB_MODEL = ChatOpenRouter(model="openai/gpt-oss-120b", max_retries=3)

memoryllm_model = ChatGroq(model="openai/gpt-oss-20b", max_retries=3,)
SLACK_MODEL = ChatOpenRouter(model="openai/gpt-oss-120b", max_retries=3)
GUARDRAIL_MODEL = ChatOpenRouter(model="deepseek/deepseek-v4.1-flash-1017", max_retries=3,temperature=0.1,rate_limiter=guardrail_rate_limiter)
CI_CD_MODEL = ChatOpenRouter(model="meta-llama/llama-3.3-70b", max_retries=3)

# Need a stronger model here
INVESTIGATION_MODEL = ChatOpenRouter(model="deepseek/deepseek-v4.1-flash-1017", max_retries=3) 
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
