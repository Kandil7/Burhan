# Athar Islamic QA System - Complete Technical Documentation

## Table of Contents

1. [Introduction](#introduction)
2. [System Architecture](#system-architecture)
3. [API Endpoints](#api-endpoints)
4. [Intent Classification](#intent-classification)
5. [Agents and Tools](#agents-and-tools)
6. [RAG Pipeline](#rag-pipeline)
7. [Quran Module](#quran-module)
8. [Configuration](#configuration)
9. [Security](#security)
10. [Deployment](#deployment)

---

# 1. Introduction

## 1.1 What is Athar?

**Athar** (آثار - "Footprints" in Arabic) is an Islamic Question-Answering System built on the **Fanar-Sadiq Multi-Agent Architecture**. The system provides accurate, grounded answers to questions about Islamic jurisprudence, Quran, and general Islamic knowledge.

## 1.2 Key Features

| Feature | Description |
|---------|-------------|
| **Intent Classification** | Automatic detection of query type using 3-tier classification |
| **RAG Pipeline** | Retrieval-Augmented Generation for grounded answers |
| **Multi-Agent** | Specialized agents for different query types |
| **Deterministic Tools** | Zakat and Inheritance calculators with madhhab support |
| **Quran Analytics** | NL2SQL for Quran statistics |
| **Multi-Language** | Arabic and English support |

## 1.3 Supported Query Types

| Intent | Arabic | Example |
|--------|--------|---------|
| Fiqh | فقه | ما حكم الزكاة؟ |
| Quran | قرآن | ما آية الكرسي؟ |
| Islamic Knowledge | علم إسلامي | من هو عمر بن الخطاب؟ |
| Zakat | زكاة | احسب الزكاة على 10000 |
| Inheritance |ميراث | كيف يقسم الميراث؟ |
| Prayer Times | أوقات الصلاة | متى وقت العصر؟ |
| Hijri Calendar | التقويم الهجري | متى رمضان؟ |
| Dua | دعاء | دعاء الصباح |
| Greeting | تحية | السلام عليكم |

---

# 2. System Architecture

## 2.1 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      FastAPI Application                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │
│  │  Query API   │  │  Quran API   │  │   Tools API           │  │
│  │  /query      │  │  /quran/*    │  │   /tools/*            │  │
│  └──────┬───────┘  └──────┬───────┘  └──────────┬───────────┘  │
│         │                 │                      │              │
│  ┌──────▼─────────────────▼──────────────────────▼───────────┐   │
│  │              ResponseOrchestrator                          │   │
│  │  - Intent Routing (INTENT_ROUTING)                        │   │
│  │  - Agent/Tool Execution                                  │   │
│  │  - Fallback Handling                                     │   │
│  └──────────────────────────┬────────────────────────────────┘   │
│                             │                                    │
│  ┌──────────────────────────▼────────────────────────────────┐   │
│  │              HybridQueryClassifier                        │   │
│  │  ├── Tier 1: Keyword Matching (confidence ≥ 0.90)        │   │
│  │  ├── Tier 2: LLM Classification (confidence ≥ 0.75)       │   │
│  │  └── Tier 3: Embedding Similarity (fallback)             │   │
│  └───────────────────────────────────────────────────────────┘   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
                             │
         ┌──────────────────┼──────────────────┐
         │                  │                  │
┌────────▼────────┐ ┌──────▼──────┐ ┌──────▼──────┐
│     AGENTS       │ │    TOOLS    │ │    QURAN    │
│                  │ │             │ │   Router    │
│ FiqhAgent        │ │ ZakatCalc   │ │             │
│ GeneralIslamic  │ │ Inheritance │ │ VerseLookup│
│ ChatbotAgent    │ │ PrayerTimes │ │ Tafsir     │
│ (9+ more)       │ │ HijriCal   │ │ NL2SQL     │
│                  │ │ DuaRetriev │ │ Validation │
└─────────────────┘ └─────────────┘ └─────────────┘
         │                  │                  │
┌────────▼─────────────────▼──────────────────▼────────┐
│                    RAG Pipeline                         │
│  ┌────────────┐  ┌────────────┐  ┌────────────────┐  │
│  │ EmbeddingModel│  │VectorStore│  │ LLM Generator  │  │
│  │Qwen3-Embed  │  │  Qdrant   │  │GPT-4o/Groq    │  │
│  └────────────┘  └────────────┘  └────────────────┘  │
└─────────────────────────────────────────────────────────┘
```

## 2.2 Request Flow

```
User Query
    │
    ▼
┌─────────────────────────────┐
│  HybridQueryClassifier      │
│  1. Keyword Match           │
│  2. LLM Classify            │
│  3. Embedding Fallback      │
└─────────────────────────────┘
    │
    ▼
┌─────────────────────────────┐
│  ResponseOrchestrator      │
│  - Lookup intent           │
│  - Get agent/tool          │
│  - Execute                 │
└─────────────────────────────┘
    │
    ▼
┌─────────────────────────────┐
│  Agent/Tool Execution      │
│  - FiqhAgent (RAG)         │
│  - ZakatCalculator         │
│  - QuranAgent              │
│  - etc.                    │
└─────────────────────────────┘
    │
    ▼
┌─────────────────────────────┐
│  Response Assembly         │
│  - Format answer           │
│  - Add citations [C1][C2] │
│  - Add metadata            │
└─────────────────────────────┘
    │
    ▼
Response with Citations
```

## 2.3 Directory Structure

```
Athar/
├── src/
│   ├── api/                    # FastAPI application
│   │   ├── main.py             # Application factory
│   │   ├── routes/             # API routes
│   │   │   ├── query.py        # Main query endpoint
│   │   │   ├── quran.py        # Quran endpoints
│   │   │   ├── tools.py        # Tool endpoints
│   │   │   ├── rag.py          # RAG endpoints
│   │   │   └── health.py       # Health check
│   │   ├── schemas/            # Pydantic models
│   │   └── middleware/         # Middleware
│   │
│   ├── agents/                 # AI Agents
│   │   ├── base.py             # BaseAgent abstraction
│   │   ├── fiqh_agent.py       # Fiqh RAG agent
│   │   ├── general_islamic_agent.py
│   │   ├── chatbot_agent.py
│   │   └── ...
│   │
│   ├── tools/                  # Deterministic tools
│   │   ├── base.py             # BaseTool abstraction
│   │   ├── zodiac_calculator.py
│   │   ├── inheritance_calculator.py
│   │   ├── prayer_times_tool.py
│   │   ├── hijri_calendar_tool.py
│   │   └── dua_retrieval_tool.py
│   │
│   ├── knowledge/              # RAG components
│   │   ├── embedding_model.py  # Qwen3 embedding
│   │   ├── vector_store.py    # Qdrant vector DB
│   │   ├── hybrid_search.py    # Semantic + keyword
│   │   └── chunker.py          # Document chunking
│   │
│   ├── quran/                  # Quran module
│   │   ├── quran_agent.py      # Quran router
│   │   ├── verse_retrieval.py  # Verse lookup
│   │   ├── nl2sql.py            # Natural language to SQL
│   │   ├── quotation_validator.py
│   │   └── tafsir_retrieval.py
│   │
│   ├── core/                   # Core orchestration
│   │   ├── router.py           # Intent classifier
│   │   ├── orchestrator.py    # Query orchestrator
│   │   ├── registry.py        # Agent registry
│   │   └── citation.py       # Citation normalizer
│   │
│   ├── config/                 # Configuration
│   │   ├── settings.py         # App settings
│   │   ├── intents.py          # Intent definitions
│   │   ├── constants.py       # Centralized constants
│   │   └── logging_config.py  # Logging setup
│   │
│   ├── infrastructure/        # External services
│   │   ├── llm_client.py       # OpenAI/Groq client
│   │   ├── llm_cache.py        # Redis caching
│   │   ├── db_sync.py         # Sync DB
│   │   └── database.py        # DB utilities
│   │
│   └── data/                   # Data layer
│       ├── models/             # DB models
│       └── ingestion/          # Data loaders
│
├── scripts/                    # Utility scripts
├── tests/                      # Test suite
├── docker/                     # Docker config
├── docs/                       # Documentation
└── pyproject.toml              # Dependencies
```

---

# 3. API Endpoints

## 3.1 Query Endpoint

### POST /api/v1/query

Main endpoint for Islamic queries.

**Request:**
```json
{
    "query": "ما حكم زكاة المال؟",
    "language": "ar",
    "madhhab": "hanafi",
    "session_id": "optional-session-id"
}
```

**Response:**
```json
{
    "query_id": "uuid-here",
    "intent": "fiqh",
    "intent_confidence": 0.92,
    "answer": "زكاة المال هي...",
    "citations": [
        {
            "id": "C1",
            "type": "quran",
            "source": "Quran",
            "reference": "9:103",
            "text_excerpt": "خُذْ مِنْ أَمْوَالِهِمْ صَدَقَةً..."
        }
    ],
    "metadata": {
        "agent": "fiqh_agent",
        "processing_time_ms": 1234,
        "classification_method": "keyword"
    }
}
```

## 3.2 Quran Endpoints

### GET /api/v1/quran/surahs
Returns list of all 114 surahs.

### GET /api/v1/quran/ayah/{surah}:{ayah}
Returns specific ayah (verse).

### POST /api/v1/quran/search
Search verses by text.

### POST /api/v1/quran/analytics
Execute NL2SQL queries on Quran.

### GET /api/v1/quran/tafsir/{surah}:{ayah}
Get tafsir for specific ayah.

### POST /api/v1/quran/validate
Validate if text is from Quran.

## 3.3 Tool Endpoints

### POST /api/v1/tools/zakat
Calculate Zakat on wealth.

### POST /api/v1/tools/inheritance
Calculate inheritance distribution.

### GET /api/v1/tools/prayer-times
Get prayer times for location.

### GET /api/v1/tools/hijri
Get Hijri date.

### GET /api/v1/tools/duas
Get duas and adhkar.

---

# 4. Intent Classification

## 4.1 Three-Tier Classifier

The system uses a hybrid approach:

### Tier 1: Keyword Matching (Fast Path)
- Checks query against predefined keyword patterns
- High confidence threshold: ≥ 0.90
- No LLM call needed
- Examples: "زكاة", "zakat", "آية", "ميراث"

### Tier 2: LLM Classification (Primary)
- Uses GPT-4o-mini or Groq Qwen3-32B
- Confidence threshold: ≥ 0.75
- Structured JSON output with intent, confidence, language, sub_intent

### Tier 3: Embedding Similarity (Fallback)
- Uses Qwen3-Embedding-0.6B
- Compares query to labeled examples
- Low confidence: 0.6

## 4.2 Intent Definitions

```python
class Intent(str, Enum):
    FIQH = "fiqh"
    QURAN = "quran"
    ISLAMIC_KNOWLEDGE = "islamic_knowledge"
    GREETING = "greeting"
    ZAKAT = "zakat"
    INHERITANCE = "inheritance"
    DUA = "dua"
    HIJRI_CALENDAR = "hijri_calendar"
    PRAYER_TIMES = "prayer_times"
```

---

# 5. Agents and Tools

## 5.1 Agents (RAG-Based)

### FiqhAgent
- **Purpose**: Answer Islamic jurisprudence questions
- **Collection**: fiqh_passages
- **Temperature**: 0.1 (deterministic)
- **Pipeline**: Embed → Retrieve → Rerank → Generate → Cite

### GeneralIslamicAgent
- **Purpose**: General Islamic knowledge (history, biography, theology)
- **Collection**: general_islamic
- **Temperature**: 0.3 (conversational)

### ChatbotAgent
- **Purpose**: Greetings and simple responses
- **Type**: Rule-based with templates

## 5.2 Tools (Deterministic)

### ZakatCalculator
Calculates Zakat based on:
- Gold nisab: 85g
- Silver nisab: 595g
- Rate: 2.5%
- Supports madhhab differences

### InheritanceCalculator
Calculates inheritance based on:
- Quranic fixed shares (furood)
- Residuary rules (asabah)
- 'Awl and radd handling
- Madhhab-specific opinions

### PrayerTimesTool
Calculates prayer times using:
- Prayer times library
- Multiple calculation methods (MWL, ISNA, etc.)
- Qibla direction

### HijriCalendarTool
Converts between:
- Gregorian ↔ Hijri
- Islamic months
- Special dates (Ramadan, Eid)

### DuaRetrievalTool
Retrieves:
- Duas from Hisn al-Muslim
- Morning/evening adhkar
- Category-based search

---

# 6. RAG Pipeline

## 6.1 Architecture

```
Query → Embedding → Hybrid Search → Rerank → LLM Generate → Cite
```

## 6.2 Embedding Model

- **Model**: Qwen/Qwen3-Embedding-0.6B
- **Dimension**: 1024
- **Provider**: HuggingFace

## 6.3 Vector Store

- **Database**: Qdrant
- **Index**: HNSW
- **Metric**: Cosine similarity

## 6.4 Hybrid Search

Combines:
1. **Semantic search**: Embedding similarity
2. **Keyword search**: BM25-like scoring
3. **Reciprocal Rank Fusion**: Combined ranking

## 6.5 Generation

- **Models**: GPT-4o-mini (OpenAI) or Qwen3-32B (Groq)
- **Temperature**: 0.1 for fiqh, 0.3 for general
- **System prompts**: Arabic/English Islamic scholar

---

# 7. Quran Module

## 7.1 Features

- **Verse Retrieval**: By surah:ayah reference
- **Search**: Fuzzy text search
- **NL2SQL**: Natural language to SQL queries
- **Tafsir**: Multiple tafsir sources
- **Quotation Validation**: Verify Quranic text

## 7.2 NL2SQL Examples

| Natural Language | SQL |
|------------------|-----|
| "كم عدد آيات سورة البقرة؟" | `SELECT verse_count FROM surahs WHERE number = 2` |
| "كم سورة مكية؟" | `SELECT COUNT(*) FROM surahs WHERE revelation_type = 'Meccan'` |
| "أطول سورة؟" | `SELECT name_en FROM surahs ORDER BY verse_count DESC LIMIT 1` |

## 7.3 Tafsir Sources

- Ibn Kathir
- Al-Jalalayn
- Al-Qurtubi

---

# 8. Configuration

## 8.1 Environment Variables

```bash
# Application
APP_NAME=Athar
APP_ENV=development
SECRET_KEY=your-secret-key

# Database
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/athar_db

# Redis
REDIS_URL=redis://localhost:6379/0

# LLM
LLM_PROVIDER=openai  # or groq
OPENAI_API_KEY=sk-...
GROQ_API_KEY=gsk_...

# Embeddings
EMBEDDING_MODEL=Qwen/Qwen3-Embedding-0.6B

# Rate Limiting
RATE_LIMIT_ENABLED=true
RATE_LIMIT_PER_MINUTE=60
```

## 8.2 Settings (Pydantic)

All settings are centralized in `src/config/settings.py`:
- Application settings
- Database configuration
- Redis configuration
- LLM provider settings
- Rate limiting
- Security

---

# 9. Security

## 9.1 Rate Limiting

- **Default**: 60 requests/minute
- **Implementation**: In-memory (can use Redis for distributed)
- **Headers**: X-RateLimit-Limit, X-RateLimit-Remaining, X-RateLimit-Reset

## 9.2 API Key Authentication

- **Header**: X-API-Key
- **Protection**: All /api/v1/* endpoints
- **Public**: /health, /docs, /redoc

## 9.3 Security Headers

- X-Content-Type-Options: nosniff
- X-Frame-Options: DENY
- X-XSS-Protection: 1; mode=block
- Strict-Transport-Security: max-age=31536000
- Referrer-Policy: strict-origin-when-cross-origin

## 9.4 Input Validation

All inputs validated with Pydantic models:
- Query length limits
- Location coordinate validation
- Asset value constraints
- Madhhab validation

---

# 10. Deployment

## 10.1 Docker

```bash
# Build
docker build -f docker/Dockerfile.api -t athar-api .

# Run
docker-compose -f docker/docker-compose.dev.yml up
```

## 10.2 Production Requirements

| Component | Specification |
|-----------|---------------|
| API | FastAPI (Uvicorn) |
| Database | PostgreSQL 16 |
| Vector DB | Qdrant |
| Cache | Redis |
| LLM | OpenAI/Groq |
| Embeddings | HuggingFace |

## 10.3 Health Checks

- `/health` - Basic health check
- `/health/ready` - Readiness probe with dependency checks

---

# Appendix: Response Formats

## Standard Response

```json
{
    "query_id": "uuid",
    "intent": "fiqh",
    "intent_confidence": 0.92,
    "answer": "Answer text with citations [C1][C2]",
    "citations": [...],
    "metadata": {...},
    "follow_up_suggestions": [...]
}
```

## Error Response

```json
{
    "error": {
        "code": "VALIDATION_ERROR",
        "message": "Human readable error",
        "details": {...}
    }
}
```

---

*Last Updated: April 2026*
*Version: 0.5.0*
*Documentation generated from source code*
