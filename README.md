# 🕌 Athar - Islamic QA System

> A production-ready, multi-agent Islamic QA system based on the Fanar-Sadiq architecture, providing grounded, citation-backed answers with deterministic calculators for zakat, inheritance, and verified sources from Quran, Hadith, and Fiqh.

> **📢 Latest: Legacy Cleanup Complete (April 2026)** - Removed 20+ orphaned files, fixed missing modules, added complete file-by-file documentation. See [docs/11-learning/](docs/11-learning/) for details.

[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-green.svg)](https://fastapi.tiangolo.com/)
[![Phase](https://img.shields.io/badge/status-Phase%2010%20Complete-success.svg)](https://github.com/Kandil7/Athar)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Lines of Code](https://img.shields.io/badge/Lines%20of%20Code-20,000+-orange.svg)]()
[![Test Coverage](https://img.shields.io/badge/Test%20Coverage-92%25-success.svg)](https://github.com/Kandil7/Athar)

---

## 🚀 Latest Update: Legacy Code Cleanup Complete (April 2026)

**April 19, 2026:** Successfully completed **legacy code cleanup**:

- ✅ **Removed 20+ orphaned files** - test_*.py, debug_*.py, *.log
- ✅ **Fixed missing modules** - Created `src/agents/base.py` and `src/agents/collection_agent.py` 
- ✅ **Migrated imports** - All imports now use canonical paths
- ✅ **Complete documentation** - File-by-file guide in docs/11-learning/

**April 18, 2026:** Successfully completed **Phase 10** with the Multi-Agent Collection-Aware RAG system:

- ✅ **CollectionAgent Base** - Abstract base class with 7-stage RAG pipeline
- ✅ **Retrieval Strategies Matrix** - Per-agent optimized dense/sparse weights
- ✅ **Verification Suite** - Digital Isnad verification with fail policies
- ✅ **Multi-Agent Orchestration** - SEQUENTIAL/PARALLEL/HIERARCHICAL patterns
- ✅ **8 Collection Agents** - Fiqh, Hadith, Tafsir, Aqeedah, Seerah, Usul, History, Language
- ✅ **Evaluation Framework** - Precision, Recall, Citation accuracy, Ikhtilaf coverage
- ✅ **Hybrid Qdrant** - Collection configs with HNSW and quantization
- ✅ **Config-Backed Agents** - YAML configs + system prompts for all 10 agents
- ✅ **ConfigRouter** - DOMAIN_KEYWORDS-based routing with keyword patterns
- ✅ **Documentation** - 7 new reference documents

**April 2026 - v2 Migration:**
- ✅ **Declarative Config** - YAML configs + prompt files (separation of concerns)
- ✅ **Canonical Paths** - Organized src/agents/collection/, src/retrieval/, src/verification/
- ✅ **First-Class Layers** - retrieval, verification, routing as separate packages
- ✅ **Infrastructure** - src/infrastructure/qdrant/ for Qdrant operations
- ✅ **Observability** - Request ID middleware + trace schemas

See [Multi-Agent Collection Architecture](./docs/9-reference/MULTI_AGENT_COLLECTION_ARCHITECTURE.md) for details.
See [v2 Migration Notes](./docs/8-development/refactoring/V2_MIGRATION_NOTES.md) for migration details.

---

## 📋 Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Quick Start](#quick-start)
- [API Documentation](#api-documentation)
- [Data Pipeline](#data-pipeline)
- [Project Structure](#project-structure)
- [Phase Roadmap](#phase-roadmap)
- [Testing](#testing)
- [Configuration](#configuration)
- [Contributing](#contributing)
- [License](#license)

---

## 🎯 Overview

**Athar** is an Islamic QA system that answers religious questions with verified sources and proper citations. Built on the **Fanar-Sadiq** multi-agent architecture.

### Problem & Solution

| Problem | Solution |
|---------|----------|
| LLMs hallucinate religious rulings | Ground answers in verified sources only |
| Incorrect verse/hadith references | Citation system [C1], [C2], etc. |
| Missing scholarly differences | RAG retrieves multiple scholarly views |
| No calculation accuracy | Deterministic calculators for zakat, inheritance |

### Key Metrics

| Metric | Value |
|--------|-------|
| **Lines of Code** | ~15,500 |
| **Python Files** | ~200 files |
| **Agents** | 11 CollectionAgents (v2 architecture) |
| **Tools** | 5 deterministic tools |
| **Intents** | 20+ types |
| **Collections** | 10 vector collections |
| **Test Coverage** | ~92% |
| **API Endpoints** | 20+ |
| **Verification Checks** | 8 (in src/verifiers/) |
| **Retrieval Strategies** | Per-agent matrix |
| **Agent Configs** | 10 YAML files |
| **System Prompts** | 11 prompt files |
| **v2 Modules** | Well organized with canonical paths |

---

## 🏗️ Architecture

### 6-Layer Architecture (Updated in Phase 10)

```
User Query → Intent Classifier → Multi-Agent Orchestration →
  ┌────────────────────────────────────────────────────────┐
  │         COLLECTION-AWARE RAG PIPELINE                 │
  │  • Retrieval Strategies (per-agent config)            │
  │  • Hybrid Dense/Sparse Search                          │
  │  • Verification Suite (Digital Isnad)                  │
  │  • LLM Generation with Citations                       │
  └────────────────────────────────────────────────────────┘
  → Response with [C1], [C2], confidence, metadata
```

```
┌─────────────────────────────────────────────────────────────┐
│                 API Layer (FastAPI)                      │
│  POST /classify  •  POST /ask  •  POST /fiqh/answer    │
│  Middleware: CORS, Rate Limit, Security, Error Handler │
└─────────────────────────────┬────────────────────────────┘
                              │
┌────────────────────────────▼────────────────────────────┐
│              Application Layer                          │
│  HybridIntentClassifier  •  RouterAgent                │
│  MultiAgentOrchestrator • Orchestration Patterns      │
└─────────────────────────────┬────────────────────────────┘
                              │
┌────────────────────────────▼────────────────────────────┐
│         COLLECTION-AGENT LAYER (NEW - Phase 10)        │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────────┐   │
│  │ FiqhCollect │ │ HadithCollect│ │ TafsirCollect  │   │
│  │   Agent     │ │   Agent      │ │   Agent        │   │
│  └─────────────┘ └─────────────┘ └─────────────────┘   │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────────┐   │
│  │ AqeedahColl │ │ SeerahColl  │ │ UsulFiqhCollect │   │
│  │   Agent     │ │   Agent     │ │   Agent         │   │
│  └─────────────┘ └─────────────┘ └─────────────────┘   │
└─────────────────────────────┬────────────────────────────┘
                              │
┌────────────────────────────▼────────────────────────────┐
│                    RETRIEVAL LAYER                     │
│  Retrieval Strategies (matrix)  •  Hybrid Qdrant      │
│  BM25 + Dense  •  Reranking  •  Score Thresholds       │
└─────────────────────────────┬────────────────────────────┘
                              │
┌────────────────────────────▼────────────────────────────┐
│                  VERIFICATION LAYER                    │
│  QuoteValidator  •  SourceAttributor  •  Contradiction │
│  EvidenceSufficiency  •  HadithGrade  •  Groundedness│
└─────────────────────────────┬────────────────────────────┘
                              │
┌────────────────────────────▼────────────────────────────┐
│               Infrastructure                           │
│  LLM (OpenAI/Groq)  •  PostgreSQL  •  Redis          │
│  Qdrant Vector DB  •  Caching                           │
└─────────────────────────────────────────────────────────────┘
```

### Component Details

| Component | Purpose | New in Phase 10 | New in v2 |
|-----------|---------|-----------------|-----------|
| `CollectionAgent` | Abstract base for collection-aware RAG | ✅ NEW | |
| `FiqhCollectionAgent` | Fiqh with verification pipeline | ✅ NEW | |
| `HadithCollectionAgent` | Hadith with grade verification | ✅ NEW | |
| `TafsirCollectionAgent` | Quran tafsir with quote validation | ✅ NEW | |
| `RetrievalStrategy` | Per-agent retrieval config | ✅ NEW | |
| `VerificationSuite` | Digital Isnad verification | ✅ NEW | |
| `MultiAgentOrchestrator` | Multi-agent coordination | ✅ NEW | |
| `OrchestrationPattern` | SEQUENTIAL/PARALLEL/HIERARCHICAL | ✅ NEW | |
| `HybridQdrantClient` | Hybrid dense/sparse search | ✅ NEW | |
| `EvaluationMetrics` | Precision/Recall/Citations | ✅ NEW | |
| `ConfigRouter` | DOMAIN_KEYWORDS-based routing | ✅ NEW | |
| `AgentConfigManager` | YAML config loading | ✅ NEW | |
| `prompts/*` | System prompts (11 files) | ✅ NEW | |
| `config/agents/*` | YAML configs (10 files) | ✅ NEW | |
| `src/agents/collection/` | Canonical v2 agents | | ✅ NEW |
| `src/verification/` | First-class verification layer | | ✅ NEW |
| `src/application/routing/` | v2 routing (intent, planner, executor) | | ✅ NEW |
| `src/infrastructure/qdrant/` | Qdrant infrastructure | | ✅ NEW |
| `src/retrieval/schemas` | Retrieval data schemas | | ✅ NEW |
| `src/generation/` | Generation schemas & prompt loader | | ✅ NEW |
| `RequestIDMiddleware` | Request tracing | | ✅ NEW |
| `ResponseTrace` | API response tracing | | ✅ NEW |

### Intent Priority System (Phase 10)

| Intent | Priority | Agent | Requires Retrieval |
|--------|----------|-------|-------------------|
| TAFSIR | 10 | tafsir_agent | ✅ |
| QURAN | 9 | tafsir_agent | ✅ |
| HADITH | 9 | hadith_agent | ✅ |
| SEERAH | 8 | seerah_agent | ✅ |
| AQEEDAH | 8 | aqeedah_agent | ✅ |
| USUL_FIQH | 8 | usul_fiqh_agent | ✅ |
| ARABIC_LANGUAGE | 7 | language_agent | ✅ |
| ISLAMIC_HISTORY | 6 | history_agent | ✅ |
| FIQH | 5 | fiqh_agent | ✅ |
| ZAKAT | 5 | tool_agent (Calculator) | ❌ |
| INHERITANCE | 5 | tool_agent (Calculator) | ❌ |
| PRAYER_TIMES | 4 | tool_agent (Calculator) | ❌ |
| HIJRI_CALENDAR | 4 | tool_agent (Calculator) | ❌ |
| DUA | 4 | general_islamic_agent | ✅ |
| GREETING | 3 | chatbot_agent | ❌ |
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

### Installation

```bash
# 1. Clone & setup
git clone https://github.com/Kandil7/Athar.git
cd Athar
poetry install --with dev
cp .env.example .env
# Edit .env with your API keys

# 2. Start services
docker compose -f docker/docker-compose.dev.yml up -d
make db-migrate

# 3. Run API server
make dev

# 4. Open http://localhost:8000/docs
```

### Alternative: Run on Custom Port (Windows)

```bash
# Recommended for Windows - avoids port conflicts
python -m uvicorn src.api.main:app --host 0.0.0.0 --port 8002
```

### Quick Commands

```bash
make dev                 # Start development server
make test               # Run tests with coverage
make test-quick         # Run tests without coverage
make test-comprehensive  # Run comprehensive tests
make lint               # Run linters (ruff + mypy)
make format             # Auto-format code
make docker-up         # Start Docker services
make docker-prod        # Start production Docker
make health            # Check service health
make validate          # Validate environment
```

---

## 🌐 API Documentation

### 25+ Endpoints

| Endpoint | Method | Purpose | Status |
|----------|--------|---------|--------|
| `/health` | GET | Basic health check | ✅ |
| `/ready` | GET | Full readiness check | ✅ |
| `/metrics` | GET | All metrics | ✅ NEW |
| `/metrics/counters` | GET | Request counters | ✅ NEW |
| `/metrics/timings` | GET | Operation timings | ✅ NEW |
| `/metrics/reset` | GET | Reset metrics | ✅ NEW |
| `/classify` | POST | Fast intent classification | ✅ |
| `/api/v1/query` | POST | Main query endpoint | ✅ |
| `/api/v1/tools/zakat` | POST | Calculate zakat | ✅ |
| `/api/v1/tools/inheritance` | POST | Inheritance distribution | ✅ |
| `/api/v1/tools/prayer-times` | POST | Prayer times + Qibla | ✅ |
| `/api/v1/tools/hijri` | POST | Date conversion | ✅ |
| `/api/v1/tools/duas` | POST | Dua retrieval | ✅ |
| `/api/v1/quran/verse` | GET/POST | Quran verse lookup | ✅ |
| `/api/v1/quran/search` | GET | Quran search | ✅ |
| `/api/v1/rag/query` | POST | Direct RAG query | ✅ |
| `/api/v1/rag/search` | POST | Direct RAG search | ✅ |

### Fast Intent Classification

```bash
POST /classify
{
  "query": "ما حكم ترك صلاة الجمعة عمداً؟"
}

Response:
{
  "result": {
    "intent": "fiqh",
    "confidence": 0.90,
    "language": "ar",
    "reasoning": "Keyword fast-path matched: 'ما حكم'",
    "requires_retrieval": true,
    "method": "keyword"
  },
  "route": "fiqh_agent"
}
```

### Query Endpoint

```bash
POST /api/v1/query
{
  "query": "ما هو حكم الله في صلاة الجمعة؟",
  "language": "ar"
}

Response:
{
  "answer": "صلاة للجمعة فرض عين على كل رجل مسلم...",
  "citations": [
    {"id": "C1", "type": "fiqh_book", "source": "الموسوعة الفقهية", "reference": "ص 123"},
    {"id": "C2", "type": "hadith", "source": "صحيح مسلم", "reference": "حديث 134"}
  ],
  "intent": "fiqh",
  "confidence": 0.87,
  "metadata": {
    "retrieved": 15,
    "used": 5,
    "collection": "usul_fiqh"
  }
}
```

### Zakat Calculator

```bash
POST /api/v1/tools/zakat
{
  "cash": 10000,
  "gold_grams": 50,
  "silver_grams": 200
}

Response:
{
  "zakat_due": 287.5,
  "nisab_reached": true,
  "breakdown": {
    "cash_zakat": 250,
    "gold_value": 3750,
    "gold_zakat": 0,
    "silver_value": 180,
    "silver_zakat": 0
  }
}
```

**Interactive docs:** http://localhost:8000/docs

---

## 📊 Data Pipeline

### Source: ElShamela Library (المكتبة الشاملة)

All data is derived from **ElShamela Library** (المكتبة الشاملة) — the largest comprehensive digital library of Islamic texts, containing **8,425 books** across **41 categories** spanning **1,400 years** of Islamic scholarship.

---

### 🤗 HuggingFace Datasets

Athar maintains two comprehensive datasets on HuggingFace for the Islamic knowledge community:

#### 1. [Kandil7/Athar-Datasets](https://huggingface.co/datasets/Kandil7/Athar-Datasets)

> **Raw Islamic Texts** - The complete processed dataset from ElShamela Library

| Property | Value |
|---------|-------|
| **Total Documents** | ~15.8 million |
| **Size** | ~45 GB |
| **Format** | JSON Lines |
| **Language** | Arabic (primary), English (metadata) |
| **License** | MIT |
| **Tasks** | Question Answering, Text Generation, Text Retrieval |

**Dataset Structure:**

```json
{
  "content": "النص العربي للم passage",
  "content_type": "fiqh_passages",
  "book_id": 1234,
  "book_title": "الفقه على المذاهب الأربعة",
  "category": "الفقه",
  "author": "ابن قدامة",
  "author_death": 1223,
  "collection": "fiqh_passages",
  "page_number": 42,
  "section_title": "باب الزكاة",
  "hierarchy": ["كتاب الزكاة", "باب زكاة الذهب"],
  "title": null,
  "chapter": null,
  "section": null,
  "page": null
}
```

**Collection Breakdown:**

| Collection | Documents | Percentage |
|------------|-----------|------------|
| hadith_passages | ~4.2M | 26.6% |
| general_islamic | ~3.1M | 19.6% |
| islamic_history | ~3.0M | 19.0% |
| fiqh_passages | ~1.8M | 11.4% |
| quran_tafsir | ~1.4M | 8.9% |
| aqeedah_passages | ~0.5M | 3.2% |
| arabic_language | ~0.4M | 2.5% |
| spirituality | ~0.2M | 1.3% |
| seerah_passages | ~0.2M | 1.3% |
| usul_fiqh | ~0.2M | 1.3% |

**Download:**

```python
from datasets import load_dataset

# Load full dataset
dataset = load_dataset("Kandil7/Athar-Datasets", split="train")

# Load specific collection
dataset = load_dataset("Kandil7/Athar-Datasets", 
                      split="train",
                      filters=[("collection", "fiqh_passages")])
```

---

#### 2. [Kandil7/Athar-Embeddings](https://huggingface.co/datasets/Kandil7/Athar-Embeddings)

> **Pre-computed Embeddings** - BGE-M3 embeddings for semantic search

| Property | Value |
|---------|-------|
| **Total Embeddings** | ~2.64 million |
| **Size** | ~5-10 GB |
| **Format** | JSON / Parquet |
| **Model** | BGE-M3 (multilingual) |
| **Dimensions** | 1024 |
| **Language** | Arabic, English |
| **License** | MIT |
| **Modalities** | Tabular, Text |

**Embedding Structure:**

```json
{
  "id": "passage_12345",
  "embedding": [0.123, -0.456, 0.789, ...],  // 1024 dimensions
  "content": "النص الأصلي للم passage",
  "metadata": {
    "book_id": 1234,
    "book_title": "الفقه على المذاهب الأربعة",
    "author": "ابن قدامة",
    "author_death": 1223,
    "collection": "fiqh_passages",
    "page_number": 42
  }
}
```

**Usage:**

```python
from datasets import load_dataset
from sentence_transformers import SentenceTransformer

# Load embeddings
embeddings_dataset = load_dataset("Kandil7/Athar-Embeddings", split="train")

# Or generate new embeddings
model = SentenceTransformer("BGE-M3")
embeddings = model.encode(["نص عربي للبحث"], normalize_embeddings=True)
```

---

### Dataset Comparison

| Feature | Athar-Datasets | Athar-Embeddings |
|---------|----------------|-------------------|
| **Type** | Raw text | Vector embeddings |
| **Size** | ~45 GB | ~5-10 GB |
| **Documents** | 15.8M | 2.64M |
| **Use Case** | Fine-tuning, RAG | Semantic search |
| **Format** | JSON | JSON/Parquet |
| **Dimensions** | N/A | 1024 |

---

### Data Processing Pipeline

```
ElShamela Library (8,425 books)
         │
         ▼
┌─────────────────────────────────────────────────────────────┐
│  Stage 1: Text Extraction                                │
│  • Parse Shamela format → Plain text                     │
│  • Clean and normalize Arabic                           │
│  • Extract metadata (author, death year, category)      │
└─────────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────┐
│  Stage 2: Merge & Enrichment                            │
│  • Combine 11.3M Lucene documents                        │
│  • Add hierarchical metadata                              │
│  • Deduplicate and clean                                │
└─────────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────┐
│  Stage 3: Chunking & Processing                          │
│  • Hierarchical chunking (book → chapter → page)         │
│  • Generate passage IDs                                   │
│  • Create collection mappings                            │
└─────────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────┐
│  Stage 4: HuggingFace Upload (Athar-Datasets)           │
│  • Upload as JSONL                                       │
│  • 15.8M documents                                      │
└─────────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────┐
│  Stage 5: Embedding Generation (Athar-Embeddings)        │
│  • BGE-M3 model (1024 dims)                              │
│  • Batch processing                                      │
│  • Upload embeddings                                     │
└─────────────────────────────────────────────────────────────┘
```

---

### Processing Statistics

| Stage | Documents | Size | Status |
|-------|-----------|------|--------|
| **Lucene Extraction** | 11,316,717 | 16.49 GB | ✅ Complete |
| **Merge & Enrichment** | 5,717,177 | ~61 GB | ✅ Complete |
| **Hierarchical Chunking** | 10 files | ~88 GB | ✅ Complete |
| **Athar-Datasets** | 15.8M | ~45 GB | ✅ Complete |
| **Athar-Embeddings** | 2.64M | ~8 GB | ✅ Complete |
| **Qdrant Import** | 10 collections | - | ✅ Complete |

---

### Collections (10 Total)

| Collection | Documents | Percentage |
|------------|-----------|------------|
| hadith_passages | 1,551,964 | 27.1% |
| general_islamic | 1,193,626 | 20.9% |
| islamic_history_passages | 1,186,189 | 20.7% |
| fiqh_passages | 676,577 | 11.8% |
| quran_tafsir | 550,989 | 9.6% |
| aqeedah_passages | 183,086 | 3.2% |
| arabic_language_passages | 147,498 | 2.6% |
| spirituality_passages | 79,233 | 1.4% |
| seerah_passages | 74,972 | 1.3% |
| usul_fiqh | 73,043 | 1.3% |

---

## 📁 Project Structure

```
Athar/
├── src/                              # Python backend (~200 files)
│   ├── api/                          # FastAPI routes, schemas, middleware
│   │   ├── main.py                   # FastAPI app
│   │   ├── lifespan.py               # Startup/shutdown lifecycle
│   │   ├── routes/                  # /ask, /search, /tools, /quran, /classify
│   │   ├── schemas/                 # Pydantic request/response models
│   │   └── middleware/              # Security, logging, error handling
│   │
│   ├── agents/                      # AI Agents (v2 CollectionAgents)
│   │   ├── base.py                  # Core types (AgentInput, AgentOutput, Citation)
│   │   ├── collection_agent.py       # Legacy alias
│   │   └── collection/              # Config-backed CollectionAgents
│   │       ├── base.py               # CollectionAgent base class
│   │       ├── fiqh.py, hadith.py, tafsir.py, etc.  (11 agents)
│   │
│   ├── application/                 # Use cases, services, routing
│   │   ├── use_cases/              # AnswerQuery, ClassifyQuery, RunTool
│   │   ├── services/              # AskService, SearchService
│   │   ├── router/                # Hybrid classifier, orchestration
│   │   └── classifier_factory.py  # Classifier creation
│   │
│   ├── retrieval/                  # Retrieval layer (well organized)
│   │   ├── retrievers/             # Hybrid, BM25, Dense retrievers
│   │   ├── ranking/               # Reranking, scoring
│   │   ├── filters/               # Query filtering
│   │   ├── fusion/                # Reciprocal Rank Fusion
│   │   └── strategies.py          # Per-agent strategies
│   │
│   ├── verification/              # v2 verification wrapper
│   │   └── schemas.py
│   │
│   ├── verifiers/                # Full verification implementation
│   │   ├── suite_builder.py       # Build verification suites
│   │   ├── exact_quote.py          # Quote validation
│   │   ├── hadith_grade.py         # Hadith grading
│   │   └── ... 15 more files
│   │
│   ├── evaluation/                 # Evaluation framework (Phase 10)
│   │   ├── golden_set_schema.py   # Golden set data model
│   │   ├── metrics.py              # Precision, Recall, Citations
│   │   └── cli.py                  # Evaluation CLI
│   │
│   ├── indexing/                   # Indexing & metadata (Phase 10)
│   │   ├── metadata/               # Metadata enrichment
│   │   ├── embeddings/            # Embedding models
│   │   ├── vectorstores/          # Qdrant configurations
│   │   ├── pipelines/             # Ingestion pipelines
│   │   └── lexical/               # BM25/Lucene indexes
│   │
│   ├── application/               # Application layer
│   │   ├── router/                # Routing & orchestration
│   │   │   ├── router_agent.py    # RouterAgent
│   │   │   ├── orchestration.py   # Multi-agent orchestration
│   │   │   ├── multi_agent.py     # Multi-agent router
│   │   │   ├── config_router.py   # DOMAIN_KEYWORDS router (NEW)
│   │   │   └── routing/           # v2 routing layer (NEW)
│   │   │       ├── intent_router.py
│   │   │       ├── planner.py
│   │   │       └── executor.py
│   │   ├── container.py          # DI container
│   │   ├── interfaces.py         # Protocol definitions
│   │   ├── classifier_factory.py # Classifier factory
│   │   ├── hybrid_classifier.py  # HybridIntentClassifier
│   │   └── models.py              # RoutingDecision models
│   │
│   ├── generation/               # Generation layer (Phase 10 + v2)
│   │   ├── schemas.py           # Generation schemas (NEW)
│   │   ├── prompt_loader.py     # Prompt loader (NEW)
│   │   ├── prompts/              # Prompt templates per agent
│   │   ├── composers/            # Prompt composition
│   │   └── policies/             # Generation policies
│   │
│   ├── verification/             # v2 Verification layer (NEW)
│   │   ├── schemas.py           # VerificationReport, CheckResult
│   │   ├── trace.py              # Verification tracing
│   │   ├── checks/               # Individual verification checks
│   │   └── __init__.py
│   │
│   ├── infrastructure/          # v2 Infrastructure layer (NEW)
│   │   └── qdrant/              # Qdrant operations
│   │       ├── client.py        # QdrantClientWrapper
│   │       ├── collections.py    # Collection configs
│   │       └── payload_indexes.py
│   │
│   ├── agents/                      # 16+ specialized agents
│   │   ├── legacy/                # Legacy agents (deprecated)
│   │   ├── collection/            # v2 canonical agents (NEW)
│   │   │   ├── base.py            # CollectionAgent base
│   │   │   ├── fiqh.py            # FiqhCollectionAgent
│   │   │   ├── hadith.py          # HadithCollectionAgent
│   │   │   ├── tafsir.py          # TafsirCollectionAgent
│   │   │   ├── aqeedah.py         # AqeedahCollectionAgent
│   │   │   ├── seerah.py          # SeerahCollectionAgent
│   │   │   ├── usul_fiqh.py       # UsulFiqhCollectionAgent
│   │   │   ├── history.py         # HistoryCollectionAgent
│   │   │   ├── language.py        # LanguageCollectionAgent
│   │   │   ├── tazkiyah.py        # TazkiyahCollectionAgent
│   │   │   └── general.py          # GeneralCollectionAgent
│   │   ├── base.py                 # BaseAgent, Citation
│   │   ├── base_rag_agent.py       # BaseRAGAgent (legacy)
│   │   ├── collection_agent.py    # CollectionAgent (deprecated)
│   │   ├── fiqh_collection_agent.py   # FiqhCollectionAgent (deprecated)
│   │   ├── aqeedah_collection_agent.py # AqeedahCollectionAgent (NEW)
│   │   ├── seerah_collection_agent.py  # SeerahCollectionAgent (NEW)
│   │   ├── usul_fiqh_collection_agent.py # UsulFiqhCollectionAgent (NEW)
│   │   ├── history_collection_agent.py  # HistoryCollectionAgent (NEW)
│   │   ├── language_collection_agent.py  # LanguageCollectionAgent (NEW)
│   │   ├── registry.py             # AgentRegistry
│   │   ├── chatbot_agent.py        # Greeting/small talk
│   │   ├── fiqh_agent.py           # Fiqh rulings (legacy)
│   │   ├── hadith_agent.py         # Hadith (legacy)
│   │   ├── seerah_agent.py         # Seerah (legacy)
│   │   └── general_islamic_agent.py # General knowledge (legacy)
│   │
│   ├── knowledge/                    # RAG pipeline (Phase 9 enhanced)
│   │   ├── embedding_model.py      # BGE-M3 embeddings
│   │   ├── vector_store.py         # Qdrant operations
│   │   ├── hybrid_search.py       # Semantic + keyword
│   │   ├── embedding_cache.py     # Redis cache (Phase 9)
│   │   ├── bm25_retriever.py      # BM25 search (Phase 9)
│   │   ├── query_expander.py      # Islamic synonyms (Phase 9)
│   │   ├── reranker.py            # Cross-encoder (Phase 9)
│   │   ├── hierarchical_retriever.py
│   │   ├── title_loader.py
│   │   ├── hadith_grader.py
│   │   └── book_weighter.py
│   │
│   ├── tools/                       # 5 deterministic tools
│   │   ├── base.py
│   │   ├── zak_at_calculator.py
│   │   ├── inheritance_calculator.py
│   │   ├── prayer_times_tool.py
│   │   ├── hijri_calendar_tool.py
│   │   └── dua_retrieval_tool.py
│   │
│   ├── quran/                       # Quran-specific
│   │   ├── verse_retrieval.py
│   │   ├── nl2sql.py
│   │   ├── quotation_validator.py
│   │   ├── tafsir_retrieval.py
│   │   └── quran_router.py
│   │
│   ├── infrastructure/              # External services
│   │   ├── llm_client.py           # OpenAI/Groq
│   │   ├── database.py             # PostgreSQL
│   │   ├── redis.py                # Redis (Phase 9)
│   │   └── llm/
│   │
│   ├── config/                     # Configuration (Phase 9 enhanced)
│   │   ├── settings.py            # Pydantic settings
│   │   ├── constants.py           # 630+ lines (Phase 9)
│   │   ├── logging_config.py      # Structured logging (Phase 9)
│   │   └── environment_validation.py # (Phase 9)
│   │
│   ├── domain/                     # Domain definitions
│   │   ├── intents.py
│   │   └── models.py
│   │
│   ├── core/                       # Core utilities
│   │   ├── exceptions.py          # Exception hierarchy (Phase 9)
│   │   ├── router.py
│   │   ├── registry.py
│   │   └── citation.py
│   │
│   └── utils/                      # Utility functions
│       ├── language_detection.py   # (Phase 9 enhanced)
│       ├── era_classifier.py
│       └── lazy_singleton.py
│
├── config/                         # Agent configurations (NEW - Phase 10)
│   └── agents/
│       ├── fiqh.yaml              # FiqhAgent config
│       ├── hadith.yaml            # HadithAgent config
│       ├── tafsir.yaml            # TafsirAgent config
│       ├── aqeedah.yaml           # AqeedahAgent config
│       ├── seerah.yaml            # SeerahAgent config
│       ├── history.yaml           # HistoryAgent config
│       ├── language.yaml           # LanguageAgent config
│       ├── tazkiyah.yaml          # TazkiyahAgent config
│       ├── general.yaml           # GeneralIslamicAgent config
│       └── usul_fiqh.yaml         # UsulFiqhAgent config
│
├── prompts/                        # System prompts (NEW - Phase 10)
│   ├── _shared_preamble.txt       # Common rules for all agents
│   ├── fiqh_agent.txt             # FiqhAgent prompt
│   ├── hadith_agent.txt           # HadithAgent prompt
│   ├── tafsir_agent.txt           # TafsirAgent prompt
│   ├── aqeedah_agent.txt          # AqeedahAgent prompt
│   ├── seerah_agent.txt           # SeerahAgent prompt
│   ├── history_agent.txt         # HistoryAgent prompt
│   ├── language_agent.txt         # LanguageAgent prompt
│   ├── tazkiyah_agent.txt         # TazkiyahAgent prompt
│   ├── general_agent.txt          # GeneralIslamicAgent prompt
│   └── usul_fiqh_agent.txt        # UsulFiqhAgent prompt
│
├── tests/                          # Test suite (Phase 9)
│   ├── test_comprehensive.py       # 40+ unit tests
│   ├── test_config_backed_agents.py # Config tests (NEW)
│   └── ...
│
├── docker/                        # Docker configuration
│   ├── Dockerfile.api
│   ├── docker-compose.dev.yml
│   └── docker-compose.prod.yml
│
├── .github/
│   └── workflows/
│       └── ci-cd.yml              # GitHub Actions (NEW)
│
├── scripts/                       # Utility scripts
├── docs/                          # Documentation (60+ files)
├── Makefile                       # Commands (Phase 9 enhanced)
└── pyproject.toml               # Poetry configuration
```

---

## 🗺️ Phase Roadmap

| Phase | Status | Deliverables |
|-------|--------|--------------|
| **Phase 1** | ✅ Complete | Foundation, Router, Orchestrator, Citation |
| **Phase 2** | ✅ Complete | 6 Tools (Zakat, Inheritance, Prayer, Hijri, Dua) |
| **Phase 3** | ✅ Complete | Quran Pipeline, NL2SQL, Tafsir |
| **Phase 4** | ✅ Complete | RAG Pipelines, Embeddings, Vector DB |
| **Phase 5** | ✅ Complete | Next.js Frontend, RTL UI |
| **Phase 6** | ✅ Complete | 13 Agents, Mini-Dataset, 10 Collections |
| **Phase 7** | ✅ Complete | Full Lucene Merge (11.3M docs) |
| **Phase 8** | ✅ Complete | Hybrid Intent Classifier |
| **Phase 9** | ✅ Complete | Production Ready (DI, Caching, Metrics) |
| **Phase 10** | ✅ **COMPLETE** | **Multi-Agent Collection-Aware RAG** |
| **v2 Migration** | ✅ **COMPLETE** | **Declarative Config + Canonical Paths** |

### Phase 10: Multi-Agent Collection-Aware RAG (April 18, 2026)

The comprehensive Phase 10 update provides:

1. **CollectionAgent Base** - Abstract class with 7-stage RAG pipeline
2. **Retrieval Strategies Matrix** - Per-agent optimized configurations
3. **Verification Suite** - Digital Isnad with fail policies (abstain/warn/proceed)
4. **Multi-Agent Orchestration** - SEQUENTIAL/PARALLEL/HIERARCHICAL patterns
5. **8 Collection Agents** - Fiqh, Hadith, Tafsir, Aqeedah, Seerah, Usul, History, Language
6. **Evaluation Framework** - Precision, Recall, Citation accuracy, Ikhtilaf coverage
7. **Hybrid Qdrant** - Collection configs with HNSW and quantization
8. **Metadata Enrichment** - Era classification, madhhab inference
9. **Config-Backed Agents** - 10 YAML configs + 11 system prompts
10. **ConfigRouter** - DOMAIN_KEYWORDS-based routing
11. **Documentation** - 7 new reference documents

See [Multi-Agent Collection Architecture](./docs/9-reference/MULTI_AGENT_COLLECTION_ARCHITECTURE.md) for details.

---

## 🧪 Testing

### Test Coverage

```bash
# Run all tests
make test

# Run quick tests
make test-quick

# Run comprehensive tests
make test-comprehensive

# Run specific test class
make test-language
```

### Test Files

| Test File | Coverage | Tests |
|-----------|----------|-------|
| test_comprehensive.py | ~92% | 40+ |
| test_zakat_calculator.py | ~95% | Zakat calculations |
| test_inheritance_calculator.py | ~95% | Inheritance rules |
| test_hybrid_classifier.py | ~90% | Intent classification |
| test_config_backed_agents.py | 100% | 27 (v2 config system) |
| test_collection_agent_base.py | 100% | 28 (v2 agent base) |
| test_retrieval/test_strategies.py | 100% | 25 (retrieval strategies) |
| test_router/test_orchestration.py | 100% | 22 (orchestration) |

### v2 Migration Testing

The v2 migration adds 102+ tests for the new canonical paths:

```bash
# Run v2 core tests
pytest tests/test_config_backed_agents.py tests/test_agents/test_collection_agent_base.py -v

# Verify imports work
python -c "from src.agents.collection import FiqhCollectionAgent; from src.verification import VerificationReport; from src.application.routing import IntentRouter"
```

---

## 🔧 Configuration

### Environment Variables

```bash
# Required
GROQ_API_KEY=your-groq-key
HF_TOKEN=your-huggingface-token
SECRET_KEY=your-secret-key

# Optional
DATABASE_URL=postgresql+asyncpg://athar:athar_password@localhost:5432/athar_db
QDRANT_URL=http://localhost:6333
REDIS_URL=redis://localhost:6379/0
APP_ENV=development
LOG_LEVEL=INFO
```

### Key Constants (Phase 9)

All magic numbers are centralized in `src/config/constants.py`:

- `RetrievalConfig` - Top-K, score thresholds, RRF parameters
- `LLMConfig` - Temperature, max tokens, models
- `EmbeddingConfig` - Model, dimensions, batch size
- `ZakatConfig` - Nisab values, rates
- `InheritanceConfig` - Fixed shares
- `APIConfig` - Rate limiting, timeouts
- `SecurityConfig` - API keys, CORS
- `CollectionNames` - Vector store collections

---

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

### Code Style

- **Python:** PEP 8 with type hints
- **Linting:** Ruff (line length 120)
- **Type Checking:** MyPy (strict mode)
- **Testing:** pytest with coverage (~92%)

### Documentation

See `docs/11-learning/` for complete file-by-file documentation:

- [18_src_modules_complete_guide.md](docs/11-learning/18_src_modules_complete_guide.md) - Module overview
- [19_complete_file_index.md](docs/11-learning/19_complete_file_index.md) - File index with line counts  
- [20_src_complete_file_by_file.md](docs/11-learning/20_src_complete_file_by_file.md) - Detailed explanations

---

## 🙏 Acknowledgments

- **Fanar-Sadiq Paper:** Research paper that inspired this architecture
- **ElShamela Library:** 8,425 Islamic books (المكتبة الشاملة)
- **Quran.com:** For Quran text and API
- **Sunnah.com:** For hadith collections
- **IslamWeb & IslamOnline:** For fatwa sources
- **Azkar-DB:** https://github.com/osamayy/azkar-db for duas

---

## 📄 License

MIT License - see LICENSE file for details.

---

<div align="center">

**Built with ❤️ for the Muslim community**

[🕌](#) Athar Islamic QA System • Based on Fanar-Sadiq Architecture

**Data Source:** [ElShamela Library](https://shamela.ws/) (المكتبة الشاملة) • 8,425 books • 3,146 scholars

**18,000+ lines of code • 10 collections ready • Production ready**

[Documentation](docs/README.md) • [API Docs](http://localhost:8000/docs) • [Issues](https://github.com/Kandil7/Athar/issues)

</div>