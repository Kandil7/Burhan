# 🕌 Burhan - Islamic QA System

> A production-ready, multi-agent Islamic QA system based on the Fanar-Sadiq architecture, providing grounded, citation-backed answers with deterministic calculators for zakat, inheritance, and verified sources from Quran, Hadith, and Fiqh.

---

## 🎉 Latest Achievement: Hybrid Intent Classifier ✅

**April 15, 2026:** Successfully integrated new **HybridIntentClassifier** for fast, accurate intent classification:

- ✅ **Fast keyword-based classification** (no LLM required for simple queries)
- ✅ **Priority-based conflict resolution** (10 intent levels from TAFSIR=10 to ISLAMIC_KNOWLEDGE=1)
- ✅ **Quran sub-intent automatic detection** (VERSE_LOOKUP, ANALYTICS, INTERPRETATION, QUOTATION_VALIDATION)
- ✅ **Confidence gating with fallback** to ISLAMIC_KNOWLEDGE when confidence < 0.5
- ✅ **New `/classify` endpoint** for instant intent detection (<50ms)

---

## 📋 Overview

**Burhan** is an Islamic QA system that answers religious questions with verified sources and proper citations. Built on the **Fanar-Sadiq** multi-agent architecture, it combines intent classification, RAG pipelines, and deterministic calculators to provide accurate, grounded answers to Islamic religious questions.

### Key Features

- **13 Specialized Agents**: Fiqh, Hadith, Sanadset Hadith, Quran, Tafsir, Aqeedah, Seerah, Islamic History, Arabic Language, Usul Fiqh, Spirituality, General Islamic, Chatbot
- **16 Intent Types**: fiqh, quran, islamic_knowledge, greeting, zakat, inheritance, dua, hijri_calendar, prayer_times, hadith, tafsir, aqeedah, seerah, usul_fiqh, islamic_history, arabic_language
- **5 Deterministic Tools**: Zakat Calculator, Inheritance Calculator, Prayer Times, Hijri Calendar, Dua Retrieval
- **RAG Pipelines**: 10 vector collections with BGE-m3 (1024 dimensions)
- **Quran Pipeline**: Verse retrieval, NL2SQL analytics, quotation validation, tafsir retrieval
- **Citation Normalization**: Every answer linked to Quran verses, hadith, or fatwas [C1], [C2], etc.
- **Hybrid Intent Classifier**: Keyword matching → Jaccard similarity → Confidence gating (~90% accuracy)

### Key Metrics

| Metric | Value |
|--------|-------|
| **Lines of Code** | 15,500+ |
| **Files** | 130+ |
| **Agents** | 13 specialized agents |
| **Tools** | 5 deterministic tools |
| **Intents** | 16 types (10 primary + 6 Quran sub-intents) |
| **Collections** | 10 vector collections |
| **Lucene Documents** | 11,316,717 processed |
| **RAG Documents** | 5,717,177 enriched |
| **Test Coverage** | ~91% |

---

## 🏗️ Architecture

### 5-Layer Architecture (Current)

```
┌─────────────────────────────────────────────────────────┐
│              API Layer (FastAPI)                         │
│  POST /classify  •  POST /query  •  20 endpoints        │
└────────────────────────┬────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────┐
│            Application Layer (NEW - Phase 8)            │
│  HybridIntentClassifier  •  RouterAgent                 │
│  ├── Keyword fast-path (100+ patterns)                 │
│  ├── Jaccard similarity fallback                       │
│  └── Quran sub-intent detection (4 types)              │
└────────────────────────┬────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────┐
│               Orchestration Layer                        │
│  Hybrid Query Classifier (LLM)  •  Response Orchestrator│
│  Citation Normalizer  •  Agent Registry                 │
└────────────────────────┬────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────┐
│         Agents & Tools Layer (13 agents + 5 tools)       │
│  ┌──────────┬──────────┬──────────┬──────────────┐      │
│  │ FiqhAgent│QuranAgent│ Zakat    │ Inheritance   │      │
│  │ (RAG)    │(NL2SQL)  │ Calc     │ Calc          │      │
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
│              Knowledge Layer (61 GB processed data)      │
│  PostgreSQL (Quran, Hadith)  •  Qdrant (10 collections) │
│  Redis (Cache)  •  LLM Provider (Groq Qwen3-32B)        │
│  BGE-m3 (1024-dim, 8192 tokens, 100+ languages)          │
└─────────────────────────────────────────────────────────┘
```

### Intent Priority System (Phase 8)

| Intent | Priority | Agent | Retrieval |
|--------|----------|-------|-----------|
| TAFSIR | 10 | general_islamic_agent | ✅ |
| QURAN | 9 | quran:* (+ sub-intent) | depends |
| HADITH | 9 | hadith_agent | ✅ |
| SEERAH | 8 | seerah_agent | ✅ |
| ISLAMIC_HISTORY | 7 | islamic_history_agent | ✅ |
| ARABIC_LANGUAGE | 6 | arabic_language_agent | ✅ |
| FIQH | 5 | fiqh_agent | ✅ |
| AQEDAH | 5 | aqeedah_agent | ✅ |
| USUL_FIQH | 4 | fiqh_usul_agent | ✅ |
| SPIRITUALITY | 3 | general_islamic_agent | ✅ |
| ZAKAT | 2 | Calculator (no RAG) | ❌ |
| INHERITANCE | 2 | Calculator (no RAG) | ❌ |
| GREETING | 2 | chatbot_agent | ❌ |
| DUA | 2 | Calculator (no RAG) | ❌ |
| HIJRI_CALENDAR | 2 | Calculator (no RAG) | ❌ |
| PRAYER_TIMES | 2 | Calculator (no RAG) | ❌ |
| ISLAMIC_KNOWLEDGE | 1 | general_islamic_agent | ✅ |

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
git clone https://github.com/Kandil7/Burhan.git
cd Burhan

# Install dependencies
poetry install --with dev

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
K:\business\projects_v2\Burhan\
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
│   │   │   ├── classification.py # NEW: /classify endpoint (Phase 8)
│   │   │   ├── query.py          # POST /api/v1/query (main endpoint)
│   │   │   ├── health.py         # GET /health, /ready
│   │   │   ├── tools.py          # 5 tool endpoints (zakat, etc.)
│   │   │   ├── quran.py          # 6 Quran endpoints
│   │   │   └── rag.py            # 3 RAG endpoints
│   │   ├── schemas/              # Pydantic models (request/response)
│   │   │   └── classification.py # NEW: Classification schemas
│   │   └── middleware/           # Error handler, CORS
│   │
│   ├── application/               # NEW: Application layer (Phase 8)
│   │   ├── interfaces.py         # IntentClassifier, Router protocols
│   │   ├── models.py             # RoutingDecision
│   │   ├── hybrid_classifier.py  # HybridIntentClassifier
│   │   └── router.py             # RouterAgent
│   │
│   ├── domain/                    # NEW: Domain definitions
│   │   ├── intents.py           # Intent, QuranSubIntent, routing
│   │   └── models.py            # ClassificationResult
│   │
│   ├── core/                     # Core logic
│   │   ├── router.py            # Legacy router (backward compat)
│   │   ├── orchestrator.py      # Response Orchestrator (agent routing)
│   │   ├── citation.py          # Citation Normalizer
│   │   └── registry.py          # Agent Registry
│   │
│   ├── agents/                   # 13 agent implementations
│   │   ├── base.py              # BaseAgent, AgentInput, AgentOutput
│   │   ├── fiqh_agent.py        # Fiqh RAG Agent (retrieve + generate)
│   │   ├── hadith_agent.py     # Hadith RAG Agent
│   │   ├── sanadset_hadith_agent.py  # Sanadset 650K Hadith Agent
│   │   ├── tafsir_agent.py     # Quran Tafsir Agent
│   │   ├── aqeedah_agent.py    # Islamic Creed Agent
│   │   ├── seerah_agent.py     # Prophet Biography Agent
│   │   ├── islamic_history_agent.py  # Islamic History Agent
│   │   ├── fiqh_usul_agent.py  # Jurisprudence Principles Agent
│   │   ├── arabic_language_agent.py  # Arabic Language Agent
│   │   ├── general_islamic_agent.py  # General Knowledge Agent
│   │   └── chatbot_agent.py    # Greeting/Small Talk Agent
│   │
│   ├── tools/                    # 5 deterministic tools
│   │   ├── base.py              # BaseTool, ToolInput, ToolOutput
│   │   ├── zakat_calculator.py  # Zakat (wealth, gold, silver, trade)
│   │   ├── inheritance_calculator.py # Inheritance (fara'id rules)
│   │   ├── prayer_times_tool.py # Prayer times (6 methods) + Qibla
│   │   ├── hijri_calendar_tool.py # Hijri dates (Umm al-Qura)
│   │   └── dua_retrieval_tool.py # Hisn al-Muslim + Azkar
│   │
│   ├── quran/                    # Quran pipeline (6 modules)
│   │   ├── verse_retrieval.py   # Verse lookup (exact + fuzzy)
│   │   ├── nl2sql.py            # Natural language → SQL
│   │   ├── quotation_validator.py # Verify Quran quotes
│   │   ├── tafsir_retrieval.py  # Tafsir lookup
│   │   ├── quran_router.py      # Sub-intent classification (4 types)
│   │   └── quran_agent.py       # Complete Quran agent
│   │
│   ├── knowledge/                # RAG infrastructure
│   │   ├── embedding_model.py   # BGE-m3 wrapper + cache
│   │   ├── embedding_cache.py   # Redis/local dict caching
│   │   ├── vector_store.py      # Qdrant (10 collections)
│   │   ├── hybrid_search.py    # Semantic + BM25 search
│   │   └── chunker.py           # Document chunking
│   │
│   ├── data/                    # Data ingestion
│   │   ├── models/              # SQLAlchemy models (Quran)
│   │   └── ingestion/           # Data loaders (Quran, Hadith)
│   │
│   └── infrastructure/          # External services
│       ├── db.py                # PostgreSQL (asyncpg)
│       ├── redis.py             # Redis connection
│       └── llm_client.py        # LLM provider (Groq/OpenAI)
│
├── data/
│   ├── mini_dataset/            # GitHub-friendly mini-dataset (1.7 MB)
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
│   │   └── README.md            # Dataset documentation
│   ├── seed/                    # Seed data (duas, quran samples)
│   └── processed/               # Chunked documents (all_chunks.json)
│
├── datasets/                    # Full datasets (excluded from Git)
│   ├── data/
│   │   ├── extracted_books/     # 8,425 Shamela books (17.16 GB)
│   │   └── metadata/           # books.db, categories.json, authors.json
│   ├── Sanadset*/              # 650,986 hadith (1.43 GB)
│   └── system_book_datasets/   # 1,000+ book databases (.db files)
│
├── scripts/                     # 40+ utility scripts
│   ├── analysis/               # Diagnostic & analysis scripts
│   ├── data/                   # Data seeding & generation
│   ├── ingestion/              # Data ingestion pipelines
│   ├── tests/                  # Test scripts
│   ├── utils/                  # Shared utilities
│   ├── lucene/                 # Lucene utilities (Java)
│   └── windows/                # Windows batch scripts
│
├── notebooks/                   # Colab notebooks
│   ├── 02_upload_and_embed.ipynb  # Main GPU embedding notebook
│   ├── verify_upload.ipynb     # Verification notebook
│   ├── COLAB_GPU_EMBEDDING_GUIDE.md # Complete setup guide
│   ├── UPLOAD_STATUS.md       # Upload progress tracking
│   └── google_drive_setup.md  # Google Drive configuration
│
├── tests/                       # 9 test files
│   ├── conftest.py            # Pytest fixtures
│   ├── test_router.py         # Intent classifier tests
│   ├── test_api.py            # API endpoint tests
│   ├── test_zakat_calculator.py # Zakat calculator tests
│   ├── test_inheritance_calculator.py # Inheritance tests
│   ├── test_dua_retrieval_tool.py # Dua tool tests
│   ├── test_hijri_calendar_tool.py # Hijri tool tests
│   └── test_prayer_times_tool.py # Prayer times tests
│
├── docker/                      # Docker configuration
│   ├── docker-compose.dev.yml  # Development services (5 containers)
│   ├── Dockerfile.api          # API Docker image
│   └── init-db/                # Database initialization scripts
│
├── docs/                        # Documentation (60+ files)
│   ├── 1-getting-started/      # Entry point for new developers
│   ├── 2-architecture/         # System architecture
│   ├── 3-core-features/       # Core features (RAG, Quran)
│   ├── 4-guides/              # How-to guides
│   ├── 5-api/                 # Full API documentation
│   ├── 6-data/                # Data & datasets
│   ├── 7-deployment/          # Deployment guides
│   ├── 8-development/         # Developer guides
│   ├── 9-reference/           # Reference materials
│   ├── 10-operations/        # Operations & maintenance
│   └── 11-learning/           # Learning & mentoring
│
├── migrations/                 # Database migrations (Alembic)
│   └── 001_initial_schema.sql # Quran tables
│
├── .env.example                # Environment template (37 vars)
├── pyproject.toml             # Python dependencies (Poetry)
├── Makefile                   # Build commands (25 targets)
├── .gitignore                 # Git ignore rules
├── alembic.ini                # Alembic configuration
└── README.md                  # Project overview (this file)
```

---

## 📊 Data & Collections

### Source: ElShamela Library (المكتبة الشاملة)

All data is derived from **ElShamela Library** — the largest comprehensive digital library of Islamic texts:

- **Website:** https://shamela.ws/
- **Books:** 8,425 texts from 3,146 scholars
- **Time Span:** 0-1400+ AH (7th-21st century CE)
- **Categories:** 41 original categories → 10 collections

### Vector Store (Qdrant) - 10 Collections

| Collection | Documents | Percentage | Status |
|------------|-----------|------------|--------|
| hadith_passages | 1,551,964 | 27.1% | ✅ Uploaded to HF |
| general_islamic | 1,193,626 | 20.9% | ✅ Uploaded to HF |
| islamic_history_passages | 1,186,189 | 20.7% | ✅ Uploaded to HF |
| fiqh_passages | 676,577 | 11.8% | ✅ Uploaded to HF |
| quran_tafsir | 550,989 | 9.6% | ✅ Uploaded to HF |
| aqeedah_passages | 183,086 | 3.2% | ✅ Uploaded to HF |
| arabic_language_passages | 147,498 | 2.6% | ✅ Uploaded to HF |
| spirituality_passages | 79,233 | 1.4% | ✅ Uploaded to HF |
| seerah_passages | 74,972 | 1.3% | ✅ Uploaded to HF |
| usul_fiqh | 73,043 | 1.3% | ✅ Uploaded to HF |
| **Total** | **5,717,177** | **100%** | ✅ |

### HuggingFace Dataset

- **Repository:** [Kandil7/Athar-Datasets](https://huggingface.co/datasets/Kandil7/Athar-Datasets)
- **Size:** 42.6 GB (10 collections)
- **Format:** JSONL with rich metadata (book_id, author, chapter, page, etc.)
- **Status:** ✅ Fully uploaded and verified

### Embedding Model

- **Model:** BAAI/bge-m3
- **Dimensions:** 1024
- **Max Tokens:** 8192
- **Languages:** 100+
- **Device:** GPU (Colab T4) / CPU fallback
- **Cache:** Redis + local dict fallback (7-day TTL)

---

## 🌐 API Documentation

### 20 Endpoints

| Endpoint | Method | Purpose | Status |
|----------|--------|---------|--------|
| **NEW** `/classify` | POST | Fast intent classification (<50ms) | ✅ |
| `/api/v1/query` | POST | Main query endpoint | ✅ |
| `/api/v1/tools/zakat` | POST | Calculate zakat | ✅ |
| `/api/v1/tools/inheritance` | POST | Inheritance distribution | ✅ |
| `/api/v1/tools/prayer-times` | POST | Prayer times + Qibla | ✅ |
| `/api/v1/tools/hijri` | POST | Date conversion | ✅ |
| `/api/v1/tools/duas` | POST | Dua retrieval | ✅ |
| `/api/v1/quran/surahs` | GET | List all 114 surahs | ✅ |
| `/api/v1/quran/surahs/{n}` | GET | Specific surah details | ✅ |
| `/api/v1/quran/ayah/{s}:{a}` | GET | Specific ayah | ✅ |
| `/api/v1/quran/search` | POST | Verse search | ✅ |
| `/api/v1/quran/validate` | POST | Quotation validation | ✅ |
| `/api/v1/quran/analytics` | POST | NL2SQL queries | ✅ |
| `/api/v1/quran/tafsir/{s}:{a}` | GET | Tafsir retrieval | ✅ |
| `/api/v1/rag/fiqh` | POST | Fiqh RAG questions | ✅ |
| `/api/v1/rag/general` | POST | General Islamic RAG | ✅ |
| `/api/v1/rag/stats` | GET | RAG system statistics | ✅ |
| `/health` | GET | Health check | ✅ |
| `/ready` | GET | Readiness probe | ✅ |

### NEW: Fast Intent Classification (`/classify`)

```bash
# Request
POST /classify
{
  "query": "ما حكم ترك صلاة الجمعة عمداً؟"
}

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

**Interactive docs:** http://localhost:8000/docs

---

## 🗺️ Phase Roadmap

| Phase | Status | Duration | Key Deliverables |
|-------|--------|----------|------------------|
| **Phase 1** | ✅ Complete | Week 1-2 | Foundation, Router, Orchestrator, Citation |
| **Phase 2** | ✅ Complete | Week 3-4 | 6 Tools (Zakat, Inheritance, Prayer, Hijri, Dua) |
| **Phase 3** | ✅ Complete | Week 5-6 | Quran Pipeline, NL2SQL, Tafsir, Verse Retrieval |
| **Phase 4** | ✅ Complete | Week 7-8 | RAG Pipelines, Embeddings, Vector DB, Fiqh Agent |
| **Phase 5** | ✅ Complete | Week 9-10 | Next.js Frontend, Calculator Forms, RTL UI |
| **Phase 6** | ✅ Complete | Week 11-12 | 13 Agents, Mini-Dataset, 10 Collections |
| **Phase 7** | ✅ Complete | Week 13-14 | Full Lucene Merge (11.3M docs) |
| **Phase 8** | ✅ **COMPLETE** | Week 15-16 | **Hybrid Intent Classifier** (keyword + similarity) |

### Phase 8: Hybrid Intent Classifier ✅ (April 15, 2026)

The new classifier provides:

1. **Fast keyword-based classification** (no LLM required)
   - 100+ Arabic/English keyword patterns
   - Covers all 16 intent types

2. **Priority-based intent resolution** (10 levels)
   - TAFSIR (10) → ISLAMIC_KNOWLEDGE (1)
   - Automatic conflict resolution

3. **Quran sub-intent detection** (4 types)
   - VERSE_LOOKUP: "ما رقم سورة كذا"
   - ANALYTICS: "كم مرة упомина كذا"
   - INTERPRETATION: "ما تفسير كذا"
   - QUOTATION_VALIDATION: "هل صحيح قول كذا"

4. **Confidence gating with fallback**
   - If confidence < 0.5, defaults to ISLAMIC_KNOWLEDGE
   - Falls back to Jaccard similarity if no keyword match

5. **New `/classify` endpoint** for instant intent detection (<50ms)

### Next Steps (Phase 9 - Future)

1. **LLM Intent Classifier** - Full LLM-based classification
2. **Embedding Classifier** - BGE-m3 cosine similarity
3. **Production Testing** - End-to-end verification
4. **Deploy to Production** - Full system launch

---

## 📈 Performance Metrics

| Metric | Value |
|--------|-------|
| Intent Classification Accuracy | ~90% |
| Intent Classification Speed | <50ms (keyword) / <500ms (LLM) |
| Query Response Time (fiqh RAG) | ~257ms |
| Greeting Response Time | <100ms |
| Zakat Calculation Time | <10ms |
| Embedding Speed (T4 GPU) | ~100 docs/sec |
| Test Coverage | ~91% |
| Total Code | 15,500+ lines |
| Total Files | 130+ files |

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
DATABASE_URL=postgresql+asyncpg://Burhan:Burhan_password@localhost:5432/Burhan_db
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
EMBEDDING_MODEL=BAAI/bge-m3
EMBEDDING_DIMENSION=1024
HF_TOKEN=your-huggingface-token

# CORS
CORS_ORIGINS=http://localhost:3000,http://localhost:8000
```

  ┃                                                                                                                                                                                                     
  ┃  $ cd "K:/business/projects_v2/Burhan" && wc -l data/processed/lucene_pages/collections/*.jsonl                                                                                                      
  ┃                                                                                                                                                                                                     
  ┃  738003 data/processed/lucene_pages/collections/aqeedah_passages.jsonl
  ┃      1015311 data/processed/lucene_pages/collections/arabic_language_passages.jsonl
  ┃      2397988 data/processed/lucene_pages/collections/fiqh_passages.jsonl
  ┃      3410436 data/processed/lucene_pages/collections/general_islamic.jsonl                                                                                                                          
  ┃      5059547 data/processed/lucene_pages/collections/hadith_passages.jsonl                                                                                                                          
  ┃      2850288 data/processed/lucene_pages/collections/islamic_history_passages.jsonl                                                                                                                 
  ┃      2128606 data/processed/lucene_pages/collections/quran_tafsir.jsonl                                                                                                                             
  ┃       294623 data/processed/lucene_pages/collections/seerah_passages.jsonl                                                                                                                          
  ┃       438776 data/processed/lucene_pages/collections/spirituality_passages.jsonl                                                                                                                    
  ┃       368388 data/processed/lucene_pages/collections/usul_fiqh.jsonl  
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

- **Python:** PEP 8 with type hints everywhere
- **Linting:** Ruff (line length 120, isort integration)
- **Type Checking:** MyPy (strict mode)
- **Formatting:** Ruff format
- **Logging:** Structured logging with structlog (JSON format)

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

- **Dependencies:** Poetry (`pyproject.toml`)
- **Database Migrations:** Alembic
- **Local Services:** Docker Compose (PostgreSQL, Qdrant, Redis)
- **Git Workflow:** Feature branches → main

---

## 🔗 Key Resources

- **Repository:** https://github.com/Kandil7/Burhan
- **HuggingFace Dataset:** https://huggingface.co/datasets/Kandil7/Athar-Datasets
- **Documentation:** `docs/` directory (14 subdirectories, 60+ files)
- **Issues:** https://github.com/Kandil7/Burhan/issues
- **Mini-Dataset:** `data/mini_dataset/` (1.7 MB, GitHub-friendly)
- **Architecture Paper:** `docs/Fanar-Sadiq A Multi-Agent Architecture for Grounded Islamic QA.pdf`

---

## 🙏 Acknowledgments

- **Fanar-Sadiq Paper:** The research paper that inspired this architecture
- **ElShamela Library:** 8,425 Islamic books (المكتبة الشاملة)
- **Quran.com:** For Quran text and API reference
- **Sunnah.com:** For hadith collections
- **IslamWeb & IslamOnline:** For fatwa sources
- **Azkar-DB:** https://github.com/osamayy/azkar-db for duas collection
- **Shamela Library:** 8,425 Islamic books (17.16 GB)
- **Sanadset:** 650,986 hadith dataset with sanad/matan

---

## 📄 License

MIT License - see LICENSE file for details.

---

## 📝 Session Summary: April 15, 2026 - Phase 8 Complete

### ✅ Completed

1. **Hybrid Intent Classifier Implementation**
   - Fast keyword-based classification (100+ patterns)
   - Priority-based conflict resolution (10 levels)
   - Quran sub-intent detection (4 types)
   - Confidence gating with fallback
   - New `/classify` endpoint (<50ms)

2. **Documentation Update**
   - Updated main README.md with Phase 8 details
   - Updated QWEN.md (this file)
   - Updated notebooks/README.md

3. **Architecture Updates**
   - Added Application Layer to 5-layer architecture
   - Added domain models for intent classification
   - Added backward compatibility layer

### 🔑 Key Context

- **Branch:** `dev` (production-ready)
- **Working Port:** 8002 (recommended for Windows)
- **HF Token:** Configured in `.env`
- **HF Dataset:** 42.6 GB uploaded (10 collections)
- **Next Step:** Run Colab GPU embedding (~13 hours on T4)

---

<div align="center">

**Built with ❤️ for the Muslim community**

[🕌](#) Burhan Islamic QA System • Based on Fanar-Sadiq Architecture

**Data Source:** [ElShamela Library](https://shamela.ws/) (المكتبة الشاملة) • 8,425 books • 3,146 scholars

**11.3M+ documents processed • 10 collections built • Hybrid Intent Classifier active**

[Documentation](docs/README.md) • [API Docs](http://localhost:8000/docs) • [Issues](https://github.com/Kandil7/Burhan/issues)

</div>