# 🚀 START HERE - Athar Islamic QA System

## ✅ Project Status: Phase 8 Complete (April 15, 2026)

### 🎉 Latest: Hybrid Intent Classifier Active

As of **April 15, 2026**, the system now includes:

- ✅ **Fast keyword-based classification** (100+ patterns, no LLM needed)
- ✅ **New `/classify` endpoint** for instant intent detection (<50ms)
- ✅ **10 priority levels** for conflict resolution
- ✅ **Quran sub-intent detection** (4 types)

### 📊 What You Have

| Component | Status | Details |
|-----------|--------|---------|
| **Code** | ✅ Active | 13 agents, 5 deterministic tools, 20 API endpoints |
| **Data** | ✅ Uploaded | 10 collections to HuggingFace (42.6 GB), 5.7M documents |
| **Embedding** | ⏳ Pending | BGE-m3 on Colab GPU (~13 hours) |
| **Infrastructure** | ✅ Ready | PostgreSQL, Redis, Qdrant (via Docker) |
| **Documentation** | ✅ Complete | 60+ docs across 14 directories |
| **Test Coverage** | ✅ ~91% | 9 test files |

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

# NEW: Test intent classification
curl -X POST http://localhost:8000/classify \
  -H "Content-Type: application/json" \
  -d '{"query": "ما حكم صلاة الجمعة؟"}'

# View API documentation
# Swagger UI: http://localhost:8000/docs
# ReDoc: http://localhost:8000/redoc
```

---

## 🌐 New: Intent Classification Endpoint

### `/classify` - Fast Intent Detection (<50ms)

```bash
# Arabic query
curl -X POST http://localhost:8000/classify \
  -H "Content-Type: application/json" \
  -d '{"query": "ما حكم ترك صلاة الجمعة عمداً؟"}'

# Response
{
  "result": {
    "intent": "fiqh",
    "confidence": 0.90,
    "language": "ar",
    "reasoning": "Keyword fast-path matched: 'ما حكم'",
    "requires_retrieval": true,
    "method": "keyword"
  },
  "route": "fiqh_agent",
  "agent_metadata": {
    "priority": 5,
    "collection": "fiqh_passages"
  }
}
```

### 16 Intent Types

| Intent | Priority | Agent | Query Type |
|--------|----------|-------|------------|
| TAFSIR | 10 | general_islamic_agent | تفسير آية كذا |
| QURAN | 9 | quran:* (+ sub-intent) | آية عن كذا |
| HADITH | 9 | hadith_agent | حديث عن كذا |
| SEERAH | 8 | seerah_agent | السيرة النبوية |
| FIQH | 5 | fiqh_agent | حكم كذا |
| ZAKAT | 2 | Calculator | حساب الزكاة |
| INHERITANCE | 2 | Calculator | الميراث |
| PRAYER_TIMES | 2 | Calculator | أوقات الصلاة |
| HIJRI_CALENDAR | 2 | Calculator | التاريخ الهجري |
| DUA | 2 | Calculator | دعاء كذا |
| GREETING | 2 | chatbot_agent | أهلاً |
| ISLAMIC_KNOWLEDGE | 1 | general_islamic_agent | (fallback) |

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
- **[Complete API Docs](../5-api/COMPLETE_DOCUMENTATION.md)** - All 20 endpoints

### Phase 8 Details
- **[Lucene Merge Complete](../10-operations/LUCENE_MERGE_COMPLETE.md)** - Phase 7 details
- **[Backup & Restore Guide](../10-operations/BACKUP_AND_RESTORE_GUIDE.md)** - HuggingFace backup

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
| **Intent Classifier** | http://localhost:8000/classify |

---

## 📜 Project Structure

```
Athar/
├── src/                          # Python backend (FastAPI)
│   ├── api/                      # API routes (20 endpoints)
│   │   ├── routes/
│   │   │   ├── classification.py  # NEW: /classify endpoint
│   │   │   ├── query.py
│   │   │   ├── tools.py
│   │   │   └── quran.py
│   │   └── schemas/
│   ├── application/              # NEW: Application layer (Phase 8)
│   │   ├── hybrid_classifier.py # HybridIntentClassifier
│   │   ├── router.py            # RouterAgent
│   │   └── interfaces.py        # Protocols
│   ├── domain/                   # NEW: Domain definitions
│   │   ├── intents.py           # 16 intent types
│   │   └── models.py            # ClassificationResult
│   ├── agents/                   # 13 specialized agents
│   ├── tools/                    # 5 deterministic tools
│   ├── quran/                    # Quran pipeline (6 modules)
│   ├── knowledge/                # RAG infrastructure
│   └── core/                     # Router, orchestrator, citation
│
├── scripts/                      # Utility scripts (40+)
├── notebooks/                    # Colab notebooks
├── data/                         # Datasets
│   └── mini_dataset/             # GitHub-friendly (1.7 MB)
├── docs/                         # Documentation (60+ files)
├── tests/                        # Pytest test suite (~91%)
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

## 📈 Phase Progress

| Phase | Status | Key Achievement |
|-------|--------|-----------------|
| Phase 1-6 | ✅ Complete | Foundation, Tools, RAG, 13 Agents |
| Phase 7 | ✅ Complete | 11.3M Lucene documents merged |
| **Phase 8** | ✅ **Complete** | **Hybrid Intent Classifier** (April 15, 2026) |
| Phase 9 | ⏳ Pending | GPU Embedding & Qdrant Import |

---

## 🎉 You're Ready!

**Next Steps:**
1. Run `make dev` to start the server
2. Visit http://localhost:8000/docs to explore the API
3. Try the new classify endpoint: `POST /classify` with `{"query": "ما حكم الزكاة؟"}`
4. Try a full query: `POST /api/v1/query` with `{"query": "ما هو حكم الله في صلاة الجمعة؟"}`

**Full Documentation:** [docs/README.md](../README.md)  
**API Reference:** [Complete API Docs](../5-api/COMPLETE_DOCUMENTATION.md)  
**Architecture:** [Architecture Overview](../2-architecture/01_ARCHITECTURE_OVERVIEW.md)

---

**Built with ❤️ for the Muslim community** 🕌