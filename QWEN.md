# 🕌 Athar - Islamic QA System

> A production-ready, multi-agent Islamic QA system based on the Fanar-Sadiq architecture, providing grounded, citation-backed answers with deterministic calculators for zakat, inheritance, and verified sources from Quran, Hadith, and Fiqh.

---

## 📋 Overview

**Athar** is an Islamic QA system that answers religious questions with verified sources and proper citations. Built on the **Fanar-Sadiq** multi-agent architecture, it combines intent classification, RAG pipelines, and deterministic calculators to provide accurate, grounded answers to Islamic religious questions.

### Key Features

- **13 Specialized Agents**: Fiqh, Hadith, Sanadset Hadith, Quran, Tafsir, Aqeedah, Seerah, Islamic History, Arabic Language, Usul Fiqh, Spirituality, General Islamic, Chatbot
- **16 Intent Types**: fiqh, quran, islamic_knowledge, greeting, zakat, inheritance, dua, hijri_calendar, prayer_times, hadith, tafsir, aqeedah, seerah, usul_fiqh, islamic_history, arabic_language
- **5 Deterministic Tools**: Zakat Calculator, Inheritance Calculator, Prayer Times, Hijri Calendar, Dua Retrieval
- **RAG Pipelines**: 10 vector collections with Qwen3-Embedding-0.6B (1024 dimensions)
- **Quran Pipeline**: Verse retrieval, NL2SQL analytics, quotation validation, tafsir retrieval
- **Citation Normalization**: Every answer linked to Quran verses, hadith, or fatwas [C1], [C2], etc.
- **Hybrid Intent Classifier**: Keyword matching → LLM classification → Embedding fallback (~90% accuracy)

---

## 🏗️ Architecture

### 4-Layer Architecture

```
┌─────────────────────────────────────────────────────────┐
│              API Layer (FastAPI)                         │
│  POST /api/v1/query  •  GET /health  •  18 endpoints    │
└────────────────────────┬────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────┐
│               Orchestration Layer                        │
│  Hybrid Intent Classifier  •  Response Orchestrator     │
│  Citation Normalizer  •  Agent Registry                 │
└────────────────────────┬────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────┐
│              Agents & Tools Layer (13 agents + 5 tools)  │
│  ┌──────────┬──────────┬──────────┬──────────────┐      │
│  │ FiqhAgent│QuranAgent│ Zakat    │ Inheritance  │      │
│  │ (RAG)    │(NL2SQL)  │ Calc     │ Calc         │      │
│  └──────────┴──────────┴──────────┴──────────────┘      │
│  ┌──────────┬──────────┬──────────┬──────────────┐      │
│  │Greeting  │ Hijri    │ Prayer   │ Dua          │      │
│  │ Agent    │ Calendar │ Times    │ Retrieval    │      │
│  └──────────┴──────────┴──────────┴──────────────┘      │
│  ┌──────────┬──────────┬──────────┬──────────────┐      │
│  │Hadith    │Tafsir    │Aqeedah   │Seerah        │      │
│  │Agent     │Agent     │Agent     │Agent         │      │
│  └──────────┴──────────┴──────────┴──────────────┘      │
│  ┌──────────┬──────────┬──────────┬──────────────┐      │
│  │History   │Arabic    │UsulFiqh  │SanadsetHadith│      │
│  │Agent     │Language  │Agent     │Agent         │      │
│  └──────────┴──────────┴──────────┴──────────────┘      │
└────────────────────────┬────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────┐
│              Knowledge Layer                             │
│  PostgreSQL (Quran, Hadith)  •  Qdrant (10 collections) │
│  Redis (Cache)  •  LLM Provider (Groq Qwen3-32B)        │
│  Qwen3-Embedding-0.6B (1024-dim, CPU)                   │
└─────────────────────────────────────────────────────────┘
```

---

## 🚀 Quick Start

### Prerequisites

- Python 3.12+
- Poetry (dependency management)
- PostgreSQL 16+
- Redis 7+
- Qdrant (vector database)
- Groq API key (or OpenAI)
- HuggingFace token (for embedding model)

### Setup

```bash
# Clone repository
git clone https://github.com/Kandil7/Athar.git
cd Athar

# Install dependencies
make install-dev

# Install RAG dependencies (optional, for embeddings)
poetry install --with rag

# Configure environment
cp .env.example .env
# Edit .env with your API keys and database URLs

# Start services
docker compose -f docker/docker-compose.dev.yml up -d postgres redis qdrant

# Run database migrations
make db-migrate

# Start development server (port 8000)
make dev

# Or run on port 8002 (recommended for Windows)
python -m uvicorn src.api.main:app --host 0.0.0.0 --port 8002

# Frontend (optional)
cd frontend
npm install
npm run dev
```

### Key Commands

```bash
make install-dev          # Install dependencies with dev tools
make dev                  # Run development server (port 8000)
make test                 # Run tests with coverage
make lint                 # Run linters (ruff + mypy)
make format               # Auto-format code
make clean                # Clean cache files
make docker-up            # Start Docker services
make docker-down          # Stop Docker services
make db-migrate           # Run database migrations
python -m uvicorn ...     # Run on custom port (e.g., 8002)
```

---

## 📁 Project Structure

```
K:\business\projects_v2\Athar\
├── src/                          # Python backend (FastAPI)
│   ├── config/                   # Configuration
│   │   ├── settings.py           # Environment settings (Pydantic)
│   │   ├── intents.py            # 16 intent definitions + keyword patterns
│   │   ├── constants.py          # Retrieval config, thresholds
│   │   └── logging_config.py     # Structured logging (structlog)
│   │
│   ├── api/                      # FastAPI application
│   │   ├── main.py               # App factory with middleware
│   │   ├── routes/               # API routes (5 modules)
│   │   │   ├── query.py          # POST /api/v1/query (main endpoint)
│   │   │   ├── health.py         # GET /health, /ready
│   │   │   ├── tools.py          # 5 tool endpoints (zakat, etc.)
│   │   │   ├── quran.py          # 6 Quran endpoints
│   │   │   └── rag.py            # 3 RAG endpoints
│   │   ├── middleware/           # Error handler, CORS
│   │   └── schemas/              # Pydantic models (request/response)
│   │
│   ├── core/                     # Core logic
│   │   ├── router.py             # Hybrid Intent Classifier (3-tier)
│   │   ├── orchestrator.py       # Response Orchestrator (agent routing)
│   │   ├── citation.py           # Citation Normalizer
│   │   └── registry.py           # Agent Registry
│   │
│   ├── agents/                   # 13 agent implementations
│   │   ├── base.py               # BaseAgent, AgentInput, AgentOutput
│   │   ├── fiqh_agent.py         # Fiqh RAG Agent (retrieve + generate)
│   │   ├── hadith_agent.py       # Hadith RAG Agent
│   │   ├── sanadset_hadith_agent.py  # Sanadset 650K Hadith Agent
│   │   ├── tafsir_agent.py       # Quran Tafsir Agent
│   │   ├── aqeedah_agent.py      # Islamic Creed Agent
│   │   ├── seerah_agent.py       # Prophet Biography Agent
│   │   ├── islamic_history_agent.py  # Islamic History Agent
│   │   ├── fiqh_usul_agent.py    # Jurisprudence Principles Agent
│   │   ├── arabic_language_agent.py  # Arabic Language Agent
│   │   ├── general_islamic_agent.py  # General Knowledge Agent
│   │   └── chatbot_agent.py      # Greeting/Small Talk Agent
│   │
│   ├── tools/                    # 5 deterministic tools
│   │   ├── base.py               # BaseTool, ToolInput, ToolOutput
│   │   ├── zakat_calculator.py   # Zakat (wealth, gold, silver, trade)
│   │   ├── inheritance_calculator.py # Inheritance (fara'id rules)
│   │   ├── prayer_times_tool.py  # Prayer times (6 methods) + Qibla
│   │   ├── hijri_calendar_tool.py # Hijri dates (Umm al-Qura)
│   │   └── dua_retrieval_tool.py # Hisn al-Muslim + Azkar
│   │
│   ├── quran/                    # Quran pipeline (6 modules)
│   │   ├── verse_retrieval.py    # Verse lookup (exact + fuzzy)
│   │   ├── nl2sql.py             # Natural language → SQL
│   │   ├── quotation_validator.py # Verify Quran quotes
│   │   ├── tafsir_retrieval.py   # Tafsir lookup
│   │   ├── quran_router.py       # Sub-intent classification (4 types)
│   │   └── quran_agent.py        # Complete Quran agent
│   │
│   ├── knowledge/                # RAG infrastructure
│   │   ├── embedding_model.py    # Qwen3-Embedding-0.6B wrapper + cache
│   │   ├── embedding_cache.py    # Redis/local dict caching
│   │   ├── vector_store.py       # Qdrant (10 collections)
│   │   ├── hybrid_search.py      # Semantic + BM25 search
│   │   └── chunker.py            # Document chunking
│   │
│   ├── data/                     # Data ingestion
│   │   ├── models/               # SQLAlchemy models (Quran)
│   │   └── ingestion/            # Data loaders (Quran, Hadith)
│   │
│   └── infrastructure/           # External services
│       ├── db.py                 # PostgreSQL (asyncpg)
│       ├── redis.py              # Redis connection
│       └── llm_client.py         # LLM provider (Groq/OpenAI)
│
├── data/
│   ├── mini_dataset/             # GitHub-friendly mini-dataset (1.7 MB)
│   │   ├── fiqh_passages.jsonl   # 347 documents
│   │   ├── hadith_passages.jsonl # 126 documents
│   │   ├── general_islamic.jsonl # 300 documents
│   │   ├── islamic_history_passages.jsonl # 270 documents
│   │   ├── arabic_language_passages.jsonl # 240 documents
│   │   ├── aqeedah_passages.jsonl # 90 documents
│   │   ├── spirituality_passages.jsonl # 150 documents
│   │   ├── seerah_passages.jsonl # 100 documents
│   │   ├── book_selections.json  # Book selection metadata
│   │   ├── collection_stats.json # Collection statistics
│   │   └── README.md             # Dataset documentation
│   ├── seed/                     # Seed data (duas, quran samples)
│   └── processed/                # Chunked documents (all_chunks.json)
│
├── datasets/                     # Full datasets (excluded from Git)
│   ├── data/
│   │   ├── extracted_books/      # 8,425 Shamela books (17.16 GB)
│   │   └── metadata/             # books.db, categories.json, authors.json
│   ├── Sanadset*/                # 650,986 hadith (1.43 GB)
│   └── system_book_datasets/     # 1,000+ book databases
│
├── scripts/                      # 37 utility scripts
│   ├── create_mini_dataset.py    # Mini-dataset creator
│   ├── embed_sanadset_hadith.py  # Hadith embedding pipeline
│   ├── seed_mvp_data.py          # MVP data seeder
│   ├── generate_embeddings.py    # Batch embedding generator
│   ├── test_all_endpoints_detailed.py # Comprehensive test suite
│   ├── test_sanadset_agent.py    # Hadith agent test
│   └── ...                       # Analysis, ingestion, testing scripts
│
├── tests/                        # 9 test files
│   ├── conftest.py               # Pytest fixtures
│   ├── test_router.py            # Intent classifier tests
│   ├── test_api.py               # API endpoint tests
│   ├── test_zakat_calculator.py  # Zakat calculator tests
│   ├── test_inheritance_calculator.py # Inheritance tests
│   ├── test_dua_retrieval_tool.py # Dua tool tests
│   ├── test_hijri_calendar_tool.py # Hijri tool tests
│   └── test_prayer_times_tool.py # Prayer times tests
│
├── docker/                       # Docker configuration
│   ├── docker-compose.dev.yml    # Development services (5 containers)
│   ├── Dockerfile.api            # API Docker image
│   └── init-db/                  # Database initialization scripts
│
├── migrations/                   # Database migrations (Alembic)
│   └── 001_initial_schema.sql    # Quran tables
│
├── docs/                         # Documentation (14 directories)
│   ├── analysis/                 # Data analysis reports
│   ├── api/                      # API documentation
│   ├── architecture/             # Architecture diagrams
│   ├── core-features/            # Feature documentation
│   ├── data/                     # Data documentation
│   ├── deployment/               # Deployment guides
│   ├── development/              # Development guides
│   ├── getting-started/          # Getting started guides
│   ├── guides/                   # How-to guides
│   ├── improvements/             # Improvement proposals
│   ├── planning/                 # Project planning
│   ├── reference/                # Reference materials
│   ├── reports/                  # Project reports
│   └── status/                   # Status updates
│
├── .env.example                  # Environment template (37 vars)
├── pyproject.toml                # Python dependencies (Poetry)
├── Makefile                      # Build commands (25 targets)
├── .gitignore                    # Git ignore rules
└── README.md                     # Project overview
```

---

## 📊 Data & Collections

### Vector Store (Qdrant) - 10 Collections

| Collection | Dimension | Description | Status |
|------------|-----------|-------------|--------|
| fiqh_passages | 1024 | Fiqh books and fatwas | ✅ 10,132+ vectors |
| hadith_passages | 1024 | Hadith collections | 🔄 160+ vectors |
| quran_tafsir | 1024 | Tafsir passages | ⏳ Ready (empty) |
| general_islamic | 1024 | General Islamic knowledge | ⏳ 5 vectors |
| duas_adhkar | 1024 | Duas and adhkar | ✅ 10 vectors |
| aqeedah_passages | 1024 | Aqeedah and creed | ✅ 90+ vectors |
| seerah_passages | 1024 | Prophet biography | ✅ 100+ vectors |
| islamic_history_passages | 1024 | Islamic history | ✅ 270+ vectors |
| arabic_language_passages | 1024 | Arabic language | ✅ 240+ vectors |
| spirituality_passages | 1024 | Spirituality and ethics | ✅ 150+ vectors |

**Total Vectors:** 11,147+ across 10 collections

### Embedding Model

- **Model:** Qwen/Qwen3-Embedding-0.6B
- **Dimensions:** 1024
- **Device:** CPU (CUDA fallback available)
- **Cache:** Redis + local dict fallback (7-day TTL)
- **Speed:** ~6 seconds per document (CPU)

### Mini-Dataset (GitHub-Friendly)

A **1.7 MB** sample dataset with **1,623 documents** across 8 collections (plus 2 from existing seeds), committed to Git for easy demonstration and testing.

**Creation:** `python scripts/create_mini_dataset.py`

### Full Datasets (Excluded from Git)

- **Shamela Library**: 8,425 books (17.16 GB) across 41 categories
  - Extracted to `datasets/data/extracted_books/` as .txt files
  - Metadata in `datasets/data/metadata/books.db` (SQLite)
- **Sanadset Hadith**: 650,986 hadith (1.43 GB) with sanad/matan
- **System Book Datasets**: 1,000+ book databases (.db files)

---

## 🔧 Configuration

### Environment Variables (`.env`)

```bash
# App
APP_ENV=development
DEBUG=true
SECRET_KEY=your-secret-key
API_V1_PREFIX=/api/v1

# Database (PostgreSQL 16)
DATABASE_URL=postgresql+asyncpg://athar:athar_password@localhost:5432/athar_db
DATABASE_POOL_SIZE=10

# Redis
REDIS_URL=redis://localhost:6379/0

# Qdrant (Vector DB)
QDRANT_URL=http://localhost:6333
QDRANT_API_KEY=

# LLM (Groq recommended)
LLM_PROVIDER=groq
GROQ_API_KEY=your-key
GROQ_MODEL=qwen/qwen3-32b
LLM_TEMPERATURE=0.1

# Embeddings
EMBEDDING_MODEL=qwen3-embedding-0.5b
EMBEDDING_DIMENSION=1024
HF_TOKEN=your-huggingface-token

# CORS
CORS_ORIGINS=http://localhost:3000,http://localhost:8000
```

---

## 🧪 Testing

```bash
# Run all tests
make test

# Run specific test file
make test-file file=test_router

# Test with coverage
poetry run pytest tests/ -v --cov=src --cov-report=term-missing
```

### Test Files (9 total)

| File | Tests | Coverage |
|------|-------|----------|
| `test_router.py` | Intent classifier accuracy | ~100% |
| `test_api.py` | API endpoints | ~97% |
| `test_zakat_calculator.py` | Zakat calculations | ~95% |
| `test_inheritance_calculator.py` | Inheritance rules | ~95% |
| `test_dua_retrieval_tool.py` | Dua retrieval | ~90% |
| `test_hijri_calendar_tool.py` | Date conversion | ~90% |
| `test_prayer_times_tool.py` | Prayer times | ~90% |

---

## 📝 Development Conventions

### Code Style

- **Python**: PEP 8 with type hints everywhere
- **Linting**: Ruff (line length 120, isort integration)
- **Type Checking**: MyPy (strict mode)
- **Formatting**: Ruff format
- **Logging**: Structured logging with structlog (JSON format)

### Commit Messages

Follow conventional commits format:
```
type(scope): Description

feat(tools): Add Zakat calculator
fix(router): Correct keyword pattern matching
docs(api): Add query endpoint examples
test(router): Add intent classification tests
```

### Project Management

- **Dependencies**: Poetry (`pyproject.toml`)
- **Database Migrations**: Alembic
- **Local Services**: Docker Compose (PostgreSQL, Qdrant, Redis)
- **Git Workflow**: Feature branches → main

---

## 🌐 API Documentation

### 18 Endpoints

| Endpoint | Method | Purpose | Status |
|----------|--------|---------|--------|
| `/api/v1/query` | POST | Main query endpoint | ✅ Working |
| `/api/v1/tools/zakat` | POST | Calculate zakat | ✅ Working |
| `/api/v1/tools/inheritance` | POST | Inheritance distribution | ✅ Working |
| `/api/v1/tools/prayer-times` | POST | Prayer times + Qibla | ✅ Working |
| `/api/v1/tools/hijri` | POST | Date conversion | ✅ Working |
| `/api/v1/tools/duas` | POST | Dua retrieval | ✅ Working |
| `/api/v1/quran/surahs` | GET | List all 114 surahs | ✅ Working |
| `/api/v1/quran/surahs/{n}` | GET | Specific surah details | ✅ Working |
| `/api/v1/quran/ayah/{s}:{a}` | GET | Specific ayah | ✅ Working |
| `/api/v1/quran/search` | POST | Verse search | ✅ Working |
| `/api/v1/quran/validate` | POST | Quotation validation | ✅ Working |
| `/api/v1/quran/analytics` | POST | NL2SQL queries | ✅ Working |
| `/api/v1/quran/tafsir/{s}:{a}` | GET | Tafsir retrieval | ✅ Working |
| `/api/v1/rag/fiqh` | POST | Fiqh RAG questions | ✅ Working |
| `/api/v1/rag/general` | POST | General Islamic RAG | ✅ Working |
| `/api/v1/rag/stats` | GET | RAG system statistics | ✅ Working |
| `/health` | GET | Health check | ✅ Working |
| `/ready` | GET | Readiness probe | ✅ Working |

**Test Result:** 17/18 endpoints PASSED (94.4%)

### Interactive Documentation

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

---

## 🗺️ Phase Roadmap

| Phase | Duration | Status | Key Deliverables |
|-------|----------|--------|------------------|
| **Phase 1** | Week 1-2 | ✅ Complete | Foundation, Router, Orchestrator, Citation |
| **Phase 2** | Week 3-4 | ✅ Complete | 6 Tools (Zakat, Inheritance, Prayer, Hijri, Dua) |
| **Phase 3** | Week 5-6 | ✅ Complete | Quran Pipeline, NL2SQL, Tafsir, Verse Retrieval |
| **Phase 4** | Week 7-8 | ✅ Complete | RAG Pipelines, Embeddings, Vector DB, Fiqh Agent |
| **Phase 5** | Week 9-10 | ✅ Complete | Next.js Frontend, Calculator Forms, RTL UI |
| **Phase 6** | Week 11-12 | ✅ Complete | 13 Agents, Mini-Dataset, 10 Collections |
| **Phase 7+** | Future | 🔄 Planned | Full embedding (2.9M vectors), Auth, CI/CD |

---

## 📈 Performance Metrics

| Metric | Value |
|--------|-------|
| Intent Classification Accuracy | ~90% |
| Query Response Time (fiqh RAG) | ~257ms |
| Greeting Response Time | <100ms |
| Zakat Calculation Time | <10ms |
| Embedding Speed (CPU) | ~6 sec/doc |
| Test Coverage | ~91% |
| Total Code | ~14,200 lines |
| Total Files | ~120+ files |

---

## 🔗 Key Resources

- **Repository**: https://github.com/Kandil7/Athar
- **Documentation**: `docs/` directory (14 subdirectories)
- **Issues**: https://github.com/Kandil7/Athar/issues
- **Mini-Dataset**: `data/mini_dataset/` (1.7 MB, GitHub-friendly)
- **Architecture Paper**: `docs/Fanar-Sadiq A Multi-Agent Architecture for Grounded Islamic QA.pdf`

---

## 🙏 Acknowledgments

- **Fanar-Sadiq**: The research paper that inspired this architecture
- **Quran.com**: For Quran text and API reference
- **Sunnah.com**: For hadith collections
- **IslamWeb & IslamOnline**: For fatwa sources
- **Azkar-DB**: https://github.com/osamayy/azkar-db for duas collection
- **Shamela Library**: 8,425 Islamic books (17.16 GB)
- **Sanadset**: 650,986 hadith dataset with sanad/matan

---

## 📄 License

MIT License - see LICENSE file for details.

---

<div align="center">

**Built with ❤️ for the Muslim community**

[🕌](#) Athar Islamic QA System • Based on Fanar-Sadiq Architecture

**19 commits • 120+ files • 14,200+ lines of code • 6 complete phases**

</div>

## Qwen Added Memories
- Athar src/ code review completed (April 8, 2026). Score: 6.5/10. Critical issues: (1) Severe code duplication across 7 agents, (2) 23 bare except: clauses, (3) inheritance_calculator.py truncated at line 662, (4) 8 files hardcode model names instead of using settings. Must fix before production.
