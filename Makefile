.PHONY: up down build logs migrate test lint format ingest help

help:
	@echo "Available commands:"
	@echo "  up              - Start all services with Docker Compose (builds if needed)"
	@echo "  down            - Stop and remove all services"
	@echo "  build           - Build Docker images"
	@echo "  logs            - Follow all service logs"
	@echo "  migrate         - Apply database migrations"
	@echo "  test            - Run pytest with coverage"
	@echo "  lint            - Run Ruff and MyPy linting"
	@echo "  format          - Apply Ruff formatting"
	@echo "  ingest          - Backfill 7 days of historical data"
	@echo "  help            - Show this help message"

up:
	docker compose up --build
	down:
	docker compose down

build:
	docker compose build

logs:
	docker compose logs -f

migrate:
	docker compose exec backend alembic upgrade head

test:
	docker compose run --rm -e RUN_MIGRATIONS=false backend pytest --cov=app --cov-report=term-missing

lint:
	docker compose run --rm -e RUN_MIGRATIONS=false backend ruff check app tests
	docker compose run --rm -e RUN_MIGRATIONS=false backend mypy app

format:
	docker compose run --rm -e RUN_MIGRATIONS=false backend ruff format app tests

ingest:
	docker compose exec backend python -m app.cli ingest --symbol BTCUSDT --timeframes 5m,15m,1h,4h,1d --days 7

# Convenience shortcuts
start: up
stop: down
restart: down up
run-tests: test
lint-code: lint
fmt-code: format
load-data: ingest

# Development shortcuts
devenv:
	cd backend && python -m app.main

frontend-dev:
	cd frontend && npm run dev

.PHONY: help up down build logs migrate test lint format ingest start stop restart run-tests lint-code fmt-code load-data devenv frontend-dev