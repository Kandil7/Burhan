# 🚀 Burhan Islamic QA System - COMPLETE SETUP GUIDE

## ✅ DATA INGESTION COMPLETE!

### 📊 Processed Data Summary

| Data Source | Items Processed | Chunks Generated | Size |
|-------------|----------------|------------------|------|
| **Islamic Books** | 100 books | 114,316 chunks | 127.08 MB |
| **Hadith (Sanadset)** | 1,000 hadith | 1,000 chunks | 0.96 MB |
| **TOTAL** | - | **115,316 chunks** | **128.03 MB** |

### 📚 Categories Processed

| Category | Chunks |
|----------|--------|
| كتب عامة (General Books) | 86,346 |
| التاريخ (History) | 8,075 |
| علوم الحديث (Hadith Sciences) | 5,631 |
| الأدب (Literature) | 5,213 |
| الفقه العام (General Fiqh) | 3,979 |
| كتب اللغة (Language Books) | 2,826 |
| العقيدة (Creed/Aqeedah) | 939 |
| التفسير (Tafsir) | 832 |
| السيرة النبوية (Prophet's Seerah) | 399 |

### 🗂️ Data Files Created

All processed data is saved in:
```
K:\business\projects_v2\Burhan\data\processed\
├── islamic_books_chunks.json    (127.08 MB)
├── hadith_chunks.json           (0.96 MB)
└── all_chunks.json              (128.03 MB - Combined)
```

---

## 🏗️ Current Infrastructure Status

### ✅ Running Services

```
Burhan-postgres  ✓ healthy (port 5432)
Burhan-redis     ✓ healthy (port 6379)
Burhan-qdrant    ✓ healthy (port 6333)
```

### ✅ Database Status

```
✓ Migrations completed
✓ Quran tables created
✓ Ready for data
```

---

## 🚀 HOW TO START THE APPLICATION

### Step 1: Verify Services Are Running

```bash
cd K:\business\projects_v2\Burhan

# Check Docker services
docker compose -f docker/docker-compose.dev.yml ps

# Expected output: All three services should show "healthy"
```

### Step 2: Install Python Dependencies

```bash
# First time only (takes 2-3 minutes)
pip install -e .

# This installs:
# - FastAPI
# - SQLAlchemy
# - Redis client
# - Qdrant client
# - And other dependencies
```

### Step 3: Start the Backend API

```bash
# Start the API server
uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000

# You should see:
# INFO: Uvicorn running on http://0.0.0.0:8000
# INFO: Application startup complete.
```

### Step 4: Test the API

Open a **new terminal** and run:

```bash
python scripts/test_api.py
```

**Or** open your browser and go to:
- **API Health**: http://localhost:8000/health
- **API Docs**: http://localhost:8000/docs (Interactive Swagger UI)
- **ReDoc**: http://localhost:8000/redoc (Alternative docs)

### Step 5: Start Frontend (Optional)

```bash
cd frontend

# Install dependencies (first time only)
npm install

# Start development server
npm run dev

# Open browser: http://localhost:3000
```

---

## 🎯 Test Queries to Try

### Via API (curl)

```bash
# Test 1: Greeting
curl -X POST http://localhost:8000/api/v1/query ^
  -H "Content-Type: application/json" ^
  -d "{\"query\": \"السلام عليكم\", \"language\": \"ar\"}"

# Test 2: Fiqh Question
curl -X POST http://localhost:8000/api/v1/query ^
  -H "Content-Type: application/json" ^
  -d "{\"query\": \"ما حكم صلاة الجمعة؟\", \"language\": \"ar\"}"

# Test 3: Quran Question
curl -X POST http://localhost:8000/api/v1/query ^
  -H "Content-Type: application/json" ^
  -d "{\"query\": \"كم عدد آيات سورة البقرة؟\", \"language\": \"ar\"}"
```

### Via Frontend (Chat UI)

Open http://localhost:3000 and try:
- السلام عليكم
- ما حكم الزكاة؟
- أعطني دعاء السفر
- كم عدد آيات سورة الإخلاص؟

---

## 📊 What's Available Right Now

### ✅ Ready to Use

| Feature | Status | Details |
|---------|--------|---------|
| **Infrastructure** | ✅ Running | PostgreSQL, Redis, Qdrant |
| **Database** | ✅ Ready | Migrations complete, Quran tables created |
| **Data Processed** | ✅ Complete | 115,316 chunks from 100 books + 1,000 hadith |
| **API Endpoints** | ⚠️ Need API start | 19 endpoints ready |
| **Frontend** | ⚠️ Need npm install | Chat UI ready |

### 🔄 Next Steps (Optional Enhancements)

| Task | Time | Description |
|------|------|-------------|
| Generate Embeddings | 15-30 min | Create vector embeddings for RAG |
| Seed Full Quran Data | 10 min | Complete 6,236 ayahs |
| Process More Books | 30-60 min | Process all 8,424 books |
| Ingest More Hadith | 15-30 min | Process more Sanadset data |

---

## 🛑 To Stop Everything

```bash
# Stop Docker services
docker compose -f docker/docker-compose.dev.yml down

# Stop API (Ctrl+C in terminal)

# Stop Frontend (Ctrl+C in terminal)
```

---

## 📝 Common Commands

```bash
# View Docker logs
docker compose -f docker/docker-compose.dev.yml logs -f

# View API logs only
docker compose -f docker/docker-compose.dev.yml logs -f api

# Restart a service
docker compose -f docker/docker-compose.dev.yml restart postgres

# Run tests
make test

# Run linter
make lint
```

---

## 📚 Documentation

| Document | Location |
|----------|----------|
| Main README | `README.md` |
| Quick Start | `RUN.md` |
| Architecture | `docs/ARCHITECTURE.md` |
| API Reference | `docs/API.md` |
| Deployment Guide | `docs/DEPLOYMENT.md` |
| Development Guide | `docs/DEVELOPMENT.md` |
| Frontend Guide | `docs/FRONTEND.md` |
| RAG Guide | `docs/RAG_GUIDE.md` |
| Quran Guide | `docs/QURAN_GUIDE.md` |

---

## 🎉 SUCCESS!

You now have:
- ✅ **115,316 text chunks** from Islamic sources
- ✅ **41 categories** of Islamic knowledge
- ✅ **100 books** processed (from 8,424 available)
- ✅ **1,000 hadith** from Sanadset 368K
- ✅ **Infrastructure running** (PostgreSQL, Redis, Qdrant)
- ✅ **Database ready** with migrations complete
- ✅ **Complete documentation** (9 comprehensive guides)

**Next: Start the API and begin asking Islamic questions!** 🕌✨

---

## 🆘 Troubleshooting

### Port Already in Use

```bash
# Find process using port 8000
netstat -ano | findstr :8000

# Kill the process
taskkill /PID <PID> /F
```

### Docker Services Not Starting

```bash
# Stop everything
docker compose -f docker/docker-compose.dev.yml down

# Remove volumes (WARNING: deletes data)
docker compose -f docker/docker-compose.dev.yml down -v

# Start fresh
docker compose -f docker/docker-compose.dev.yml up -d
```

### API Won't Start

```bash
# Check if dependencies are installed
python -c "import fastapi"

# Reinstall if needed
pip install -e .
```

---

**Ready to run? Execute Step 2 (Install dependencies) and Step 3 (Start API) above!** 🚀
