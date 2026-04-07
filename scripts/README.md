# Athar Scripts

Automation scripts for managing the Athar Islamic QA System.

---

## Directory Structure

```
scripts/
├── analysis/                  # Diagnostic & analysis scripts
│   ├── analyze_dataset.py     # Complete dataset analysis
│   ├── analyze_db.py          # Database analysis
│   ├── analyze_sanadset.py    # SanadSet analysis
│   ├── analyze_sanadset2.py   # SanadSet analysis v2
│   ├── analyze_shamela_dbs.py # Shamela DB analysis
│   ├── analyze_system_db.py   # System DB analysis
│   ├── analyze_system_db2.py  # System DB analysis v2
│   ├── analyze_system_databases.py # System databases
│   ├── analyze_system_content.py # System content analysis
│   ├── analyze_page_content.py # Page content analysis
│   ├── analyze_deep_content.py # Deep content analysis
│   ├── analyze_content2.py    # Content analysis v2
│   ├── analyze_chunk_quality.py # Chunk quality analysis
│   ├── analyze_books_metadata.py # Books metadata analysis
│   ├── analyze_lucene.py      # Lucene index analysis
│   ├── check_quran_db.py      # Quran DB checker
│   ├── check_datasets.py      # Dataset integrity checker
│   └── inspect_db.py          # Database inspector
│
├── data/                      # Data seeding & generation
│   ├── create_mini_dataset.py # Create GitHub-friendly mini-dataset
│   ├── embed_all_collections.py # Production embedding pipeline
│   ├── embed_sanadset_hadith.py # SanadSet hadith embedding
│   ├── generate_embeddings.py   # Batch embedding generator
│   ├── seed_mvp_data.py         # Seed MVP data
│   ├── seed_quran_data.py       # Seed Quran data
│   ├── seed_rag_quick.py        # Quick RAG seeding
│   ├── create_category_mapping.py # Category mapping creator
│   ├── prepare_datasets_for_upload.py # Dataset uploader
│   ├── prepare_datasets_for_upload_v2.py # Dataset uploader v2
│   ├── extract_master_catalog.py # Master catalog extractor
│   └── find_text_content.py    # Text content finder
│
├── ingestion/                 # Data ingestion pipelines
│   ├── chunk_books.py         # Book chunking utility
│   ├── complete_ingestion.py  # Complete ingestion pipeline
│   ├── import_azkar_db.py     # Azkar-DB importer
│   ├── ingest_and_run.py      # Ingest and run full pipeline
│   ├── ingest_extracted_books.py # Ingest extracted books
│   ├── chunk_all_books.py     # Chunk all books
│   ├── extract_lucene_index.py # Extract Lucene index
│   └── extract_lucene_content.py # Extract Lucene content
│
├── tests/                     # Test scripts
│   ├── comprehensive_test.py      # Comprehensive validation suite
│   ├── test_all_endpoints.py      # Test all endpoints
│   ├── test_all_endpoints_detailed.py # Detailed endpoint tests
│   ├── test_all_endpoints.ps1   # PowerShell endpoint tests
│   ├── test_api.py          # Quick API smoke test
│   ├── test_camel_tools.py  # Camel tools tests
│   ├── test_full_pipeline.py # Full pipeline tests
│   ├── test_llm.py          # LLM tests
│   ├── test_orchestrator.py # Orchestrator tests
│   ├── test_query_route.py  # Query route tests
│   └── test_sanadset_agent.py # SanadSet agent tests
│
├── utils/                     # Shared utilities
│   └── utils.py              # Common helpers (paths, logging, progress)
│
├── lucene/                    # Lucene utilities
│   ├── LuceneExtractor.java  # Lucene index extractor
│   ├── LuceneExtractor.class # Compiled extractor
│   ├── read_lucene.java      # Lucene index reader
│   └── read_lucene.class     # Compiled reader
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
├── cli.py                     # Python CLI interface
├── quick_test.py              # Quick smoke test
└── README.md                 # This file
```

---

## Quick Start

### Dataset Management

```bash
# Check dataset integrity
python scripts/analysis/check_datasets.py

# Analyze datasets
python scripts/analysis/analyze_dataset.py --report

# Create mini-dataset for MVP
python scripts/data/create_mini_dataset.py
```

### Data Ingestion & Embedding

```bash
# Ingest books and hadith
python scripts/ingestion/complete_ingestion.py --books 100 --hadith 1000

# Generate embeddings (with checkpointing)
python scripts/data/generate_embeddings.py --collection all

# Embed SanadSet hadith (with resume support)
python scripts/data/embed_sanadset_hadith.py --limit 1000

# Seed MVP data
python scripts/data/seed_mvp_data.py
```

### Testing

```bash
# Quick smoke test
python scripts/quick_test.py

# Comprehensive endpoint tests
python scripts/tests/test_all_endpoints_detailed.py

# Full validation suite
python scripts/tests/comprehensive_test.py
```

### CLI Interface

```bash
python scripts/cli.py help
python scripts/cli.py start
python scripts/cli.py stop
python scripts/cli.py test
python scripts/cli.py status
python scripts/cli.py ingest --books 100 --hadith 1000
python scripts/cli.py embed --limit 5000
python scripts/cli.py check
python scripts/cli.py quick-test
```

---

## Script Features

### Shared Utilities (`utils/utils.py`)

```python
from scripts.utils import (
    get_project_root,      # Project root path
    get_data_dir,          # Data directory path
    get_datasets_dir,      # Datasets directory path
    setup_script_logger,   # Consistent logging setup
    ProgressBar,           # Progress bar wrapper
    format_size,           # Human-readable file sizes
    format_duration,       # Human-readable durations
)
```

### Key Script Features

| Script | Features |
|--------|----------|
| `create_mini_dataset.py` | Flexible book matching, progress bars, balanced sampling |
| `seed_mvp_data.py` | Redis cache bypass, per-collection builders |
| `generate_embeddings.py` | Category routing, batch processing, error recovery |
| `embed_sanadset_hadith.py` | Checkpointing, resume support, atomic writes |
| `test_all_endpoints_detailed.py` | Response validation, colored output |
| `analyze_dataset.py` | Super-category grouping, chunking recommendations |
| `check_datasets.py` | File validation, JSON/CSV integrity |
| `quick_test.py` | Fast smoke test, all endpoints, exit codes |
| `cli.py` | All-in-one management |

---

## Conventions

### Logging

All scripts use consistent logging format:

```
2026-04-07 10:30:00 [INFO] script-name: message
```

### Progress Bars

Progress bars use tqdm with consistent format:

```
Embedding fiqh_passages: 100/100 [01:23<00:00, 1.20 batch/s]
```

### Error Handling

- All scripts handle `KeyboardInterrupt` gracefully
- Errors are logged with context
- Exit codes: 0 = success, 1 = failure

---

## Documentation

- **Quick Reference:** `docs/guides/02_QUICK_REFERENCE.md`
- **Architecture:** `docs/architecture/01_ARCHITECTURE_OVERVIEW.md`
- **Windows Guide:** `docs/guides/windows.md`
- **Setup Guide:** `docs/guides/setup.md`

---

*Last Updated: April 2026*
