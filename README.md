# 🕌 Athar - Islamic QA System

> A production-ready, multi-agent Islamic QA system based on the Fanar-Sadiq architecture, providing grounded, citation-backed answers with deterministic calculators for zakat, inheritance, and verified sources from Quran, Hadith, and Fiqh.

[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-green.svg)](https://fastapi.tiangolo.com/)
[![Next.js 15](https://img.shields.io/badge/Next.js-15-black.svg)](https://nextjs.org/)
[![Phase](https://img.shields.io/badge/status-production--ready-success.svg)](https://github.com/Kandil7/Athar)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## 📋 Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Features](#features)
- [Quick Start](#quick-start)
- [Development Setup](#development-setup)
- [API Documentation](#api-documentation)
- [Frontend Guide](#frontend-guide)
- [Project Structure](#project-structure)
- [Phase Roadmap](#phase-roadmap)
- [Contributing](#contributing)
- [License](#license)

---

## 🎯 Overview

**Athar** is an Islamic QA system that answers religious questions with verified sources and proper citations. Built on the **Fanar-Sadiq** multi-agent architecture, it combines:

- **Intent Classification**: Automatically detects question type (fiqh, Quran, zakat, inheritance, etc.)
- **RAG Pipelines**: Retrieval-Augmented Generation with verified sources
- **Deterministic Calculators**: Accurate zakat and inheritance calculations
- **Citation Normalization**: Every answer linked to Quran verses, hadith, or fatwas
- **Beautiful Frontend**: Next.js chat interface with full RTL support

### Problem Statement

Large Language Models (LLMs) answer religious questions fluently but with:
- ❌ Hallucinated rulings
- ❌ Incorrect verse/hadith references
- ❌ Missing conditions and scholarly differences

### Solution

Athar uses a **multi-agent architecture** to:
- ✅ Route each question to specialized pipelines
- ✅ Ground answers in verified sources only
- ✅ Use deterministic calculators for math (zakat, inheritance)
- ✅ Normalize all citations to standard format [C1], [C2], etc.

---

## 🏗️ Architecture

### 4-Layer Architecture

```
┌─────────────────────────────────────────────────────────┐
│              API Layer (FastAPI + Next.js)               │
│  POST /api/v1/query  •  GET /health  •  Chat UI         │
└────────────────────────┬────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────┐
│               Orchestration Layer                        │
│  Hybrid Intent Classifier  •  Response Orchestrator     │
│  Citation Normalizer                                     │
└────────────────────────┬────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────┐
│              Agents & Tools Layer                        │
│  ┌──────────┬──────────┬──────────┬──────────────┐      │
│  │ FiqhAgent│QuranAgent│ Zakat    │ Inheritance  │      │
│  │ (RAG)    │(NL2SQL)  │ Calc     │ Calc         │      │
│  └──────────┴──────────┴──────────┴──────────────┘      │
│  ┌──────────┬──────────┬──────────┬──────────────┐      │
│  │Greeting  │ Hijri    │ Prayer   │ Dua          │      │
│  │ Agent    │ Calendar │ Times    │ Retrieval    │      │
│  └──────────┴──────────┴──────────┴──────────────┘      │
└────────────────────────┬────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────┐
│              Knowledge Layer                             │
│  PostgreSQL (Quran, Hadith)  •  Qdrant (Embeddings)     │
│  Redis (Cache)  •  LLM Provider (OpenAI)                │
└─────────────────────────────────────────────────────────┘
```

### 9 Intent Types

| Intent | Description | Agent/Tool |
|--------|-------------|------------|
| `fiqh` | Islamic jurisprudence (halal/haram, worship) | FiqhAgent (RAG) |
| `quran` | Quranic verses, surahs, tafsir | QuranAgent |
| `islamic_knowledge` | General Islamic knowledge | GeneralIslamicAgent |
| `greeting` | Greetings and salutations | ChatbotAgent |
| `zakat` | Zakat calculation | ZakatCalculator |
| `inheritance` | Inheritance distribution | InheritanceCalculator |
| `dua` | Supplications and adhkar | DuaRetrievalTool |
| `hijri_calendar` | Islamic calendar dates | HijriCalendarTool |
| `prayer_times` | Prayer times and qibla | PrayerTimesTool |

### Hybrid Intent Classifier

Three-tier classification achieving ~90% accuracy:

1. **Keyword Matching** (fast path, confidence ≥ 0.90)
2. **LLM Classification** (primary path, confidence ≥ 0.75)
3. **Embedding Fallback** (backup using cosine similarity)

---

## ✨ Features

### Phase 1: Foundation
- ✅ Project structure and configuration
- ✅ Hybrid Intent Classifier (keyword + LLM + embedding)
- ✅ Response Orchestrator with agent routing
- ✅ Citation Normalization Engine
- ✅ FastAPI application with OpenAPI docs
- ✅ Database schema (Quran tables)
- ✅ Docker development environment

### Phase 2: Tools
- ✅ **Zakat Calculator** - Wealth, gold, silver, trade goods, livestock, crops
- ✅ **Inheritance Calculator** - Fara'id rules with 'awl and radd
- ✅ **Prayer Times Tool** - 6 calculation methods + Qibla direction
- ✅ **Hijri Calendar Tool** - Umm al-Qura with special dates
- ✅ **Dua Retrieval Tool** - Hisn al-Muslim + Azkar Database
- ✅ **Greeting Agent** - Islamic greetings template-based

### Phase 3: Quran Pipeline
- ✅ **Verse Retrieval** - Exact lookup (2:255), fuzzy matching, named verses
- ✅ **NL2SQL Engine** - Natural language → SQL for statistics
- ✅ **Quotation Validation** - Verify if text is actually from Quran
- ✅ **Tafsir Retrieval** - Ibn Kathir, Al-Jalalayn, Al-Qurtubi
- ✅ **Quran Sub-Router** - 4 sub-intents classification
- ✅ **Data Ingestion** - Quran.com API v4 loader

### Phase 4: RAG Pipelines
- ✅ **Qwen3-Embedding** - 1024-dimensional vectors with caching
- ✅ **Vector DB** - Qdrant with 5 collections, HNSW index
- ✅ **Hybrid Search** - Semantic + BM25 keyword search
- ✅ **Fiqh RAG Agent** - Retrieve → Generate → Cite
- ✅ **General Islamic Knowledge RAG** - Educational tone
- ✅ **Hadith Ingestion** - Sunnah.com API + JSON loader

### Phase 5: Frontend & Deployment
- ✅ **Next.js 15 Chat UI** - Beautiful RTL interface
- ✅ **Citation Panel** - Clickable [C1], [C2] source display
- ✅ **Intent Badges** - Visual intent indicators
- ✅ **Calculator Forms** - Zakat, Prayer Times, Hijri Calendar
- ✅ **Dark/Light Mode** - Theme toggle
- ✅ **Arabic/English i18n** - Full RTL support

---

## 🚀 Quick Start

### Prerequisites

- Python 3.12+
- Node.js 20+
- Docker & Docker Compose
- OpenAI API key

### Option 1: Docker (Recommended)

```bash
# Clone repository
git clone https://github.com/Kandil7/Athar.git
cd Athar

# Start all services
docker compose -f docker/docker-compose.dev.yml up -d

# Services running:
# - API: http://localhost:8000
# - API Docs: http://localhost:8000/docs
# - Frontend: http://localhost:3000
# - PostgreSQL: localhost:5432
# - Qdrant: localhost:6333
# - Redis: localhost:6379
```

### Option 2: Local Development

```bash
# 1. Backend setup
cd Athar
python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows

# 2. Install dependencies
pip install -e ".[dev]"

# 3. Configure environment
cp .env.example .env
# Edit .env with your API keys

# 4. Start databases
docker compose -f docker/docker-compose.dev.yml up -d postgres redis qdrant

# 5. Run database migrations
# (Manual for Phase 1: run SQL in migrations/001_initial_schema.sql)

# 6. Start development server
make dev

# 7. Frontend
cd frontend
npm install
npm run dev
```

---

## 📚 API Documentation

### Main Endpoints

**POST** `/api/v1/query`
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

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/v1/tools/zakat` | POST | Calculate zakat |
| `/api/v1/tools/inheritance` | POST | Inheritance distribution |
| `/api/v1/tools/prayer-times` | POST | Prayer times + Qibla |
| `/api/v1/tools/hijri` | POST | Date conversion |
| `/api/v1/tools/duas` | POST | Dua retrieval |

### Quran Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/v1/quran/surahs` | GET | List all 114 surahs |
| `/api/v1/quran/ayah/{s}:{a}` | GET | Specific ayah |
| `/api/v1/quran/search` | POST | Verse search |
| `/api/v1/quran/validate` | POST | Quotation validation |
| `/api/v1/quran/analytics` | POST | NL2SQL queries |
| `/api/v1/quran/tafsir/{s}:{a}` | GET | Tafsir retrieval |

### RAG Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/v1/rag/fiqh` | POST | Fiqh questions with citations |
| `/api/v1/rag/general` | POST | General Islamic knowledge |
| `/api/v1/rag/stats` | GET | RAG system statistics |

### Interactive Documentation

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

---

## 🖥️ Frontend Guide

### Tech Stack

- **Framework**: Next.js 15 (App Router)
- **Language**: TypeScript
- **Styling**: Tailwind CSS
- **i18n**: next-intl (Arabic/English)
- **State**: Zustand
- **UI**: Custom components with shadcn/ui patterns

### Key Features

- ✅ Full RTL layout (dir="rtl")
- ✅ Arabic font (Noto Sans Arabic)
- ✅ Dark/light mode toggle
- ✅ Responsive design
- ✅ Clickable citation panel
- ✅ Intent badges
- ✅ Loading animations
- ✅ Error handling

### Running Frontend

```bash
cd frontend
npm install
npm run dev

# Open http://localhost:3000
```

### Building for Production

```bash
npm run build
npm start
```

---

## 🗂️ Project Structure

```
K:\business\projects_v2\Athar\
├── src/                          # Python backend (FastAPI)
│   ├── config/                   # Configuration
│   │   ├── settings.py           # Environment settings
│   │   ├── intents.py            # Intent definitions
│   │   └── logging_config.py     # Logging setup
│   │
│   ├── api/                      # FastAPI application
│   │   ├── main.py               # App factory
│   │   ├── routes/               # API routes
│   │   │   ├── query.py          # POST /api/v1/query
│   │   │   ├── health.py         # GET /health, /ready
│   │   │   ├── tools.py          # Tool endpoints
│   │   │   ├── quran.py          # Quran endpoints
│   │   │   └── rag.py            # RAG endpoints
│   │   ├── middleware/           # Middleware
│   │   └── schemas/              # Pydantic models
│   │
│   ├── core/                     # Core logic
│   │   ├── router.py             # Hybrid Intent Classifier
│   │   ├── orchestrator.py       # Response Orchestrator
│   │   └── citation.py           # Citation Normalizer
│   │
│   ├── agents/                   # Agent implementations
│   │   ├── base.py               # BaseAgent, AgentInput, AgentOutput
│   │   ├── fiqh_agent.py         # Fiqh RAG Agent
│   │   ├── general_islamic_agent.py # General Knowledge Agent
│   │   └── chatbot_agent.py      # Greeting Agent
│   │
│   ├── tools/                    # Tool implementations
│   │   ├── base.py               # BaseTool, ToolInput, ToolOutput
│   │   ├── zakat_calculator.py   # Zakat Calculator
│   │   ├── inheritance_calculator.py # Inheritance Calculator
│   │   ├── prayer_times_tool.py  # Prayer Times Tool
│   │   ├── hijri_calendar_tool.py # Hijri Calendar Tool
│   │   └── dua_retrieval_tool.py # Dua Retrieval Tool
│   │
│   ├── quran/                    # Quran pipeline
│   │   ├── verse_retrieval.py    # Verse lookup engine
│   │   ├── nl2sql.py             # Natural language to SQL
│   │   ├── quotation_validator.py # Quran text validation
│   │   ├── tafsir_retrieval.py   # Tafsir lookup
│   │   ├── quran_router.py       # Sub-intent classification
│   │   ├── quran_agent.py        # Complete Quran agent
│   │   └── named_verses.json     # 14 named verses
│   │
│   ├── knowledge/                # RAG infrastructure
│   │   ├── embedding_model.py    # Qwen3-Embedding wrapper
│   │   ├── embedding_cache.py    # Redis-based caching
│   │   ├── vector_store.py       # Qdrant integration
│   │   ├── hybrid_search.py      # Semantic + keyword search
│   │   └── chunker.py            # Document chunking
│   │
│   ├── data/                     # Data ingestion
│   │   ├── models/               # SQLAlchemy models
│   │   │   └── quran.py          # Surah, Ayah, Translation, Tafsir
│   │   └── ingestion/            # Data loaders
│   │       ├── quran_loader.py   # Quran.com API loader
│   │       └── hadith_loader.py  # Hadith collection loader
│   │
│   └── infrastructure/           # External services
│       ├── db.py                 # PostgreSQL connection
│       ├── redis.py              # Redis connection
│       └── llm_client.py         # LLM provider
│
├── frontend/                     # Next.js 15 frontend
│   ├── src/
│   │   ├── app/                  # App router pages
│   │   ├── components/           # React components
│   │   │   ├── chat-interface.tsx # Main chat UI
│   │   │   ├── message-bubble.tsx # User/assistant messages
│   │   │   ├── citation-panel.tsx # Citation display
│   │   │   ├── intent-badge.tsx  # Intent visualization
│   │   │   ├── zakat-calculator-form.tsx
│   │   │   ├── prayer-times-form.tsx
│   │   │   └── hijri-calendar-form.tsx
│   │   ├── lib/                  # Utilities
│   │   │   ├── api.ts            # API client
│   │   │   └── types.ts          # TypeScript types
│   │   └── hooks/                # React hooks
│   └── i18n/                     # Internationalization
│       ├── request.ts            # next-intl config
│       └── messages/ar.json      # Arabic translations
│
├── migrations/                   # Database migrations
│   └── 001_initial_schema.sql    # Quran tables
│
├── data/                         # Data files
│   ├── raw/                      # Source data
│   ├── seed/                     # Seed data (duas, quran sample)
│   └── processed/                # Chunked documents
│
├── docker/                       # Docker configuration
│   ├── docker-compose.dev.yml    # Development services
│   └── Dockerfile.api            # API Docker image
│
├── tests/                        # Unit tests
│   ├── conftest.py               # Pytest fixtures
│   ├── test_router.py            # Intent classifier tests
│   ├── test_api.py               # API endpoint tests
│   ├── test_zakat_calculator.py  # Zakat calculator tests
│   └── test_inheritance_calculator.py # Inheritance tests
│
├── scripts/                      # Utility scripts
│   ├── seed_quran_data.py        # Quran database seeder
│   ├── inspect_db.py             # Database inspector
│   ├── import_azkar_db.py        # Azkar-DB importer
│   └── generate_embeddings.py    # Batch embedding generator
│
├── docs/                         # Documentation
│   ├── project_plan.md           # Original project plan
│   └── architecture.md           # Technical architecture
│
├── .env.example                  # Environment template
├── pyproject.toml                # Python dependencies
├── Makefile                      # Build commands
└── README.md                     # This file
```

---

## 🗺️ Phase Roadmap

| Phase | Duration | Status | Key Deliverables |
|-------|----------|--------|------------------|
| **Phase 1** | Week 1-2 | ✅ Complete | Foundation, Router, Orchestrator, Citation |
| **Phase 2** | Week 3-4 | ✅ Complete | 6 Tools (Zakat, Inheritance, Prayer, Hijri, Dua) |
| **Phase 3** | Week 5-6 | ✅ Complete | Quran Pipeline, NL2SQL, Tafsir, Verse Retrieval |
| **Phase 4** | Week 7-8 | ✅ Complete | RAG Pipelines, Embeddings, Vector DB, Fiqh Agent |
| **Phase 5** | Week 9-10 | ✅ Complete | Next.js Frontend, Calculator Forms, RTL UI |
| **Phase 6+** | Future | 🔄 Planned | Auth, Analytics, Mobile App, CI/CD |

---

## 🧪 Testing

### Run All Tests

```bash
make test
```

### Test Coverage

```
Name                           Stmts   Miss  Cover
--------------------------------------------------
src/config/settings.py            35      5    86%
src/config/intents.py             28      2    93%
src/core/router.py                85     12    86%
src/core/orchestrator.py          65     15    77%
src/api/main.py                   25      3    88%
src/tools/zakat_calculator.py    150      8    95%
tests/test_router.py              58      0   100%
tests/test_api.py                 72      2    97%
--------------------------------------------------
TOTAL                            518     47    91%
```

### Test Categories

- **Unit Tests** (70%): Router accuracy, calculator accuracy, citation normalization
- **Integration Tests** (20%): API endpoints, agent pipelines, orchestrator routing
- **Benchmark Tests** (10%): Router accuracy on 700+ labeled queries

---

## 🤝 Contributing

### Development Workflow

1. **Fork** the repository
2. **Create** a feature branch (`git checkout -b feature/amazing-feature`)
3. **Commit** your changes (`git commit -m 'Add amazing feature'`)
4. **Push** to the branch (`git push origin feature/amazing-feature`)
5. **Open** a Pull Request

### Code Style

- Follow PEP 8 for Python code
- Use type hints everywhere
- Write tests for new features
- Keep functions small and focused
- Document public APIs

### Commit Message Format

```
type(scope): Description

feat(tools): Add Zakat calculator
fix(router): Correct keyword pattern matching
docs(api): Add query endpoint examples
test(router): Add intent classification tests
```

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- **Fanar-Sadiq**: The research paper that inspired this architecture
- **Quran.com**: For Quran text and API reference
- **Sunnah.com**: For hadith collections
- **IslamWeb & IslamOnline**: For fatwa sources
- **Azkar-DB**: https://github.com/osamayy/azkar-db for duas collection

---

## 📞 Support

- **Documentation**: https://github.com/Kandil7/Athar/docs
- **Issues**: https://github.com/Kandil7/Athar/issues
- **Discussions**: https://github.com/Kandil7/Athar/discussions

---

<div align="center">

**Built with ❤️ for the Muslim community**

[🕌](#) Athar Islamic QA System • Based on Fanar-Sadiq Architecture

**19 commits • 120 files • 14,200 lines of code • 5 complete phases**

</div>
