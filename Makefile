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

dev:
	@ echo -e '$(BUILD_PRINT)(dev) Building the api and ui containers'
	@ docker-compose --file dev.yml --env-file docker/.env build fingerprinter-api fingerprinter-ui

prod:
	@ echo -e '$(BUILD_PRINT)(prod) Building the api and ui containers'
	@ docker-compose --file prod.yml --env-file docker/.env build fingerprinter-api fingerprinter-ui

start-dev:
	@ echo -e '$(BUILD_PRINT)(dev) Starting the api and ui containers'
	@ docker-compose --file dev.yml --env-file docker/.env up -d fingerprinter-api fingerprinter-ui

stop-dev:
	@ echo -e '$(BUILD_PRINT)(dev) Stopping the api and ui containers'
	@ docker-compose --file dev.yml --env-file docker/.env stop fingerprinter-api fingerprinter-ui

start-prod:
	@ echo -e '$(BUILD_PRINT)(prod) Starting the api and ui containers'
	@ docker-compose --file prod.yml --env-file docker/.env up -d fingerprinter-api fingerprinter-ui

stop-prod:
	@ echo -e '$(BUILD_PRINT)(prod) Stopping the api and  ui containers'
	@ docker-compose --file prod.yml --env-file docker/.env stop fingerprinter-api fingerprinter-ui
