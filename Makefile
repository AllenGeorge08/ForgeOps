PYTHON ?= python
.DEFAULT_GOAL := help

.PHONY: help run investigate test

help:
	@echo "make run agent=<name>  -  run any agent module"
	@echo "make investigate       -  run investigation agent"
	@echo "make test              -  run pytest"

run:
	$(PYTHON) -m app.agents.$(agent)

investigate:
	$(PYTHON) -m app.agents.investigation_agent

test:
	$(PYTHON) -m pytest