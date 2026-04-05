# Athar - Islamic QA System

Multi-Agent Islamic QA System based on Fanar-Sadiq architecture.

## Quick Start

```bash
# Install dependencies
make install-dev

# Run development server
make dev

# Run tests
make test
```

## Requirements

- Python 3.12+
- Poetry (for dependency management)
- Docker & Docker Compose (for services)

## Available Commands

| Command | Description |
|---------|-------------|
| `make install-dev` | Install all dependencies including dev tools |
| `make dev` | Run development server with hot reload |
| `make test` | Run tests with coverage report |
| `make lint` | Run ruff and mypy |
| `make format` | Auto-format code |
| `make docker-up` | Start PostgreSQL, Redis, Qdrant |
| `make docker-down` | Stop Docker services |
| `make clean` | Clean cache files |

## Environment Setup

1. Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```

2. Update the values in `.env` with your configuration.

## Architecture

```
User Query
    ↓
Intent Classifier (Hybrid: Keyword + LLM + Embedding)
    ↓
Router → Agent/Tool
    ↓
Response Orchestrator → Final Answer
```

## Project Structure

```
athar/
├── src/
│   ├── api/           # FastAPI routes and endpoints
│   ├── agents/        # AI agents (Fiqh, Quran, etc.)
│   ├── core/          # Orchestrator, Router, Citation
│   ├── config/        # Settings, Intents
│   ├── tools/         # Calculators and utilities
│   └── infrastructure/ # DB, cache, external services
├── tests/             # Test suite
├── migrations/        # Database migrations
├── docker/            # Docker configuration
└── docs/              # Documentation
```