# 🚀 How to Run Athar Islamic QA System

**Last Updated:** April 12, 2026

---

## ⚡ Quick Start (5 Minutes)

### Prerequisites Check

```bash
# 1. Python 3.12+ ✅
python --version

# 2. Poetry ✅
poetry --version

# 3. Docker Desktop (needs to be running)
docker info

# 4. Port 8002 available
netstat -ano | findstr :8002
```

### Step-by-Step

#### 1. Start Docker Desktop

**IMPORTANT:** Docker Desktop must be running before starting services.

- **Windows:** Search "Docker Desktop" in Start Menu → Launch
- Wait for whale icon in system tray (green = running)
- Verify: `docker ps`

#### 2. Start Infrastructure Services

```bash
# Start PostgreSQL, Qdrant, Redis
docker compose -f docker/docker-compose.dev.yml up -d postgres redis qdrant

# Wait 30 seconds for services to initialize
timeout /t 30

# Verify services running
docker compose -f docker/docker-compose.dev.yml ps
```

**Expected Output:**
```
NAME                STATUS                    PORTS
athar-postgres      Up (healthy)              0.0.0.0:5432->5432/tcp
athar-qdrant        Up (healthy)              0.0.0.0:6333->6333/tcp
athar-redis         Up                        0.0.0.0:6379->6379/tcp
```

#### 3. Run Database Migrations

```bash
# Create Quran tables
make db-migrate
```

#### 4. Start API Server

```bash
# Option A: Using Make (port 8000)
make dev

# Option B: Custom port (recommended for Windows)
python -m uvicorn src.api.main:app --host 0.0.0.0 --port 8002 --reload
```

#### 5. Verify It Works

```bash
# Open browser
http://localhost:8002/docs

# Or test with curl
curl http://localhost:8002/health
```

---

## 🔧 Configuration

### Environment Variables (.env)

Already configured with:
- ✅ PostgreSQL: `localhost:5432`
- ✅ Qdrant: `http://localhost:6333`
- ✅ Redis: `localhost:6379`
- ⚠️ **GROQ_API_KEY:** Needs your key (get from https://console.groq.com/)

### Get Groq API Key (Required for LLM)

1. Go to: https://console.groq.com/
2. Sign up (free tier available)
3. Create API key
4. Add to `.env`:
   ```
   GROQ_API_KEY=gsk_your_key_here
   ```

---

## 📊 Current Status

| Component | Status | Notes |
|-----------|--------|-------|
| **Infrastructure** | ⏳ Needs Docker Desktop | PostgreSQL, Qdrant, Redis |
| **Database** | ⏳ Needs migration | Run `make db-migrate` |
| **Embeddings** | ✅ **COMPLETE** | 5.7M vectors on HuggingFace |
| **LLM Provider** | ⚠️ Needs API key | Groq or OpenAI |
| **API Server** | ⏳ Not running | Port 8002 |
| **Frontend** | ❌ Not built | Optional Next.js |

---

## 🎯 What's Ready vs What's Needed

### ✅ Already Complete

- ✅ 5.7M embeddings on HuggingFace (685 files)
- ✅ 10 collections organized by topic
- ✅ Modal pipeline for embedding
- ✅ 13 specialized agents
- ✅ 5 deterministic tools (zakat, inheritance, etc.)
- ✅ 18 API endpoints
- ✅ Test suite (~91% coverage)

### ⏳ Needs Setup

- ⏳ Docker Desktop running
- ⏳ PostgreSQL service
- ⏳ Qdrant service
- ⏳ Redis service
- ⏳ Groq/OpenAI API key

---

## 🚀 Full Pipeline (Once Services Running)

```bash
# 1. Start services
docker compose -f docker/docker-compose.dev.yml up -d

# 2. Wait for healthy
docker compose -f docker/docker-compose.dev.yml ps

# 3. Run migrations
make db-migrate

# 4. Start API
python -m uvicorn src.api.main:app --host 0.0.0.0 --port 8002 --reload

# 5. Test endpoint
curl http://localhost:8002/health

# 6. Open interactive docs
start http://localhost:8002/docs
```

---

## ⚠️ Troubleshooting

### Docker Desktop Not Starting

**Windows:**
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

### PostgreSQL Connection Refused

```bash
# Check if running
docker ps | findstr postgres

# Restart if needed
docker compose -f docker/docker-compose.dev.yml restart postgres
```

### Qdrant Not Accessible

```bash
# Check Qdrant
curl http://localhost:6333/collections

# Should return: {"result": {"collections": []}, "status": "ok"}
```

---

## 💡 Quick Commands Reference

| Command | Purpose |
|---------|---------|
| `docker compose -f docker/docker-compose.dev.yml up -d` | Start all services |
| `docker compose -f docker/docker-compose.dev.yml down` | Stop all services |
| `docker compose -f docker/docker-compose.dev.yml ps` | Check service status |
| `make db-migrate` | Run database migrations |
| `python -m uvicorn ... --port 8002` | Start API server |
| `make test` | Run tests |
| `make dev` | Development server (port 8000) |

---

**Ready to run!** 🚀
