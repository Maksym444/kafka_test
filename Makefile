.DEFAULT_GOAL := default

ifneq (,$(wildcard ./.env))
    include .env
    export
endif

# ----------------------------------------------------------------------------------------------------------------------

default: rebootd logs

help: ## This help
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)

start: ## Start all containers
	docker compose  -f docker-compose.yml -f docker-compose.main.yml up \
		--scale telegram_fetcher=${CONSUMER_SCALE_FACTOR} \
		--scale processor=${PROCESSOR_SCALE_FACTOR}

startd: ## Srart all containers (detached)
	docker compose -f docker-compose.yml -f docker-compose.main.yml up -d \
		--scale telegram_fetcher=${CONSUMER_SCALE_FACTOR} \
		--scale processor=${PROCESSOR_SCALE_FACTOR}

lenses: ## Start with kafka-lenses (diagnosis tool)
	docker compose -f docker-compose.yml -f docker-compose.lenses.yml down -t 1
	docker compose -f docker-compose.yml -f docker-compose.lenses.yml up -d
	docker compose -f docker-compose.yml -f docker-compose.lenses.yml logs -f -t --tail=100

stop: ## Stop all containers
	docker compose -f docker-compose.yml -f docker-compose.main.yml down

restart: ## Restart all containers
	docker compose -f docker-compose.yml -f docker-compose.main.yml restart

build: ## Build all or c=name container images
	docker compose -f docker-compose.yml -f docker-compose.main.yml -f docker-compose.test.yml build ${c}

buildf: ## Build all or c=name container images (force)
	docker compose -f docker-compose.yml -f docker-compose.main.yml -f docker-compose.test.yml build --no-cache ${c}

reboot: stop start ## Reboot all containers

rebootd: stop startd ## Reboot all containers (detached)

logs: ## Show all or c=name container logs.
	docker compose -f docker-compose.yml -f docker-compose.main.yml logs -f -t --tail=100 ${c}

top: ## Show list of containers (extended)
	docker compose top

ps: ## Show list of containers
	docker compose ps

bash: ## Run bash in c=<name> service container
	docker compose exec -it $(c) bash


# ----------------------------------------------------------------------------------------------------------------------
tests: ## Run all tests.
	docker compose  -f docker-compose.yml -f docker-compose.main.yml -f docker-compose.test.yml down -t 1
	docker compose  -f docker-compose.yml -f docker-compose.main.yml -f docker-compose.test.yml up \
		--scale telegram_fetcher=${CONSUMER_SCALE_FACTOR} \
		--scale processor=${PROCESSOR_SCALE_FACTOR}

testsd: ## Run all tests (detached)
	docker compose  -f docker-compose.yml -f docker-compose.main.yml -f docker-compose.test.yml down -t 1
	docker compose  -f docker-compose.yml -f docker-compose.main.yml -f docker-compose.test.yml up -d \
		--scale telegram_fetcher=${CONSUMER_SCALE_FACTOR} \
		--scale processor=${PROCESSOR_SCALE_FACTOR}


# ----------------------------------------------------------------------------------------------------------------------
export: ## Export env vars
	export $(cat .env | sed 's/#.*//g' | xargs)
