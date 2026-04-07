# Athar Documentation

Complete documentation for the Athar Islamic QA System.

---

## 📁 Documentation Structure

### 🚀 Getting Started (Start Here)

| Document | Purpose | When to Read |
|----------|---------|--------------|
| **[index.md](index.md)** | This file - documentation index | Always |
| **[../architecture/01_ARCHITECTURE_OVERVIEW.md](../architecture/01_ARCHITECTURE_OVERVIEW.md)** | System architecture overview | **First** |
| **[../guides/running.md](../guides/running.md)** | Quick start guide | First time |

---

### 🏗️ Architecture (System Design)

| Document | Purpose | Priority |
|----------|---------|----------|
| **[../architecture/01_ARCHITECTURE_OVERVIEW.md](../architecture/01_ARCHITECTURE_OVERVIEW.md)** | Complete system architecture with diagrams | ⭐ **Read First** |
| **[../architecture/technical-architecture.md](../architecture/technical-architecture.md)** | Technical architecture details | Secondary |
| **[../architecture/branch-strategy.md](../architecture/branch-strategy.md)** | Git workflow & version control | For contributors |

---

### 📘 User Guides (How to Use)

| Document | Purpose | Audience |
|----------|---------|----------|
| **[../guides/running.md](../guides/running.md)** | Quick start guide | All users |
| **[../guides/setup.md](../guides/setup.md)** | Complete setup from scratch | First-time users |
| **[../guides/windows.md](../guides/windows.md)** | Windows-specific guide | Windows users |

---

### 🔧 Development (Building)

| Document | Purpose | Audience |
|----------|---------|----------|
| **[../development/index.md](../development/index.md)** | Developer guide | Developers |
| **[../development/frontend.md](../development/frontend.md)** | Frontend guide | Frontend developers |
| **[../development/embeddings.md](../development/embeddings.md)** | Embedding model setup | ML engineers |

---

### ⚙️ API & Core Features

| Document | Purpose | Audience |
|----------|---------|----------|
| **[../api/reference.md](../api/reference.md)** | Complete API reference | Developers, API users |
| **[../core-features/rag.md](../core-features/rag.md)** | RAG pipeline guide | ML engineers |
| **[../core-features/quran.md](../core-features/quran.md)** | Quran pipeline guide | Developers |
| **[../deployment/index.md](../deployment/index.md)** | Production deployment | DevOps |

---

### 📊 Project Reports (Status & History)

| Document | Purpose | When to Read |
|----------|---------|--------------|
| **[../reports/30_FINAL_PROJECT_SUMMARY.md](../reports/30_FINAL_PROJECT_SUMMARY.md)** | Project completion status | Project overview |
| **[../reports/31_FIX_SUMMARY.md](../reports/31_FIX_SUMMARY.md)** | Fixes applied | Troubleshooting |
| **[../reports/32_TEST_RESULTS.md](../reports/32_TEST_RESULTS.md)** | Initial test results | Quick overview |
| **[../reports/33_COMPREHENSIVE_TEST_RESULTS.md](../reports/33_COMPREHENSIVE_TEST_RESULTS.md)** | Detailed test analysis | Deep dive |
| **[../reports/34_100_PERCENT_COMPLETE.md](../reports/34_100_PERCENT_COMPLETE.md)** | What's needed for 100% | Future planning |

---

### 📋 Reference & Research

| Document | Purpose |
|----------|---------|
| **[../reference/40_project_plan.md](../reference/40_project_plan.md)** | Original project plan |
| **[../reference/41_COMPREHENSIVE_PROJECT_EXPLANATION.md](../reference/41_COMPREHENSIVE_PROJECT_EXPLANATION.md)** | Complete project explanation |
| **Fanar-Sadiq Paper.pdf** | Research paper (architecture foundation) |

---

## 🎯 Quick Navigation

### I want to...

| Goal | Read This | Priority |
|------|-----------|----------|
| **Start using Athar** | [../guides/running.md](../guides/running.md) | ⭐ First |
| **Understand the system** | [../architecture/01_ARCHITECTURE_OVERVIEW.md](../architecture/01_ARCHITECTURE_OVERVIEW.md) | ⭐ First |
| **Use the API** | [../api/reference.md](../api/reference.md) | Important |
| **Deploy to production** | [../deployment/index.md](../deployment/index.md) | Important |
| **Develop features** | [../development/index.md](../development/index.md) | Important |
| **Understand RAG** | [../core-features/rag.md](../core-features/rag.md) | ML/AI |
| **Work with Quran** | [../core-features/quran.md](../core-features/quran.md) | Quran work |
| **Set up from scratch** | [../guides/setup.md](../guides/setup.md) | New setup |

---

## 🔗 Recommended Reading Paths

### Path A: For Users (Quick Start)
```
getting-started/index → guides/running → architecture/01_ARCHITECTURE_OVERVIEW
```

### Path B: For Developers (Understand & Build)
```
architecture/01_ARCHITECTURE_OVERVIEW → development/index → api/reference
```

### Path C: For Architects (System Design)
```
architecture/01_ARCHITECTURE_OVERVIEW → architecture/technical-architecture → Fanar-Sadiq Paper.pdf
```

### Path D: For DevOps (Deployment)
```
architecture/01_ARCHITECTURE_OVERVIEW → deployment/index → api/reference
```

### Path E: For ML Engineers (RAG Pipeline)
```
architecture/01_ARCHITECTURE_OVERVIEW → core-features/rag → development/embeddings
```

---

## 📊 Documentation Statistics

| Category | Count |
|----------|-------|
| **Getting Started** | 1 |
| **Architecture** | 3 |
| **User Guides** | 3 |
| **Development** | 3 |
| **API** | 3 |
| **Core Features** | 2 |
| **Deployment** | 1 |
| **Reports** | 5 |
| **Reference** | 2 |
| **Research** | 1 |
| **TOTAL** | **24** |

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

**Need help?** Run `build.bat help` or check the main [README.md](../README.md)

---

*Last Updated: April 7, 2026 | Version: 0.5.0*
