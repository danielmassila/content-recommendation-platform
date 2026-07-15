.PHONY: help up down reset migrate api demo counts py-build py-smoke py-download py-import py-eval py-reco py-all test-python test-python-docker
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
	@echo "  demo             Full demo: reset + migrate + import + reco + counts + api"
	@echo ""
	@echo "Python jobs (Docker):"
	@echo "  py-build         Build reco-job image"
	@echo "  py-smoke         Run smoke checks on dataset/pipeline"
	@echo "  py-download      Download dataset into ./datasets (not committed)"
	@echo "  py-import        Import dataset into DB"
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
	./mvnw -q -DskipTests spring-boot:run \
	  -Dspring-boot.run.arguments=--spring.main.web-application-type=none

api:
	./mvnw spring-boot:run

# Reco ML jobs
py-build:
	docker compose build reco-job

py-smoke:
	docker compose run --rm reco-job python -m jobs.smoke_data

py-download:
	docker compose run --rm reco-job python -m jobs.download_dataset

py-import:
	docker compose run --rm reco-job python -m jobs.import_dataset

py-reco:
	docker compose run --rm reco-job python -m jobs.run_reco

py-eval:
	docker compose run --rm reco-job python -m jobs.evaluate_offline --split loo --k 10 --n 50 --neighbors 50

py-all: py-build py-download py-smoke py-import py-reco


# Full demo: rebuild DB, migrate schema, import data, compute recos, show counts, run API
demo: reset migrate py-all py-eval counts api
	@echo ""
	@echo "Demo ready:"
	@echo " - API     -> http://localhost:8081"
	@echo " - Adminer -> http://localhost:8080"


# Tests
test-python:
	cd reco-ml && . .venv/bin/activate && pytest -q

test-python-docker:
	docker compose run --rm reco-tests
