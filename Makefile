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

# The legacy docker/ and bash/ targets read their settings from docker/.env (stage 4 replaces both).
-include docker/.env

.DEFAULT_GOAL := help
.PHONY: help install-uv install lock format lint lint-fix typecheck check-architecture check-spec \
        test test-unit test-feature check-quality check-all

#-----------------------------------------------------------------------------
# Setup
#-----------------------------------------------------------------------------
help: ## Display available targets
	@ echo -e "$(BUILD_PRINT)Available targets:$(END_BUILD_PRINT)"
	@ grep -hE '^[a-zA-Z0-9_-]+:.*?## .*$$' $(MAKEFILE_LIST) \
		| sort \
		| awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-22s\033[0m %s\n", $$1, $$2}'

install-uv: ## Install uv if not present
	@ command -v uv >/dev/null || curl -LsSf https://astral.sh/uv/install.sh | sh

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
	@ npx -y @fission-ai/openspec@1.4.1 validate --specs --strict --no-interactive
	@ for change in $$(ls -d openspec/changes/*/specs 2>/dev/null | cut -d/ -f3); do \
		npx -y @fission-ai/openspec@1.4.1 validate "$$change" --type change --strict --no-interactive || exit 1; \
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

test-unit: ## Run unit tests only
	@ uv run pytest $(TEST_PATH) $(UNIT_LANE) -m "unit"

test-feature: ## Run BDD feature tests only
	@ uv run pytest $(TEST_PATH) $(UNIT_LANE) -m "feature"

#-----------------------------------------------------------------------------
# Legacy local-run targets (removed in stage 4, DEC-14)
#-----------------------------------------------------------------------------
install-os-dependencies-redhat:
	@ ./bash/install_os_dependencies.sh

run-local-api:
	@ ./bash/run_api.sh

run-local-ui:
	@ ./bash/run_ui.sh

run-local-redis-redhat:
	@ sudo systemctl enable redis --now

stop-local-gunicorn:
	@ ./bash/stop_gunicorn.sh
#------------------------------------------------------------------------------
# Ubuntu related commands
#------------------------------------------------------------------------------

install-os-dependencies-ubuntu:
	@ sudo apt install git python3-pip redis-server curl

run-local-redis-ubuntu:
	@ sudo cp docker/redis.conf /etc/redis/redis.conf
	@ sudo systemctl restart redis.service

#-----------------------------------------------------------------------------
# Service commands
#-----------------------------------------------------------------------------
build-services:
	@ echo -e '$(BUILD_PRINT)Building the containers'
	@ docker-compose --file docker/docker-compose.yml --env-file docker/.env build

start-services:
	@ echo -e '$(BUILD_PRINT)(dev) Starting the containers'
	@ docker-compose --file docker/docker-compose.yml --env-file docker/.env up -d

stop-services:
	@ echo -e '$(BUILD_PRINT)(dev) Stopping the containers'
	@ docker-compose --file docker/docker-compose.yml --env-file docker/.env stop

#-----------------------------------------------------------------------------
# Fuseki helpers
#-----------------------------------------------------------------------------

fuseki-create-test-dbs:
	@ echo "$(BUILD_PRINT)Building "test-dataset" at http://localhost:$(if $(RDF_FINGERPRINTER_FUSEKI_ADMIN_PASSWORD),$(RDF_DIFFER_FUSEKI_PORT),unknown port)/$$/datasets"
	@ sleep 7
	@ curl -v --anyauth --user 'admin:$(RDF_FINGERPRINTER_FUSEKI_ADMIN_PASSWORD)' -d 'dbType=mem&dbName=test-dataset'  'http://localhost:$(RDF_FINGERPRINTER_FUSEKI_PORT)/$$/datasets'
	@ curl -v -X POST -H content-type:application/rdf+xml --anyauth --user 'admin:$(RDF_FINGERPRINTER_FUSEKI_ADMIN_PASSWORD)' -T ./tests/resources/treaties-source-ap.rdf -G http://localhost:$(RDF_FINGERPRINTER_FUSEKI_PORT)/test-dataset/data

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
