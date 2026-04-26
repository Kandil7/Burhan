.PHONY: help install install-dev dev test lint format clean docker-up docker-down db-migrate db-migrate-create run

# ============================================
# Burhan - Poetry-based commands
# Phase 9: Enhanced with new commands
# ============================================

help:
	@echo "Burhan - Islamic QA System"
	@echo ""
	@echo "Available commands:"
	@echo "  make install-dev    Install dependencies with dev tools"
	@echo "  make dev            Run development server"
	@echo "  make test           Run tests with coverage"
	@echo "  make test-quick     Run quick tests without coverage"
	@echo "  make lint           Run linters (ruff + mypy)"
	@echo "  make format         Auto-format code"
	@echo "  make clean         Clean cache files"
	@echo "  make docker-up     Start Docker services"
	@echo "  make docker-down   Stop Docker services"
	@echo "  make docker-prod   Start production Docker"
	@echo "  make db-migrate   Run database migrations"
	@echo "  make db-reset     Reset database"
	@echo "  make run          Run production server"
	@echo "  make health      Check service health"
	@echo "  make validate    Validate environment setup"

# ============================================
# Installation
# ============================================

install:
	poetry install

install-dev:
	poetry install --with dev

# ============================================
# Development
# ============================================

dev:
	poetry run uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000

run:
	poetry run uvicorn src.api.main:app --host 0.0.0.0 --port 8000

# ============================================
# Testing
# ============================================

test:
	poetry run pytest tests/ -v --cov=src --cov-report=term-missing

test-quick:
	poetry run pytest tests/ -v --cov=false

test-comprehensive:
	poetry run pytest tests/test_comprehensive.py -v

test-language:
	poetry run pytest tests/test_comprehensive.py::TestLanguageDetection -v -k "language"

# ============================================
# Code Quality
# ============================================

lint:
	poetry run ruff check src/ tests/
	poetry run mypy src/

lint-fix:
	poetry run ruff check --fix src/ tests/

format:
	poetry run ruff check --fix src/ tests/
	poetry run ruff format src/ tests/

type-check:
	poetry run mypy src/

# ============================================
# Docker
# ============================================

docker-up:
	docker compose -f docker/docker-compose.dev.yml up -d

docker-down:
	docker compose -f docker/docker-compose.dev.yml down

docker-prod:
	docker compose -f docker/docker-compose.prod.yml up -d

docker-prod-down:
	docker compose -f docker/docker-compose.prod.yml down

docker-logs:
	docker compose -f docker/docker-compose.dev.yml logs -f

docker-build:
	docker build -f docker/Dockerfile.api -t Burhan-api:latest .

# ============================================
# Database
# ============================================

db-migrate:
	poetry run alembic upgrade head

db-migrate-create:
	@if [ -z "$(message)" ]; then \
		echo "Usage: make db-migrate-create message='your message'"; \
		exit 1; \
	fi
	poetry run alembic revision --autogenerate -m "$(message)"

db-reset:
	poetry run alembic downgrade base
	poetry run alembic upgrade head

db-seed:
	poetry run python scripts/seed_quran_sample.py

# ============================================
# Health & Monitoring
# ============================================

health:
	@curl -s http://localhost:8000/health | python -m json.tool || echo "Service not running"

metrics:
	@curl -s http://localhost:8000/metrics | python -m json.tool || echo "Service not running"

# ============================================
# Environment Validation
# ============================================

validate:
	@echo "Validating environment..."; \
	python -c "from src.config.settings import settings; print('✓ Settings loaded'); from src.config.constants import RetrievalConfig; print('✓ Constants loaded')" || echo "✗ Validation failed"

# ============================================
# Cleanup
# ============================================

clean:
	@echo "Cleaning Python cache..."
	rm -rf .pytest_cache .mypy_cache tests/.pytest_cache
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type f -name "*.pyo" -delete 2>/dev/null || true
	rm -rf .coverage htmlcov/ 2>/dev/null || true
	@echo "✓ Clean complete"

# ============================================
# Utilities
# ============================================

deps-update:
	poetry update

deps-outdated:
	poetry show --outdated

shell:
	poetry shell

# Run specific test file
test-file:
	poetry run pytest tests/$(file).py -v