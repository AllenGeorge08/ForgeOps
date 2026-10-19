# ForgeOps Dockerfile
#
# Build:
#   docker build -t forgeops .
#
# Run (inject secrets at runtime, never bake .env into the image):
#   docker run -p 8000:8000 --env-file .env forgeops
#
# Required env vars (see .env.example):
#   GROQ_API_KEY, OPENROUTER_API_KEY,
#   GITHUB_ACCESS_TOKEN, SLACK_BOT_AUTH_TOKEN, SLACK_TEAM_ID

FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir \
    fastapi==0.141.1 \
    uvicorn[standard]==0.52.4 \
    python-dotenv==1.2.3 \
    pydantic==2.12.5 \
    langgraph \
    langchain-groq==1.1.3 \
    langchain-openrouter==0.2.9 \
    langchain-core==1.6.3 \
    mem0ai==2.1.0 \
    langchain-mcp-adapters==0.3.2 \
    qdrant-client==1.19.1

# Copy application code
COPY app ./app
COPY pyproject.toml ./

# Copy env template only (do NOT copy .env - secrets are injected at runtime)
COPY .env.example .env.example

# Expose FastAPI port
EXPOSE 8000

# Run the API
CMD ["uvicorn", "app.api.app:application", "--host", "0.0.0.0", "--port", "8000"]
