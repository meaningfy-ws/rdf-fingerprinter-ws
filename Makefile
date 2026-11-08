SHELL = /bin/bash -o pipefail

BUILD_PRINT     = \e[1;34m
END_BUILD_PRINT = \e[0m

ICON_DONE     = [done]
ICON_ERROR    = [x]
ICON_PROGRESS = [-]

# No-src layout: the top-level package lives at the repo root.
REPO_ROOT    = $(shell pwd)
PACKAGE_NAME = fingerprinter
TEST_PATH    = $(REPO_ROOT)/tests

# Coverage flags — appended only in coverage-aware targets, never in pytest.ini.
COV_FLAGS = --cov=$(PACKAGE_NAME) \
            --cov-report=term-missing \
            --cov-report=xml:$(REPO_ROOT)/coverage.xml \
            --cov-fail-under=80

# The unit lane never collects the container tests.
UNIT_LANE = --ignore=$(TEST_PATH)/integration --ignore=$(TEST_PATH)/e2e

COMPOSE_FILE     = $(REPO_ROOT)/infra/compose.yaml
COMPOSE_DEV_FILE = $(REPO_ROOT)/infra/compose.dev.yaml
ENV_FILE         = $(REPO_ROOT)/infra/.env
COMPOSE          = docker compose -f $(COMPOSE_FILE) --env-file $(ENV_FILE)
# The development override also publishes Redis, Fuseki and PlantUML on 127.0.0.1.
COMPOSE_DEV      = docker compose -f $(COMPOSE_FILE) -f $(COMPOSE_DEV_FILE) --env-file $(ENV_FILE)
PROJECT_NAME     = rdf-fingerprinter-ws

.DEFAULT_GOAL := help
.PHONY: help install-uv install lock format lint lint-fix typecheck check-architecture check-spec \
        test test-unit test-feature test-containers check-quality check-all \
        init-env check-env up up-dev up-deps down rebuild build-images logs run-api run-ui run-worker

#-----------------------------------------------------------------------------
# Setup
#-----------------------------------------------------------------------------
help: ## Display available targets
	@ echo -e "$(BUILD_PRINT)Available targets:$(END_BUILD_PRINT)"
	@ grep -hE '^[a-zA-Z0-9_-]+:.*?## .*$$' $(MAKEFILE_LIST) \
		| sort \
		| awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-22s\033[0m %s\n", $$1, $$2}'

install-uv: ## Install uv if not present
	@ command -v uv >/dev/null || curl -LsSf https://astral.sh/uv/0.13.5/install.sh | sh

install: install-uv ## Install the project dependencies (all groups; does NOT lock)
	@ echo -e "$(BUILD_PRINT)$(ICON_PROGRESS) Installing dependencies$(END_BUILD_PRINT)"
	@ uv sync
	@ echo -e "$(BUILD_PRINT)$(ICON_DONE) Dependencies installed$(END_BUILD_PRINT)"

lock: ## Update uv.lock
	@ uv lock

#-----------------------------------------------------------------------------
# Code quality
#-----------------------------------------------------------------------------
format: ## Format code with Ruff
	@ uv run ruff format $(PACKAGE_NAME) $(TEST_PATH)

lint-fix: ## Run Ruff checks with auto-fix
	@ uv run ruff check --fix $(PACKAGE_NAME) $(TEST_PATH)

lint: ## Run Ruff lint and format checks
	@ echo -e "$(BUILD_PRINT)$(ICON_PROGRESS) Running Ruff checks$(END_BUILD_PRINT)"
	@ uv run ruff check $(PACKAGE_NAME) $(TEST_PATH)
	@ uv run ruff format --check $(PACKAGE_NAME) $(TEST_PATH)
	@ echo -e "$(BUILD_PRINT)$(ICON_DONE) Ruff checks passed$(END_BUILD_PRINT)"

typecheck: ## Run mypy type checks
	@ echo -e "$(BUILD_PRINT)$(ICON_PROGRESS) Running mypy$(END_BUILD_PRINT)"
	@ uv run mypy $(PACKAGE_NAME)
	@ echo -e "$(BUILD_PRINT)$(ICON_DONE) Type checks passed$(END_BUILD_PRINT)"

check-architecture: ## Check architecture constraints with import-linter
	@ echo -e "$(BUILD_PRINT)$(ICON_PROGRESS) Checking architecture constraints$(END_BUILD_PRINT)"
	@ uv run lint-imports --config $(REPO_ROOT)/.importlinter
	@ echo -e "$(BUILD_PRINT)$(ICON_DONE) Architecture checks passed$(END_BUILD_PRINT)"

check-spec: ## Validate the OpenSpec specs and every change that carries spec deltas (pinned CLI, strict)
	@ npx -y --prefer-offline @fission-ai/openspec@1.4.1 validate --specs --strict --no-interactive
	@ for change in $$(ls -d openspec/changes/*/specs 2>/dev/null | cut -d/ -f3); do \
		npx -y --prefer-offline @fission-ai/openspec@1.4.1 validate "$$change" --type change --strict --no-interactive || exit 1; \
	done

check-quality: lint typecheck check-architecture check-spec check-docs ## Static checks: lint + typecheck + architecture + spec + docs
	@ echo -e "$(BUILD_PRINT)$(ICON_DONE) All quality checks passed$(END_BUILD_PRINT)"

check-all: check-quality test ## Full suite: quality + unit and feature tests
	@ echo -e "$(BUILD_PRINT)$(ICON_DONE) Full verification suite passed$(END_BUILD_PRINT)"

#-----------------------------------------------------------------------------
# Tests
#-----------------------------------------------------------------------------
test: ## Run the unit and feature tests, with the coverage floor
	@ echo -e "$(BUILD_PRINT)$(ICON_PROGRESS) Running unit and feature tests$(END_BUILD_PRINT)"
	@ uv run pytest $(TEST_PATH) $(UNIT_LANE) -m "unit or feature" $(COV_FLAGS) --junitxml=$(REPO_ROOT)/test-results.xml
	@ echo -e "$(BUILD_PRINT)$(ICON_DONE) Unit and feature tests passed$(END_BUILD_PRINT)"

test-containers: ## Run the integration and e2e tests against Docker containers (no coverage floor)
	@ echo -e "$(BUILD_PRINT)$(ICON_PROGRESS) Running container tests$(END_BUILD_PRINT)"
	@ uv run pytest $(TEST_PATH) -m "integration or e2e" $(COV_FLAGS) --cov-report=xml:$(REPO_ROOT)/coverage-containers.xml --cov-fail-under=0 --junitxml=$(REPO_ROOT)/test-results-containers.xml
	@ echo -e "$(BUILD_PRINT)$(ICON_DONE) Container tests passed$(END_BUILD_PRINT)"

test-unit: ## Run unit tests only
	@ uv run pytest $(TEST_PATH) $(UNIT_LANE) -m "unit"

test-feature: ## Run BDD feature tests only
	@ uv run pytest $(TEST_PATH) $(UNIT_LANE) -m "feature"

#-----------------------------------------------------------------------------
# Stack (docker compose) and local runs; settings in infra/.env (cp infra/.env.example infra/.env)
#-----------------------------------------------------------------------------
init-env: ## Write infra/.env from the example with random secrets (refuses to overwrite one)
	@ test ! -e $(ENV_FILE) || (echo -e "$(ICON_ERROR) $(ENV_FILE) exists: not overwritten" && exit 1)
	@ umask 077; while IFS= read -r line; do \
		case "$$line" in \
			*=change-me) printf '%s=%s\n' "$${line%%=*}" "$$(openssl rand -hex 32)";; \
			*) printf '%s\n' "$$line";; \
		esac; \
	done < $(REPO_ROOT)/infra/.env.example > $(ENV_FILE)
	@ echo -e "$(BUILD_PRINT)$(ICON_DONE) Wrote $(ENV_FILE) with random secrets$(END_BUILD_PRINT)"

check-env:
	@ test -f $(ENV_FILE) || (echo -e "$(ICON_ERROR) Missing $(ENV_FILE). Run: make init-env" && exit 1)
	@ ! grep -q '^[^#]*=change-me' $(ENV_FILE) || (echo -e "$(ICON_ERROR) $(ENV_FILE) still holds change-me: replace every one, or delete it and run: make init-env" && exit 1)

up: check-env ## Start the stack (docker compose up -d)
	@ $(COMPOSE) up -d

up-dev: check-env ## Start the stack with Redis, Fuseki and PlantUML also published on 127.0.0.1
	@ $(COMPOSE_DEV) up -d

up-deps: check-env ## Start only Redis, Fuseki and PlantUML (on 127.0.0.1), for run-api, run-ui and run-worker
	@ $(COMPOSE_DEV) up -d redis fuseki plantuml

down: ## Stop and remove the stack's containers (volumes stay; needs no infra/.env)
	@ docker compose -p $(PROJECT_NAME) down

rebuild: check-env ## Rebuild the images and start the stack (docker compose up -d --build)
	@ $(COMPOSE) up -d --build

# What CI runs: the compose file is valid and the three images build (nothing is pushed).
build-images: ## Check the compose file and build the api, ui and worker images
	@ set -e; created=; \
	if [ ! -f $(ENV_FILE) ]; then cp infra/.env.example $(ENV_FILE); created=1; fi; \
	trap '[ -z "$$created" ] || rm -f $(ENV_FILE)' EXIT; \
	docker compose -f $(COMPOSE_FILE) --env-file $(ENV_FILE) config -q; \
	docker compose -f $(COMPOSE_FILE) -f $(COMPOSE_DEV_FILE) --env-file $(ENV_FILE) config -q; \
	for target in api ui worker; do \
		docker build --target $$target -f infra/docker/Dockerfile -t rdf-fingerprinter-ws-$$target:check .; \
	done

logs: check-env ## Follow the stack's logs
	@ $(COMPOSE) logs -f

# Run one service on the host against the stack's Fuseki, Redis and PlantUML (make up-deps; published on 127.0.0.1 by the development override).
# Do not run them next to the full stack: both would take jobs from the same queue and split the job files.
LOCAL_RUN = set -a && . $(ENV_FILE) && set +a && \
	RDF_FINGERPRINTER_FUSEKI_LOCATION=http://localhost RDF_FINGERPRINTER_REDIS_LOCATION=redis://localhost \
	RDF_FINGERPRINTER_PLANTUML_LOCATION=http://localhost RDF_FINGERPRINTER_API_LOCATION=http://localhost

run-api: check-env ## Run the API on the host (needs `make up-deps`)
	@ $(LOCAL_RUN) uv run gunicorn --worker-class uvicorn_worker.UvicornWorker --bind 127.0.0.1:$$RDF_FINGERPRINTER_API_PORT 'fingerprinter.bootstrap:api_app()'

run-ui: check-env ## Run the UI on the host (needs the API)
	@ $(LOCAL_RUN) uv run gunicorn --worker-class gthread --threads $${RDF_FINGERPRINTER_GUNICORN_UI_THREADS:-8} --bind 127.0.0.1:$$RDF_FINGERPRINTER_UI_PORT 'fingerprinter.bootstrap:ui_app()'

run-worker: check-env ## Run the Celery worker on the host (needs `make up-deps`)
	@ $(LOCAL_RUN) uv run celery -A fingerprinter.bootstrap:celery_app worker --loglevel $$RDF_FINGERPRINTER_LOG_LEVEL

#-----------------------------------------------------------------------------
# Docs (Antora)
#-----------------------------------------------------------------------------
.PHONY: install-antora build-docs preview-docs check-docs clean-docs

DOCS_DIR  = docs
DOCS_SITE = $(DOCS_DIR)/build/site
DOCS_PORT ?= 8082

install-antora: ## Install the Antora doc toolchain (npm) in docs/
	@ cd $(DOCS_DIR) && npm install

build-docs: ## Build the documentation site from the working tree to docs/build/site/
	@ cd $(DOCS_DIR) && npx antora --fetch antora-playbook.local.yml

preview-docs: build-docs ## Build then serve the docs at http://localhost:$(DOCS_PORT)
	@ python3 -m http.server --directory $(DOCS_SITE) $(DOCS_PORT)

check-docs: ## Every docs page is in the navigation
	@ python3 -I $(DOCS_DIR)/tools/check_docs.py

clean-docs: ## Remove the built docs and node_modules
	@ rm -rf $(DOCS_DIR)/build $(DOCS_DIR)/node_modules
