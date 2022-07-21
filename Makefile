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
	docker compose -f docker-compose.yml -f docker-compose.lenses.yml logs -f -t
#	docker-compose -f docker-compose.lenses.yml up -d
#	docker-compose logs -f --tail=100

stop:
	docker compose -f docker-compose.yml -f docker-compose.main.yml down -t 4

restart:
	docker compose -f docker-compose.yml -f docker-compose.main.yml restart

rebuild:
	docker compose -f docker-compose.yml -f docker-compose.main.yml build

rebuildf:
	docker compose -f docker-compose.yml -f docker-compose.main.yml build --no-cache

reboot: stop start

startd:
	docker compose -f docker-compose.yml -f docker-compose.main.yml up -d

rebootd: stop startd

logs:
	docker compose -f docker-compose.yml -f docker-compose.main.yml logs -f -t

top:
	docker compose top

export:
	export $(cat .env | sed 's/#.*//g' | xargs)
