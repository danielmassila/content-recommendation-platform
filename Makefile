.PHONY: help up down reset migrate api frontend demo-data counts py-build py-smoke py-download py-import py-enrich-tmdb py-eval py-reco py-all test-frontend test-backend test-python test-python-docker
# Help

.DEFAULT_GOAL := help

help:
	@echo "Targets:"
	@echo "  up               Start docker services (db/adminer/etc.)"
	@echo "  down             Stop docker services"
	@echo "  reset            Stop + remove volumes, then start services"
	@echo "  migrate          Run Flyway migrations (Spring without web server)"
	@echo "  api              Run Spring Boot API"
	@echo "  counts           Show row counts in core tables"
	@echo "  demo-data        Reset DB, import demo data and compute recommendations"
	@echo "  frontend         Install locked dependencies and run the React app"
	@echo ""
	@echo "Python jobs (Docker):"
	@echo "  py-build         Build reco-job image"
	@echo "  py-smoke         Run smoke checks on dataset/pipeline"
	@echo "  py-download      Download dataset into ./datasets (not committed)"
	@echo "  py-import        Import dataset into DB"
	@echo "  py-enrich-tmdb   Enrich imported MovieLens items with TMDB metadata"
	@echo "  py-reco          Compute recommendations and write them into DB"
	@echo "  py-eval          Offline evaluation (train/test split) with Precision@K, Recall@K, MAP@K"
	@echo "  py-all           Build + smoke + import + reco"
	@echo ""
	@echo "Tests:"
	@echo "  test-python      Run pytest locally (requires reco-ml/.venv)"
	@echo "  test-python-docker Run pytest in Docker (reco-tests service)"

# Infra

up:
	docker compose up -d

down:
	docker compose down

reset:
	docker compose down -v
	docker compose up -d

counts:
	docker compose exec db psql -U reco_user -d reco_db -c "SELECT COUNT(*) AS users FROM users;"
	docker compose exec db psql -U reco_user -d reco_db -c "SELECT COUNT(*) AS items FROM items;"
	docker compose exec db psql -U reco_user -d reco_db -c "SELECT COUNT(*) AS ratings FROM ratings;"
	docker compose exec db psql -U reco_user -d reco_db -c "SELECT COUNT(*) AS recommendations FROM recommendations;"


# Spring Boot

# Run Spring only to apply Flyway migrations (no web server)
migrate:
	set -a; . ./.env; set +a; \
	export DB_HOST="$${API_DB_HOST:-localhost}"; \
	export DB_NAME="$${POSTGRES_DB:-reco_db}"; \
	export DB_USER="$${POSTGRES_USER:-reco_user}"; \
	export DB_PASSWORD="$${POSTGRES_PASSWORD:-reco_pass}"; \
	cd backend && ./mvnw -q -DskipTests spring-boot:run \
	  -Dspring-boot.run.arguments=--spring.main.web-application-type=none

api:
	set -a; . ./.env; set +a; \
	export DB_HOST="$${API_DB_HOST:-localhost}"; \
	export DB_NAME="$${POSTGRES_DB:-reco_db}"; \
	export DB_USER="$${POSTGRES_USER:-reco_user}"; \
	export DB_PASSWORD="$${POSTGRES_PASSWORD:-reco_pass}"; \
	cd backend && ./mvnw spring-boot:run

frontend:
	cd frontend && npm ci && npm run dev

# Reco ML jobs
py-build:
	docker compose build reco-job

py-smoke:
	docker compose run --rm reco-job python -m jobs.smoke_data

py-download:
	docker compose run --rm reco-job python -m jobs.download_dataset

py-import:
	docker compose run --rm reco-job python -m jobs.import_dataset

py-enrich-tmdb:
	docker compose run --rm reco-job python -m jobs.enrich_tmdb

py-reco:
	docker compose run --rm reco-job python -m jobs.run_reco

py-eval:
	docker compose run --rm reco-job python -m jobs.evaluate_offline --split loo --k 10 --n 50 --neighbors 50

py-all: py-build py-download py-smoke py-import py-reco


# Full demo dataset: rebuild DB, migrate schema, import data and compute recommendations
demo-data: reset migrate py-all py-eval counts
	@echo ""
	@echo "Demo data ready. Start 'make api' and 'make frontend' in separate terminals."
	@echo " - API      -> http://localhost:8081"
	@echo " - Frontend -> http://localhost:5173"
	@echo " - Adminer  -> http://localhost:8082"


# Tests
test-frontend:
	cd frontend && npm ci && npm run lint && npm test -- --run && npm run build

test-backend:
	cd backend && ./mvnw verify

test-python:
	cd reco-ml && . .venv/bin/activate && pytest -q

test-python-docker:
	docker compose run --rm reco-tests
