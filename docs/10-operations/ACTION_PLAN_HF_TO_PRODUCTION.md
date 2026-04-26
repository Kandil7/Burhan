# 🚀 Burhan - Complete Action Plan: From Upload to Production

**Created:** April 8, 2026  
**HF Repo:** https://huggingface.co/datasets/Kandil7/Burhan-Datasets  
**Status:** Ready for upload + embedding + deployment

---

## 📋 PHASE 1: Complete HuggingFace Upload (30-60 minutes)

### Step 1: Run Upload Script

```bash
# From project root
poetry run python scripts/upload_to_huggingface_complete.py --upload --compress --resume
```

### Step 2: Monitor Progress

```bash
# Check progress (in another terminal)
poetry run python scripts/upload_to_huggingface_complete.py --progress
```

### Step 3: Verify Upload

```bash
poetry run python scripts/upload_to_huggingface_complete.py --verify
```

### Expected Output
```
✅ seerah_passages (compressed)
✅ usul_fiqh (compressed)
✅ spirituality_passages (compressed)
✅ aqeedah_passages (compressed)
✅ arabic_language_passages (compressed)
✅ quran_tafsir (compressed)
✅ islamic_history_passages (compressed)
✅ general_islamic (compressed)
✅ fiqh_passages (compressed)
✅ hadith_passages (compressed)
✅ master_catalog.json
✅ category_mapping.json
✅ author_catalog.json
```

---

## 📋 PHASE 2: Embed Collections on Colab GPU (13 hours free / 4 hours paid)

### Step 1: Open Colab Notebook

1. Go to: https://colab.research.google.com
2. Upload: `notebooks/02_upload_and_embed.ipynb`
3. Set runtime: **Runtime → Change runtime type → GPU (T4)**

### Step 2: Run Notebook Cells

Execute cells in order:
1. ✅ Verify GPU
2. ✅ Install dependencies
3. ✅ Mount Google Drive
4. ✅ Download from HuggingFace (15-30 min)
5. ✅ Configure settings
6. ✅ Load BGE-M3 model (3 min)
7. ✅ **Embed all collections** (6-13 hours) ← MAIN STEP
8. ✅ Check progress
9. ✅ Upload to Qdrant (1-2 hours)
10. ✅ Verify upload
11. ✅ Test retrieval
12. ✅ Final summary

### Step 3: Wait for Completion

- **Free T4:** ~13 hours total
- **Paid A100:** ~3-4 hours total

### Expected Output
```
✅ TOTAL VECTORS: 7,050,000+
✅ 10 collections in Qdrant
✅ All metadata preserved
```

---

## 📋 PHASE 3: Test All 13 Agents (1 day)

### Step 1: Update Configuration

Add Qdrant connection to `.env`:
```bash
QDRANT_URL=http://your-qdrant:6333
QDRANT_API_KEY=your-key
```

### Step 2: Run Agent Tests

```bash
# Test all agents
poetry run pytest tests/ -v

# Test specific agents
poetry run pytest tests/test_fiqh_agent.py -v
poetry run pytest tests/test_hadith_agent.py -v
```

### Step 3: Manual Testing

```bash
# Start API server
python -m uvicorn src.api.main:app --host 0.0.0.0 --port 8002

# Test queries
curl -X POST http://localhost:8002/api/v1/query \
  -H "Content-Type: application/json" \
  -d '{"query": "ما حكم الصلاة؟"}'
```

---

## 📋 PHASE 4: Migrate Remaining Agents (1 day)

### Agents to Migrate to BaseRAGAgent

1. HadithAgent
2. TafsirAgent
3. AqeedahAgent
4. IslamicHistoryAgent
5. ArabicLanguageAgent
6. UsulFiqhAgent

### Migration Pattern

```python
# Before (200 lines):
class HadithAgent(BaseAgent):
    def __init__(self):
        self.embedding_model = ...
        self.vector_store = ...
        # ... lots of duplication

    async def execute(self, input):
        # ... retrieval logic
        # ... generation logic

# After (30 lines):
class HadithAgent(BaseRAGAgent):
    COLLECTION = "hadith_passages"
    TOP_K_RETRIEVAL = 15
    SCORE_THRESHOLD = 0.65
```

---

## 📋 PHASE 5: Deploy to Production (1 day)

### Step 1: Create Production Docker Compose

```yaml
# docker-compose.prod.yml
version: '3.8'
services:
  api:
    build: .
    ports: ["8000:8000"]
    env_file: .env
    depends_on: [qdrant, redis]
    restart: unless-stopped

  qdrant:
    image: qdrant/qdrant:latest
    volumes:
      - qdrant_data:/qdrant/storage
    ports: ["6333:6333"]
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    ports: ["6379:6379"]
    restart: unless-stopped

volumes:
  qdrant_data:
```

### Step 2: Deploy

```bash
# Build and start
docker compose -f docker-compose.prod.yml up -d

# Check status
docker compose -f docker-compose.prod.yml ps

# View logs
docker compose -f docker-compose.prod.yml logs -f api
```

### Step 3: Verify Production

```bash
# Health check
curl http://your-server:8000/health

# Test query
curl -X POST http://your-server:8000/api/v1/query \
  -H "Content-Type: application/json" \
  -d '{"query": "ما حكم الصلاة؟"}'
```

---

## 📊 Timeline Summary

| Phase | Task | Time | Status |
|-------|------|------|--------|
| 1 | HuggingFace Upload | 30-60 min | ⏳ Ready |
| 2 | Colab GPU Embedding | 13 hrs (free) | ⏳ Ready |
| 3 | Test Agents | 1 day | ⏳ Pending |
| 4 | Migrate Agents | 1 day | ⏳ Pending |
| 5 | Deploy to Production | 1 day | ⏳ Pending |

**Total Time to Production:** ~2 weeks (including embedding time)

---

## 💰 Cost Estimation

| Resource | Free Option | Paid Option |
|----------|-------------|-------------|
| Colab GPU (T4) | FREE | - |
| Colab GPU (A100) | - | ~$10-15 |
| Qdrant (self-hosted) | FREE | ~$50/month |
| Qdrant Cloud | 1 GB free | ~$50/month |
| API Hosting | Local | ~$20-100/month |
| **Total** | **FREE** | **~$80-165/month** |

---

## ⚠️ Critical Path

The critical path (longest sequential tasks) is:

```
HuggingFace Upload (1 hr)
    ↓
Colab GPU Embedding (13 hrs) ← BOTTLENECK
    ↓
Qdrant Upload (2 hrs)
    ↓
Agent Testing (1 day)
    ↓
Production Deployment (1 day)
```

**Minimum time to production: ~17 hours + 2 days**

---

## 🎯 Immediate Next Steps (Today)

1. ✅ **Run upload script:**
   ```bash
   poetry run python scripts/upload_to_huggingface_complete.py --upload --compress --resume
   ```

2. ✅ **Start Colab notebook:**
   - Upload `notebooks/02_upload_and_embed.ipynb` to Colab
   - Set GPU runtime
   - Start embedding

3. ✅ **Monitor progress:**
   - Check upload progress every 15 min
   - Check embedding progress every hour

---

**Ready to execute! Just run the upload script and start Colab.** 🚀
