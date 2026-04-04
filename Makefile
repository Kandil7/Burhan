.PHONY: dev test lint clean docker-up docker-down db-migrate db-migrate-create install

# Development
dev:
	uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000

# Testing
test:
	pytest tests/ -v --cov=src --cov-report=term-missing

# Linting
lint:
	ruff check src/ tests/
	mypy src/

# Format
format:
	ruff check --fix src/ tests/
	ruff format src/ tests/

# Docker
docker-up:
	docker compose -f docker/docker-compose.dev.yml up -d

docker-down:
	docker compose -f docker/docker-compose.dev.yml down

docker-logs:
	docker compose -f docker/docker-compose.dev.yml logs -f

# Database migrations
db-migrate:
	alembic upgrade head

db-migrate-create:
	@if [ -z "$(message)" ]; then \
		echo "Usage: make db-migrate-create message='your message'"; \
		exit 1; \
	fi
	alembic revision --autogenerate -m "$(message)"

# Install
install:
	pip install -e .

install-dev:
	pip install -e ".[dev]"

# Clean
clean:
	@echo "Cleaning Python cache..."
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type f -name "*.pyo" -delete 2>/dev/null || true
	@echo "Clean complete."
