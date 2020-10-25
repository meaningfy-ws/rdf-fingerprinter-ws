include docker/.env

BUILD_PRINT = \e[1;34mSTEP: \e[0m

#-----------------------------------------------------------------------------
# Basic commands
#-----------------------------------------------------------------------------

install-dev:
	@ echo "$(BUILD_PRINT)Installing the local requirements"
	@ pip install --upgrade pip
	@ pip install -r requirements/dev.txt

install-prod:
	@ echo "$(BUILD_PRINT)Installing the production requirements"
	@ pip install --upgrade pip
	@ pip install -r requirements.txt

test:
	@ echo "$(BUILD_PRINT)Running the tests"
	@ pytest

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
	@ echo "$(BUILD_PRINT)Building 'test-dataset' dataset at http://localhost:$(if $(RDF_FINGERPRINTER_FUSEKI_PORT),$(RDF_FINGERPRINTER_FUSEKI_PORT),unknown port)/$$/datasets"
	@ sleep 2
	@ curl --anyauth --user 'admin:$(RDF_FINGERPRINTER_FUSEKI_ADMIN_PASSWORD)' -d 'dbType=mem&dbName=test-dataset'  'http://fuseki:3020/$$/datasets'
	@ curl -X POST -H content-type:application/rdf+xml -T ./tests/resources/treaties-source-ap.rdf -G http://localhost:$(RDF_FINGERPRINTER_FUSEKI_PORT)/test-dataset/data

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