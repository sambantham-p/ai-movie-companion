# Movie Companion developer commands. Run `make help` for the list.
# Backend commands run through uv inside backend/; frontend commands through npm inside frontend/.

SHELL := /bin/bash
.DEFAULT_GOAL := help

BACKEND  := backend
FRONTEND := frontend
COMPOSE  := docker compose -f infra/docker-compose.yml
UV       := cd $(BACKEND) && uv run
NPM      := cd $(FRONTEND) && npm

.PHONY: help setup setup-backend setup-frontend env \
        infra-up infra-down infra-reset migrate migration \
        api web worker-jobs worker-browser browser-selfcheck chrome-cdp \
        test test-backend test-backend-unit test-frontend \
        lint lint-backend lint-frontend format build check clean \
        security security-code security-secrets security-deps

help: ## List all commands
	@grep -hE '^[a-zA-Z_-]+:.*?## ' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'

# --- Setup ----------------------------------------------------------------------------

setup: setup-backend setup-frontend env ## Install everything and create local env files

setup-backend: ## uv sync with the browser extra and dev tools
	cd $(BACKEND) && uv sync --extra browser

setup-frontend: ## npm ci
	$(NPM) ci

env: ## Create backend/.env and frontend/.env.local from examples (never overwrites)
	@test -f $(BACKEND)/.env || (cp $(BACKEND)/.env.example $(BACKEND)/.env && echo "created backend/.env")
	@test -f $(FRONTEND)/.env.local || (cp $(FRONTEND)/.env.example $(FRONTEND)/.env.local && echo "created frontend/.env.local")

# --- Infrastructure -------------------------------------------------------------------

infra-up: ## Start Postgres + Redis (Docker, 127.0.0.1 only)
	$(COMPOSE) up -d --wait

infra-down: ## Stop Postgres + Redis (data kept)
	$(COMPOSE) down

infra-reset: ## Stop Postgres + Redis and DELETE their data
	$(COMPOSE) down -v

migrate: ## Apply Alembic migrations
	$(UV) alembic upgrade head

migration: ## Create a migration: make migration m="add movies table"
	@test -n "$(m)" || (echo 'usage: make migration m="message"' && exit 1)
	$(UV) alembic revision --autogenerate -m "$(m)"

# --- Run ------------------------------------------------------------------------------

api: ## Run the FastAPI server (reload) on :8000
	$(UV) mc-api

web: ## Run the Vite dev server on :5173
	$(NPM) run dev

worker-jobs: ## Run the cloud-safe jobs worker
	$(UV) arq movie_companion.jobs.worker.WorkerSettings

worker-browser: ## Run the browser worker (home machine only)
	$(UV) arq movie_companion.browser.worker.WorkerSettings

browser-selfcheck: ## Open Chrome on a local test page and close it (never visits BookMyShow)
	$(UV) python -m movie_companion.browser.selfcheck

chrome-cdp: ## Start Chrome with the dedicated profile for BROWSER_MODE=cdp
	./scripts/start-chrome-cdp.sh

# --- Quality --------------------------------------------------------------------------

test: test-backend test-frontend ## All tests with coverage gates (>= 85%)

# Test suites are kept locally (not in the public repo); without them these targets no-op.
HAS_BACKEND_TESTS  := $(wildcard $(BACKEND)/tests)
HAS_FRONTEND_TESTS := $(wildcard $(FRONTEND)/src/test)

test-backend: ## Backend unit + integration tests with coverage
	$(if $(HAS_BACKEND_TESTS),$(UV) pytest --cov --cov-report=term-missing,@echo "No backend tests in this checkout; skipping.")

test-backend-unit: ## Backend unit tests only (no services needed)
	$(if $(HAS_BACKEND_TESTS),$(UV) pytest tests/unit,@echo "No backend tests in this checkout; skipping.")

test-frontend: ## Frontend tests with coverage
	$(if $(HAS_FRONTEND_TESTS),$(NPM) run coverage,@echo "No frontend tests in this checkout; skipping.")

lint: lint-backend lint-frontend ## All linters and type checks

lint-backend: ## ruff lint + format check, mypy strict
	$(UV) ruff check .
	$(UV) ruff format --check .
	$(UV) mypy

lint-frontend: ## oxlint, prettier check, tsc
	$(NPM) run lint
	$(NPM) run format:check
	$(NPM) run typecheck

format: ## Auto-format backend and frontend
	$(UV) ruff format .
	$(UV) ruff check --fix .
	$(NPM) run format

build: ## Production build of the frontend
	$(NPM) run build

# --- Security (free, open source; versions pinned for reproducible results) ---------------

SEMGREP   := uvx semgrep@1.184.0
PIP_AUDIT := uvx pip-audit@2.10.1
SEMGREP_RULES := --config p/python --config p/fastapi --config p/typescript --config p/react \
                 --config p/secrets

security: security-code security-secrets security-deps ## All security scans

security-code: ## Semgrep static analysis (bugs + security) on backend and frontend source
	$(SEMGREP) scan $(SEMGREP_RULES) --metrics=off --error --quiet backend/src frontend/src

security-secrets: ## gitleaks: no secrets anywhere in the repo (config: .gitleaks.toml)
	gitleaks dir --no-banner --redact --config .gitleaks.toml .

security-deps: ## Known-vulnerability audit of Python and npm dependencies
	cd $(BACKEND) && uv export --frozen --no-hashes --no-emit-project --all-extras \
		--format requirements-txt -o .audit-requirements.txt >/dev/null
	$(PIP_AUDIT) -r $(BACKEND)/.audit-requirements.txt --progress-spinner off; \
		status=$$?; rm -f $(BACKEND)/.audit-requirements.txt; exit $$status
	$(NPM) audit --audit-level=high

check: lint security test build ## What CI runs

clean: ## Remove caches, coverage and build output
	rm -rf $(BACKEND)/.pytest_cache $(BACKEND)/.mypy_cache $(BACKEND)/.ruff_cache \
		$(BACKEND)/.coverage $(BACKEND)/htmlcov $(FRONTEND)/dist $(FRONTEND)/coverage
