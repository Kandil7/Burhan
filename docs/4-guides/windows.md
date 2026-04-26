# 🚀 Burhan Islamic QA System - Quick Start Guide (Windows)

## 📋 Batch Scripts Available

We've created easy-to-use batch scripts for Windows. Just double-click to run!

---

## 🎯 Recommended Workflow

### **For First Time Users:**

```
1. install.bat           (Install all dependencies)
2. menu.bat              (Open main menu)
3. Select option 1       (Start application)
```

### **For Returning Users:**

```
1. menu.bat              (Open main menu)
2. Select option 1       (Start application)
```

---

## 📚 Script Reference

### 🎮 `menu.bat` (Start Here!)
**Purpose:** Main menu with all options

**What it does:**
- Shows all available options
- Quick access to all features
- Status overview

**Usage:**
```
Double-click: menu.bat
```

---

### 🚀 `start.bat`
**Purpose:** Start the full application (API + Frontend)

**What it does:**
- Checks Docker services
- Installs dependencies (if needed)
- Starts Backend API (port 8000)
- Optionally starts Frontend (port 3000)
- Opens API docs in browser

**Usage:**
```
Double-click: start.bat
```

**After running:**
- API: http://localhost:8000
- API Docs: http://localhost:8000/docs
- Frontend: http://localhost:3000 (if selected)

---

### 🏃 `start.bat` → Option 8: Quick Start
**Purpose:** Start only the Backend API (no frontend)

**What it does:**
- Checks Docker services
- Starts Backend API only
- Opens API docs

**Usage:**
```
Run menu.bat
Select option 8
```

---

### 🧪 `test.bat`
**Purpose:** Test all API endpoints

**What it does:**
- Tests health endpoint
- Tests query endpoint
- Tests zakat calculator
- Tests prayer times
- Tests Quran endpoints

**Usage:**
```
Double-click: test.bat
```

**Note:** API must be running first!

---

### 📥 `ingest_data.bat`
**Purpose:** Process more Islamic books and hadith

**What it does:**
- Processes books from datasets/data/extracted_books/
- Ingests hadith from Sanadset
- Creates chunks for RAG pipeline
- Saves to data/processed/

**Options:**
- Quick: 50 books + 500 hadith (~2 min)
- Recommended: 100 books + 1000 hadith (~5 min)
- Full: 500 books + 5000 hadith (~20 min)

**Usage:**
```
Double-click: ingest_data.bat
```

---

### ⚙️ `install.bat`
**Purpose:** Install all dependencies

**What it does:**
- Checks Python installation
- Installs backend dependencies
- Checks Node.js installation
- Installs frontend dependencies

**Usage:**
```
Double-click: install.bat
```

**Note:** Only needed once on first setup!

---

### 🛑 `stop.bat`
**Purpose:** Stop all Docker services

**What it does:**
- Stops PostgreSQL, Redis, Qdrant
- Frees up system resources

**Usage:**
```
Double-click: stop.bat
```

---

### 📊 `process_and_embed.bat`
**Purpose:** Process books and generate embeddings

**What it does:**
- Chunks books into passages
- Generates embeddings with Qwen3-Embedding
- Stores in Qdrant vector database

**Usage:**
```
Double-click: process_and_embed.bat
```

**Note:** Requires GPU for fast processing (CPU works but slower)

---

## 🎯 Common Tasks

### Task 1: First Time Setup
```
1. install.bat
2. menu.bat → Option 1 (Start Application)
3. Wait for API to start
4. Open: http://localhost:8000/docs
```

### Task 2: Daily Use
```
1. menu.bat → Option 1 (Start Application)
2. Use the application
3. menu.bat → Option 6 (Stop Services) when done
```

### Task 3: Test Everything
```
1. menu.bat → Option 1 (Start Application)
2. menu.bat → Option 2 (Test API)
```

### Task 4: Add More Data
```
1. menu.bat → Option 3 (Ingest Data)
2. Choose amount (50/100/500 books)
3. Wait for processing
```

---

## ⚠️ Troubleshooting

### Issue: "Docker not found"

**Solution:**
- Install Docker Desktop from https://www.docker.com/products/docker-desktop
- Make sure Docker is running (check system tray)

---

### Issue: "Port already in use"

**Solution:**
```bash
# Find what's using port 8000
netstat -ano | findstr :8000

# Kill the process
taskkill /PID <PID> /F
```

---

### Issue: "Python not found"

**Solution:**
- Install Python 3.12+ from https://www.python.org/downloads/
- Make sure to check "Add Python to PATH" during installation

---

### Issue: API won't start

**Solution:**
```
1. Run: install.bat (reinstall dependencies)
2. Check Docker: menu.bat → Option 5
3. Check logs: Start API manually and watch for errors
```

---

## 📊 What Each Port Does

| Port | Service | Purpose |
|------|---------|---------|
| **8000** | Backend API | Main API server |
| **3000** | Frontend | Chat UI (Next.js) |
| **5432** | PostgreSQL | Database |
| **6379** | Redis | Cache & sessions |
| **6333** | Qdrant | Vector database |

---

## 🎓 Learning Resources

| Resource | Location |
|----------|----------|
| Main README | `README.md` |
| Setup Guide | `SETUP_COMPLETE.md` |
| Architecture | `docs/ARCHITECTURE.md` |
| API Reference | `docs/API.md` |
| API Docs (Live) | http://localhost:8000/docs |

---

## 🎉 Quick Commands Reference

```bash
# Start everything
menu.bat → Option 1

# Test API
test.bat

# Add more data
ingest_data.bat

# Stop everything
stop.bat

# Check status
menu.bat → Option 5

# Install dependencies
install.bat
```

---

**Ready to go? Double-click `menu.bat` to get started!** 🕌✨
