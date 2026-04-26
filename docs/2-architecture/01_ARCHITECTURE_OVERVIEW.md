# 🏗️ Burhan Architecture Overview

## 📊 Complete System Architecture (Updated: April 15, 2026 - Phase 8)

```
┌─────────────────────────────────────────────────────────────────┐
│                        USER INTERFACE LAYER                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐       │
│  │  Next.js 15  │    │   Swagger    │    │   Future:    │       │
│  │  Frontend    │    │    UI/ReDoc  │    │  Mobile App  │       │
│  │  (Port 3000) │    │ (Port 8000)  │    │  (React Nat) │       │
│  └──────┬───────┘    └──────┬───────┘    └──────────────┘       │
│         │                   │                                    │
│    ┌────┴───────────────────┴────┐                             │
│    │      /classify endpoint     │  ← جديد! (<50ms)             │
│    └─────────────────────────────┘                             │
└─────────────────────────────────────────────────────────────────┘
          │
          ▼
┌─────────────────────────────────────────────────────────────────┐
│                      API GATEWAY LAYER                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│              FastAPI Application (Port 8000)                     │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │              Middleware Stack                             │   │
│  │  • CORS  • Error Handler  • Request Logging  • Auth     │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                  │
│  ┌────────────┐ ┌──────────┐ ┌──────┐ ┌────┐ ┌────────────┐    │
│  │ **NEW**    │ │/api/v1/  │ │/api/ │ │... │ │ /health    │    │
│  │ /classify  │ │ query    │ │v1/   │ │    │ │ /ready     │    │
│  │            │ │          │ │quran │ │    │ │ /docs      │    │
│  └─────┬──────┘ └────┬─────┘ └──┬───┘ └────┘ └────────────┘    │
│        │              │         │                                 │
└────────┼──────────────┼─────────┼─────────────────────────────────┘
         │              │         │
         ▼              ▼         ▼
┌─────────────────────────────────────────────────────────────────┐
│            APPLICATION LAYER (NEW - Phase 8)                    │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌─────────────────────┐      ┌──────────────────────┐          │
│  │ HybridIntentClassifier│     │ RouterAgent           │          │
│  │                      │     │                       │          │
│  │ • Keyword fast-path  │────▶│ • Priority resolution │          │
│  │   (100+ patterns)   │     │   (10 levels)         │          │
│  │ • Jaccard fallback  │     │ • Metadata attachment │          │
│  │ • Confidence gating │     │ • Quran sub-intents  │          │
│  │   (<0.5 → fallback) │     │   (4 types)           │          │
│  └──────────────────────┘     └──────────┬───────────┘          │
│                                          │                       │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │              Domain Models                                │   │
│  │  • Intent (16 types + 4 Quran sub-intents)               │   │
│  │  • ClassificationResult (confidence, method, routing)   │   │
│  │  • RoutingDecision (agent, metadata, requires_retrieval)│   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                  │
└──────────────────────────────────────┬──────────────────────────┘
                                       │
┌──────────────────────────────────────┼──────────────────────────┐
│                  ORCHESTRATION LAYER                             │
├──────────────────────────────────────┼──────────────────────────┤
│                                      │                          │
│  ┌───────────────────────────────────┴───────────────────────┐   │
│  │              Hybrid Query Classifier (LLM-tier)            │   │
│  │  • Tier 1: Keywords (0.92 confidence) - Fast              │   │
│  │  • Tier 2: LLM (0.75 confidence) - Detailed               │   │
│  │  • Tier 3: Embeddings (0.60 confidence) - Fallback         │   │
│  └───────────────────────────────────────────────────────────┘   │
│                                          │                       │
│  ┌─────────────────────┐      ┌──────────────────────┐          │
│  │ ResponseOrchestrator│     │ AgentRegistry         │          │
│  │                      │     │ • 13 agents + 5 tools │          │
│  │ • Register agents    │     │ • Dynamic routing    │          │
│  │ • Register tools     │     │ • Fallback handling   │          │
│  │ • Route by intent    │     │                       │          │
│  │ • Format responses   │     │                       │          │
│  └──────────┬───────────┘     └──────────┬───────────┘          │
│             │                          │                       │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │              CitationNormalizer                           │   │
│  │  • Detect citation patterns ([C1], [C2])                 │   │
│  │  • Map to verified sources                               │   │
│  │  • Generate URLs (quran.com, sunnah.com)                 │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                  │
└──────────────────────────────────────┬──────────────────────────┘
                                       │
          ┌────────────────────────────┼────────────────────────┐
          ▼                            ▼                        ▼
┌──────────────────┐  ┌──────────────────────┐  ┌──────────────────┐
│   AGENTS LAYER   │  │    TOOLS LAYER       │  │  QURAN PIPELINE  │
├──────────────────┤  ├──────────────────────┤  ├──────────────────┤
│                  │  │                      │  │                  │
│ • FiqhAgent      │  │ • ZakatCalculator    │  │ • VerseRetrieval │
│   (RAG-based)    │  │   (Deterministic)    │  │   Engine         │
│                  │  │                      │  │                  │
│ • GeneralIslamic │  │ • InheritanceCalc    │  │ • NL2SQL Engine  │
│   Agent (RAG)    │  │   (Fara'id rules)    │  │                  │
│                  │  │                      │  │ • Quotation      │
│ • ChatbotAgent   │  │ • PrayerTimesTool    │  │   Validator      │
│   (Greetings)    │  │   (6 methods)        │  │                  │
│                  │  │                      │  │ • Tafsir         │
│                  │  │ • HijriCalendarTool  │  │   Retrieval      │
│                  │  │   (Umm al-Qura)      │  │                  │
│                  │  │                      │  │ • QuranSubRouter │
│                  │  │ • DuaRetrievalTool   │  │   (4 sub-intents)│
│                  │  │   (Hisn al-Muslim)   │  │                  │
│                  │  │                      │  │                  │
└────────┬─────────┘  └──────────┬───────────┘  └────────┬────────┘
         │                       │                        │
         └───────────────────────┼────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────┐
│                    KNOWLEDGE LAYER                               │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐   │
│  │  PostgreSQL  │  │    Qdrant    │  │       Redis          │   │
│  │   (Port 5432)│  │ (Port 6333)  │  │    (Port 6379)       │   │
│  │              │  │              │  │                      │   │
│  │ • Surahs     │  │ Collections: │  │ • Embedding Cache   │   │
│  │ • Ayahs      │  │ • fiqh       │  │   (7-day TTL)       │   │
│  │ • Translations│ │ • hadith     │  │ • Response Cache    │   │
│  │ • Tafsirs    │  │ • quran      │  │   (1-hour TTL)      │   │
│  │ • Query Logs │  │ • general    │  │ • Session Storage   │   │
│  │              │  │ • duas       │  │                      │   │
│  └──────────────┘  └──────────────┘  └──────────────────────┘   │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │            External Services (Updated)                   │   │
│  │                                                           │   │
│  │  • Groq API (Qwen3-32B) - LLM generation                 │   │
│  │  • Quran.com API v4 - Quran data seeding                 │   │
│  │  • BAAI/bge-m3 - Vector generation (1024-dim, 8192 token)│   │
│  │  • HuggingFace - Dataset storage (42.6 GB)               │   │
│  │                                                           │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 📁 Improved File Structure (Updated: Phase 8)

```
K:\business\projects_v2\Burhan\
│
├── 📜 BUILD & SCRIPTS
│   ├── build.bat                   # Main build system (ALL commands)
│   ├── start.bat                   # Quick start (wrapper)
│   ├── stop.bat                    # Quick stop (wrapper)
│   ├── test.bat                    # Quick test (wrapper)
│   ├── install.bat                 # Quick install (wrapper)
│   ├── menu.bat                    # Interactive menu (wrapper)
│   ├── ingest_data.bat             # Data ingestion (wrapper)
│   ├── process_and_embed.bat       # Embeddings (wrapper)
│   └── scripts/
│       ├── cli.py                  # Python CLI alternative
│       ├── complete_ingestion.py   # Data ingestion pipeline
│       ├── chunk_books.py          # Book chunking utility
│       ├── generate_embeddings.py  # Embedding generation
│       ├── seed_quran_data.py      # Quran database seeder
│       ├── backup_embeddings_and_qdrant.py  # HuggingFace backup
│       └── [other utilities]
│
├── 🐍 BACKEND (Python/FastAPI)
│   └── src/
│       ├── config/                 # Configuration
│       │   ├── settings.py         # Environment settings
│       │   ├── intents.py          # Intent definitions (backward compat)
│       │   ├── constants.py        # Thresholds, config values
│       │   └── logging_config.py   # Logging setup
│       │
│       ├── api/                    # FastAPI application (20 endpoints!)
│       │   ├── main.py             # App factory
│       │   ├── routes/
│       │   │   ├── classification.py  # NEW! /classify endpoint
│       │   │   ├── query.py        # POST /api/v1/query
│       │   │   ├── tools.py        # Tool endpoints (5)
│       │   │   ├── quran.py        # Quran endpoints (6)
│       │   │   ├── rag.py          # RAG endpoints (3)
│       │   │   └── health.py       # Health checks
│       │   ├── middleware/         # Middleware
│       │   └── schemas/            # Pydantic models
│       │
│       ├── application/             # NEW! Application Layer (Phase 8)
│       │   ├── interfaces.py       # IntentClassifier, Router protocols
│       │   ├── models.py           # RoutingDecision
│       │   ├── hybrid_classifier.py # HybridIntentClassifier
│       │   └── router.py           # RouterAgent
│       │
│       ├── domain/                  # NEW! Domain Layer (Phase 8)
│       │   ├── intents.py          # Intent, QuranSubIntent (16+4)
│       │   └── models.py           # ClassificationResult
│       │
│       ├── core/                   # Core logic
│       │   ├── router.py           # Hybrid Intent Classifier (LLM-tier)
│       │   ├── orchestrator.py     # Response Orchestrator
│       │   └── citation.py         # Citation Normalizer
│       │
│       ├── agents/                 # AI agents (13)
│       │   ├── base.py             # Base agent interface
│       │   ├── fiqh_agent.py       # Fiqh RAG Agent
│       │   ├── hadith_agent.py     # Hadith RAG Agent
│       │   ├── general_islamic_agent.py
│       │   ├── chatbot_agent.py
│       │   └── ... (more agents)
│       │
│       ├── tools/                  # Deterministic tools (5)
│       │   ├── base.py             # Base tool interface
│       │   ├── zakat_calculator.py
│       │   ├── inheritance_calculator.py
│       │   ├── prayer_times_tool.py
│       │   ├── hijri_calendar_tool.py
│       │   └── dua_retrieval_tool.py
│       │
│       ├── quran/                  # Quran pipeline
│       │   ├── verse_retrieval.py
│       │   ├── nl2sql.py
│       │   ├── quotation_validator.py
│       │   ├── tafsir_retrieval.py
│       │   ├── quran_router.py     # Quran sub-intent router
│       │   ├── quran_agent.py
│       │   └── named_verses.json
│       │
│       ├── knowledge/              # RAG infrastructure
│       │   ├── embedding_model.py  # BAAI/bge-m3 wrapper (NEW!)
│       │   ├── embedding_cache.py  # Redis cache
│       │   ├── vector_store.py     # Qdrant integration
│       │   ├── hybrid_search.py    # Semantic + BM25
│       │   └── chunker.py
│       │
│       ├── data/                   # Data layer
│       │   ├── models/             # SQLAlchemy models
│       │   └── ingestion/          # Data loaders
│       │
│       └── infrastructure/         # External services
│           ├── db.py               # PostgreSQL
│           ├── redis.py            # Redis
│           └── llm_client.py       # Groq/OpenAI
│
├── 🎨 FRONTEND (Next.js 15)
│   └── frontend/
│       ├── src/
│       │   ├── app/                # App router pages
│       │   ├── components/         # React components
│       │   ├── lib/                # Utilities
│       │   └── hooks/              # Custom hooks
│       ├── i18n/                   # Internationalization
│       └── public/                 # Static assets
│
├── 🗄️ DATA
│   ├── datasets/                   # Source data
│   │   ├── data/
│   │   │   ├── extracted_books/   # 8,424 Islamic books
│   │   │   └── metadata/          # Categories, authors
│   │   └── Sanadset 368K/         # Hadith narrators
│   │
│   └── data/                       # Processed data
│       ├── processed/              # Chunked documents
│       ├── seed/                   # Sample data
│       └── embeddings/             # Vector embeddings
│
├── 🐳 DOCKER
│   └── docker/
│       ├── docker-compose.dev.yml  # Development services
│       ├── Dockerfile.api          # API Docker image
│       └── init-db/                # Database init scripts
│
├── 📚 DOCUMENTATION
│   ├── README.md                   # Main overview
│   ├── START_HERE.md               # Entry point
│   ├── QUICK_REFERENCE.md          # Command cheat sheet
│   ├── WINDOWS_GUIDE.md            # Windows-specific guide
│   ├── SETUP_COMPLETE.md           # Setup instructions
│   └── docs/
│       ├── ARCHITECTURE.md         # Technical architecture
│       ├── API.md                  # API reference
│       ├── DEPLOYMENT.md           # Deployment guide
│       ├── DEVELOPMENT.md          # Developer guide
│       ├── FRONTEND.md             # Frontend guide
│       ├── RAG_GUIDE.md            # RAG pipeline
│       └── QURAN_GUIDE.md          # Quran pipeline
│
├── 🧪 TESTS
│   └── tests/
│       ├── conftest.py
│       ├── test_router.py
│       ├── test_api.py
│       ├── test_zakat_calculator.py
│       ├── test_inheritance_calculator.py
│       ├── test_prayer_times_tool.py
│       ├── test_hijri_calendar_tool.py
│       └── test_dua_retrieval_tool.py
│
├── ⚙️ CONFIGURATION
│   ├── pyproject.toml              # Python dependencies
│   ├── .env.example                # Environment template
│   ├── Makefile                    # Unix build commands
│   └── migrations/                 # Database migrations
│
└── 🗑️ GITIGNORED
    ├── .venv/                      # Python virtual env
    ├── __pycache__/                # Python cache
    ├── .env                        # Environment variables
    └── node_modules/               # Frontend dependencies
```

---

## 🎯 Build System Commands

### Core Commands
```bash
build.bat setup           # Full initial setup
build.bat start           # Start application
build.bat stop            # Stop all services
build.bat test            # Run tests
build.bat status          # Check status
build.bat menu            # Interactive menu
```

### Data Commands
```bash
build.bat data:ingest     # Process books/hadith
build.bat data:embed      # Generate embeddings
build.bat data:quran      # Seed Quran database
build.bat data:status     # View statistics
```

### Database Commands
```bash
build.bat db:migrate      # Run migrations
build.bat db:shell        # PostgreSQL shell
build.bat db:backup       # Backup database
```

### Maintenance Commands
```bash
build.bat clean           # Clean artifacts
build.bat reset           # Full reset
build.bat logs [service]  # View logs
build.bat docker:prune    # Clean Docker
build.bat help            # Show help
```

---

## 📊 Data Flow Diagram

```
User Question
    │
    ▼
┌─────────────────┐
│  API Endpoint   │  POST /api/v1/query
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Query Classifier│  3-tier classification
│                 │  1. Keywords (fast)
│                 │  2. LLM (primary)
│                 │  3. Embeddings (fallback)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Orchestrator    │  Route to agent/tool
└────────┬────────┘
         │
    ┌────┴────┬───────────┬──────────┐
    ▼         ▼           ▼          ▼
┌──────┐ ┌───────┐ ┌────────┐ ┌───────┐
│Fiqh  │ │Quran  │ │ Zakat  │ │Prayer │
│Agent │ │Agent  │ │ Calc   │ │Times  │
└──┬───┘ └───┬───┘ └───┬────┘ └───┬───┘
   │         │         │          │
   ▼         ▼         ▼          ▼
┌─────────────────────────────────────┐
│         Knowledge Layer             │
│  PostgreSQL • Qdrant • Redis        │
└─────────────────┬───────────────────┘
                  │
                  ▼
┌─────────────────────────────────────┐
│      Citation Normalizer            │
│  [C1], [C2] → Verified Sources      │
└─────────────────┬───────────────────┘
                  │
                  ▼
┌─────────────────────────────────────┐
│        Response Assembly            │
│  Answer + Citations + Metadata      │
└─────────────────┬───────────────────┘
                  │
                  ▼
             User Response
```

---

## 🔐 Security Layers

```
┌─────────────────────────────────────────┐
│  Layer 1: Input Validation              │
│  • Pydantic models                      │
│  • Type checking                        │
│  • Sanitization                         │
└─────────────────┬───────────────────────┘
                  │
┌─────────────────▼───────────────────────┐
│  Layer 2: CORS & Middleware             │
│  • Allowed origins                      │
│  • Error handling                       │
│  • Request logging                      │
└─────────────────┬───────────────────────┘
                  │
┌─────────────────▼───────────────────────┐
│  Layer 3: Database Security             │
│  • Parameterized queries                │
│  • SQL injection prevention             │
│  • Connection pooling                   │
└─────────────────┬───────────────────────┘
                  │
┌─────────────────▼───────────────────────┐
│  Layer 4: RAG Grounding                 │
│  • Verified sources only                │
│  • Citation tracking                    │
│  • No hallucination                     │
└─────────────────────────────────────────┘
```

---

**This architecture is production-ready and based on the Fanar-Sadiq research paper.** 🕌✨
