.PHONY: help up tools down reset migrate api frontend counts py-build py-smoke py-sync-catalog py-sync-movie py-stage py-publish py-eval py-reco test-frontend test-backend test-python test-python-docker
# Help

.DEFAULT_GOAL := help

UNAME_S := $(shell uname -s)
ifeq ($(UNAME_S),Darwin)
JAVA_21_HOME ?= $(shell /usr/libexec/java_home -v 21 2>/dev/null)
else
JAVA_21_HOME ?= $(JAVA_HOME)
endif

help:
	@echo "Targets:"
	@echo "  up               Start the application services"
	@echo "  tools            Start the application services with Adminer"
	@echo "  down             Stop docker services"
	@echo "  reset            Stop + remove volumes, then start services"
	@echo "  migrate          Run Flyway migrations (Spring without web server)"
	@echo "  api              Run Spring Boot API"
	@echo "  counts           Show row counts in core tables"
	@echo "  frontend         Install locked dependencies and run the React app"
	@echo ""
	@echo "Python jobs (Docker):"
	@echo "  py-build         Build reco-job image"
	@echo "  py-smoke         Inspect legacy MovieLens CSV files"
	@echo "  py-sync-catalog  Load missing films from links.csv (DATA_DIR, CATALOG_LIMIT)"
	@echo "  py-sync-movie    Create or refresh a film (TMDB_ID required)"
	@echo "  py-stage         Load MovieLens staging (DATA_DIR, BATCH_SIZE)"
	@echo "  py-publish       Validate and publish staging (IMPORT_ID required)"
	@echo "  py-reco          Compute recommendations and write them into DB"
	@echo "  py-eval          Evaluate application ratings only (external corpus not included)"
	@echo ""
	@echo "Tests:"
	@echo "  test-python      Run pytest locally (requires reco-ml/.venv)"
	@echo "  test-python-docker Run pytest in Docker (reco-tests service)"

# Infra

up:
	docker compose up -d

tools:
	docker compose --profile tools up -d

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
	export JAVA_HOME="$(JAVA_21_HOME)"; \
	export PATH="$(JAVA_21_HOME)/bin:$$PATH"; \
	export DB_HOST="$${API_DB_HOST:-localhost}"; \
	export DB_NAME="$${POSTGRES_DB:-reco_db}"; \
	export DB_USER="$${POSTGRES_USER:-reco_user}"; \
	export DB_PASSWORD="$${POSTGRES_PASSWORD:-reco_pass}"; \
	cd backend && ./mvnw -q -DskipTests spring-boot:run \
	  -Dspring-boot.run.arguments=--spring.main.web-application-type=none

api:
	set -a; . ./.env; set +a; \
	export JAVA_HOME="$(JAVA_21_HOME)"; \
	export PATH="$(JAVA_21_HOME)/bin:$$PATH"; \
	export DB_HOST="$${API_DB_HOST:-localhost}"; \
	export DB_NAME="$${POSTGRES_DB:-reco_db}"; \
	export DB_USER="$${POSTGRES_USER:-reco_user}"; \
	export DB_PASSWORD="$${POSTGRES_PASSWORD:-reco_pass}"; \
	cd backend && ./mvnw spring-boot:run

frontend:
	cd frontend && npm ci && npm run dev

# Reco ML jobs
DATA_DIR ?= /datasets/raw_data
BATCH_SIZE ?= 10000
CATALOG_LIMIT ?= 100
CATALOG_DELAY ?= 0.25

# DATA_DIR is a path inside the job container.

py-build:
	docker compose build reco-job

py-smoke:
	docker compose run --rm reco-job python -m jobs.smoke_data

py-sync-catalog:
	docker compose run --rm reco-job python -m jobs.sync_tmdb_catalog --links "$(DATA_DIR)/links.csv" --limit "$(CATALOG_LIMIT)" --delay "$(CATALOG_DELAY)"

py-sync-movie:
	@test -n "$(TMDB_ID)" || (echo "Usage: make py-sync-movie TMDB_ID=603"; exit 1)
	docker compose run --rm reco-job python -m jobs.sync_tmdb_movie "$(TMDB_ID)"

py-stage:
	docker compose run --rm reco-job python -m jobs.stage_movielens --data-dir "$(DATA_DIR)" --batch-size "$(BATCH_SIZE)"

py-publish:
	@test -n "$(IMPORT_ID)" || (echo "Usage: make py-publish IMPORT_ID=<uuid> DATA_DIR=/datasets/..."; exit 1)
	docker compose run --rm reco-job python -m jobs.publish_movielens --import-id "$(IMPORT_ID)" --links "$(DATA_DIR)/links.csv"

py-reco:
	@test -n "$(DATASET_VERSION)" || (echo "Usage: make py-reco DATASET_VERSION=sha256:..."; exit 1)
	docker compose run --rm reco-job python -m jobs.run_reco --dataset-version "$(DATASET_VERSION)"

py-eval:
	docker compose run --rm reco-job python -m jobs.evaluate_offline --split loo --k 10 --n 50 --neighbors 50

# Tests
test-frontend:
	cd frontend && npm ci && npm run lint && npm test -- --run && npm run build

test-backend:
	cd backend && JAVA_HOME="$(JAVA_21_HOME)" PATH="$(JAVA_21_HOME)/bin:$$PATH" ./mvnw verify

test-python:
	cd reco-ml && . .venv/bin/activate && pytest -q

test-python-docker:
	docker compose run --rm reco-tests
