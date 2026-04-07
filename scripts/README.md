# Athar Scripts

Automation scripts for managing the Athar Islamic QA System.

---

## Directory Structure

```
scripts/
├── utils.py                   # Shared utilities (paths, logging, progress bars)
├── check_datasets.py          # Dataset integrity checker
├── quick_test.py              # Quick smoke test for all endpoints
├── cli.py                     # Python CLI interface
│
├── analysis/                  # Diagnostic & analysis scripts
│   ├── analyze_dataset.py     # Complete dataset analysis with recommendations
│   ├── analyze_db.py          # Database analysis
│   ├── analyze_sanadset.py    # SanadSet analysis
│   ├── analyze_sanadset2.py   # SanadSet analysis v2
│   ├── analyze_shamela_dbs.py # Shamela DB analysis
│   ├── analyze_system_db.py   # System DB analysis
│   ├── analyze_system_db2.py  # System DB analysis v2
│   ├── check_quran_db.py      # Quran DB checker
│   └── inspect_db.py          # Database inspector with schema display
│
├── data/                      # Data seeding & generation
│   ├── create_mini_dataset.py # Create GitHub-friendly mini-dataset
│   ├── embed_all_collections.py # Production embedding pipeline with checkpointing
│   ├── embed_sanadset_hadith.py # SanadSet hadith embedding with resume support
│   ├── generate_embeddings.py   # Batch embedding generator
│   ├── seed_mvp_data.py         # Seed MVP data for all collections
│   ├── seed_quran_data.py       # Seed Quran data
│   └── seed_rag_quick.py        # Quick RAG seeding
│
├── ingestion/                 # Data ingestion pipelines
│   ├── chunk_books.py         # Book chunking utility
│   ├── complete_ingestion.py  # Complete ingestion pipeline
│   ├── import_azkar_db.py     # Azkar-DB importer
│   ├── ingest_and_run.py      # Ingest and run full pipeline
│   └── ingest_extracted_books.py # Ingest extracted books
│
├── tests/                     # Test scripts
│   ├── comprehensive_test.py      # Comprehensive validation suite
│   ├── test_all_endpoints.py      # Test all endpoints
│   ├── test_all_endpoints_detailed.py # Detailed endpoint tests with checks
│   ├── test_all_endpoints.ps1   # PowerShell endpoint tests
│   ├── test_api.py          # Quick API smoke test
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
└── README.md               # This file
```

---

## Quick Start

### Dataset Management

```bash
# Check dataset integrity
python scripts/check_datasets.py

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
python scripts/data/generate_embeddings.py --collection fiqh_passages --limit 1000

# Embed SanadSet hadith (with resume support)
python scripts/data/embed_sanadset_hadith.py --limit 1000
python scripts/data/embed_sanadset_hadith.py --no-resume  # Start fresh

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

# Test specific agent
python scripts/tests/test_sanadset_agent.py
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
python scripts/cli.py check        # Dataset integrity
python scripts/cli.py quick-test   # Smoke test
python scripts/cli.py db migrate
python scripts/cli.py db shell
```

---

## Script Features

### Shared Utilities (`utils.py`)

All scripts use common utilities for consistency:

```python
from scripts.utils import (
    get_project_root,      # Project root path
    get_data_dir,          # Data directory path
    get_datasets_dir,      # Datasets directory path
    setup_script_logger,   # Consistent logging setup
    ProgressBar,           # Progress bar wrapper
    format_size,           # Human-readable file sizes
    format_duration,       # Human-readable durations
    add_project_root_to_path,  # Add src to sys.path
)
```

### Key Script Features

| Script | Features |
|--------|----------|
| `create_mini_dataset.py` | Flexible book matching, progress bars, balanced sampling |
| `seed_mvp_data.py` | Redis cache bypass, per-collection builders, progress tracking |
| `generate_embeddings.py` | Category routing, batch processing, error recovery |
| `embed_sanadset_hadith.py` | Checkpointing, resume support, atomic writes |
| `test_all_endpoints_detailed.py` | Response validation, colored output, configurable port |
| `test_sanadset_agent.py` | Agent initialization checks, multi-query testing |
| `analyze_dataset.py` | Super-category grouping, chunking recommendations |
| `check_datasets.py` | File validation, JSON/CSV integrity, detailed reports |
| `quick_test.py` | Fast smoke test, all endpoints, exit codes |
| `cli.py` | All-in-one management, dataset checks, quick tests |

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
- Errors are logged with context (exc_info=True)
- Exit codes: 0 = success, 1 = failure

### Path Handling

All paths use `pathlib.Path` with `scripts.utils` helpers:

```python
from scripts.utils import get_data_dir, get_datasets_dir

data_dir = get_data_dir("processed")      # -> project/data/processed
datasets_dir = get_datasets_dir("data")   # -> project/datasets/data
```

---

## Documentation

- **Quick Reference:** `docs/guides/02_QUICK_REFERENCE.md`
- **Architecture:** `docs/architecture/01_ARCHITECTURE_OVERVIEW.md`
- **Windows Guide:** `docs/guides/windows.md`
- **Setup Guide:** `docs/guides/setup.md`

---

*Last Updated: April 2026*
