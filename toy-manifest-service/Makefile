################################################################################
# fancy help target from https://marmelab.com/blog/2016/02/29/auto-documented-makefile.html
.PHONY: help
help:
	@fgrep -h " ## " $(MAKEFILE_LIST) | fgrep -v fgrep | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'

################################################################################
# Local docker development helpers.

DOCKER_COMPOSE ?= docker-compose
SERVICE_NAME = toy-manifest-service

.PHONY: builder
builder: ## Build the developer image
	docker build -f ./Dockerfile-builder -t $(SERVICE_NAME)-builder:latest .

.PHONY: build
build: builder ## Build the service
	$(DOCKER_COMPOSE) -f docker-compose.yml build

layers:
	mkdir layers

.PHONY: run
run: build  layers ## Run the service
	$(DOCKER_COMPOSE) -f docker-compose.yml up

.PHONY: shell
shell: build ## Run in shell in service container
	$(DOCKER_COMPOSE) -f docker-compose.yml run -v $$PWD/src:/code $(SERVICE_NAME) /bin/sh

.PHONY: test
test: builder ## Test the code using pytest
	docker run -ti --rm -v $$PWD/src:/code $(SERVICE_NAME)-builder pipenv install --dev; pipenv run pytest


################################################################################
# Housekeepking helpers.

.PHONY: clean
clean: ## Clean build directories and local docker artifacts
	docker-compose rm -f -v
	docker rmi -f $(SERVICE_NAME)-builder:latest
	docker rmi -f $(SERVICE_NAME):latest
	docker volume rm -f toy-manifest-service_db_data
