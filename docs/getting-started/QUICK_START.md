# Athar - Quick Start Guide

**For:** New developers, contributors, and users  
**Time:** 30 minutes to get running

---

## 🎯 What You'll Get

After completing this guide, you'll have:
- ✅ Backend API running on localhost:8000
- ✅ API documentation at localhost:8000/docs
- ✅ Test queries working
- ✅ Understanding of the system

---

## Prerequisites (5 minutes)

### Required Software

1. **Python 3.12+**
   ```bash
   python --version
   ```

2. **Poetry** (dependency manager)
   ```bash
   pip install poetry
   ```

3. **Docker** (for databases)
   ```bash
   docker --version
   ```

### Clone Repository

```bash
git clone https://github.com/Kandil7/Athar.git
cd Athar
```

---

## Step 1: Install Dependencies (5 minutes)

```bash
# Install Python dependencies
poetry install --with dev

# Verify installation
poetry run python -c "import fastapi; print('✓ FastAPI installed')"
```

---

## Step 2: Configure Environment (5 minutes)

```bash
# Copy environment template
cp .env.example .env

# Edit .env with your values
# Required:
# - GROQ_API_KEY or OPENAI_API_KEY
# - HF_TOKEN (for embedding model)
```

**Minimal .env:**
```bash
APP_ENV=development
DEBUG=true
SECRET_KEY=change-this-to-random-string
GROQ_API_KEY=your-groq-key-here
HF_TOKEN=your-huggingface-token
```

---

## Step 3: Start Databases (3 minutes)

```bash
# Start PostgreSQL, Redis, Qdrant
docker compose -f docker/docker-compose.dev.yml up -d

# Verify services running
docker compose -f docker/docker-compose.dev.yml ps
```

**Expected output:**
```
athar-postgres   Up (healthy)
athar-redis      Up (healthy)
athar-qdrant     Up (healthy)
```

---

## Step 4: Start API Server (2 minutes)

```bash
# Start development server
make dev

# Or manually:
poetry run uvicorn src.api.main:app --reload --port 8000
```

**Expected output:**
```
INFO: Uvicorn running on http://0.0.0.0:8000
INFO: Application startup complete.
```

---

## Step 5: Verify Installation (5 minutes)

### 1. Check Health

```bash
curl http://localhost:8000/health
```

**Expected:**
```json
{
  "status": "healthy",
  "version": "0.1.0"
}
```

### 2. Open API Docs

Visit: **http://localhost:8000/docs**

You should see Swagger UI with all endpoints.

### 3. Test Query

```bash
curl -X POST http://localhost:8000/api/v1/query \
  -H "Content-Type: application/json" \
  -d '{"query": "السلام عليكم", "language": "ar"}'
```

**Expected:**
```json
{
  "intent": "greeting",
  "intent_confidence": 0.95,
  "answer": "وعليكم السلام ورحمة الله وبركاته"
}
```

---

## 🚀 Next Steps

### Option 1: Test Tools (No Data Required)

These tools work immediately:

```bash
# Zakat calculator
curl -X POST http://localhost:8000/api/v1/tools/zakat \
  -H "Content-Type: application/json" \
  -d '{"wealth": 10000}'

# Prayer times
curl -X POST http://localhost:8000/api/v1/tools/prayer-times \
  -H "Content-Type: application/json" \
  -d '{"latitude": 21.4225, "longitude": 39.8262}'

# Hijri calendar
curl -X POST http://localhost:8000/api/v1/tools/hijri \
  -H "Content-Type: application/json" \
  -d '{"date": "2026-04-07"}'
```

### Option 2: Seed Data for RAG (1 hour)

```bash
# Seed mini-dataset (1.7 MB, 1,623 docs)
python scripts/seed_mvp_data.py

# Or seed full data (requires Lucene extraction)
python scripts/extract_master_catalog.py
python scripts/extract_all_lucene_pipeline.py
```

### Option 3: Start Frontend (10 minutes)

```bash
cd frontend
npm install
npm run dev

# Open http://localhost:3000
```

---

## 📊 What Works Now?

### ✅ Working Immediately

| Feature | Status | Test |
|---------|--------|------|
| Health check | ✅ | `GET /health` |
| Greeting agent | ✅ | Query: "السلام عليكم" |
| Zakat calculator | ✅ | Tool endpoint |
| Prayer times | ✅ | Tool endpoint |
| Hijri calendar | ✅ | Tool endpoint |
| API documentation | ✅ | `/docs` |

### ⏳ Requires Data Seeding

| Feature | Data Needed | Time |
|---------|-------------|------|
| Fiqh RAG | Fiqh passages | 30 min |
| Hadith RAG | Hadith passages | 30 min |
| Quran lookup | Quran tables | 10 min |
| Tafsir lookup | Tafsir passages | 30 min |
| Aqeedah RAG | Aqeedah passages | 30 min |

---

## 🐛 Troubleshooting

### "Port 8000 already in use"

```bash
# Kill port 8000
./kill_port_8000.ps1

# Or use different port
make dev -- --port 8002
```

### "Database connection failed"

```bash
# Check Docker
docker compose -f docker/docker-compose.dev.yml ps

# Restart services
docker compose -f docker/docker-compose.dev.yml restart
```

### "Module not found"

```bash
# Reinstall dependencies
poetry install --with dev
```

### "LLM API key missing"

```bash
# Check .env file
cat .env | grep GROQ_API_KEY

# Get free key from: https://console.groq.com
```

---

## 📚 Learn More

### Read These Docs

1. `README.md` - Project overview
2. `docs/COMPLETE_DOCUMENTATION.md` - Full docs
3. `docs/FILE_REFERENCE.md` - File tree

### Run Tests

```bash
# Quick test
python scripts/quick_test.py

# Full test suite
make test

# Specific test
poetry run pytest tests/test_router.py -v
```

---

## 🎓 Understanding the System

### Architecture in 30 Seconds

```
User Query
    ↓
Intent Classifier (detects question type)
    ↓
Route to Agent (fiqh, hadith, quran, etc.)
    ↓
Agent Retrieves Documents (from vector DB)
    ↓
LLM Generates Answer (with citations)
    ↓
Response with [C1], [C2] citations
```

### Key Components

1. **Router** - Detects intent (fiqh, greeting, zakat, etc.)
2. **Orchestrator** - Routes query to right agent
3. **Agents** - Specialized handlers per intent
4. **Vector DB** - Stores document embeddings
5. **LLM** - Generates answers from context

---

## ✅ Success Checklist

- [ ] Python 3.12+ installed
- [ ] Poetry installed
- [ ] Repository cloned
- [ ] Dependencies installed (`poetry install`)
- [ ] .env configured
- [ ] Docker services running
- [ ] API server started
- [ ] Health check passing (`/health`)
- [ ] API docs accessible (`/docs`)
- [ ] Test query working

**If all checked: You're ready! 🎉**

---

*Next: Read COMPLETE_DOCUMENTATION.md for advanced features*
