# Lucene Extraction - Complete Guide

## ✅ STATUS: FULLY WORKING

As of April 7, 2026 - Lucene extraction pipeline is production-ready!

---

## 🚀 Quick Start

### Test Mode (15 minutes)

Extract small samples from 3 indexes:

```bash
python scripts/extract_all_lucene_pipeline.py --quick
```

**Extracts:**
- Esnad: 1,000 hadith chains
- Author: 1,000 biographies
- Book: 1,000 book docs

**Time:** ~15 seconds  
**Output:** ~3 MB

---

### Full Mode (3-5 hours)

Extract ALL indexes completely:

```bash
python scripts/extract_all_lucene_pipeline.py
```

**Extracts:**
| Index | Docs | Time | Output |
|-------|------|------|--------|
| esnad | 35,526 | 5 min | ~3 MB |
| author | 3,146 | 5 min | ~2 MB |
| book | 8,425 | 10 min | ~10 MB |
| title | 3,914,618 | 30-60 min | ~500 MB |
| page | ~7.3M | 2-4 hours | ~8-12 GB |
| aya | 6,236 | 5 min | ~5 MB |
| s_author | 3,000 | 5 min | ~3 MB |
| s_book | 8,400 | 10 min | ~10 MB |
| **TOTAL** | **~11M** | **3-5 hours** | **~13 GB** |

---

## 📂 Output Files

```
data/processed/
├── lucene_esnad.json           # Hadith chains (3 MB)
├── lucene_author.json          # Author bios (2 MB)
├── lucene_book.json            # Book index (10 MB)
├── lucene_title.json           # Chapters/sections (500 MB)
├── lucene_page.json            # Full Arabic text (8-12 GB)
├── lucene_aya.json             # Quran verses (5 MB)
├── lucene_s_author.json        # Search author (3 MB)
└── lucene_s_book.json          # Search book (10 MB)
```

---

## 🎯 What Each Index Contains

### 1. Esnad (Hadith Chains)

**Purpose:** Hadith authentication with sanad/matn separation

**Fields:**
```json
{
  "id": "1456-2",
  "hadeeth": "5570",
  "esnad": "3783 4500 620 4539 4323 2779 2594"
}
```

**Use for:**
- Hadith verification
- Chain of narrator analysis
- Cross-referencing hadith across books

---

### 2. Author (Biographies)

**Purpose:** Scholar biographical information

**Fields:**
```json
{
  "author_id": "7",
  "body": "الإمام مسلم بن الحجاج النيسابوري..."
}
```

**Use for:**
- Author information
- Scholarly network analysis
- Chronological studies

---

### 3. Book (Book Index)

**Purpose:** Book-level metadata

**Fields:**
```json
{
  "book_id": "622",
  "book": "كتاب الإقناع في الفقه الحنبلي",
  "author": "الحجاوي"
}
```

**Use for:**
- Book catalog
- Title lookup
- Author bibliography

---

### 4. Title (Chapters/Sections) ⭐ IMPORTANT

**Purpose:** Hierarchical table of contents

**Fields:**
```json
{
  "book_key": "622-1",
  "body": "كتاب الطهارة",
  "author": "الحجاوي",
  "page": "1",
  "parent": "0"
}
```

**Use for:**
- Chapter/section structure
- Navigation hierarchy
- Table of contents generation
- Chunk boundary detection

---

### 5. Page (Full Arabic Text) ⭐⭐⭐ MOST IMPORTANT

**Purpose:** Complete Arabic text of every page

**Fields:**
```json
{
  "book_key": "622-1",
  "body": "بسم الله الرحمن الرحيم\n\n[full page text here...]",
  "author": "الحجاوي",
  "page": "1"
}
```

**Use for:**
- **Main content for RAG**
- Full-text search
- Verse/hadith retrieval
- Answer generation

**Note:** This is the LARGEST index (8-12 GB)

---

### 6. Aya (Quran Verses)

**Purpose:** Quran verse index

**Fields:**
```json
{
  "book_key": "23619-1",
  "verse": "1:1",
  "text": "بسم الله الرحمن الرحيم"
}
```

**Use for:**
- Quran verse lookup
- Tafsir linking
- Verse validation

---

## ⚙️ Advanced Usage

### Extract Specific Index

```bash
python scripts/extract_all_lucene_pipeline.py --index title
```

### Extract Multiple Indexes

```bash
python scripts/extract_all_lucene_pipeline.py --index title --index page
```

### Limit Docs for Testing

```bash
python scripts/extract_all_lucene_pipeline.py --index page --max-docs 10000
```

---

## 🐛 Troubleshooting

### "Java not found"

Install Java 11+:
```bash
# Download from: https://www.oracle.com/java/technologies/downloads/
```

### "Could not load codec 'Lucene95'"

Missing backward codecs JAR. Make sure you have:
```
lib/lucene/lucene-backward-codecs-9.12.0.jar
```

### "Out of memory"

Increase Java heap:
```python
# In extract_all_lucene_pipeline.py, change:
JAVA_OPTS="-Xmx4g"  # from -Xmx2g
```

### "Extraction too slow"

Normal speeds:
- Esnad: ~7,000 docs/sec
- Title: ~65,000 docs/sec
- Page: ~500-1,000 docs/sec (larger text)

---

## 📊 After Extraction: Next Steps

### Step 1: Verify Quality

```bash
python scripts/data/lucene/verify_lucene_extraction.py
```

### Step 2: Merge with Master Catalog

```bash
python scripts/data/lucene/merge_lucene_with_master.py
```

This joins Lucene content with master_catalog.json to add:
- Book titles
- Author names
- Author death years
- Categories
- Collection mappings

### Step 3: Build Hierarchical Chunks

```bash
python scripts/data/lucene/run_pipeline.py
```

Creates RAG-ready chunks with:
- Chapter/page boundaries preserved
- Full metadata on every chunk
- Organized by collection (11 JSONL files)

### Step 4: Upload to Hugging Face

Use Colab notebook:
```
notebooks/04_upload_to_huggingface.ipynb
```

### Step 5: Embed on Colab GPU

Use Colab notebook:
```
notebooks/01_embed_all_collections.ipynb
```

### Step 6: Import to Qdrant

```bash
python scripts/import_to_qdrant.py
```

---

## 💡 Tips

### Run Overnight

Start before sleeping:
```bash
# Evening:
python scripts/extract_all_lucene_pipeline.py

# Morning: Check results
```

### Monitor Progress

Watch console output - prints progress every 1,000-10,000 docs.

### Check Output Files

```bash
# List all extracted files
dir data\processed\lucene_*.json

# Check file sizes
for %f in (data\processed\lucene_*.json) do @echo %~nf: %~zf bytes
```

### Resume After Interruption

The script is NOT resumable, but you can:
1. Delete incomplete output file
2. Re-run with `--index` for just that index
3. Other indexes already extracted are safe

---

## 🎓 Understanding the Data Flow

```
Lucene Indexes (binary)
    ↓ Java Extractor
JSON Files (structured)
    ↓ Merge with master_catalog.json
Enriched Documents (with metadata)
    ↓ Hierarchical Chunker
RAG-Ready Chunks (300-600 tokens each)
    ↓ Embedding Model
Vector Embeddings (1024-dim)
    ↓ Qdrant
Search Index (for queries)
```

---

*Last updated: April 7, 2026, 7:10 PM*
