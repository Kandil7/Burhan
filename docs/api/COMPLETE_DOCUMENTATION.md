# 🕌 Athar Islamic QA System - Complete Documentation

**Version:** 2.0  
**Last Updated:** April 7, 2026  
**Status:** Production-Ready (Phase 6 Complete)

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Architecture Overview](#architecture-overview)
3. [System Components](#system-components)
4. [Data Pipeline](#data-pipeline)
5. [Installation & Setup](#installation--setup)
6. [Development Guide](#development-guide)
7. [API Reference](#api-reference)
8. [Deployment](#deployment)
9. [Testing](#testing)
10. [Troubleshooting](#troubleshooting)
11. [Contributing](#contributing)
12. [License](#license)

---

## Executive Summary

### What is Athar?

Athar is a production-ready, multi-agent Islamic QA system that answers religious questions with verified sources from Quran, Hadith, and Fiqh. Built on the Fanar-Sadiq architecture, it combines intent classification, RAG pipelines, and deterministic calculators.

### Key Metrics

| Metric | Value |
|--------|-------|
| **Lines of Code** | 14,200+ |
| **Files** | 120+ |
| **Agents** | 13 specialized agents |
| **Tools** | 5 deterministic tools |
| **Intents** | 16 types |
| **Collections** | 10 vector collections |
| **Books** | 8,425 Islamic texts |
| **Hadith** | 650,986 narrations |
| **Test Coverage** | ~91% |

### Core Features

- ✅ **16 Intent Classification** - Detects question type automatically
- ✅ **13 Specialized Agents** - Fiqh, Hadith, Quran, Tafsir, Aqeedah, etc.
- ✅ **5 Deterministic Tools** - Zakat, Inheritance, Prayer Times, Hijri, Dua
- ✅ **RAG Pipelines** - Retrieval-Augmented Generation with verified sources
- ✅ **Quran Pipeline** - Verse retrieval, NL2SQL, tafsir, quotation validation
- ✅ **Citation System** - Every answer linked to Quran verses, hadith, or fatwas
- ✅ **Next.js Frontend** - Beautiful RTL chat interface with Arabic/English

---

## Architecture Overview

### 4-Layer Architecture

```
┌─────────────────────────────────────────────────────────┐
│              API Layer (FastAPI + Next.js)               │
│  POST /api/v1/query  •  GET /health  •  Chat UI         │
│  18 endpoints  •  OpenAPI docs  •  CORS                 │
└────────────────────────┬────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────┐
│               Orchestration Layer                        │
│  Hybrid Intent Classifier (3-tier)                      │
│  Response Orchestrator (agent routing)                  │
│  Citation Normalizer ([C1], [C2], etc.)                 │
│  Agent Registry (13 agents + 5 tools)                   │
└────────────────────────┬────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────┐
│              Agents & Tools Layer                        │
│                                                         │
│  AGENTS (13):                                           │
│  ┌──────────┬──────────┬──────────┬──────────────┐      │
│  │ FiqhAgent│QuranAgent│ Hadith   │ Sanadset     │      │
│  │ (RAG)    │(NL2SQL)  │ (RAG)    │ Hadith(RAG)  │      │
│  └──────────┴──────────┴──────────┴──────────────┘      │
│  ┌──────────┬──────────┬──────────┬──────────────┐      │
│  │Tafsir    │Aqeedah   │Seerah    │History       │      │
│  │Agent     │Agent     │Agent     │Agent         │      │
│  └──────────┴──────────┴──────────┴──────────────┘      │
│  ┌──────────┬──────────┬──────────┬──────────────┐      │
│  │UsulFiqh  │Arabic    │General   │Chatbot       │      │
│  │Agent     │Language  │Islamic   │Agent         │      │
│  └──────────┴──────────┴──────────┴──────────────┘      │
│                                                         │
│  TOOLS (5):                                             │
│  ┌──────────┬──────────┬──────────┬──────────────┐      │
│  │Zakat     │Inherit.  │Prayer    │Hijri         │      │
│  │Calc      │Calc      │Times     │Calendar      │      │
│  └──────────┴──────────┴──────────┴──────────────┘      │
│  ┌──────────────────────────────────────────────┐       │
│  │Dua Retrieval Tool                            │       │
│  └──────────────────────────────────────────────┘       │
└────────────────────────┬────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────┐
│              Knowledge Layer                            │
│                                                         │
│  DATA SOURCES:                                          │
│  • master.db (8,425 books catalog)                     │
│  • Lucene indexes (13.7 GB Arabic text)                │
│  • Sanadset (650K hadith with chains)                  │
│  • Shamela Library (8,425 books, 16.4 GB)              │
│                                                         │
│  VECTOR STORE:                                          │
│  • Qdrant (10 collections, 1024-dim vectors)           │
│  • Qwen3-Embedding-0.6B model                          │
│  • Redis cache (7-day TTL)                             │
│                                                         │
│  RELATIONAL:                                            │
│  • PostgreSQL 16 (Quran, Hadith tables)                │
│  • Redis 7 (caching, sessions)                         │
│  • LLM: Groq Qwen3-32B / OpenAI GPT-4o-mini            │
└─────────────────────────────────────────────────────────┘
```

### Data Flow

```
User Query
    ↓
Intent Classification (3-tier hybrid)
    ├─ Fast: Keyword matching (≥0.90 confidence)
    ├─ Primary: LLM classification (≥0.75)
    └─ Backup: Embedding similarity
    ↓
Response Orchestrator
    ↓
Route to Agent/Tool
    ├─ Fiqh/Hadith/Tafsir/etc → RAG Agent
    ├─ Quran → NL2SQL + Verse Retrieval
    ├─ Zakat/Inheritance → Calculator
    └─ Greeting → Chatbot
    ↓
Citation Normalization
    ↓
Response with [C1], [C2] citations
```

---

## System Components

### 1. Core Orchestration

**Files:**
- `src/core/router.py` - Hybrid Intent Classifier
- `src/core/orchestrator.py` - Response Orchestrator
- `src/core/citation.py` - Citation Normalizer
- `src/core/registry.py` - Agent Registry

**Intent Classifier:**
```python
# 3-tier classification
if keyword_match(query, confidence >= 0.90):
    return intent  # Fast path
elif llm_classify(query, confidence >= 0.75):
    return intent  # Primary path
else:
    return embedding_classify(query)  # Backup
```

**Response Orchestrator:**
```python
async def route_query(query: str, intent: Intent, **kwargs) -> AgentOutput:
    agent = registry.get_for_intent(intent)
    result = await agent.execute(query, **kwargs)
    return citation.normalize(result)
```

### 2. Agents (13 Total)

| Agent | Type | Purpose | RAG |
|-------|------|---------|-----|
| FiqhAgent | RAG | Islamic jurisprudence | ✅ |
| HadithAgent | RAG | Prophetic traditions | ✅ |
| SanadsetHadithAgent | RAG | Sanadset hadith | ✅ |
| TafsirAgent | RAG | Quran interpretation | ✅ |
| AqeedahAgent | RAG | Islamic creed | ✅ |
| SeerahAgent | RAG | Prophet biography | ✅ |
| IslamicHistoryAgent | RAG | Islamic history | ✅ |
| FiqhUsulAgent | RAG | Jurisprudence principles | ✅ |
| ArabicLanguageAgent | RAG | Arabic grammar/literature | ✅ |
| GeneralIslamicAgent | RAG | General knowledge | ✅ |
| QuranAgent | NL2SQL | Quran queries | ✅ |
| ChatbotAgent | Template | Greetings/small talk | ❌ |

**Agent Base Class:**
```python
class BaseAgent:
    async def execute(self, input: AgentInput) -> AgentOutput:
        """Execute agent with input."""
        pass
    
    async def retrieve(self, query: str, top_k: int = 10) -> List[Document]:
        """Retrieve relevant documents."""
        pass
    
    async def generate(self, query: str, docs: List[Document]) -> str:
        """Generate answer from documents."""
        pass
```

### 3. Tools (5 Total)

| Tool | Purpose | Deterministic |
|------|---------|---------------|
| ZakatCalculator | Zakat calculation | ✅ |
| InheritanceCalculator | Estate distribution | ✅ |
| PrayerTimesTool | Prayer times + Qibla | ✅ |
| HijriCalendarTool | Hijri date conversion | ✅ |
| DuaRetrievalTool | Dua/adhkar retrieval | ✅ |

### 4. API Endpoints (18 Total)

#### Main Endpoints

| Endpoint | Method | Purpose | Status |
|----------|--------|---------|--------|
| `/api/v1/query` | POST | Main query | ✅ |
| `/health` | GET | Health check | ✅ |
| `/ready` | GET | Readiness probe | ✅ |

#### Tool Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/v1/tools/zakat` | POST | Calculate zakat |
| `/api/v1/tools/inheritance` | POST | Inheritance distribution |
| `/api/v1/tools/prayer-times` | POST | Prayer times + Qibla |
| `/api/v1/tools/hijri` | POST | Date conversion |
| `/api/v1/tools/duas` | POST | Dua retrieval |

#### Quran Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/v1/quran/surahs` | GET | List all 114 surahs |
| `/api/v1/quran/surahs/{n}` | GET | Specific surah |
| `/api/v1/quran/ayah/{s}:{a}` | GET | Specific ayah |
| `/api/v1/quran/search` | POST | Verse search |
| `/api/v1/quran/validate` | POST | Quotation validation |
| `/api/v1/quran/analytics` | POST | NL2SQL queries |

#### RAG Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/v1/rag/fiqh` | POST | Fiqh RAG questions |
| `/api/v1/rag/general` | POST | General Islamic |
| `/api/v1/rag/stats` | GET | RAG statistics |

---

## Data Pipeline

### Complete Data Flow

```
┌─────────────────────────────────────────────────────────┐
│              RAW DATA SOURCES                           │
│                                                         │
│  1. master.db (50 MB)                                   │
│     • 8,425 books catalog                               │
│     • 3,146 authors with death years                    │
│     • 41 categories                                     │
│                                                         │
│  2. Lucene Indexes (13.7 GB)                            │
│     • page/ (7.3M docs)                                 │
│     • title/ (3.9M docs)                                │
│     • esnad/ (35K hadith chains)                        │
│                                                         │
│  3. Sanadset (1.43 GB)                                  │
│     • 650,986 hadith with sanad/matan                   │
│                                                         │
│  4. Extracted Books (16.4 GB)                           │
│     • 8,425 books in TXT format                         │
│                                                         │
│  5. Service Databases (148 MB)                          │
│     • hadeeth.db (37K cross-refs)                       │
│     • tafseer.db (65K mappings)                         │
│     • S2.db (3.2M morphological roots)                  │
└────────────────────────┬────────────────────────────────┘
                         │
                         ↓ Java Extractor (Lucene 9.12)
┌─────────────────────────────────────────────────────────┐
│              EXTRACTED DATA                             │
│                                                         │
│  • lucene_esnad.json (3 MB)                             │
│  • lucene_author.json (2 MB)                            │
│  • lucene_book.json (10 MB)                             │
│  • lucene_title.json (500 MB)                           │
│  • lucene_page.json (8-12 GB)                           │
│  • master_catalog.json (10 MB)                          │
│  • category_mapping.json (5 MB)                         │
│  • author_catalog.json (2 MB)                           │
└────────────────────────┬────────────────────────────────┘
                         ↓ Hierarchical Chunking
┌─────────────────────────────────────────────────────────┐
│              RAG-READY CHUNKS                           │
│                                                         │
│  Structure per chunk:                                   │
│  {                                                      │
│    "book_id": 622,                                      │
│    "title": "كتاب الإقناع",                              │
│    "author": "الحجاوي",                                  │
│    "author_death": 968,                                 │
│    "category": "الفقه الحنبلي",                          │
│    "collection": "fiqh_passages",                       │
│    "page": 42,                                          │
│    "chapter": "باب الوضوء",                              │
│    "hadith_refs": [323, 1030],                          │
│    "content": "..."                                     │
│  }                                                      │
│                                                         │
│  Total: ~500K-1M chunks across 10 collections          │
│  Chunk size: 300-600 tokens                             │
│  Overlap: 50-75 tokens                                  │
└────────────────────────┬────────────────────────────────┘
                         ↓ Qwen3-Embedding-0.6B
┌─────────────────────────────────────────────────────────┐
│              VECTOR EMBEDDINGS                          │
│                                                         │
│  Model: Qwen/Qwen3-Embedding-0.6B                      │
│  Dimensions: 1024                                       │
│  Device: CPU (CUDA available)                           │
│  Cache: Redis + local dict (7-day TTL)                  │
│                                                         │
│  Collections:                                           │
│  • fiqh_passages (~10,000 vectors)                      │
│  • hadith_passages (~650,000 vectors)                   │
│  • quran_tafsir (~6,000 vectors)                        │
│  • aqeedah_passages (~5,000 vectors)                    │
│  • seerah_passages (~5,000 vectors)                     │
│  • islamic_history (~8,000 vectors)                     │
│  • arabic_language (~6,000 vectors)                     │
│  • spirituality_passages (~4,000 vectors)               │
│  • general_islamic (~5,000 vectors)                     │
│  • duas_adhkar (~1,000 vectors)                         │
│                                                         │
│  Total: ~700K+ vectors                                  │
└────────────────────────┬────────────────────────────────┘
                         ↓ Qdrant Import
┌─────────────────────────────────────────────────────────┐
│              QDRANT VECTOR DB                           │
│                                                         │
│  • 10 collections                                       │
│  • HNSW index (M=16, ef_construct=128)                  │
│  • Hybrid search (semantic + BM25)                      │
│  • Metadata filtering                                   │
│                                                         │
│  Performance:                                           │
│  • Search latency: <50ms (top-10)                       │
│  • Memory: ~5-8 GB                                      │
│  • Storage: ~10-15 GB                                   │
└─────────────────────────────────────────────────────────┘
```

### Extraction Pipeline

**Step 1: Extract Master Catalog** (5 minutes)
```bash
python scripts/extract_master_catalog.py
```

**Step 2: Extract Lucene Indexes** (3-5 hours)
```bash
python scripts/extract_all_lucene_pipeline.py
```

**Step 3: Build Hierarchical Chunks** (1-2 hours)
```bash
python scripts/chunk_all_books.py
```

**Step 4: Upload to Hugging Face** (2-4 hours, Colab)
```
notebooks/04_upload_to_huggingface.ipynb
```

**Step 5: Embed on Colab GPU** (3 hours)
```
notebooks/01_embed_all_collections.ipynb
```

**Step 6: Import to Qdrant** (1 hour)
```bash
python scripts/import_to_qdrant.py
```

---

## Installation & Setup

### Prerequisites

- **Python:** 3.12+
- **Java:** 11+ (for Lucene extraction)
- **Node.js:** 20+ (for frontend)
- **Docker:** (for databases)
- **PostgreSQL:** 16+
- **Redis:** 7+
- **Qdrant:** (vector database)

### Backend Setup

```bash
# 1. Clone repository
git clone https://github.com/Kandil7/Athar.git
cd Athar

# 2. Install Python dependencies
poetry install --with dev

# 3. Configure environment
cp .env.example .env
# Edit .env with your API keys

# 4. Start databases
docker compose -f docker/docker-compose.dev.yml up -d postgres redis qdrant

# 5. Run database migrations
make db-migrate

# 6. Start development server
make dev

# API docs: http://localhost:8000/docs
```

### Frontend Setup

```bash
cd frontend
npm install
npm run dev

# Open http://localhost:3000
```

### Environment Variables

```bash
# Application
APP_ENV=development
DEBUG=true
SECRET_KEY=your-secret-key
API_V1_PREFIX=/api/v1

# Database
DATABASE_URL=postgresql+asyncpg://athar:athar_password@localhost:5432/athar_db

# Redis
REDIS_URL=redis://localhost:6379/0

# Qdrant
QDRANT_URL=http://localhost:6333

# LLM (Groq recommended)
LLM_PROVIDER=groq
GROQ_API_KEY=your-key
GROQ_MODEL=qwen/qwen3-32b

# Embeddings
EMBEDDING_MODEL=Qwen/Qwen3-Embedding-0.6B
HF_TOKEN=your-huggingface-token
```

---

## Development Guide

### Project Structure

```
Athar/
├── src/                          # Python backend
│   ├── config/                   # Configuration
│   │   ├── settings.py           # Environment settings
│   │   ├── intents.py            # 16 intent definitions
│   │   └── logging_config.py     # Structured logging
│   │
│   ├── api/                      # FastAPI application
│   │   ├── main.py               # App factory
│   │   ├── routes/               # 5 route modules
│   │   │   ├── query.py          # POST /api/v1/query
│   │   │   ├── health.py         # GET /health, /ready
│   │   │   ├── tools.py          # 5 tool endpoints
│   │   │   ├── quran.py          # 6 Quran endpoints
│   │   │   └── rag.py            # 3 RAG endpoints
│   │   └── schemas/              # Pydantic models
│   │
│   ├── core/                     # Core logic
│   │   ├── router.py             # Intent classifier
│   │   ├── orchestrator.py       # Response orchestrator
│   │   ├── citation.py           # Citation normalizer
│   │   └── registry.py           # Agent registry
│   │
│   ├── agents/                   # 13 agents
│   │   ├── base.py               # Base class
│   │   ├── fiqh_agent.py
│   │   ├── hadith_agent.py
│   │   ├── sanadset_hadith_agent.py
│   │   ├── tafsir_agent.py
│   │   ├── aqeedah_agent.py
│   │   ├── seerah_agent.py
│   │   ├── islamic_history_agent.py
│   │   ├── fiqh_usul_agent.py
│   │   ├── arabic_language_agent.py
│   │   ├── general_islamic_agent.py
│   │   └── chatbot_agent.py
│   │
│   ├── tools/                    # 5 tools
│   │   ├── base.py
│   │   ├── zakat_calculator.py
│   │   ├── inheritance_calculator.py
│   │   ├── prayer_times_tool.py
│   │   ├── hijri_calendar_tool.py
│   │   └── dua_retrieval_tool.py
│   │
│   ├── quran/                    # Quran pipeline
│   │   ├── verse_retrieval.py
│   │   ├── nl2sql.py
│   │   ├── quotation_validator.py
│   │   ├── tafsir_retrieval.py
│   │   ├── quran_router.py
│   │   └── quran_agent.py
│   │
│   └── knowledge/                # RAG infrastructure
│       ├── embedding_model.py
│       ├── embedding_cache.py
│       ├── vector_store.py
│       ├── hybrid_search.py
│       ├── chunker.py
│       └── hierarchical_chunker.py
│
├── data/
│   ├── mini_dataset/             # GitHub-friendly (1.7 MB)
│   ├── processed/                # Extracted/chunked data
│   └── athar-datasets-v2/        # Upload-ready datasets
│
├── datasets/                     # Full datasets (excluded from Git)
│   ├── system_book_datasets/     # Shamela databases (14.4 GB)
│   │   ├── master.db             # Complete catalog
│   │   ├── cover.db              # Book covers
│   │   ├── book/*.db             # 8,427 book databases
│   │   ├── service/*.db          # Cross-references
│   │   └── store/                # Lucene indexes (13.7 GB)
│   ├── data/extracted_books/     # 8,425 books (16.4 GB)
│   └── Sanadset*/                # 650K hadith (1.43 GB)
│
├── scripts/                      # 40+ utility scripts
│   ├── extract_master_catalog.py
│   ├── extract_all_lucene_pipeline.py
│   ├── LuceneExtractor.java
│   ├── create_mini_dataset.py
│   ├── chunk_all_books.py
│   ├── seed_mvp_data.py
│   └── test_*.py                 # Test scripts
│
├── notebooks/                    # Google Colab notebooks
│   ├── setup_colab_env.ipynb
│   ├── 01_embed_all_collections.ipynb
│   ├── 04_upload_to_huggingface.ipynb
│   └── 05_upload_to_kaggle.ipynb
│
├── tests/                        # Unit & integration tests
│   ├── conftest.py
│   ├── test_router.py
│   ├── test_api.py
│   ├── test_zakat_calculator.py
│   └── test_inheritance_calculator.py
│
├── docker/                       # Docker configuration
│   ├── docker-compose.dev.yml
│   └── Dockerfile.api
│
├── docs/                         # Documentation (14 dirs)
│   ├── analysis/
│   ├── api/
│   ├── architecture/
│   └── ...
│
├── pyproject.toml                # Python dependencies
├── Makefile                      # Build commands
├── .env.example                  # Environment template
└── README.md                     # Project overview
```

### Key Commands

```bash
# Development
make dev                    # Start development server
make lint                   # Run linters
make format                 # Auto-format code
make test                   # Run tests

# Data Processing
python scripts/extract_master_catalog.py    # Extract master.db
python scripts/extract_all_lucene_pipeline.py  # Extract Lucene
python scripts/chunk_all_books.py           # Build chunks
python scripts/create_category_mapping.py   # Category mapping

# Testing
python scripts/quick_test.py                # Quick API test
python scripts/test_all_endpoints_detailed.py  # Full test
python scripts/check_datasets.py            # Dataset integrity

# Docker
make docker-up            # Start all services
make docker-down          # Stop services
make docker-logs          # View logs
```

---

## API Reference

### Query Endpoint

**POST** `/api/v1/query`

**Request:**
```json
{
  "query": "ما حكم زكاة المال؟",
  "language": "ar",
  "madhhab": "hanafi"
}
```

**Response:**
```json
{
  "query_id": "uuid-string",
  "intent": "zakat",
  "intent_confidence": 0.92,
  "answer": "زكاة المال تجب إذا بلغ النصاب...",
  "citations": [
    {
      "id": "C1",
      "type": "quran",
      "source": "Quran 9:103",
      "reference": "Surah At-Tawbah, Ayah 103",
      "url": "https://quran.com/9/103"
    }
  ],
  "metadata": {
    "agent": "zakat_tool",
    "processing_time_ms": 150
  }
}
```

### Tool Endpoints

All tool endpoints follow the same pattern:

**POST** `/api/v1/tools/{tool_name}`

**Zakat Calculator Example:**
```json
{
  "wealth": 10000,
  "gold_value": 5000,
  "debts": 2000,
  "nisab_threshold": 595
}
```

**Response:**
```json
{
  "zakat_amount": 650.25,
  "nisab_met": true,
  "breakdown": {
    "wealth_zakat": 250.00,
    "gold_zakat": 125.00,
    "total": 650.25
  }
}
```

---

## Deployment

### Docker Deployment

```bash
# Production build
docker compose -f docker/docker-compose.prod.yml up -d

# Services:
# - API: http://localhost:8000
# - Frontend: http://localhost:3000
# - PostgreSQL: localhost:5432
# - Qdrant: localhost:6333
# - Redis: localhost:6379
```

### Google Colab (for Embedding)

1. Upload notebooks to Colab
2. Select T4 GPU runtime
3. Run all cells
4. Download embeddings

### Hugging Face Datasets

1. Prepare datasets: `python scripts/prepare_datasets_for_upload_v2.py`
2. Upload via Colab notebook
3. Repository: `https://huggingface.co/datasets/Kandil7/Athar-Datasets`

---

## Testing

### Run All Tests

```bash
make test
```

### Test Categories

| Test File | Coverage | Purpose |
|-----------|----------|---------|
| `test_router.py` | Intent classifier accuracy (~100%) | Router |
| `test_api.py` | API endpoints (~97%) | API |
| `test_zakat_calculator.py` | Zakat calculations (~95%) | Tools |
| `test_inheritance_calculator.py` | Inheritance rules (~95%) | Tools |
| `test_dua_retrieval_tool.py` | Dua retrieval (~90%) | Tools |
| `test_hijri_calendar_tool.py` | Date conversion (~90%) | Tools |
| `test_prayer_times_tool.py` | Prayer times (~90%) | Tools |

### Quick Smoke Test

```bash
python scripts/quick_test.py --port 8002
```

### Comprehensive Test Suite

```bash
python scripts/test_all_endpoints_detailed.py
```

---

## Troubleshooting

### Common Issues

**1. "Port 8000 already in use"**

```bash
# Kill port 8000
./kill_port_8000.ps1

# Or use different port
python -m uvicorn src.api.main:app --port 8002
```

**2. "Redis connection failed"**

```bash
# Redis fallback is automatic (local dict cache)
# Check Redis status
redis-cli ping
```

**3. "Lucene extraction fails"**

```bash
# Ensure Java is installed
java -version

# Check classpath includes backward-codecs
# Required: lucene-backward-codecs-9.12.0.jar
```

**4. "Embedding model not found"**

```bash
# Download from HuggingFace
huggingface-cli download Qwen/Qwen3-Embedding-0.6B
```

**5. "Qdrant collection not found"**

```bash
# Check collections
curl http://localhost:6333/collections

# Create collection
python scripts/create_collection.py fiqh_passages
```

---

## Contributing

### Development Workflow

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

### Code Style

- Python: PEP 8 with type hints
- Linting: Ruff (line length 120)
- Type Checking: MyPy (strict mode)
- Testing: pytest with coverage

### Commit Messages

```
type(scope): Description

feat(tools): Add Zakat calculator
fix(router): Correct keyword pattern matching
docs(api): Add query endpoint examples
test(router): Add intent classification tests
```

---

## License

MIT License - see LICENSE file for details.

---

**Built with ❤️ for the Muslim community**

[🕌](#) Athar Islamic QA System • Based on Fanar-Sadiq Architecture

**19 commits • 120+ files • 14,200+ lines of code • 6 complete phases**
