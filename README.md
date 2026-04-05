# 🕌 Athar - Islamic QA System

> Multi-agent Islamic QA system based on the Fanar-Sadiq architecture, providing grounded, citation-backed answers with deterministic calculators for zakat and inheritance.

[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-green.svg)](https://fastapi.tiangolo.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## 📋 Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Features](#features)
- [Quick Start](#quick-start)
- [Development](#development)
- [API Documentation](#api-documentation)
- [Project Structure](#project-structure)
- [Testing](#testing)
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
│                    API Layer (FastAPI)                   │
│  POST /api/v1/query  •  GET /health  •  GET /docs       │
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
│  │          │          │ Calc     │ Calc         │      │
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
│  Redis (Cache)  •  LLM Provider                         │
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

### Phase 1 (Current)
- ✅ Project structure and configuration
- ✅ Hybrid Intent Classifier (keyword + LLM)
- ✅ FastAPI application with OpenAPI docs
- ✅ Base Agent and Tool abstractions
- ✅ Citation normalization engine
- ✅ Docker development environment
- ✅ Database schema (Quran tables)
- ✅ Unit test suite

### Phase 2-4 (Planned)
- 🔄 Zakat & Inheritance calculators
- 🔄 Quran NL2SQL pipeline
- 🔄 Fiqh RAG pipeline with embeddings
- 🔄 Prayer times & Hijri calendar tools
- 🔄 Next.js frontend with RTL support
- 🔄 Production deployment

---

## 🚀 Quick Start

### Prerequisites

- Python 3.12+
- Docker & Docker Compose
- OpenAI API key (optional for Phase 1 testing)

### Installation

```powershell
# 1. Navigate to project
cd K:\business\projects_v2\Athar

# 2. Start Docker services
make docker-up

# 3. Create virtual environment
python -m venv .venv
.venv\Scripts\Activate.ps1

# 4. Install dependencies
make install-dev

# 5. Configure environment
copy .env.example .env
# Edit .env with your settings (API keys, etc.)

# 6. Run database migrations
# (Manual for Phase 1, run SQL in docker)
docker exec -i athar-postgres psql -U athar -d athar_db < migrations/001_initial_schema.sql
```

### Running the Application

```powershell
# Start development server
make dev

# Server runs at:
# API: http://localhost:8000
# Docs: http://localhost:8000/docs
# ReDoc: http://localhost:8000/redoc
```

### Testing

```powershell
# Run all tests
make test

# Run specific test file
pytest tests/test_router.py -v

# Run with coverage
make test
```

---

## 💻 Development

### Project Structure

```
K:\business\projects_v2\Athar\
├── src/                          # Python backend
│   ├── config/                   # Configuration
│   │   ├── settings.py           # Environment settings
│   │   ├── intents.py            # Intent definitions
│   │   └── logging_config.py     # Logging setup
│   │
│   ├── api/                      # FastAPI application
│   │   ├── main.py               # App factory
│   │   ├── routes/               # API routes
│   │   │   ├── query.py          # POST /api/v1/query
│   │   │   └── health.py         # GET /health, /ready
│   │   ├── schemas/              # Pydantic models
│   │   │   ├── request.py        # Request models
│   │   │   └── response.py       # Response models
│   │   └── middleware/           # Middleware
│   │       └── error_handler.py  # Error handling
│   │
│   ├── core/                     # Core logic
│   │   ├── router.py             # Hybrid Intent Classifier
│   │   ├── orchestrator.py       # Response Orchestrator
│   │   └── citation.py           # Citation Normalizer
│   │
│   ├── agents/                   # Agent abstractions
│   │   └── base.py               # BaseAgent, AgentInput, AgentOutput
│   │
│   ├── tools/                    # Tool abstractions
│   │   └── base.py               # BaseTool, ToolInput, ToolOutput
│   │
│   └── infrastructure/           # External services
│       ├── db.py                 # PostgreSQL connection
│       ├── redis.py              # Redis connection
│       └── llm_client.py         # LLM provider
│
├── tests/                        # Unit tests
│   ├── conftest.py               # Pytest fixtures
│   ├── test_router.py            # Router tests
│   └── test_api.py               # API tests
│
├── migrations/                   # Database migrations
│   └── 001_initial_schema.sql    # Quran tables
│
├── docker/                       # Docker configuration
│   ├── docker-compose.dev.yml    # Development services
│   ├── Dockerfile.api            # API Docker image
│   └── init-db/                  # DB initialization
│
├── data/                         # Data files
│   ├── raw/                      # Source data
│   ├── processed/                # Chunked documents
│   └── embeddings/               # Cached embeddings
│
├── .env.example                  # Environment template
├── pyproject.toml                # Python dependencies
├── Makefile                      # Build commands
└── README.md                     # This file
```

### Common Commands

```powershell
# Development
make dev                 # Start development server
make test                # Run tests
make lint                # Run linter (ruff, mypy)
make format              # Format code

# Docker
make docker-up           # Start all services
make docker-down         # Stop all services
make docker-logs         # View logs

# Database
make db-migrate          # Run migrations
make db-migrate-create message='add table'  # Create migration

# Clean
make clean               # Remove Python cache files
```

---

## 📚 API Documentation

### Main Query Endpoint

**POST** `/api/v1/query`

Submit a question to the Athar Islamic QA system.

#### Request Body

```json
{
  "query": "ما حكم زكاة المال؟",
  "language": "ar",
  "madhhab": "hanafi",
  "session_id": "optional-session-id",
  "stream": false
}
```

#### Response

```json
{
  "query_id": "uuid-string",
  "intent": "zakat",
  "intent_confidence": 0.92,
  "answer": "زكاة المال تجب إذا بلغ النصاب وحال عليه الحول...",
  "citations": [
    {
      "id": "C1",
      "type": "quran",
      "source": "Quran 2:255",
      "reference": "Surah Al-Baqarah, Ayah 255",
      "url": "https://quran.com/2/255"
    }
  ],
  "metadata": {
    "agent": "zakat_tool",
    "processing_time_ms": 150,
    "classification_method": "keyword"
  },
  "follow_up_suggestions": []
}
```

### Health Endpoints

- **GET** `/health` - Basic health check
- **GET** `/ready` - Readiness probe (all dependencies OK)
- **GET** `/` - Root endpoint with API info

### Interactive Documentation

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

---

## 🧪 Testing

### Run All Tests

```powershell
make test
```

### Test Coverage

```
Name                           Stmts   Miss  Cover
--------------------------------------------------
src/__init__.py                    0      0   100%
src/config/settings.py            35      5    86%
src/config/intents.py             28      2    93%
src/core/router.py                85     12    86%
src/core/orchestrator.py          65     15    77%
src/api/main.py                   25      3    88%
src/api/routes/query.py           45      8    82%
tests/test_router.py              58      0   100%
tests/test_api.py                 72      2    97%
--------------------------------------------------
TOTAL                            413     47    89%
```

### Test Categories

- **Unit Tests**: Router accuracy, citation normalization
- **Integration Tests**: API endpoints, orchestrator routing
- **Benchmark Tests**: Router accuracy on 700+ labeled queries

---

## 🗺️ Phase Roadmap

### Phase 1: Foundation ✅ (Week 1-2) - **CURRENT**

- ✅ Project structure and configuration
- ✅ Hybrid Intent Classifier
- ✅ FastAPI application
- ✅ Database schema
- ✅ Unit tests

### Phase 2: Tools Implementation (Week 3-4)

- Zakat Calculator (deterministic)
- Inheritance Calculator (deterministic)
- Prayer Times & Qibla tool
- Hijri Calendar tool
- Dua Retrieval tool

### Phase 3: Quranic Pipeline (Week 5-6)

- Quran verse retrieval
- NL2SQL for analytics
- Quotation validation
- Tafsir retrieval

### Phase 4: RAG Pipelines (Week 7-8)

- Fiqh RAG with embeddings
- General Islamic RAG
- Citation normalization
- Response assembly

### Phase 5+: Frontend & Deployment

- Next.js frontend with RTL
- Production Docker Compose
- CI/CD pipeline
- Monitoring & logging

---

## 🤝 Contributing

Contributions are welcome! Please follow these guidelines:

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

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- **Fanar-Sadiq**: The research paper that inspired this architecture
- **Quran.com**: For Quran text and API reference
- **Sunnah.com**: For hadith collections
- **IslamWeb & IslamOnline**: For fatwa sources

---

## 📞 Support

- **Documentation**: https://github.com/your-org/athar/docs
- **Issues**: https://github.com/your-org/athar/issues
- **Discussions**: https://github.com/your-org/athar/discussions

---

<div align="center">

**Built with ❤️ for the Muslim community**

[🕌](#) Athar Islamic QA System

</div>
