# ⚡ Athar Quick Reference Card

## 🚀 Most Common Commands

### Start Working
```bash
build.bat start           # Start everything (API + Frontend)
build.bat start:api       # Start API only
build.bat stop            # Stop everything
```

### First Time Setup
```bash
build.bat setup           # Complete setup (install + data + docker)
```

### Testing
```bash
build.bat test            # Run all tests
build.bat test:api        # Test API endpoints only
build.bat test:unit       # Run Python unit tests
```

### Data Management
```bash
build.bat data:ingest     # Process more books/hadith
build.bat data:embed      # Generate embeddings
build.bat data:status     # View data statistics
build.bat data:quran      # Seed Quran database
```

### Database
```bash
build.bat db:migrate      # Run migrations
build.bat db:shell        # Open PostgreSQL shell
build.bat db:backup       # Backup database
```

### Maintenance
```bash
build.bat status          # Check all services
build.bat logs            # View all logs
build.bat logs api        # View API logs only
build.bat clean           # Clean build artifacts
build.bat reset           # Full reset (WARNING: deletes data)
build.bat docker:prune    # Clean Docker resources
```

---

## 📱 Quick Access URLs

| Service | URL |
|---------|-----|
| **API Docs** | http://localhost:8000/docs |
| **ReDoc** | http://localhost:8000/redoc |
| **Frontend** | http://localhost:3000 |
| **Health Check** | http://localhost:8000/health |

---

## 🎯 Common Workflows

### Daily Use
```
1. build.bat start
2. Work with application
3. build.bat stop (when done)
```

### Add More Data
```
1. build.bat data:ingest
2. Choose amount (50/100/500 books)
3. Wait for processing
```

### Check Everything
```
build.bat status          # Service status
build.bat test            # Run tests
build.bat data:status     # Data statistics
```

### Troubleshooting
```
build.bat logs api        # View API errors
build.bat stop            # Stop everything
build.bat start           # Start fresh
```

---

## 📂 Important Files & Folders

| Path | Purpose |
|------|---------|
| `build.bat` | Main command system |
| `scripts/cli.py` | Python CLI alternative |
| `.env` | Environment variables |
| `data/processed/` | Processed data chunks |
| `docs/` | Documentation files |
| `tests/` | Test files |

---

## 🆘 Emergency Commands

```bash
# API not responding
build.bat stop
build.bat start:api

# Port in use
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# Clean slate
build.bat reset
build.bat setup

# View errors
build.bat logs api
```

---

## 💡 Pro Tips

1. **Use build.bat for everything** - One command system
2. **Check status first** - `build.bat status` before troubleshooting
3. **Test after changes** - `build.bat test` to verify
4. **Backup before reset** - `build.bat db:backup`
5. **View logs for errors** - `build.bat logs api`

---

**Full documentation:** `README.md` and `docs/` folder  
**Need help?** Run: `build.bat help`
