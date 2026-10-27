PYTHON ?= python
.DEFAULT_GOAL := help

.PHONY: help run investigate test test-github test-cicd test-slack test-investigation test-memory test-api test-all docker-build docker-run docker-clean

help:
	@echo " ForgeOps — Available Commands"
	@echo ""
	@echo "  make run agent=<name>        Run any agent module directly"
	@echo "  make investigate             Run investigation agent"
	@echo "  make test                    Run all unit tests"
	@echo "  make test-github             Run GitHub agent tests"
	@echo "  make test-cicd               Run CI/CD agent tests"
	@echo "  make test-slack              Run Slack agent tests"
	@echo "  make test-investigation      Run investigation agent tests"
	@echo "  make test-memory             Run memory layer tests"
	@echo "  make test-api                Run FastAPI endpoint tests"
	@echo "  make test-all                Run every test suite"
	@echo ""
	@echo "  make docker-build            Build the ForgeOps Docker image"
	@echo "  make docker-run              Run ForgeOps via Docker Compose"
	@echo "  make docker-clean            Stop and remove containers"

run:
	$(PYTHON) -m app.agents.$(agent)

investigate:
	$(PYTHON) -m app.agents.investigation_agent

test:
	$(PYTHON) -m pytest

test-github:
	$(PYTHON) -m pytest tests/agents/test_github_agent.py -v

test-cicd:
	$(PYTHON) -m pytest tests/agents/test_cicd_agent.py -v

test-slack:
	$(PYTHON) -m pytest tests/agents/test_slack_agent.py -v

test-investigation:
	$(PYTHON) -m pytest tests/agents/test_investigation_agent.py -v

test-memory:
	$(PYTHON) -m pytest tests/memory/test_memory_layer.py -v

test-api:
	$(PYTHON) -m pytest tests/api/test_api.py -v

test-all: test test-github test-cicd test-slack test-investigation test-memory test-api

docker-build:
	docker build -t forgeops .

docker-run:
	docker compose up --build

docker-clean:
	docker compose down --remove-orphans
