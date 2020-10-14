################################################################################
# fancy help target from https://marmelab.com/blog/2016/02/29/auto-documented-makefile.html
.PHONY: help
help:
	@fgrep -h " ## " $(MAKEFILE_LIST) | fgrep -v fgrep | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'

################################################################################
# Local docker development helpers.

.PHONY: builder
builder: ## Build the developer image
	docker build -f ./Dockerfile-builder -t toy-manifest-service-builder:latest .

.PHONY: build
build: builder ## Build the service
	docker-compose -f docker-compose.yml build

layers:
	mkdir layers

.PHONY: run
run: build  layers ## Run the service
	docker-compose -f docker-compose.yml up

.PHONY: shell
shell: build ## Run in shell in service container
	docker-compose -f docker-compose.yml run -v $$PWD/src:/code toy-manifest-service sh

.PHONY: test
test: builder ## Test the code using pytest
	docker-compose -f docker-compose-test.yml run --volume=$$PWD:/build toy-manifest-service-tester sh -c "pipenv install --dev; pipenv run pytest"
	docker-compose -f docker-compose-test.yml rm -v -f -s


.PHONY: sqitch
sqitch: ## Setup sqitch developer environment
	docker pull sqitch/sqitch:1.1.0
	curl -L https://git.io/JJKCn -o sqitch && chmod +x sqitch
	docker run -d --rm -p 5432:5432 -e POSTGRES_USER=manifests -e POSTGRES_PASSWORD=oci_comp-123 postgres:13
	./sqitch target -v
	./sqitch status toy_manifest_db_test
	./sqitch deploy toy_manifest_db_test

.PHONY: build-db
build-db: ## Build the postgres database image with sqitch init script
	./sqitch bundle
	docker build -t toy-manifest-service-db -f Dockerfile-db .

.PHONY: testdb
testdb:
	docker run --rm -p 5432:5432 -e POSTGRES_USER=manifests -e POSTGRES_PASSWORD=oci_comp-123 postgres:13

################################################################################
# Housekeepking helpers.

.PHONY: clean
clean: ## Clean build directories and local docker artifacts
	docker-compose -f docker-compose.yml rm -f -v -s
	docker-compose -f docker-compose-test.yml rm -f -v -s
	docker rmi -f toy-manifest-service-builder:latest
	docker rmi -f toy-manifest-service:latest
