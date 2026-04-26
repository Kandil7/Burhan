# Burhan Scripts

Automation scripts for managing the Burhan Islamic QA System.

---

## Directory Structure

```
scripts/
├── analysis/                  # Diagnostic & analysis scripts (23 files)
│   ├── analyze_dataset.py      # Complete dataset analysis
│   ├── analyze_db.py           # Database analysis
│   ├── analyze_sanadset.py     # SanadSet analysis
│   ├── analyze_sanadset2.py    # SanadSet analysis v2
│   ├── analyze_shamela_dbs.py  # Shamela DB analysis
│   ├── analyze_system_db.py    # System DB analysis
│   ├── analyze_system_db2.py   # System DB analysis v2
│   ├── analyze_system_databases.py # System databases
│   ├── analyze_system_content.py  # System content analysis
│   ├── analyze_page_content.py    # Page content analysis
│   ├── analyze_deep_content.py   # Deep content analysis
│   ├── analyze_content2.py       # Content analysis v2
│   ├── analyze_chunk_quality.py  # Chunk quality analysis
│   ├── analyze_books_metadata.py # Books metadata analysis
│   ├── analyze_lucene.py        # Lucene index analysis
│   ├── check_quran_db.py        # Quran DB checker
│   ├── check_datasets.py        # Dataset integrity checker
│   ├── inspect_db.py            # Database inspector
│   ├── analyze_system_content.py
│   └── ... (more analysis scripts)
│
├── data/                       # Data seeding & generation
│   ├── create_mini_dataset.py  # Create GitHub-friendly mini-dataset
│   ├── embed_all_collections.py # Production embedding pipeline
│   ├── embed_sanadset_hadith.py  # SanadSet hadith embedding
│   ├── generate_embeddings.py    # Batch embedding generator
│   ├── seed_mvp_data.py          # Seed MVP data
│   ├── seed_quran_data.py        # Seed Quran data
│   ├── seed_rag_quick.py         # Quick RAG seeding
│   ├── create_category_mapping.py # Category mapping creator
│   ├── prepare_datasets_for_upload.py # Dataset uploader
│   ├── prepare_datasets_for_upload_v2.py # Dataset uploader v2
│   ├── extract_master_catalog.py # Master catalog extractor
│   ├── find_text_content.py     # Text content finder
│   └── lucene/                   # Lucene processing
│       ├── merge_lucene_with_master.py
│       ├── extract_lucene_pages.py
│       ├── verify_lucene_extraction.py
│       ├── decode_lucene_content.py
│       └── run_pipeline.py
│
├── ingestion/                  # Data ingestion pipelines
│   ├── chunk_books.py           # Book chunking utility
│   ├── complete_ingestion.py     # Complete ingestion pipeline
│   ├── import_azkar_db.py        # Azkar-DB importer
│   ├── ingest_and_run.py        # Ingest and run full pipeline
│   ├── ingest_extracted_books.py # Ingest extracted books
│   ├── chunk_all_books.py       # Chunk all books
│   ├── extract_lucene_index.py   # Extract Lucene index
│   └── extract_lucene_content.py # Extract Lucene content
│
├── tests/                      # Test scripts
│   ├── comprehensive_test.py       # Comprehensive validation suite
│   ├── test_all_endpoints.py        # Test all endpoints
│   ├── test_all_endpoints_detailed.py # Detailed endpoint tests
│   ├── test_all_endpoints.ps1       # PowerShell endpoint tests
│   ├── test_api.py                  # Quick API smoke test
│   ├── test_camel_tools.py          # Camel tools tests
│   ├── test_full_pipeline.py        # Full pipeline tests
│   ├── test_llm.py                  # LLM tests
│   ├── test_orchestrator.py         # Orchestrator tests
│   ├── test_query_route.py          # Query route tests
│   ├── test_sanadset_agent.py       # SanadSet agent tests
│   ├── ultra_test_api.py            # Ultra API tests
│   └── ... (more test scripts)
│
├── utils/                      # Shared utilities
│   └── utils.py                # Common helpers (paths, logging, progress)
│
├── lucene/                     # Lucene utilities (Java)
│   ├── LuceneExtractor.java    # Lucene index extractor
│   ├── LuceneExtractor.class   # Compiled extractor
│   ├── read_lucene.java        # Lucene index reader
│   └── read_lucene.class       # Compiled reader
│
├── windows/                    # Windows batch scripts
│   ├── start.bat               # Start application
│   ├── stop.bat                # Stop services
│   ├── test.bat                # Test API
│   ├── install.bat             # Install dependencies
│   ├── menu.bat                # Interactive menu
│   ├── ingest_data.bat         # Process data
│   └── process_and_embed.bat  # Generate embeddings
│
├── backup_embeddings_and_qdrant.py   # Full backup to HuggingFace
├── restore_from_huggingface.py       # Restore from HuggingFace
├── download_embeddings_and_upload_qdrant.py # Download & import
├── cli.py                            # Python CLI interface
├── quick_test.py                     # Quick smoke test
├── test_query_error.py               # Query error handling
└── README.md                         # This file
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

# Backup to HuggingFace
python scripts/backup_embeddings_and_qdrant.py

# Restore from HuggingFace
python scripts/restore_from_huggingface.py
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

## Script Categories

### 1. Analysis Scripts (23 files)

Used for diagnosing and analyzing the datasets:

| Script | Purpose |
|--------|---------|
| `analyze_dataset.py` | Complete dataset analysis with reports |
| `analyze_db.py` | Database analysis |
| `analyze_sanadset.py` | SanadSet hadith analysis |
| `analyze_shamela_dbs.py` | Shamela database analysis |
| `analyze_lucene.py` | Lucene index analysis |
| `check_datasets.py` | Dataset integrity validation |

### 2. Data Scripts (15 files)

Used for data processing and embedding:

| Script | Purpose |
|--------|---------|
| `create_mini_dataset.py` | Create GitHub-friendly mini-dataset (1.7 MB) |
| `embed_all_collections.py` | Production embedding pipeline |
| `generate_embeddings.py` | Batch embedding with checkpointing |
| `embed_sanadset_hadith.py` | Hadith embedding with resume support |
| `seed_mvp_data.py` | Seed MVP data to Qdrant |
| `backup_embeddings_and_qdrant.py` | Full backup to HuggingFace |
| `restore_from_huggingface.py` | Restore from HuggingFace |

### 3. Ingestion Scripts (8 files)

Used for data ingestion pipelines:

| Script | Purpose |
|--------|---------|
| `complete_ingestion.py` | Complete ingestion pipeline |
| `chunk_books.py` | Book chunking utility |
| `ingest_extracted_books.py` | Ingest extracted Shamela books |
| `import_azkar_db.py` | Import Azkar-DB duas |

### 4. Test Scripts (13 files)

Used for testing the system:

| Script | Purpose |
|--------|---------|
| `test_all_endpoints_detailed.py` | Detailed endpoint tests |
| `comprehensive_test.py` | Full validation suite |
| `test_api.py` | Quick API smoke test |
| `quick_test.py` | Fast smoke test |
| `test_query_route.py` | Query routing tests |

---

## Shared Utilities (`utils/utils.py`)

```python
from scripts.utils import (
    get_project_root,      # Project root path
    get_data_dir,          # Data directory path
    get_datasets_dir,      # Datasets directory path
    setup_script_logger,   # Consistent logging setup
    ProgressBar,           # Progress bar wrapper
    format_size,           # Human-readable file sizes
    format_duration,      # Human-readable durations
)
```

---

## Key Script Features

| Script | Features |
|--------|----------|
| `create_mini_dataset.py` | Flexible book matching, progress bars, balanced sampling |
| `seed_mvp_data.py` | Redis cache bypass, per-collection builders |
| `generate_embeddings.py` | Category routing, batch processing, error recovery |
| `embed_sanadset_hadith.py` | Checkpointing, resume support, atomic writes |
| `test_all_endpoints_detailed.py` | Response validation, colored output |
| `backup_embeddings_and_qdrant.py` | Full system backup to HuggingFace |
| `restore_from_huggingface.py` | Restore from HuggingFace |
| `quick_test.py` | Fast smoke test, all endpoints, exit codes |
| `cli.py` | All-in-one management CLI |

---

## Conventions

### Logging

All scripts use consistent logging format:

```
2026-04-15 10:30:00 [INFO] script-name: message
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

- **Quick Reference:** [docs/4-guides/02_QUICK_REFERENCE.md](../docs/4-guides/02_QUICK_REFERENCE.md)
- **Architecture:** [docs/2-architecture/01_ARCHITECTURE_OVERVIEW.md](../docs/2-architecture/01_ARCHITECTURE_OVERVIEW.md)
- **Windows Guide:** [docs/4-guides/windows.md](../docs/4-guides/windows.md)
- **Setup Guide:** [docs/4-guides/setup.md](../docs/4-guides/setup.md)

---

## Phase 8 Status

As of **April 15, 2026**:

- ✅ Phase 8 (Hybrid Intent Classifier) complete
- ✅ 10 collections uploaded to HuggingFace (42.6 GB)
- ⏳ GPU embedding pending (~13 hours on Colab T4)

---

*Last Updated: April 15, 2026*

*Built with ❤️ for the Muslim community*