# 🚀 START HERE - Athar Islamic QA System

## ✅ Project Status: ACTIVE DEVELOPMENT

### 📊 What You Have

| Component | Status | Details |
|-----------|--------|---------|
| **Code** | ✅ Active | 7 active agents, 5 deterministic tools, 18 API endpoints |
| **Data** | ✅ Processed | 10 Qdrant collections, 11,147+ vectors |
| **Infrastructure** | ✅ Ready | PostgreSQL, Redis, Qdrant (via Docker) |
| **Documentation** | ✅ Complete | 60+ docs across 14 directories |

---

## 🎯 Quick Start

### Prerequisites
- Python 3.12+
- Poetry (dependency management)
- Docker Desktop (for PostgreSQL, Redis, Qdrant)
- Groq API key (or OpenAI)

### Step 1: Install Dependencies
```bash
# Clone repository (if not already done)
git clone https://github.com/Kandil7/Athar.git
cd Athar

# Install Python dependencies
make install-dev

# Install RAG dependencies (optional, for embeddings)
poetry install --with rag
```

### Step 2: Configure Environment
```bash
# Copy environment template
cp .env.example .env

# Edit .env with your API keys and database URLs
# Required: GROQ_API_KEY (or OpenAI key)
# Required: HF_TOKEN (for embedding model)
```

### Step 3: Start Infrastructure
```bash
# Start PostgreSQL, Redis, Qdrant
docker compose -f docker/docker-compose.dev.yml up -d

# Run database migrations
make db-migrate
```

### Step 4: Start Development Server
```bash
# Option A: Using Make (port 8000)
make dev

# Option B: Custom port (recommended for Windows)
python -m uvicorn src.api.main:app --host 0.0.0.0 --port 8002
```

### Step 5: Verify Installation
```bash
# Run tests
make test

# Check health endpoint
curl http://localhost:8000/health

# View API documentation
# Swagger UI: http://localhost:8000/docs
# ReDoc: http://localhost:8000/redoc
```

---

## 📚 Documentation

### Getting Started
- **[START_HERE.md](START_HERE.md)** ← You are here!
- **[setup.md](../4-guides/setup.md)** - Detailed setup guide
- **[running.md](../4-guides/running.md)** - Running the application
- **[windows.md](../4-guides/windows.md)** - Windows-specific guide

### Architecture & Core Features
- **[Architecture Overview](../2-architecture/01_ARCHITECTURE_OVERVIEW.md)** - System design
- **[Quran System](../3-core-features/quran.md)** - Quran pipeline
- **[RAG Pipeline](../3-core-features/rag.md)** - Retrieval-augmented generation

### API Reference
- **[Complete API Docs](../5-api/COMPLETE_DOCUMENTATION.md)** - All 18 endpoints

### Data & Embeddings
- [Datasets Guide](../6-data/QUICK_START_DATASETS.md)** - Dataset management
- **[Embeddings Guide](../8-development/embeddings.md)** - Embedding pipeline

**Full index:** [docs/README.md](../README.md)

---

## 🌐 Access Points

Once started:

| Service | URL |
|---------|-----|
| **API Documentation** | http://localhost:8000/docs |
| **Alternative Docs** | http://localhost:8000/redoc |
| **Health Check** | http://localhost:8000/health |
| **Readiness Probe** | http://localhost:8000/ready |

---

## 📜 Project Structure

```
Athar/
├── src/                          # Python backend (FastAPI)
│   ├── api/                      # API routes (18 endpoints)
│   ├── agents/                   # 7 active agents
│   ├── tools/                    # 5 deterministic tools
│   ├── quran/                    # Quran pipeline (6 modules)
│   ├── knowledge/                # RAG infrastructure
│   ├── core/                     # Router, orchestrator, citation
│   └── config/                   # Settings, intents, constants
│
├── scripts/                      # Utility scripts (40+)
│   ├── data/                     # Data processing & seeding
│   ├── ingestion/                # Data ingestion pipelines
│   └── tests/                    # Test scripts
│
├── data/                         # Datasets
│   ├── mini_dataset/             # GitHub-friendly mini-dataset (1.7 MB)
│   └── seed/                     # Seed data (duas, quran samples)
│
├── docs/                         # Documentation (60+ files)
├── tests/                        # Pytest test suite
├── docker/                       # Docker configuration
└── migrations/                   # Database migrations
```

---

## 🎯 Common Commands

```bash
# Development
make install-dev          # Install dependencies
make dev                  # Start development server (port 8000)
make test                 # Run tests with coverage
make lint                 # Run linters (ruff + mypy)
make format               # Auto-format code

# Docker
make docker-up            # Start Docker services (postgres, redis, qdrant)
make docker-down          # Stop Docker services

# Database
make db-migrate           # Run database migrations

# Custom port (Windows)
python -m uvicorn src.api.main:app --host 0.0.0.0 --port 8002
```

### Windows Batch Files
```batch
build.bat                 # Main build system
start-athar.bat           # Quick start
stop-athar.bat            # Quick stop
download-embeddings-to-qdrant.bat  # Download embeddings
```

---

## 🆘 Troubleshooting

### Port Already in Use
```bash
# Use a different port
python -m uvicorn src.api.main:app --host 0.0.0.0 --port 8002
```

### Docker Services Not Starting
```bash
# Check Docker status
docker ps

# View logs
docker compose -f docker/docker-compose.dev.yml logs
```

### Missing Environment Variables
```bash
# Ensure .env file exists and is configured
cp .env.example .env
# Edit .env with your API keys
```

### Import Errors
```bash
# Reinstall dependencies
poetry install --with rag
```

---

## 📊 System Requirements

| Requirement | Status | Notes |
|-------------|--------|-------|
| Python 3.12+ | ✅ Required | For backend |
| Poetry | ✅ Required | Dependency management |
| Docker | ✅ Required | For databases (PostgreSQL, Redis, Qdrant) |
| 8GB RAM | ✅ Minimum | 16GB recommended for embeddings |
| 20GB Disk | ✅ Minimum | For data & Docker |
| Groq API Key | ✅ Required | For LLM inference |
| HuggingFace Token | ✅ Required | For embedding model |

---

## 🎉 You're Ready!

**Next Steps:**
1. Run `make dev` to start the server
2. Visit http://localhost:8000/docs to explore the API
3. Try a query: `POST /api/v1/query` with `{"query": "What is zakat?"}`

**Full Documentation:** [docs/README.md](../README.md)  
**API Reference:** [Complete API Docs](../5-api/COMPLETE_DOCUMENTATION.md)  
**Architecture:** [Architecture Overview](../2-architecture/01_ARCHITECTURE_OVERVIEW.md)

---

**Built with ❤️ for the Muslim community** 🕌
