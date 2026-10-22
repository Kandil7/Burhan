# Burhan Scripts

Operational and maintenance scripts. `pytest` only collects `tests/` at the
repository root, so nothing in this directory runs as part of the test suite;
the `smoke_` and `probe_` prefixes make that honest.

## Layout

```
scripts/
├── cli.py                 # All-in-one management CLI (start, stop, db, ingest...)
├── utils.py               # Shared helpers (paths, logging, progress)
│
├── data/                  # Dataset preparation, embedding, seeding, backup
│   ├── embed_full_to_qdrant.py      # Full-corpus loader (prefetches from the Hub)
│   ├── embed_mini_v2_to_qdrant.py   # Mini loader; fetches missing data/mini_dataset_v2 files
│   ├── create_mini_dataset_v2.py    # Rebuild the mini sample from data/processed
│   ├── seed_mvp_data.py / seed_quran_sample.py / seed_tafsir_data.py
│   ├── generate_embeddings.py       # Batch embedding with checkpointing
│   ├── embed_all_collections.py / embed_sanadset_hadith.py / embed_duas_to_qdrant.py
│   ├── backup_embeddings_and_qdrant.py     # Upload snapshots to HuggingFace
│   ├── restore_from_huggingface.py  # Restore snapshots from HuggingFace
│   ├── download_embeddings_and_upload_qdrant.py
│   ├── upload_mini_dataset_v2.py and other Hub uploaders
│   └── lucene/                      # Lucene index extraction & merge (Java output lives in data/processed)
│
├── ingestion/             # Corpus importers and chunkers
│   ├── complete_ingestion.py / ingest_and_run.py / ingest_extracted_books.py
│   ├── chunk_books.py / chunk_all_books.py
│   ├── Bayan_chunker.py / seerah_agentic_chunker_*.py / seerah_hierarchical_chunker.py
│   ├── import_azkar_db.py           # Azkar-DB duas
│   └── extract_lucene_index.py / extract_lucene_content.py
│
├── quality/               # The quality fence and its baselines
│   ├── reachability_report.py       # Live/dead analysis; --write-manifest refreshes the fence
│   ├── legacy_manifest.json         # The frozen boundary the architecture tests read
│   ├── eval_harness.py              # retrieve / score / ask / route / compare
│   ├── golden_set.json              # 20 curated questions with acceptable intents
│   └── baseline/                    # Recorded metric runs
│
├── evaluation/            # Manual evaluation scripts (Seerah RAG) and their outputs
│   ├── eval_seerah.py / rag_eval_seerah.py
│   └── rag_eval_results.csv / rag_eval_seerah.jsonl
│
├── smoke/                 # Manual API smoke scripts (server must be running)
│   ├── smoke_all_endpoints.py       # All 20 HTTP endpoints, compact
│   ├── smoke_all_endpoints_suite.py # Longer, detailed output
│   ├── smoke_api.py / quick_test.py / check_api.py
│   └── smoke_*.py                   # Agent, LLM, routing, pipeline smokes
│
├── tools/                 # One-off probes and utilities (historical)
│   ├── debug_*.py                   # Debugging session leftovers
│   ├── probe_*.py                   # Classifier/API probes (renamed from test_*)
│   ├── launch_server.py / md_to_notebook.py / upload_readme_v3.py
│
└── windows/               # Windows launchers
    ├── start-athar.bat              # Full stack up + migrations via scripts/cli.py
    ├── start_server.bat / start-8003.bat / stop-athar.bat
    ├── download-embeddings-to-qdrant.bat
    ├── extract_all_lucene.bat
    └── build.bat
```

## Quick Start

### Data & Embedding

```bash
# Full-corpus load (resumes; classic HTTP transfer, direct-download fallback)
python scripts/data/embed_full_to_qdrant.py --all --recreate --device cuda --half

# Mini sample loader (fetches data/mini_dataset_v2 payloads from the Hub)
python scripts/data/embed_mini_v2_to_qdrant.py --all --recreate

# Backup / restore snapshots
python scripts/data/backup_embeddings_and_qdrant.py
python scripts/data/restore_from_huggingface.py
```

### Smoke Testing

Start the API server, then:

```bash
python scripts/smoke/smoke_all_endpoints.py       # compact bucket by bucket
python scripts/smoke/smoke_all_endpoints_suite.py # verbose with per-field checks
```

### Quality Fence

```bash
python scripts/quality/reachability_report.py            # analyze only
python scripts/quality/reachability_report.py --write-manifest  # deliberate changes only
python scripts/quality/eval_harness.py score             # golden-set retrieval scoring
```

## CLI Interface

```bash
python scripts/cli.py start        # docker stack + migrations
python scripts/cli.py db migrate   # applies migrations/*.sql in order
python scripts/cli.py quick-test
```

## Conventions

- Scripts insert the project root into `sys.path` themselves; run them from the
  repository root.
- Never hardcode secrets; read settings from `src.config.settings`.
- pytest never collects anything here; keep test naming for `tests/` only.
