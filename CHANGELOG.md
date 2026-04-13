# Changelog

All notable changes to the Athar Islamic QA System will be documented in this file.

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
