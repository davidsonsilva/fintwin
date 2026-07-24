.PHONY: up down test test-api build

up:
	docker compose up --build

down:
	docker compose down

test: test-api

test-api:
	cd apps/api && .venv/Scripts/python.exe -m pytest -q

build:
	docker compose build
