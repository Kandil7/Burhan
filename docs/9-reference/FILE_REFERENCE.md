# Burhan Project - Complete File Reference

**Last Updated:** April 7, 2026

---

## 📁 Complete File Tree

```
K:\business\projects_v2\Burhan\
│
├── README.md                                    # Project overview (main)
├── QWEN.md                                      # AI assistant context
├── STATUS.md                                    # Current project status
├── Makefile                                     # Build commands (25 targets)
├── pyproject.toml                               # Python dependencies (Poetry)
├── poetry.lock                                  # Locked dependencies
├── .python-version                              # Python version (3.12)
├── .env.example                                 # Environment template (37 vars)
├── .gitignore                                   # Git ignore rules
├── .dockerignore                                # Docker ignore rules
├── STOP.bat                                     # Emergency stop script
├── build.bat                                    # Build script
├── kill_port_8000.ps1                           # Port killer
│
├── src/                                         # Python backend (FastAPI)
│   ├── __init__.py
│   │
│   ├── config/                                  # Configuration
│   │   ├── __init__.py
│   │   ├── settings.py                          # Environment settings
│   │   ├── intents.py                           # 16 intent definitions + keywords
│   │   ├── constants.py                         # Retrieval config
│   │   └── logging_config.py                    # Structured logging
│   │
│   ├── api/                                     # FastAPI application
│   │   ├── __init__.py
│   │   ├── main.py                              # App factory
│   │   ├── routes/                              # API routes
│   │   │   ├── __init__.py
│   │   │   ├── query.py                         # POST /api/v1/query
│   │   │   ├── health.py                        # GET /health, /ready
│   │   │   ├── tools.py                         # 5 tool endpoints
│   │   │   ├── quran.py                         # 6 Quran endpoints
│   │   │   └── rag.py                           # 3 RAG endpoints
│   │   ├── middleware/                          # Error handler, CORS
│   │   └── schemas/                             # Pydantic models
│   │
│   ├── core/                                    # Core logic
│   │   ├── __init__.py
│   │   ├── router.py                            # Hybrid Intent Classifier (3-tier)
│   │   ├── orchestrator.py                      # Response Orchestrator
│   │   ├── citation.py                          # Citation Normalizer
│   │   └── registry.py                          # Agent Registry
│   │
│   ├── agents/                                  # 13 agent implementations
│   │   ├── __init__.py
│   │   ├── base.py                              # BaseAgent, AgentInput, AgentOutput
│   │   ├── fiqh_agent.py                        # Fiqh RAG Agent
│   │   ├── hadith_agent.py                      # Hadith RAG Agent
│   │   ├── sanadset_hadith_agent.py             # Sanadset 650K Hadith Agent
│   │   ├── tafsir_agent.py                      # Quran Tafsir Agent
│   │   ├── aqeedah_agent.py                     # Islamic Creed Agent
│   │   ├── seerah_agent.py                      # Prophet Biography Agent
│   │   ├── islamic_history_agent.py             # Islamic History Agent
│   │   ├── fiqh_usul_agent.py                   # Jurisprudence Principles Agent
│   │   ├── arabic_language_agent.py             # Arabic Language Agent
│   │   ├── general_islamic_agent.py             # General Knowledge Agent
│   │   └── chatbot_agent.py                     # Greeting/Small Talk Agent
│   │
│   ├── tools/                                   # 5 deterministic tools
│   │   ├── __init__.py
│   │   ├── base.py                              # BaseTool, ToolInput, ToolOutput
│   │   ├── utils/                               # Tool utilities
│   │   ├── zakat_calculator.py                  # Zakat (wealth, gold, silver, trade)
│   │   ├── inheritance_calculator.py            # Inheritance (fara'id rules)
│   │   ├── prayer_times_tool.py                 # Prayer times (6 methods) + Qibla
│   │   ├── hijri_calendar_tool.py               # Hijri dates (Umm al-Qura)
│   │   └── dua_retrieval_tool.py                # Hisn al-Muslim + Azkar
│   │
│   ├── quran/                                   # Quran pipeline
│   │   ├── __init__.py
│   │   ├── verse_retrieval.py                   # Verse lookup (exact + fuzzy)
│   │   ├── nl2sql.py                            # Natural language → SQL
│   │   ├── quotation_validator.py               # Verify Quran quotes
│   │   ├── tafsir_retrieval.py                  # Tafsir lookup
│   │   ├── quran_router.py                      # Sub-intent classification
│   │   ├── quran_agent.py                       # Complete Quran agent
│   │   └── named_verses.json                    # 14 named verses
│   │
│   ├── knowledge/                               # RAG infrastructure
│   │   ├── __init__.py
│   │   ├── embedding_model.py                   # Qwen3-Embedding-0.6B wrapper
│   │   ├── embedding_cache.py                   # Redis/local dict caching
│   │   ├── vector_store.py                      # Qdrant (10 collections)
│   │   ├── hybrid_search.py                     # Semantic + BM25 search
│   │   ├── chunker.py                           # Document chunking
│   │   └── hierarchical_chunker.py              # 4-level hierarchical chunking
│   │
│   ├── data/                                    # Data ingestion
│   │   ├── models/                              # SQLAlchemy models
│   │   │   └── quran.py                         # Surah, Ayah, Translation, Tafsir
│   │   └── ingestion/                           # Data loaders
│   │       ├── quran_loader.py                  # Quran.com API loader
│   │       └── hadith_loader.py                 # Hadith collection loader
│   │
│   └── infrastructure/                          # External services
│       ├── __init__.py
│       ├── db.py                                # PostgreSQL (asyncpg)
│       ├── redis.py                             # Redis connection
│       └── llm_client.py                        # LLM provider (Groq/OpenAI)
│
├── data/                                        # Data files
│   ├── mini_dataset/                            # GitHub-friendly (1.7 MB, 1,623 docs)
│   │   ├── fiqh_passages.jsonl
│   │   ├── hadith_passages.jsonl
│   │   ├── general_islamic.jsonl
│   │   ├── aqeedah_passages.jsonl
│   │   ├── spirituality_passages.jsonl
│   │   ├── seerah_passages.jsonl
│   │   ├── islamic_history_passages.jsonl
│   │   ├── arabic_language_passages.jsonl
│   │   ├── book_selections.json
│   │   ├── collection_stats.json
│   │   └── README.md
│   │
│   ├── processed/                               # Extracted/chunked data
│   │   ├── master_catalog.json                  # 8,465 books with metadata
│   │   ├── category_mapping.json                # 41→10 collection mapping
│   │   ├── author_catalog.json                  # 3,146 authors
│   │   ├── lucene_esnad.json                    # Hadith chains (extracted)
│   │   ├── lucene_author.json                   # Author bios (extracted)
│   │   ├── lucene_book.json                     # Book index (extracted)
│   │   ├── chunking_stats.json                  # Chunking statistics
│   │   └── category_mapping.json                # Book→category mapping
│   │
│   ├── seed/                                    # Seed data
│   │   ├── duas.json                            # Hisn al-Muslim duas
│   │   └── quran_sample.json                    # Quran sample data
│   │
│   └── raw/                                     # Raw source data
│
├── datasets/                                    # Full datasets (excluded from Git)
│   ├── system_book_datasets/                    # Shamela databases (14.4 GB)
│   │   ├── master.db                            # Complete book catalog (50 MB)
│   │   ├── cover.db                             # Book covers (30 MB, 1,004 covers)
│   │   ├── book/                                # 8,427 book databases (671.8 MB)
│   │   │   ├── 000/                             # Category 000
│   │   │   ├── 001/                             # Category 001
│   │   │   └── ... 999/                         # Category 999
│   │   ├── service/                             # Service databases (148 MB)
│   │   │   ├── hadeeth.db                       # 37K hadith cross-refs
│   │   │   ├── tafseer.db                       # 65K tafsir mappings
│   │   │   ├── S1.db                            # Metadata/links
│   │   │   ├── S2.db                            # 3.2M morphological roots
│   │   │   └── trajim.db                        # Biographical entries
│   │   ├── store/                               # Lucene indexes (13.7 GB)
│   │   │   ├── page/                            # Full Arabic text (13.2 GB)
│   │   │   ├── title/                           # Section titles (56 MB, 3.9M docs)
│   │   │   ├── esnad/                           # Hadith chains (0.5 GB, 35K docs)
│   │   │   ├── author/                          # Author bios (1.9 MB)
│   │   │   ├── book/                            # Book index
│   │   │   ├── aya/                             # Quran verses
│   │   │   ├── s_author/                        # Search author
│   │   │   └── s_book/                          # Search book
│   │   ├── update/                              # Update tracking
│   │   └── user/                                # User preferences
│   │       └── data.db                          # 15 user tables
│   │
│   ├── data/                                    # Extracted books
│   │   ├── extracted_books/                     # 8,425 books (16.4 GB, TXT)
│   │   └── metadata/                            # Book metadata (11 MB)
│   │       ├── books.db                         # SQLite book database
│   │       ├── books.json                       # Book list (5.9 MB)
│   │       ├── authors.json                     # Author list (588 KB)
│   │       ├── categories.json                  # Categories (5 KB)
│   │       └── guid_index.json                  # GUID index (1.5 MB)
│   │
│   └── Sanadset*/                               # 650,986 hadith (1.43 GB)
│       └── sanadset.csv                         # Hadith with sanad/matan
│
├── scripts/                                     # 40+ utility scripts
│   ├── README.md                                # Scripts documentation
│   ├── utils.py                                 # Shared utilities
│   │
│   ├── DATA EXTRACTION:
│   ├── extract_master_catalog.py                # Extract master.db (5 min)
│   ├── extract_all_lucene_pipeline.py           # Full Lucene extraction (3-5 hrs)
│   ├── extract_all_lucene.bat                   # Windows batch version
│   ├── LuceneExtractor.java                     # Java Lucene extractor
│   ├── simple_lucene_extract.py                 # Simple Lucene test
│   │
│   ├── DATA PROCESSING:
│   ├── prepare_datasets_for_upload.py           # v1: Raw book preparation
│   ├── prepare_datasets_for_upload_v2.py        # v2: Hierarchical chunks
│   ├── create_mini_dataset.py                   # Mini-dataset creator
│   ├── create_category_mapping.py               # 41→11 category mapping
│   ├── chunk_all_books.py                       # Batch book chunking
│   ├── seed_mvp_data.py                         # MVP data seeder
│   ├── seed_quran_data.py                       # Quran data seeder
│   ├── seed_rag_quick.py                        # Quick RAG seeding
│   ├── generate_embeddings.py                   # Batch embedding generator
│   ├── embed_sanadset_hadith.py                 # Hadith embedding pipeline
│   ├── embed_all_collections.py                 # All collections embedding
│   ├── import_azkar_db.py                       # Azkar-DB importer
│   ├── inspect_db.py                            # Database inspector
│   ├── ingest_extracted_books.py                # Book ingestion
│   ├── complete_ingestion.py                    # Complete ingestion pipeline
│   │
│   ├── ANALYSIS:
│   ├── analyze_dataset.py                       # Dataset analysis
│   ├── analyze_db.py                            # Database analysis
│   ├── analyze_sanadset.py                      # Sanadset analysis
│   ├── analyze_shamela_dbs.py                   # Shamela DB analysis
│   ├── analyze_system_db.py                     # System DB analysis
│   ├── analyze_system_db2.py                    # System DB analysis v2
│   ├── check_quran_db.py                        # Quran DB checker
│   │
│   ├── TESTING:
│   ├── test_all_endpoints_detailed.py           # Detailed endpoint tests
│   ├── test_all_endpoints.py                    # All endpoint tests
│   ├── test_all_endpoints.ps1                   # PowerShell version
│   ├── test_api.py                              # API smoke test
│   ├── test_router.py                           # Router tests
│   ├── test_orchestrator.py                     # Orchestrator tests
│   ├── test_camel_tools.py                      # Camel tools test
│   ├── test_llm.py                              # LLM test
│   ├── test_full_pipeline.py                    # Full pipeline test
│   ├── test_query_route.py                      # Query route test
│   ├── test_sanadset_agent.py                   # Sanadset agent test
│   ├── comprehensive_test.py                    # Comprehensive test suite
│   ├── quick_test.py                            # Quick smoke test
│   │
│   ├── UTILITIES:
│   ├── cli.py                                   # CLI entry point
│   ├── check_datasets.py                        # Dataset integrity checker
│   └── chunk_books.py                           # Book chunking utility
│
├── notebooks/                                   # Google Colab notebooks
│   ├── README.md                                # Notebook documentation
│   ├── google_drive_setup.md                    # Google Drive guide
│   ├── setup_colab_env.ipynb                    # Environment setup
│   ├── 01_embed_all_collections.ipynb           # Embed all collections
│   ├── 04_upload_to_huggingface.ipynb           # Upload to HF
│   └── 05_upload_to_kaggle.ipynb                # Upload to Kaggle
│
├── tests/                                       # Test suite
│   ├── __init__.py
│   ├── conftest.py                              # Pytest fixtures
│   ├── test_router.py                           # Intent classifier tests
│   ├── test_api.py                              # API endpoint tests
│   ├── test_zakat_calculator.py                 # Zakat calculator tests
│   ├── test_inheritance_calculator.py           # Inheritance tests
│   ├── test_dua_retrieval_tool.py               # Dua tool tests
│   ├── test_hijri_calendar_tool.py              # Hijri tool tests
│   └── test_prayer_times_tool.py                # Prayer times tests
│
├── docker/                                      # Docker configuration
│   ├── docker-compose.dev.yml                   # Development services
│   ├── Dockerfile.api                           # API Docker image
│   └── init-db/                                 # DB initialization scripts
│
├── migrations/                                  # Database migrations
│   └── 001_initial_schema.sql                   # Quran tables
│
├── docs/                                        # Documentation (14 directories)
│   ├── README.md                                # Docs overview
│   ├── COMPLETE_DOCUMENTATION.md                # Complete system docs
│   ├── analysis/                                # Data analysis reports
│   ├── api/                                     # API documentation
│   ├── architecture/                            # Architecture diagrams
│   ├── core-features/                           # Feature documentation
│   ├── data/                                    # Data documentation
│   ├── datasets/                                # Dataset guides
│   │   ├── huggingface_setup.md                 # HF upload guide
│   ├── deployment/                              # Deployment guides
│   ├── development/                             # Development guides
│   ├── getting-started/                         # Getting started guides
│   ├── guides/                                  # How-to guides
│   ├── improvements/                            # Improvement proposals
│   ├── planning/                                # Project planning
│   ├── reference/                               # Reference materials
│   ├── reports/                                 # Project reports
│   └── status/                                  # Status updates
│
├── lib/                                         # External libraries
│   └── lucene/                                  # Lucene JAR files
│       ├── lucene-core-9.12.0.jar
│       ├── lucene-core-10.0.0.jar
│       ├── lucene-queryparser-9.12.0.jar
│       ├── lucene-backward-codecs-9.12.0.jar
│       └── lucene-backward-codecs-10.0.0.jar
│
├── output/                                      # Output files
│   └── lucene_*.json                            # Extracted Lucene data
│
├── _hello.txt                                   # Test file
├── .code-review-graphignore                     # Code review ignore rules
└── .github/                                     # GitHub configuration
    └── workflows/                               # GitHub Actions
```

---

## 📊 File Statistics

| Category | Count | Total Size |
|----------|-------|------------|
| **Python Scripts** | 85+ files | ~14,200 lines |
| **Java Files** | 1 file | ~70 lines |
| **Notebooks** | 5 files | ~300 cells |
| **Tests** | 8 files | ~900 lines |
| **Documentation** | 20+ files | ~5,000 lines |
| **Data Files** | 100+ files | ~17 GB |
| **Config Files** | 10 files | ~500 lines |

---

## 🎯 Key Files by Purpose

### Getting Started
1. `README.md` - Start here
2. `.env.example` - Configuration
3. `Makefile` - Commands

### Core System
1. `src/api/main.py` - App entry
2. `src/core/router.py` - Intent classifier
3. `src/core/orchestrator.py` - Response router
4. `src/core/registry.py` - Agent registry

### Data Pipeline
1. `scripts/extract_master_catalog.py` - Extract metadata
2. `scripts/extract_all_lucene_pipeline.py` - Extract content
3. `scripts/chunk_all_books.py` - Build chunks
4. `notebooks/01_embed_all_collections.ipynb` - Embed

### Testing
1. `scripts/quick_test.py` - Quick smoke test
2. `scripts/test_all_endpoints_detailed.py` - Full test
3. `tests/` - Unit tests

---

*Last updated: April 7, 2026*
