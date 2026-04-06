# 📚 Athar Islamic QA System - Documentation Index

Welcome to the comprehensive documentation for the **Athar Islamic QA System**.

---

## 📁 Documentation Structure

```
docs/
├── getting-started/          # Quick start guides
├── architecture/             # System architecture
├── technical/                # Technical documentation
├── reports/                  # Project reports
├── reference/                # Reference materials
├── guides/                   # How-to guides
└── Fanar-Sadiq Paper.pdf     # Research paper
```

---

## 🚀 Quick Start

### Getting Started Guides
| File | Description |
|------|-------------|
| [getting-started/00_README.md](getting-started/00_README.md) | Project introduction and quick start |
| [getting-started/01_ARCHITECTURE_OVERVIEW.md](getting-started/01_ARCHITECTURE_OVERVIEW.md) | System architecture diagram |
| [getting-started/02_QUICK_REFERENCE.md](getting-started/02_QUICK_REFERENCE.md) | Quick reference guide |

### How-to Guides
| File | Description |
|------|-------------|
| [guides/01_RUN.md](guides/01_RUN.md) | How to run the application |
| [guides/02_SETUP_COMPLETE.md](guides/02_SETUP_COMPLETE.md) | Complete setup guide |
| [guides/03_WINDOWS_GUIDE.md](guides/03_WINDOWS_GUIDE.md) | Windows setup guide |

---

## 🏗️ Architecture

| File | Description |
|------|-------------|
| [architecture/03_architecture.md](architecture/03_architecture.md) | Detailed architecture |
| [architecture/04_BRANCH_STRATEGY.md](architecture/04_BRANCH_STRATEGY.md) | Git branching strategy |
| [architecture/05_IMPROVEMENTS_SUMMARY.md](architecture/05_IMPROVEMENTS_SUMMARY.md) | Phase 5 improvements |

---

## 📖 Technical Documentation

### Development & Setup
| File | Description |
|------|-------------|
| [technical/10_DEVELOPMENT.md](technical/10_DEVELOPMENT.md) | Development setup |
| [technical/11_FRONTEND.md](technical/11_FRONTEND.md) | Frontend documentation |
| [technical/12_EMBEDDING_SETUP.md](technical/12_EMBEDDING_SETUP.md) | Embedding model setup |

### API & Integration
| File | Description |
|------|-------------|
| [technical/20_API.md](technical/20_API.md) | API documentation |
| [technical/25_FULL_DOCUMENTATION.md](technical/25_FULL_DOCUMENTATION.md) | Complete technical docs |
| [technical/26_API_REFERENCE.md](technical/26_API_REFERENCE.md) | Complete API reference |

### Core Features
| File | Description |
|------|-------------|
| [technical/21_RAG_GUIDE.md](technical/21_RAG_GUIDE.md) | RAG pipeline guide |
| [technical/22_QURAN_GUIDE.md](technical/22_QURAN_GUIDE.md) | Quran module guide |
| [technical/23_DEPLOYMENT.md](technical/23_DEPLOYMENT.md) | Deployment guide |

---

## 📊 Project Reports

| File | Description |
|------|-------------|
| [reports/30_FINAL_PROJECT_SUMMARY.md](reports/30_FINAL_PROJECT_SUMMARY.md) | Project summary |
| [reports/31_FIX_SUMMARY.md](reports/31_FIX_SUMMARY.md) | Fixes summary |
| [reports/32_TEST_RESULTS.md](reports/32_TEST_RESULTS.md) | Test results |
| [reports/33_COMPREHENSIVE_TEST_RESULTS.md](reports/33_COMPREHENSIVE_TEST_RESULTS.md) | Comprehensive tests |
| [reports/34_100_PERCENT_COMPLETE.md](reports/34_100_PERCENT_COMPLETE.md) | 100% completion report |
| [reports/35_CODE_REVIEW_FULL.md](reports/35_CODE_REVIEW_FULL.md) | Full code review |
| [reports/36_PHASE_5_IMPROVEMENTS.md](reports/36_PHASE_5_IMPROVEMENTS.md) | Phase 5 improvements |

---

## 📚 Reference Materials

| File | Description |
|------|-------------|
| [reference/40_project_plan.md](reference/40_project_plan.md) | Original project plan |
| [reference/41_COMPREHENSIVE_PROJECT_EXPLANATION.md](reference/41_COMPREHENSIVE_PROJECT_EXPLANATION.md) | Full project explanation |
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
