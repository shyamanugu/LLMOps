# Backend developer tasks. Mirrors what CI runs (pr-checks.yml) so "make check"
# locally == the PR gate. Uses the current Python; create a venv first if desired.
#
#   make install   install runtime + dev + eval extras (editable)
#   make lint      ruff + black --check + mypy (non-mutating; matches CI)
#   make format    apply black + ruff --fix
#   make test      pytest (unit; integration skipped without live Azure)
#   make run       run the API locally with reload
#   make eval      run the evaluation gate on changed use cases
#   make check     lint + test (the fast pre-push gate)

PY ?= python
PORT ?= 8000
SUBSET ?= changed

.DEFAULT_GOAL := help
.PHONY: help install lint format test test-all run eval check clean

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-12s\033[0m %s\n", $$1, $$2}'

install: ## Install package with dev + eval extras (editable)
	$(PY) -m pip install --upgrade pip
	$(PY) -m pip install -e ".[dev,eval]"

lint: ## Static checks: ruff, black --check, mypy (matches CI, non-mutating)
	$(PY) -m ruff check .
	$(PY) -m black --check .
	$(PY) -m mypy src

format: ## Auto-fix formatting/imports
	$(PY) -m ruff check --fix .
	$(PY) -m black .

test: ## Unit tests (integration tests skipped without live services)
	$(PY) -m pytest -m "not integration" --cov=llmops --cov-report=term-missing

test-all: ## All tests including @integration (needs live Azure/Langfuse)
	$(PY) -m pytest

run: ## Run the API locally with autoreload
	$(PY) -m uvicorn llmops.api.main:app --reload --host 0.0.0.0 --port $(PORT)

eval: ## Run the evaluation gate (SUBSET=changed|full)
	$(PY) evals/run.py --subset $(SUBSET) --fail-under baseline

check: lint test ## Fast pre-push gate: lint + unit tests

clean: ## Remove caches and build artifacts
	rm -rf .pytest_cache .mypy_cache .ruff_cache htmlcov .coverage build dist *.egg-info
	find . -type d -name __pycache__ -prune -exec rm -rf {} +
