# Athar Islamic QA System - Documentation Index

Welcome to the comprehensive documentation for the **Athar Islamic QA System**.

---

## 📁 Documentation Structure

```
docs/
├── getting-started/          # Entry point & overview
├── architecture/             # System architecture & design
├── guides/                   # How-to guides (setup, running, windows)
├── development/             # Developer guides (dev, frontend, embeddings)
├── api/                      # API documentation
├── core-features/            # RAG, Quran modules
├── deployment/               # Production deployment
├── improvements/             # Phase improvements & changelogs
├── reports/                  # Project reports & status
└── Fanar-Sadiq Paper.pdf     # Research paper
```

---

## 🚀 Quick Start

### Getting Started
| File | Description |
|------|-------------|
| [getting-started/index.md](getting-started/index.md) | Project introduction |
| [architecture/01_ARCHITECTURE_OVERVIEW.md](architecture/01_ARCHITECTURE_OVERVIEW.md) | System architecture diagram |
| [guides/running.md](guides/running.md) | Quick start guide |

### User Guides
| File | Description |
|------|-------------|
| [guides/running.md](guides/running.md) | How to run the application |
| [guides/setup.md](guides/setup.md) | Complete setup guide |
| [guides/windows.md](guides/windows.md) | Windows setup guide |

---

## 🏗️ Architecture

| File | Description |
|------|-------------|
| [architecture/01_ARCHITECTURE_OVERVIEW.md](architecture/01_ARCHITECTURE_OVERVIEW.md) | High-level system overview |
| [architecture/technical-architecture.md](architecture/technical-architecture.md) | Detailed technical architecture |
| [architecture/branch-strategy.md](architecture/branch-strategy.md) | Git branching strategy |

---

## 🔧 Development

| File | Description |
|------|-------------|
| [development/index.md](development/index.md) | Development setup |
| [development/frontend.md](development/frontend.md) | Frontend documentation |
| [development/embeddings.md](development/embeddings.md) | Embedding model setup |

---

## 📖 API Documentation

| File | Description |
|------|-------------|
| [api/reference.md](api/reference.md) | API documentation |
| [api/endpoints.md](api/endpoints.md) | Complete API endpoints reference |
| [api/complete.md](api/complete.md) | Full technical documentation |

---

## ⚡ Core Features

| File | Description |
|------|-------------|
| [core-features/rag.md](core-features/rag.md) | RAG pipeline guide |
| [core-features/quran.md](core-features/quran.md) | Quran module guide |

---

## 🚢 Deployment

| File | Description |
|------|-------------|
| [deployment/index.md](deployment/index.md) | Production deployment guide |

---

## 📊 Project Reports

| File | Description |
|------|-------------|
| [reports/30_FINAL_PROJECT_SUMMARY.md](reports/30_FINAL_PROJECT_SUMMARY.md) | Project summary |
| [reports/31_FIX_SUMMARY.md](reports/31_FIX_SUMMARY.md) | Fixes summary |
| [reports/32_TEST_RESULTS.md](reports/32_TEST_RESULTS.md) | Test results |
| [reports/33_COMPREHENSIVE_TEST_RESULTS.md](reports/33_COMPREHENSIVE_TEST_RESULTS.md) | Comprehensive tests |
| [reports/34_100_PERCENT_COMPLETE.md](reports/34_100_PERCENT_COMPLETE.md) | 100% completion report |

---

## 📚 Reference

| File | Description |
|------|-------------|
| [reference/40_project_plan.md](reference/40_project_plan.md) | Original project plan |
| [reference/41_COMPREHENSIVE_PROJECT_EXPLANATION.md](reference/41_COMPREHENSIVE_PROJECT_EXPLANATION.md) | Complete project explanation |
| [reference/42_DOCUMENTATION_REVIEW.md](reference/42_DOCUMENTATION_REVIEW.md) | Documentation review |

---

## 📕 Research Paper

- [Fanar-Sadiq Paper.pdf](Fanar-Sadiq%20A%20Multi-Agent%20Architecture%20for%20Grounded%20Islamic%20QA.pdf) - The research paper that inspired this architecture

---

## 🔑 Quick Links

### API Endpoints
| Endpoint | Description |
|----------|-------------|
| `POST /api/v1/query` | Main query endpoint |
| `GET /api/v1/quran/surahs` | List all surahs |
| `POST /api/v1/tools/zakat` | Calculate Zakat |
| `POST /api/v1/tools/inheritance` | Calculate inheritance |

### Intent Classification
| Intent | Handler |
|--------|---------|
| `fiqh` | FiqhAgent (RAG) |
| `quran` | QuranAgent |
| `islamic_knowledge` | GeneralIslamicAgent |
| `zakat` | ZakatCalculator |
| `inheritance` | InheritanceCalculator |
| `prayer_times` | PrayerTimesTool |
| `hijri_calendar` | HijriCalendarTool |
| `dua` | DuaRetrievalTool |
| `greeting` | ChatbotAgent |

---

## 🚀 Quick Start Commands

```bash
# Install dependencies
poetry install

# Run the API
python -m uvicorn src.api.main:app --reload

# Access API docs
# Open http://localhost:8000/docs
```

---

## 📞 Support

For questions or issues, please check the documentation or open an issue on GitHub.

---

*Last updated: April 2026*
*Version: 0.5.0*
