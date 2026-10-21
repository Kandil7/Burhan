# Changelog

All notable changes to the Burhan Islamic QA System will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Production Docker Compose with healthchecks and resource limits
- GitHub Actions CI/CD pipeline (lint, test, build)
- Alembic migration framework for database versioning
- Comprehensive `.env.example` with 50+ configuration variables
- Rate limiting middleware configuration
- Sentry error tracking integration support
- HuggingFace backup/restore scheduling configuration
- `src/data/ingestion/quran_loader.py` upserts surahs, verses, and translations
  from the bundled JSON sample or the Quran.com v4 API (114 surahs, 6236 verses,
  Saheeh International translation).
- `scripts/data/embed_mini_v2_to_qdrant.py` embeds the bundled 10k-row mini
  datasets for `fiqh_passages`, `hadith_passages`, `islamic_history_passages`,
  and `general_islamic`, so every registered collection can answer retrieval
  queries. It uses the same encoder and payload schema as the query path.
- `scripts/data/seed_tafsir_data.py` fills the `tafsirs` table from three
  verse-keyed sources: al-Jalalayn and al-Qurtubi from `api.alquran.cloud`, and
  Ibn Kathir from `api.quran.com` tafsir id 14. It upserts on
  `(ayah_id, source_name)`, supports `--source`, `--surah-start`,
  `--surah-end`, and `--dry-run`.
- The `tafsirs` table holds 18,676 rows after seeding: al-Jalalayn 6,236,
  al-Qurtubi 6,235, Ibn Kathir 6,205. `/api/v1/quran/tafsir/{s}:{a}` now returns
  200 with commentary instead of 404.
- The dev compose file bind-mounts `../data` into the API container, so
  regenerated seed files are visible without an image rebuild.
- `scripts/data/embed_duas_to_qdrant.py` embeds the dua seed files into the
  registered `duas_adhkar` collection. It reads `data/seed/duas.json` and
  `data/seed/azkar_imported.json`, writes `book_title`, `page_number`,
  `section_title`, `category`, and `reference` payloads, and supports
  `--device`, `--half`, and `--recreate`.
- `migrations/versions/003_align_unique_constraint_names.sql` renames the
  database-generated UNIQUE constraints on `ayahs`, `translations`, and
  `tafsirs` to the names the SQLAlchemy models declare.

### Changed
- **BREAKING**: Default embedding model from `qwen3-embedding-0.5b` to `BAAI/bge-m3`
- **BREAKING**: Dockerfile now uses Poetry for dependency management
- Production mode defaults to 4 uvicorn workers (no `--reload`)
- Database pool size increased from 10 to 20 (production default)
- Redis max connections increased from 50 to 100

### Fixed
- Resolved `seerah_agent.py` vs `seerah_agent_v2.py` duplication (now single clean file)
- Dockerfile dependency installation (was using `pip install -e .` instead of Poetry)
- Removed `--reload` flag from production Dockerfile
- Container image now contains the `rag` group. Poetry 1.8.3 turns `--no-dev`
  into `--only main`, which silently dropped `--with rag`, so torch was never
  installed and each uvicorn worker exited at import.
- Both compose files load the repository `.env` through `env_file`, and the API
  service no longer sets an empty `OPENAI_API_KEY` that overrode the real value.
- The API service mounts a named `hf_cache` volume, so BGE-M3 is read from the
  cache instead of being downloaded into the container on every start.
- The Qdrant importer writes absolute row ids and supports `--start-shard`,
  `--end-shard`, `--row-start`, `--row-end`, and `--defer-index`. A resumed
  upload can no longer shift ids or overwrite earlier rows.
- `scripts/data/seed_quran_data.py` imported a `QuranLoader` that did not exist
  and resolved the project root one directory too high, so every documented
  invocation failed. It now runs from the repository root, supports
  `--source json --file PATH`, and derives the global verse number from the
  canonical per-surah verse counts, which stops a partial JSON file from
  renumbering verses that are already stored.
- Quotation validation missed verbatim verses once the full Quran was loaded.
  The SQL candidate filter normalized alef maksura, ta marbuta, and tatweel
  differently from the Python normalizer, and it returned an unordered window
  of common words. It now queries a matching skeleton with the whole input
  first and only falls back to word filters for mistyped quotes.
- The embedding model returned CUDA tensors through `.numpy()` without copying
  them to host memory, so any GPU-side import failed with a device-type error.
- `POST /api/v1/tools/zakat` returned 500 for its own documented example because
  the request used `trade_goods` and `stocks` while `ZakatAssets` exposes
  `trade_goods_value` and `stocks_value`. Both spellings now work, and unknown
  asset or heir keys return 422 with the accepted field list instead of a 500.
- The zakat and inheritance handlers converted every exception, including
  intentional validation errors, into a generic 500.
- `GET /api/v1/fiqh/test` and `GET /metrics/reset` were reachable in production.
  Both are development-only now and return 404 unless `DEBUG=true`; metrics
  reset accepts POST only.
- The catalog and collection indexing pipelines returned zero counts while
  doing nothing. They now raise an explicit error that points at the working
  embedding scripts.
- The multi-collection retriever swallowed per-collection failures without a
  log line, which hid Qdrant outages from the operator.
- `/api/v1/quran/tafsir/{s}:{a}` returned an empty list for an existing verse
  with no commentary. It returns 404, matching the documented contract.
- `docs/5-api/COMPLETE_DOCUMENTATION.md` listed removed endpoints
  (`/api/v1/query`, `/api/v1/rag/*`) and removed agents. The agent and endpoint
  tables now match the running application.
- Tool intents routed to deterministic tools from `/api/v1/ask` crashed with
  `'ToolOutput' object has no attribute 'answer'`, because the use case treated
  every routed target as a RAG agent. Tool results are now adapted to the agent
  output shape, and calculators that only exist behind `/tools/*` return a
  pointer instead of an error.
- The duas intent matched the generic words `طلب` and `إجابة`, so a question
  like "ما هو فضل طلب العلم؟" was routed to the dua tool. Both words were
  removed; `دعاء`, `أدعية`, `الدعاء`, and `تضرع` remain.
- The dua tool searched only English occasion names, so an Arabic request such
  as "أدعية الصباح" returned nothing. Arabic occasion hints now map to the
  stored dataset occasions.
- `scripts/ingestion/import_azkar_db.py` pointed at
  `refs/heads/main`, while the upstream repository publishes on `master`, and
  it wrote to `scripts/data/seed/` instead of `data/seed/`. It downloaded the
  SQLite dump that the converter could not read. It now resolves the project
  root correctly, accepts both published payload shapes, maps Arabic
  categories onto the tool's occasion ids, and writes 345 azkar entries.
- The dua tool ignored the curated `search_keywords` field, so a query such as
  "الاستغفار" missed entries whose text never contains that exact word.
- `TafsirRetrievalEngine` returned sources in whatever order the database
  happened to produce. Queries now order by `source_name`, `id`, so repeated
  calls return an identical list, and source availability is stable.
- `src/application/services/tool_service.py` returned `success=True` with
  "not implemented" text for every tool. It now delegates to the real
  prayer-times, Hijri, and dua tools, propagates the tool's own success flag,
  and fails loudly for the HTTP-only calculators.
- `RunToolUseCase` raised `NotImplementedError` for every tool type. It now
  dispatches through the repaired tool service.
- `ClassifyService` returned a fixed `GENERAL_ISLAMIC` intent at zero
  confidence. It now delegates to `ClassifyQueryUseCase`.
- `TraceService.build_trace` discarded the events it had collected and returned
  an empty list. It now delegates to `BuildTraceUseCase`.
- Inheritance maths underpaid residuary heirs. The son-only and general
  asabah branches reported a per-heir `amount` next to an aggregate `fraction`,
  so a 100,000 estate with one wife and two sons distributed 56,250 and left
  43,750 unassigned. Each row now reports the aggregate amount.
- Multiple wives were given `1/8 × wife_count`, so two wives received 1/4 and
  squeezed the residuary heirs. The wives' fard is a single share split among
  them; the row is named "Wives" and stays at 1/8 or 1/4.
- `/api/v1/ask` reported `answer_mode="answer"` even when the LLM call failed
  and the response was the raw `[C1]` evidence text. Such responses now report
  `answer_mode="evidence"`, add a `generation_fallback` verification issue, and
  set `requires_human_review`. A missing LLM client takes the same path.
- The collection agents hardcoded `max_tokens` (1024 to 1792), so
  `LLM_MAX_TOKENS` could not constrain them. Providers that enforce a small
  per-minute output quota rejected every request. Each agent now calls
  `settings.resolve_max_tokens(budget)`, which clamps to the configured
  ceiling. `/api/v1/search/simple` applies the same clamp to `RAG_MAX_TOKENS`.
- The contradiction verifier flattened every retrieved passage into one text
  block and treated a substring `"لا "` as a negation. Any answer sentence
  without a negation then "contradicted" the block, because the block always
  contained one, so almost every Arabic answer was marked unverified. The check
  now compares one sentence against one passage, matches negation as a whole
  token, ignores `لا شك` and `لا ... إلا`, and requires substantial shared
  content words. It also catches numeric conflicts per passage.
- Every collection agent reported `evidence_filtered_out` whenever reranking or
  verification dropped a candidate, which is normal. The issue is now raised
  only when every candidate was dropped.
- `scripts/data/duas.json` and `scripts/ingestion/import_azkar_db.py` feed the
  dua tool, but the registered `duas_adhkar` collection stayed empty and
  `search/simple?collection=duas_adhkar` returned nothing. The new
  `scripts/data/embed_duas_to_qdrant.py` embeds all 355 seed entries.
- `001_initial_schema.sql` left three UNIQUE constraints unnamed, so PostgreSQL
  named them after their columns while the models declare `uq_ayah_surah_number`,
  `uq_translation`, and `uq_tafsir`. Migration
  `003_align_unique_constraint_names.sql` renames them idempotently.
- `python scripts/cli.py db migrate` could not run on Windows: it built
  `docker exec ... < file`, and PowerShell does not support the `<` operator.
  The CLI now feeds each SQL file to `psql` as stdin, which works on both
  platforms, and stops at the first failing migration.
- The CLI crashed on every command in a Windows console because it printed
  status emoji to a cp1252 stream. It now reconfigures stdout and stderr to
  UTF-8 with replacement, so the commands run instead of raising
  `UnicodeEncodeError`.
- `/api/v1/ask` answered questions about zakat and inheritance rulings by
  telling the user to call `/api/v1/tools/*`: the tool intents tied with FIQH on
  keyword count and won on priority, but the calculators need amounts or heirs.
  A calculator intent now requires a number, and inheritance also accepts a
  named case, so "ما هي أحكام زكاة عروض التجارة؟" is answered from the fiqh
  collection while "زكاة 100000 ريال" still reaches the calculator.
- The `علي` keyword routed every question containing the preposition `على` to
  Seerah, `مسلم` in the hadith list matched `المسلم`, and the bare month
  `رمضان` outranked fiqh for "صيام رمضان". The first two keywords are now
  phrases, and calendar padding ranks below FIQH on a tie.
- `HybridQueryClassifier._keyword_match` duplicated the classifier's conflict
  resolution instead of delegating it, so the two paths disagreed. It now
  delegates to `KeywordBasedClassifier`.
- Tool answers dumped raw JSON. Hijri dates and prayer times now render as
  readable Arabic lines.
- The exact-quote verifier compared Arabic quotes without folding diacritics,
  alef forms, or ta-marbuta, so a correctly quoted passage was reported as a
  hallucination whenever the model dropped tashkeel.

### Removed
- 70+ obsolete scripts (analysis, one-off uploads, duplicate utilities)
- 45+ duplicate documentation files (status reports, code review duplicates)
- 4 obsolete notebooks from `docs/notebooks/`
- Empty placeholder directories (`models/`, `output/`, `lib/`)
- Duplicate Windows batch scripts in `scripts/windows/`
- Compiled Java binaries (`.class` files)

### Archived
- 17 analysis scripts moved to `scripts/archive/`
- 4 planning documents moved to `docs/archive/planning/`
- 3 improvement reports moved to `docs/archive/improvements/`
- 3 Java source files moved to `scripts/archive/lucene/`

---

## [0.6.0] - 2026-04-10

### Added
- 10 vector collections with 11,147+ vectors
- BaseRAGAgent pattern for code reuse
- HuggingFace dataset upload (42.6 GB)
- Backup/restore functionality for embeddings
- Mini-dataset (1.7 MB, 1,623 documents)

### Changed
- Migrated from Qwen3-Embedding-0.6B to BAAI/bge-m3
- Replaced Google Drive dependency with local Colab disk
- Updated notebook workflow (2 active, 1 archived)

---

## [0.5.0] - 2026-04-08

### Added
- 13 specialized agents (Fiqh, Hadith, Quran, etc.)
- 5 deterministic tools (Zakat, Inheritance, Prayer Times, Hijri, Dua)
- Quran pipeline with NL2SQL and tafsir retrieval
- Structured logging with structlog
- Intent classifier with 16 intent types (~90% accuracy)

### Changed
- Code review completed (score: 6.5/10)
- Fixed inheritance_calculator.py truncation

---

## [0.4.0] - 2026-04-01

### Added
- RAG pipelines with Qdrant vector DB
- Embedding model (Qwen3-Embedding-0.6B)
- Fiqh agent with retrieval + generation
- Docker Compose for development services

---

## [0.3.0] - 2026-03-25

### Added
- Quran pipeline (6 modules)
- NL2SQL analytics
- Quotation validation
- Tafsir retrieval

---

## [0.2.0] - 2026-03-15

### Added
- 5 deterministic tools (Zakat, Inheritance, Prayer Times, Hijri, Dua)
- Hybrid intent classifier
- Response orchestrator
- Citation normalizer

---

## [0.1.0] - 2026-03-01

### Added
- Initial project structure
- FastAPI application with 18 endpoints
- 4-layer architecture
- PostgreSQL and Redis integration
- Basic intent routing

---

## Version History Summary

| Version | Date | Key Features | Status |
|---------|------|--------------|--------|
| 0.6.0 | 2026-04-10 | 10 collections, HF upload, backup/restore | Released |
| 0.5.0 | 2026-04-08 | 13 agents, 5 tools, Quran pipeline | Released |
| 0.4.0 | 2026-04-01 | RAG pipelines, embeddings | Released |
| 0.3.0 | 2026-03-25 | Quran module, NL2SQL | Released |
| 0.2.0 | 2026-03-15 | Tools, intent classifier | Released |
| 0.1.0 | 2026-03-01 | Initial structure | Released |
