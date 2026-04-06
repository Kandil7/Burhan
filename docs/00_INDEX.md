# Athar Islamic QA System - Complete Documentation

Welcome to the comprehensive documentation for the **Athar Islamic QA System**. This document provides complete coverage of the entire application from architecture to deployment.

---

## 📚 Documentation Index

### Getting Started
- **[00_README.md](getting-started/00_README.md)** - Project introduction and quick start
- **[01_ARCHITECTURE_OVERVIEW.md](getting-started/01_ARCHITECTURE_OVERVIEW.md)** - System architecture diagram
- **[02_QUICK_REFERENCE.md](getting-started/02_QUICK_REFERENCE.md)** - Quick reference guide

### Architecture
- **[03_architecture.md](architecture/03_architecture.md)** - Detailed architecture
- **[04_BRANCH_STRATEGY.md](architecture/04_BRANCH_STRATEGY.md)** - Git branching strategy
- **[05_IMPROVEMENTS_SUMMARY.md](architecture/05_IMPROVEMENTS_SUMMARY.md)** - Phase 5 improvements

### Technical Documentation
- **[10_DEVELOPMENT.md](technical/10_DEVELOPMENT.md)** - Development setup
- **[11_FRONTEND.md](technical/11_FRONTEND.md)** - Frontend documentation
- **[12_EMBEDDING_SETUP.md](technical/12_EMBEDDING_SETUP.md)** - Embedding model setup
- **[20_API.md](technical/20_API.md)** - API documentation
- **[21_RAG_GUIDE.md](technical/21_RAG_GUIDE.md)** - RAG pipeline guide
- **[22_QURAN_GUIDE.md](technical/22_QURAN_GUIDE.md)** - Quran module guide
- **[23_DEPLOYMENT.md](technical/23_DEPLOYMENT.md)** - Deployment guide

### Reports
- **[30_FINAL_PROJECT_SUMMARY.md](reports/30_FINAL_PROJECT_SUMMARY.md)** - Project summary
- **[31_FIX_SUMMARY.md](reports/31_FIX_SUMMARY.md)** - Fixes summary
- **[32_TEST_RESULTS.md](reports/32_TEST_RESULTS.md)** - Test results
- **[33_COMPREHENSIVE_TEST_RESULTS.md](reports/33_COMPREHENSIVE_TEST_RESULTS.md)** - Comprehensive tests
- **[34_100_PERCENT_COMPLETE.md](reports/34_100_PERCENT_COMPLETE.md)** - 100% completion report
- **[35_CODE_REVIEW_FULL.md](reports/35_CODE_REVIEW_FULL.md)** - Full code review
- **[36_PHASE_5_IMPROVEMENTS.md](reports/36_PHASE_5_IMPROVEMENTS.md)** - Phase 5 improvements

### Reference
- **[40_project_plan.md](reference/40_project_plan.md)** - Project plan
- **[41_COMPREHENSIVE_PROJECT_EXPLANATION.md](reference/41_COMPREHENSIVE_PROJECT_EXPLANATION.md)** - Full project explanation
- **[42_DOCUMENTATION_REVIEW.md](reference/42_DOCUMENTATION_REVIEW.md)** - Documentation review

### Guides
- **[01_RUN.md](guides/01_RUN.md)** - How to run the application
- **[02_SETUP_COMPLETE.md](guides/02_SETUP_COMPLETE.md)** - Complete setup guide
- **[03_WINDOWS_GUIDE.md](guides/03_WINDOWS_GUIDE.md)** - Windows setup guide

---

## 🔑 Quick Links

### API Endpoints
| Endpoint | Description |
|----------|-------------|
| `POST /api/v1/query` | Main query endpoint |
| `GET /api/v1/quran/surahs` | List all surahs |
| `GET /api/v1/quran/ayah/{surah}:{ayah}` | Get specific ayah |
| `POST /api/v1/quran/search` | Search verses |
| `POST /api/v1/quran/analytics` | Quran analytics (NL2SQL) |
| `POST /api/v1/tools/zakat` | Calculate Zakat |
| `POST /api/v1/tools/inheritance` | Calculate inheritance |
| `GET /api/v1/tools/prayer-times` | Get prayer times |
| `GET /api/v1/tools/hijri` | Get Hijri date |
| `GET /api/v1/tools/duas` | Get duas and adhkar |

### Intent Classification
| Intent | Description | Handler |
|--------|-------------|---------|
| `fiqh` | Islamic jurisprudence | FiqhAgent (RAG) |
| `quran` | Quranic queries | QuranAgent |
| `islamic_knowledge` | General Islamic knowledge | GeneralIslamicAgent |
| `zakat` | Zakat calculation | ZakatCalculator |
| `inheritance` | Inheritance distribution | InheritanceCalculator |
| `prayer_times` | Prayer times | PrayerTimesTool |
| `hijri_calendar` | Hijri dates | HijriCalendarTool |
| `dua` | Supplications | DuaRetrievalTool |
| `greeting` | Greetings | ChatbotAgent |

---

## 🚀 Quick Start

```bash
# Clone and setup
git clone https://github.com/Kandil7/Athar.git
cd Athar

# Install dependencies
poetry install

# Run the API
python -m uvicorn src.api.main:app --reload

# Access API docs
# Open http://localhost:8000/docs
```

---

## 📖 Documentation Sections

### 1. Project Overview
Athar is an Islamic QA System based on the **Fanar-Sadiq Multi-Agent Architecture** that provides:
- Intent classification with 9+ intent types
- Retrieval-Augmented Generation (RAG) for grounded answers
- Deterministic calculators for Zakat and Inheritance
- Quran analytics with NL2SQL
- Multi-language support (Arabic & English)

### 2. Architecture
The system uses a three-tier architecture:
- **API Layer**: FastAPI with routes for queries, tools, and Quran
- **Orchestration Layer**: HybridQueryClassifier + ResponseOrchestrator
- **Agent Layer**: Specialized agents (FiqhAgent, QuranAgent, etc.)

### 3. RAG Pipeline
1. Query embedding with Qwen3-Embedding-0.6B
2. Hybrid search (semantic + keyword)
3. Answer generation with GPT-4o-mini or Groq

### 4. Security Features
- Rate limiting (60 req/min)
- API key authentication
- Input validation
- Security headers

---

## 📞 Support

For questions or issues, please check the documentation or open an issue on GitHub.

---

*Last updated: April 2026*
*Version: 0.5.0*
