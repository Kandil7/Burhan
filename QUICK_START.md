# 🚀 Quick Start Guide - Athar Islamic QA System

**Last Updated:** April 12, 2026

---

## ⚡ Automatic Start (Recommended)

### Option 1: Start Everything

**Double-click:** `start-athar.bat`

This will:
1. ✅ Check Docker Desktop is running
2. ✅ Start PostgreSQL, Qdrant, Redis
3. ✅ Wait for services to initialize
4. ✅ Run database migrations
5. ✅ Start API server on port 8002

**Then open:** http://localhost:8002/docs

---

### Option 2: Download Embeddings to Qdrant

**Double-click:** `download-embeddings-to-qdrant.bat`

This will:
1. ✅ Download 685 embedding files from HuggingFace (~20-30 GB)
2. ✅ Upload 5.7M vectors to Qdrant
3. ✅ Verify all 10 collections

**Time:** 30-60 minutes (depends on internet speed)

---

### Option 3: Stop Everything

**Double-click:** `stop-athar.bat`

This will:
- ✅ Stop all Docker containers
- ✅ Free up system resources

---

## 📋 Manual Steps

### Prerequisites

1. **Docker Desktop** must be running
   - Windows: Search "Docker Desktop" → Launch
   - Wait for green whale icon in system tray

2. **HuggingFace Token** in `.env`
   ```
   HF_TOKEN=hf_your_token_here
   ```

3. **Groq API Key** in `.env` (for LLM queries)
   ```
   GROQ_API_KEY=gsk_your_key_here
   ```
   Get free key: https://console.groq.com/

---

### Step 1: Start Infrastructure

```bash
# Start PostgreSQL, Qdrant, Redis
docker compose -f docker/docker-compose.dev.yml up -d postgres redis qdrant

# Wait 30 seconds
timeout /t 30

# Verify
docker compose -f docker/docker-compose.dev.yml ps
```

**Expected:**
```
NAME                STATUS                    PORTS
athar-postgres      Up (healthy)              0.0.0.0:5432->5432/tcp
athar-qdrant        Up (healthy)              0.0.0.0:6333->6333/tcp
athar-redis         Up                        0.0.0.0:6379->6379/tcp
```

---

### Step 2: Download Embeddings to Qdrant

```bash
# Run the download and upload script
poetry run python scripts/download_embeddings_and_upload_qdrant.py
```

**This will:**
- Download 685 files from `Kandil7/Athar-Embeddings`
- Upload 5.7M vectors to Qdrant
- Create 10 collections
- Verify everything

**Time:** 30-60 minutes

---

### Step 3: Start API Server

```bash
# Start on port 8002
python -m uvicorn src.api.main:app --host 0.0.0.0 --port 8002 --reload
```

---

### Step 4: Verify

**Browser:**
- API Docs: http://localhost:8002/docs
- Health: http://localhost:8002/health

**Command line:**
```bash
curl http://localhost:8002/health
```

**Expected:**
```json
{
  "status": "healthy",
  "timestamp": "2026-04-12T..."
}
```

---

## 🧪 Test the System

### Test 1: Health Check

```bash
curl http://localhost:8002/health
```

### Test 2: Query Fiqh Agent

```bash
curl -X POST http://localhost:8002/api/v1/query ^
  -H "Content-Type: application/json" ^
  -d "{\"query\": \"ما حكم صلاة الجماعة؟\"}"
```

### Test 3: Zakat Calculator

```bash
curl -X POST http://localhost:8002/api/v1/tools/zakat ^
  -H "Content-Type: application/json" ^
  -d "{\"wealth\": 10000, \"nisab\": 5000}"
```

### Test 4: Qdrant Collections

```bash
curl http://localhost:6333/collections
```

**Expected:**
```json
{
  "result": {
    "collections": [
      {"name": "fiqh_passages"},
      {"name": "hadith_passages"},
      ... (10 collections)
    ]
  },
  "status": "ok"
}
```

---

## 📊 What's Ready

| Component | Status | Details |
|-----------|--------|---------|
| **Embeddings** | ✅ COMPLETE | 5.7M vectors on HuggingFace (685 files) |
| **Docker Services** | ⏳ Needs start | PostgreSQL, Qdrant, Redis |
| **Qdrant Collections** | ⏳ Needs upload | Run download script |
| **API Server** | ⏳ Needs start | Port 8002 |
| **LLM Provider** | ⚠️ Needs key | Groq or OpenAI |

---

## ⚠️ Troubleshooting

### Docker Desktop Not Starting

1. Enable WSL2: `wsl --install`
2. Restart computer
3. Launch Docker Desktop
4. Wait for green whale icon

### Port Already in Use

```bash
# Check what's using port 8002
netstat -ano | findstr :8002

# Kill the process (replace PID)
taskkill /PID 12345 /F
```

### Qdrant Connection Refused

```bash
# Check if running
docker ps | findstr qdrant

# Restart
docker compose -f docker/docker-compose.dev.yml restart qdrant
```

### HuggingFace Download Fails

```bash
# Verify token
poetry run python -c "from huggingface_hub import login; login(token='hf_your_token')"

# Test download
poetry run python scripts/verify_embeddings_repo.py
```

---

## 🎯 Next Steps After Running

1. ✅ Test all 18 API endpoints: http://localhost:8002/docs
2. ✅ Run test suite: `make test`
3. ✅ Check RAG retrieval with real queries
4. ✅ Monitor Qdrant performance
5. ✅ Deploy to production (optional)

---

## 📞 Support

- **Documentation:** `docs/` directory (60+ files)
- **Issues:** https://github.com/Kandil7/Athar/issues
- **API Docs:** http://localhost:8002/docs
- **HuggingFace:** https://huggingface.co/datasets/Kandil7/Athar-Datasets

---

**Ready to run!** 🚀
