.PHONY: help install install-dev dev test lint format clean docker-up docker-down db-migrate db-migrate-create run

# ============================================
# ATHAR - Poetry-based commands
# ============================================

help:
	@echo "Athar - Islamic QA System"
	@echo ""
	@echo "Available commands:"
	@echo "  make install-dev    Install dependencies with dev tools"
	@echo "  make dev            Run development server"
	@echo "  make test           Run tests with coverage"
	@echo "  make lint           Run linters (ruff + mypy)"
	@echo "  make format          Auto-format code"
	@echo "  make clean          Clean cache files"
	@echo "  make docker-up      Start Docker services"
	@echo "  make docker-down    Stop Docker services"
	@echo "  make db-migrate     Run database migrations"
	@echo "  make run            Run production server"

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

test-watch:
	poetry run pytest tests/ -v --watch

# ============================================
# Code Quality
# ============================================

lint:
	poetry run ruff check src/ tests/
	poetry run mypy src/

format:
	poetry run ruff check --fix src/ tests/
	poetry run ruff format src/ tests/

# ============================================
# Docker
# ============================================

docker-up:
	docker compose -f docker/docker-compose.dev.yml up -d

docker-down:
	docker compose -f docker/docker-compose.dev.yml down

docker-logs:
	docker compose -f docker/docker-compose.dev.yml logs -f

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