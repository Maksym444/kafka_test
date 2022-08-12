.DEFAULT_GOAL := default

ifneq (,$(wildcard ./.env))
    include .env
    export
endif

# ----------------------------------------------------------------------------------------------------------------------

default: rebootd logs

start:
	docker compose  -f docker-compose.yml -f docker-compose.main.yml up

lenses:
	docker compose -f docker-compose.yml -f docker-compose.lenses.yml down -t 1
	docker compose -f docker-compose.yml -f docker-compose.lenses.yml up -d
	docker compose -f docker-compose.yml -f docker-compose.lenses.yml logs -f -t --tail=100

stop:
	docker compose -f docker-compose.yml -f docker-compose.main.yml down

restart:
	docker compose -f docker-compose.yml -f docker-compose.main.yml restart

rebuild:
	docker compose -f docker-compose.yml -f docker-compose.main.yml -f docker-compose.test.yml build

rebuildf:
	docker compose -f docker-compose.yml -f docker-compose.main.yml -f docker-compose.test.yml build --no-cache

rebuild-dev:
	docker compose -f docker-compose.yml -f docker-compose.main.yml  -f docker-compose.test.yml  build

rebuild-devf:
	docker compose -f docker-compose.yml -f docker-compose.main.yml  -f docker-compose.test.yml  build --no-cache

reboot: stop start

startd:
	docker compose -f docker-compose.yml -f docker-compose.main.yml up -d \
		--scale consumer=${CONSUMER_SCALE_FACTOR} \
		--scale processor=${PROCESSOR_SCALE_FACTOR}

rebootd: stop startd

logs:
	docker compose -f docker-compose.yml -f docker-compose.main.yml logs -f -t --tail=100

top:
	docker compose top

ps:
	docker compose ps


# ----------------------------------------------------------------------------------------------------------------------
tests:
	docker compose  -f docker-compose.yml -f docker-compose.main.yml -f docker-compose.test.yml down -t 1
	docker compose  -f docker-compose.yml -f docker-compose.main.yml -f docker-compose.test.yml up \
		--scale consumer=${CONSUMER_SCALE_FACTOR}

testsd:
	docker compose  -f docker-compose.yml -f docker-compose.main.yml -f docker-compose.test.yml down -t 1
	docker compose  -f docker-compose.yml -f docker-compose.main.yml -f docker-compose.test.yml up -d \
		--scale consumer=${CONSUMER_SCALE_FACTOR}


# ----------------------------------------------------------------------------------------------------------------------
export:
	export $(cat .env | sed 's/#.*//g' | xargs)
