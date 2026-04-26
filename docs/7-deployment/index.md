# 🚀 Burhan Deployment Guide

Complete guide for deploying Burhan Islamic QA system to production.

---

## 📋 Table of Contents

- [Prerequisites](#prerequisites)
- [Environment Setup](#environment-setup)
- [Docker Deployment](#docker-deployment)
- [Manual Deployment](#manual-deployment)
- [Database Migrations](#database-migrations)
- [Configuration](#configuration)
- [Monitoring](#monitoring)
- [Troubleshooting](#troubleshooting)

---

## ⚙️ Prerequisites

### Required Software

- **Docker** 20.10+
- **Docker Compose** 2.0+
- **Git** 2.30+

### Required Services

- **PostgreSQL** 16
- **Redis** 7
- **Qdrant** (latest)
- **OpenAI API Key** (for LLM and embeddings)

### Hardware Requirements

| Environment | CPU | RAM | Storage |
|-------------|-----|-----|---------|
| **Development** | 2 cores | 4GB | 20GB |
| **Staging** | 4 cores | 8GB | 50GB |
| **Production** | 8 cores | 32GB | 200GB |

---

## 🔧 Environment Setup

### 1. Clone Repository

```bash
git clone https://github.com/Kandil7/Burhan.git
cd Burhan
```

### 2. Create Environment File

```bash
cp .env.example .env
```

### 3. Configure Environment Variables

Edit `.env` file:

```env
# Application
APP_NAME=Burhan
APP_ENV=production
DEBUG=false
SECRET_KEY=your-super-secret-key-here

# Database
DATABASE_URL=postgresql+asyncpg://Burhan:your_password@postgres:5432/Burhan_db

# Redis
REDIS_URL=redis://:your_redis_password@redis:6379/0

# Qdrant
QDRANT_URL=http://qdrant:6333
QDRANT_API_KEY=your_qdrant_api_key

# LLM
OPENAI_API_KEY=sk-your-openai-key

# CORS
CORS_ORIGINS=https://yourdomain.com
```

---

## 🐳 Docker Deployment

### Development Mode

```bash
# Start all services
docker compose -f docker/docker-compose.dev.yml up -d

# View logs
docker compose -f docker/docker-compose.dev.yml logs -f

# Stop services
docker compose -f docker/docker-compose.dev.yml down
```

### Production Mode

```bash
# 1. Build images
docker compose -f docker/docker-compose.prod.yml build

# 2. Start services
docker compose -f docker/docker-compose.prod.yml up -d

# 3. Verify health
docker compose -f docker/docker-compose.prod.yml ps
```

### Services

| Service | Port | Purpose |
|---------|------|---------|
| **API** | 8000 | FastAPI backend |
| **Frontend** | 3000 | Next.js chat UI |
| **PostgreSQL** | 5432 | Relational database |
| **Redis** | 6379 | Cache and sessions |
| **Qdrant** | 6333 | Vector database |
| **Nginx** | 80, 443 | Reverse proxy |

---

## 📦 Manual Deployment

### 1. Backend Setup

```bash
# Create virtual environment
python -m venv /opt/Burhan/venv
source /opt/Burhan/venv/bin/activate

# Install dependencies
pip install -e "/opt/Burhan[prod]"

# Setup systemd service
sudo nano /etc/systemd/system/Burhan-api.service
```

**Burhan-api.service:**
```ini
[Unit]
Description=Burhan API
After=network.target postgresql.service redis.service

[Service]
Type=simple
User=Burhan
Group=Burhan
WorkingDirectory=/opt/Burhan
Environment=PATH=/opt/Burhan/venv/bin
ExecStart=/opt/Burhan/venv/bin/uvicorn src.api.main:app --host 0.0.0.0 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
```

### 2. Frontend Setup

```bash
cd /opt/Burhan/frontend

# Install dependencies
npm ci

# Build for production
npm run build

# Start production server
npm start
```

### 3. Nginx Configuration

```nginx
server {
    listen 80;
    server_name yourdomain.com;

    # Frontend
    location / {
        proxy_pass http://localhost:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    # API
    location /api/ {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    # Static files
    location /static/ {
        alias /opt/Burhan/frontend/.next/static/;
        expires 1y;
    }
}
```

---

## 🗄️ Database Migrations

### Initial Setup

```bash
# Run migration script
psql -U Burhan -d Burhan_db -f migrations/001_initial_schema.sql
psql -U Burhan -d Burhan_db -f migrations/002_quran_translations_tafsir.sql
```

### Seed Quran Data

```bash
# Option 1: Sample data (4 surahs)
python scripts/seed_quran_data.py --sample

# Option 2: Full data from API
python scripts/seed_quran_data.py --source api
```

### Verify Database

```bash
# Connect to database
psql -U Burhan -d Burhan_db

# Check tables
\dt

# Count ayahs
SELECT COUNT(*) FROM ayahs;
-- Expected: 6236

# Count surahs
SELECT COUNT(*) FROM surahs;
-- Expected: 114
```

---

## ⚙️ Configuration

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `APP_NAME` | No | Burhan | Application name |
| `APP_ENV` | Yes | development | Environment (development/production) |
| `DEBUG` | Yes | false | Debug mode |
| `DATABASE_URL` | Yes | - | PostgreSQL connection string |
| `REDIS_URL` | Yes | - | Redis connection string |
| `QDRANT_URL` | Yes | - | Qdrant server URL |
| `OPENAI_API_KEY` | Yes | - | OpenAI API key |
| `CORS_ORIGINS` | Yes | - | Allowed origins (comma-separated) |

### Qdrant Collections

Collections are auto-created on first use:

- `fiqh_passages` - Fiqh books and fatwas
- `hadith_passages` - Hadith collections
- `quran_tafsir` - Tafsir passages
- `general_islamic` - General knowledge
- `duas_adhkar` - Duas collection

---

## 📊 Monitoring

### Health Checks

```bash
# API health
curl http://localhost:8000/health

# Database health
docker exec Burhan-postgres pg_isready -U Burhan

# Redis health
docker exec Burhan-redis redis-cli ping

# Qdrant health
curl http://localhost:6333/healthz
```

### Logs

```bash
# View all logs
docker compose logs -f

# View specific service
docker compose logs -f api
docker compose logs -f frontend
```

### Metrics

**Phase 6+ (Planned):**
- Prometheus metrics endpoint: `/metrics`
- Grafana dashboard
- Error tracking (Sentry)

---

## 🔧 Troubleshooting

### Common Issues

**1. Database Connection Error**

```
Error: Cannot connect to database
```

**Solution:**
```bash
# Check if PostgreSQL is running
docker ps | grep postgres

# Check connection string
echo $DATABASE_URL

# Test connection
docker exec -it Burhan-postgres psql -U Burhan -d Burhan_db -c "SELECT 1;"
```

---

**2. Redis Connection Error**

```
Error: Cannot connect to Redis
```

**Solution:**
```bash
# Check if Redis is running
docker ps | grep redis

# Test connection
docker exec -it Burhan-redis redis-cli ping
```

---

**3. Qdrant Collection Not Found**

```
Error: Collection 'fiqh_passages' not found
```

**Solution:**
Collections are auto-created on first API call. Call any RAG endpoint to trigger creation.

---

**4. CORS Error**

```
Error: CORS policy blocked request
```

**Solution:**
Update `CORS_ORIGINS` in `.env`:
```env
CORS_ORIGINS=https://yourdomain.com,http://localhost:3000
```

---

**5. OpenAI API Error**

```
Error: Invalid API key
```

**Solution:**
Verify OpenAI API key in `.env`:
```bash
curl https://api.openai.com/v1/models \
  -H "Authorization: Bearer $OPENAI_API_KEY"
```

---

### Performance Tuning

**PostgreSQL:**
```sql
-- Increase shared buffers
ALTER SYSTEM SET shared_buffers = '2GB';

-- Increase work memory
ALTER SYSTEM SET work_mem = '64MB';

-- Reload configuration
SELECT pg_reload_conf();
```

**Qdrant:**
```yaml
# docker-compose.yml
qdrant:
  environment:
    QDRANT__STORAGE__PERFORMANCE__OPTIMIZER_CPU_BUDGET: 8
    QDRANT__STORAGE__PERFORMANCE__MAX_SEARCH_THREADS: 4
```

---

## 🚀 Deployment Checklist

### Pre-Deployment

- [ ] All tests passing (`make test`)
- [ ] No linting errors (`make lint`)
- [ ] Environment variables configured
- [ ] Database migrations ready
- [ ] Docker images built
- [ ] SSL certificates obtained

### Deployment

- [ ] Backup production database
- [ ] Pull latest code
- [ ] Run migrations
- [ ] Rebuild Docker images
- [ ] Restart services
- [ ] Verify health checks
- [ ] Test key endpoints

### Post-Deployment

- [ ] Monitor error logs
- [ ] Check response times
- [ ] Verify database connectivity
- [ ] Test chat interface
- [ ] Review monitoring dashboards

---

<div align="center">

**Deployment Version:** 1.0  
**Last Updated:** Phase 5 Complete  
**Status:** Production-Ready

</div>
