.DEFAULT_GOAL := default

ifneq (,$(wildcard ./.env))
    include .env
    export
endif

# ----------------------------------------------------------------------------------------------------------------------

default: reboot

start:
	docker-compose up

lenses:
	docker compose -f docker-compose.lenses.yml down -t 1
	docker compose -f docker-compose.lenses.yml up
#	docker-compose -f docker-compose.lenses.yml up -d
#	docker-compose logs -f --tail=100

stop:
	docker-compose down

restart:
	docker-compose restart

rebuild:
	docker-compose build

rebuildf:
	docker-compose build --no-cache

reboot:
	docker-compose down && docker-compose up

startd:
	docker-compose up -d

rebootd:
	docker-compose down && docker-compose up -d

logs:
	docker-compose logs -f -t

top:
	docker-compose top

export:
	export $(cat .env | sed 's/#.*//g' | xargs)
