# 📜 Athar Scripts

Automation scripts for managing the Athar Islamic QA System.

## 📁 Directory Structure

```
scripts/
├── windows/              # Windows batch scripts (quick launch)
│   ├── start.bat         # Start application
│   ├── stop.bat          # Stop services
│   ├── test.bat          # Test API
│   ├── install.bat       # Install dependencies
│   ├── menu.bat          # Interactive menu
│   ├── ingest_data.bat   # Process data
│   └── process_and_embed.bat # Generate embeddings
│
├── cli.py                # Python CLI interface
├── complete_ingestion.py # Data ingestion pipeline
├── chunk_books.py        # Book chunking utility
├── generate_embeddings.py # Embedding generation
├── seed_quran_data.py    # Quran database seeder
├── test_api.py           # API test suite
├── import_azkar_db.py    # Azkar-DB importer
├── inspect_db.py         # Database inspector
└── ingest_and_run.py     # All-in-one runner
```

## 🎯 Recommended Usage

### For Windows Users
```
Double-click: scripts\windows\menu.bat
Or use: build.bat (in project root)
```

### For Command Line
```bash
python scripts/cli.py start
python scripts/cli.py test
python scripts/cli.py help
```

### For Build System
```bash
build.bat start
build.bat test
build.bat help
```

## 📚 Documentation

- **Quick Reference:** `docs/QUICK_REFERENCE.md`
- **Architecture:** `docs/ARCHITECTURE_OVERVIEW.md`
- **Windows Guide:** `docs/guides/WINDOWS_GUIDE.md`
- **Setup Guide:** `docs/guides/SETUP_COMPLETE.md`
