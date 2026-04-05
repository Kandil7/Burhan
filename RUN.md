# 🚀 Quick Start - Athar Islamic QA System

## Option 1: One-Command Start (Recommended)

```bash
# Windows
docker compose -f docker/docker-compose.dev.yml up -d

# Then open:
# - Frontend: http://localhost:3000
# - API Docs: http://localhost:8000/docs
```

## Option 2: Step-by-Step

### Step 1: Start Infrastructure

```bash
# Start PostgreSQL, Redis, Qdrant
docker compose -f docker/docker-compose.dev.yml up -d postgres redis qdrant

# Wait 10 seconds for services to be ready
timeout /t 10

# Verify services
docker compose -f docker/docker-compose.dev.yml ps
```

### Step 2: Run Migrations

```bash
# On Windows
docker exec -i athar-postgres psql -U athar -d athar_db < migrations/001_initial_schema.sql
```

### Step 3: Start Backend API

```bash
# Install dependencies (first time only)
pip install -e .

# Start API
uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000
```

### Step 4: Start Frontend

```bash
cd frontend
npm install  # First time only
npm run dev
```

## Test It Works

```bash
# Test API health
curl http://localhost:8000/health

# Test query
curl -X POST http://localhost:8000/api/v1/query ^
  -H "Content-Type: application/json" ^
  -d "{\"query\": \"السلام عليكم\", \"language\": \"ar\"}"
```

## Stop Everything

```bash
docker compose -f docker/docker-compose.dev.yml down
```

## View Logs

```bash
# All services
docker compose -f docker/docker-compose.dev.yml logs -f

# API only
docker compose -f docker/docker-compose.dev.yml logs -f api
```
