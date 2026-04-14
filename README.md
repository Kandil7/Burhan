# 🕌 Athar - Islamic QA System

> A production-ready, multi-agent Islamic QA system based on the Fanar-Sadiq architecture, providing grounded, citation-backed answers with deterministic calculators for zakat, inheritance, and verified sources from Quran, Hadith, and Fiqh.

[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-green.svg)](https://fastapi.tiangolo.com/)
[![Phase](https://img.shields.io/badge/status-Phase%207%20Complete-success.svg)](https://github.com/Kandil7/Athar)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## 🎉 Latest Achievement: Complete Lucene Merge ✅

**April 8, 2026:** Successfully processed **11.3M+ documents** from [ElShamela Library](https://shamela.ws/) (المكتبة الشاملة):
- ✅ 7,358,148 page documents (16.14 GB)
- ✅ 3,914,618 title documents (341 MB)
- ✅ 35,526 hadith chains (esnad)
- ✅ 8,425 book metadata files
- ✅ **10 RAG-ready collections** built (5,717,177 enriched documents)
- ✅ **10 hierarchical chunk files** created
- ✅ Disk-based memory-efficient processing (<2 GB RAM)

📖 **Full details:** [Lucene Merge Complete](docs/10-operations/LUCENE_MERGE_COMPLETE.md)

---

## 📋 Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Quick Start](#quick-start)
- [API Documentation](#api-documentation)
- [Data Pipeline](#data-pipeline)
- [Project Structure](#project-structure)
- [Phase Roadmap](#phase-roadmap)
- [Documentation](#documentation)
- [Contributing](#contributing)
- [License](#license)

---

## 🎯 Overview

**Athar** is an Islamic QA system that answers religious questions with verified sources and proper citations. Built on the **Fanar-Sadiq** multi-agent architecture.

### Problem & Solution

| Problem | Solution |
|---------|----------|
| LLMs hallucinate religious rulings | Ground answers in verified sources only |
| Incorrect verse/hadith references | Citation system [C1], [C2], etc. |
| Missing scholarly differences | RAG retrieves multiple scholarly views |
| No calculation accuracy | Deterministic calculators for zakat, inheritance |

### Key Metrics

| Metric | Value |
|--------|-------|
| **Lines of Code** | 14,200+ |
| **Files** | 120+ |
| **Agents** | 13 specialized agents |
| **Tools** | 5 deterministic tools |
| **Intents** | 16 types |
| **Collections** | 10 vector collections |
| **Books** | 8,425 Islamic texts |
| **Lucene Documents** | 11,316,717 processed |
| **RAG Documents** | 5,717,177 enriched |
| **Test Coverage** | ~91% |

---

## 🏗️ Architecture

```
User Query → Intent Classifier (3-tier hybrid) → Route to Agent →
  RAG Retrieval / Calculator / NL2SQL → Generate Answer →
    Citation Normalization → Response with [C1], [C2]
```

### 4-Layer Architecture

```
┌─────────────────────────────────────────────────────────┐
│              API Layer (FastAPI + Next.js)               │
│  POST /api/v1/query  •  GET /health  •  18 endpoints    │
└────────────────────────┬────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────┐
│               Orchestration Layer                        │
│  Hybrid Intent Classifier  •  Response Orchestrator     │
│  Citation Normalizer  •  Agent Registry                 │
└────────────────────────┬────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────┐
│         Agents & Tools Layer (13 agents + 5 tools)       │
│  Fiqh, Hadith, Quran, Tafsir, Aqeedah, Seerah, etc.    │
│  Zakat Calc, Inheritance Calc, Prayer Times, Hijri, Dua │
└────────────────────────┬────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────┐
│           Knowledge Layer (61 GB processed data)         │
│  PostgreSQL  •  Qdrant (10 collections)  •  Redis       │
│  Lucene Indexes  •  Master Catalog  •  LLM (Groq)       │
└─────────────────────────────────────────────────────────┘
```

---

## 🚀 Quick Start

```bash
# 1. Clone & setup
git clone https://github.com/Kandil7/Athar.git
cd Athar
poetry install --with dev
cp .env.example .env
# Edit .env with your API keys

# 2. Start services
docker compose -f docker/docker-compose.dev.yml up -d
make db-migrate

# 3. Run API server
make dev

# 4. Open http://localhost:8000/docs
```

---

## 🌐 API Documentation

### 18 Endpoints

| Endpoint | Method | Purpose | Status |
|----------|--------|---------|--------|
| `/api/v1/query` | POST | Main query endpoint | ✅ |
| `/api/v1/tools/zakat` | POST | Calculate zakat | ✅ |
| `/api/v1/tools/inheritance` | POST | Inheritance distribution | ✅ |
| `/api/v1/tools/prayer-times` | POST | Prayer times + Qibla | ✅ |
| `/api/v1/tools/hijri` | POST | Date conversion | ✅ |
| `/api/v1/tools/duas` | POST | Dua retrieval | ✅ |
| `/api/v1/quran/*` | GET/POST | Quran endpoints (6) | ✅ |
| `/api/v1/rag/*` | GET/POST | RAG endpoints (3) | ✅ |
| `/health`, `/ready` | GET | Health checks | ✅ |

**Interactive docs:** http://localhost:8000/docs

---

## 📊 Data Pipeline

### Source: ElShamela Library (المكتبة الشاملة)

All data is derived from **ElShamela Library** (المكتبة الشاملة) — the largest comprehensive digital library of Islamic texts, containing **8,425 books** across **41 categories** spanning **1,400 years** of Islamic scholarship.

- **Website:** https://shamela.ws/
- **Format:** Proprietary Shamela format → Extracted to plain text
- **Books:** 8,425 texts from 3,146 scholars
- **Time Span:** 0-1400+ AH (7th-21st century CE)

### Complete Flow (Phase 7 - COMPLETE ✅)

```
ElShamela Library → Extraction → Merge & Enrichment → Collections → Chunks → (Next: Embedding)
```

### Processing Statistics

| Stage | Documents | Size | Status |
|-------|-----------|------|--------|
| **Lucene Extraction** | 11,316,717 | 16.49 GB | ✅ Complete |
| **Merge & Enrichment** | 5,717,177 | ~61 GB | ✅ Complete |
| **Hierarchical Chunking** | 10 files | ~88 GB | ✅ Complete |
| **Embedding** | - | - | ⏳ TODO (Colab GPU) |
| **Qdrant Import** | - | - | ⏳ TODO |

### Collections (10 Total)

| Collection | Documents | Percentage |
|------------|-----------|------------|
| hadith_passages | 1,551,964 | 27.1% |
| general_islamic | 1,193,626 | 20.9% |
| islamic_history_passages | 1,186,189 | 20.7% |
| fiqh_passages | 676,577 | 11.8% |
| quran_tafsir | 550,989 | 9.6% |
| aqeedah_passages | 183,086 | 3.2% |
| arabic_language_passages | 147,498 | 2.6% |
| spirituality_passages | 79,233 | 1.4% |
| seerah_passages | 74,972 | 1.3% |
| usul_fiqh | 73,043 | 1.3% |

---

## 📁 Project Structure

```
Athar/
├── src/                          # Python backend (FastAPI)
│   ├── api/                      # 18 REST endpoints
│   ├── core/                     # Router, orchestrator, citation
│   ├── agents/                   # 13 specialized agents
│   ├── tools/                    # 5 deterministic tools
│   ├── quran/                    # Quran pipeline
│   └── knowledge/                # RAG infrastructure
│
├── data/
│   ├── mini_dataset/             # GitHub-friendly (1.7 MB)
│   └── processed/                # ✅ 61 GB processed data
│       ├── master_catalog.json   # 8,425 books
│       ├── category_mapping.json # 40→10 mapping
│       ├── author_catalog.json   # 3,146 authors
│       └── lucene_pages/         # ✅ COMPLETE MERGE
│           ├── collections/      # 10 JSONL files (5.7M docs)
│           └── chunks/           # 10 chunk files
│
├── datasets/                     # Full datasets (14.4 GB, excluded from Git)
├── scripts/                      # 40+ utility scripts
├── notebooks/                    # Colab notebooks
├── tests/                        # Test suite (9 files)
├── docker/                       # Docker configuration
└── docs/                         # Documentation (60+ files)
```

---

## 🗺️ Phase Roadmap

| Phase | Status | Deliverables |
|-------|--------|--------------|
| **Phase 1** | ✅ Complete | Foundation, Router, Orchestrator, Citation |
| **Phase 2** | ✅ Complete | 6 Tools (Zakat, Inheritance, Prayer, Hijri, Dua) |
| **Phase 3** | ✅ Complete | Quran Pipeline, NL2SQL, Tafsir |
| **Phase 4** | ✅ Complete | RAG Pipelines, Embeddings, Vector DB |
| **Phase 5** | ✅ Complete | Next.js Frontend, RTL UI |
| **Phase 6** | ✅ Complete | 13 Agents, Mini-Dataset, 10 Collections |
| **Phase 7** | ✅ **COMPLETE** | **Full Lucene Merge (11.3M docs, 10 collections, 5.7M enriched docs)** |
| **Phase 8** | ⏳ TODO | Embedding (Colab GPU), Qdrant Import, Testing |

### Next Steps (Phase 8)

1. **Embed Collections** (3-5 hours, Colab T4 GPU)
2. **Import to Qdrant** (1 hour)
3. **Test RAG Retrieval** (30 min)
4. **Deploy to Production** (1 day)

---

## 📚 Documentation

### Getting Started
- **[docs/1-getting-started/START_HERE.md](docs/1-getting-started/START_HERE.md)** - Entry point for new developers

### Core Documentation
- **[docs/10-operations/LUCENE_MERGE_COMPLETE.md](docs/10-operations/LUCENE_MERGE_COMPLETE.md)** - ✅ **Complete merge statistics & guide**
- **[docs/5-api/COMPLETE_DOCUMENTATION.md](docs/5-api/COMPLETE_DOCUMENTATION.md)** - Full system docs
- **[docs/2-architecture/01_ARCHITECTURE_OVERVIEW.md](docs/2-architecture/01_ARCHITECTURE_OVERVIEW.md)** - Architecture decisions
- **[docs/9-reference/FILE_REFERENCE.md](docs/9-reference/FILE_REFERENCE.md)** - Complete file tree

### Dataset Guides
- **[docs/6-data/LUCENE_EXTRACTION_COMPLETE_GUIDE.md](docs/6-data/LUCENE_EXTRACTION_COMPLETE_GUIDE.md)** - Lucene extraction
- **[docs/6-data/MASTER_DB_INTEGRATION_PLAN.md](docs/6-data/MASTER_DB_INTEGRATION_PLAN.md)** - Master.db integration

### Full Documentation Index
See **[docs/README.md](docs/README.md)** for complete documentation listing (60+ files).

---

## 🔧 Configuration

### Environment Variables

```bash
# Required
GROQ_API_KEY=your-groq-key
HF_TOKEN=your-huggingface-token
SECRET_KEY=your-secret-key

# Optional
DATABASE_URL=postgresql+asyncpg://athar:athar_password@localhost:5432/athar_db
QDRANT_URL=http://localhost:6333
REDIS_URL=redis://localhost:6379/0
```

### Key Commands

```bash
make dev              # Start development server
make test             # Run tests
make lint             # Run linters
make format           # Auto-format code
make docker-up        # Start Docker services
```

---

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

### Code Style

- Python: PEP 8 with type hints
- Linting: Ruff (line length 120)
- Type Checking: MyPy (strict mode)
- Testing: pytest with coverage (~91%)

---

## 📄 License

MIT License - see LICENSE file for details.

---

<div align="center">

**Built with ❤️ for the Muslim community**

[🕌](#) Athar Islamic QA System • Based on Fanar-Sadiq Architecture

**Data Source:** [ElShamela Library](https://shamela.ws/) (المكتبة الشاملة) • 8,425 books • 3,146 scholars

**11.3M+ documents processed • 10 collections built • Ready for production**

[Documentation](docs/README.md) • [API Docs](http://localhost:8000/docs) • [Issues](https://github.com/Kandil7/Athar/issues)

</div>
