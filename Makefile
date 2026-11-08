include docker/.env

BUILD_PRINT = \e[1;34mSTEP: \e[0m


install-os-dependencies-redhat:
	@ ./bash/install_os_dependencies.sh

install-python-dependencies-redhat:
	@ ./bash/setup_python.sh

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
	@ sudo apt install git python3-pip redis-server python3.8-venv curl

run-local-redis-ubuntu:
	@ sudo cp docker/redis.conf /etc/redis/redis.conf
	@ sudo systemctl restart redis.service

install-python-dependencies-ubuntu:
	@ echo "$(BUILD_PRINT)Installing the production requirements"
	@ python3 -m venv env
	@ pip install --upgrade pip
	@ uv sync

#-----------------------------------------------------------------------------
# Basic commands
#-----------------------------------------------------------------------------
install:
	@ echo "$(BUILD_PRINT)Installing the dependencies"
	@ uv sync

test:
	@ echo "$(BUILD_PRINT)Running the tests"
	@ uv run pytest

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
# Gherkin feature and acceptance test generation commands
#-----------------------------------------------------------------------------

FEATURES_FOLDER = tests/features
STEPS_FOLDER = tests/steps
FEATURE_FILES := $(wildcard $(FEATURES_FOLDER)/*.feature)
EXISTENT_TEST_FILES = $(wildcard $(STEPS_FOLDER)/*.py)
HYPOTHETICAL_TEST_FILES :=  $(addprefix $(STEPS_FOLDER)/test_, $(notdir $(FEATURE_FILES:.feature=.py)))
TEST_FILES := $(filter-out $(EXISTENT_TEST_FILES),$(HYPOTHETICAL_TEST_FILES))

generate-tests-from-features: $(TEST_FILES)
	@ echo "$(BUILD_PRINT)The following test files should be generated: $(TEST_FILES)"
	@ echo "$(BUILD_PRINT)Done generating missing feature files"
	@ echo "$(BUILD_PRINT)Verifying if there are any missing step implementations"
	@ py.test --generate-missing --feature $(FEATURES_FOLDER)

$(addprefix $(STEPS_FOLDER)/test_, $(notdir $(STEPS_FOLDER)/%.py)): $(FEATURES_FOLDER)/%.feature
	@ echo "$(BUILD_PRINT)Generating the testfile "$@"  from "$<" feature file"
	@ pytest-bdd generate $< > $@
	@ sed -i  's|features|../features|' $@
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
