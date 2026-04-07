# Athar Scripts

Automation scripts for managing the Athar Islamic QA System.

---

## Directory Structure

```
scripts/
├── analysis/                 # Diagnostic & analysis scripts
│   ├── analyze_dataset.py   # Dataset analysis
│   ├── analyze_db.py        # Database analysis
│   ├── analyze_sanadset.py  # SanadSet analysis
│   ├── analyze_sanadset2.py # SanadSet analysis v2
│   ├── analyze_shamela_dbs.py # Shamela DB analysis
│   ├── analyze_system_db.py   # System DB analysis
│   ├── analyze_system_db2.py  # System DB analysis v2
│   ├── check_quran_db.py    # Quran DB checker
│   └── inspect_db.py       # Database inspector
│
├── data/                    # Data seeding & generation
│   ├── create_mini_dataset.py    # Create mini dataset
│   ├── embed_all_collections.py # Embed all collections
│   ├── embed_sanadset_hadith.py # Embed SanadSet hadith
│   ├── generate_embeddings.py  # Generate embeddings
│   ├── seed_mvp_data.py         # Seed MVP data
│   ├── seed_quran_data.py       # Seed Quran data
│   └── seed_rag_quick.py        # Quick RAG seeding
│
├── ingestion/               # Data ingestion pipelines
│   ├── chunk_books.py       # Book chunking utility
│   ├── complete_ingestion.py # Complete ingestion
│   ├── import_azkar_db.py   # Azkar-DB importer
│   ├── ingest_and_run.py    # Ingest and run
│   └── ingest_extracted_books.py # Ingest extracted books
│
├── tests/                   # Test scripts
│   ├── comprehensive_test.py    # Comprehensive tests
│   ├── test_all_endpoints.py    # Test all endpoints
│   ├── test_all_endpoints_detailed.py # Detailed endpoint tests
│   ├── test_all_endpoints.ps1   # PowerShell endpoint tests
│   ├── test_api.py          # API tests
│   ├── test_camel_tools.py  # Camel tools tests
│   ├── test_full_pipeline.py # Full pipeline tests
│   ├── test_llm.py          # LLM tests
│   ├── test_orchestrator.py # Orchestrator tests
│   ├── test_query_route.py  # Query route tests
│   └── test_sanadset_agent.py # SanadSet agent tests
│
├── windows/                 # Windows batch scripts
│   ├── start.bat            # Start application
│   ├── stop.bat             # Stop services
│   ├── test.bat             # Test API
│   ├── install.bat          # Install dependencies
│   ├── menu.bat             # Interactive menu
│   ├── ingest_data.bat      # Process data
│   └── process_and_embed.bat # Generate embeddings
│
├── cli.py                   # Python CLI interface
└── README.md               # This file
```

---

## Quick Usage

### Windows Users
```
Double-click: scripts\windows\menu.bat
Or use: build.bat (in project root)
```

### Command Line
```bash
python scripts/cli.py start
python scripts/cli.py test
python scripts/cli.py help
```

### Build System
```bash
build.bat start
build.bat test
build.bat help
```

---

## Documentation

- **Quick Reference:** `docs/guides/02_QUICK_REFERENCE.md`
- **Architecture:** `docs/architecture/01_ARCHITECTURE_OVERVIEW.md`
- **Windows Guide:** `docs/guides/windows.md`
- **Setup Guide:** `docs/guides/setup.md`

---

*Last Updated: April 2026*
