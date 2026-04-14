# Lucene Extraction Guide

## 🎯 What We're Extracting

The Lucene indexes contain **ALL the Arabic text content** from 8,425 books:

| Index | Size | Docs | What It Has |
|-------|------|------|-------------|
| **page/** | 13.2 GB | ~7.3M | Full Arabic text of every page |
| **title/** | 56 MB | 3.9M | Chapter/section titles with hierarchy |
| **esnad/** | 0.5 GB | 35K | Hadith chains (sanad/matn separated) |
| **book/** | Varies | 8.4K | Book-level metadata |
| **author/** | 1.9 MB | 3K | Author biographies |

---

## 🚀 Quick Start

### Test Extraction (5 minutes)

Extract small indexes to verify everything works:

```bash
python scripts/extract_all_lucene.py --index esnad
```

This extracts 35K hadith chains in ~5 minutes.

### Full Extraction (2-4 hours)

Extract ALL indexes:

```bash
python scripts/extract_all_lucene.py --all
```

**What it does:**
1. Downloads Lucene JARs (if needed)
2. Compiles Java extractor
3. Extracts each index in batches
4. Saves as JSONL files (one per batch)
5. Organizes by index name

---

## 📂 Output Structure

```
data/processed/lucene_extraction/
├── title/
│   ├── title_part0001.jsonl    # ~500K docs per file
│   ├── title_part0002.jsonl
│   └── ...
├── page/
│   ├── page_part0001.jsonl     # ~500K docs per file
│   ├── page_part0002.jsonl
│   └── ... (15+ files)
├── esnad/
│   └── esnad_part0001.jsonl    # All 35K hadith chains
├── book/
│   └── book_part0001.jsonl     # 8.4K book docs
└── author/
    └── author_part0001.jsonl   # 3K author bios
```

---

## ⏱️ Time Estimates

| Index | Docs | Time | Output Size |
|-------|------|------|-------------|
| esnad | 35K | 5 min | ~3 MB |
| author | 3K | 5 min | ~2 MB |
| book | 8.4K | 10 min | ~10 MB |
| title | 3.9M | 30-60 min | ~500 MB |
| page | 7.3M | 2-4 hours | ~8-12 GB |
| **TOTAL** | **~11M** | **3-5 hours** | **~13 GB** |

---

## 🔧 Commands

### Extract specific index
```bash
python scripts/extract_all_lucene.py --index title
```

### Extract multiple indexes
```bash
python scripts/extract_all_lucene.py --index title --index esnad
```

### Extract all (full run)
```bash
python scripts/extract_all_lucene.py --all
```

### Limit for testing
```bash
python scripts/extract_all_lucene.py --index page --max-docs 10000
```

### Custom batch size
```bash
python scripts/extract_all_lucene.py --all --batch-size 1000000
```

---

## 📊 After Extraction

### Step 1: Verify Quality
```bash
python scripts/data/lucene/verify_lucene_extraction.py
```

### Step 2: Merge with Master Catalog
```bash
python scripts/data/lucene/merge_lucene_with_master.py
```

This joins Lucene content with master_catalog.json metadata.

### Step 3: Create RAG-Ready Chunks
```bash
python scripts/data/lucene/run_pipeline.py
```

Creates hierarchical chunks organized by collection.

---

## 🎓 What's in Each Index

### Title Index (3.9M docs)

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
- Table of contents
- Hierarchy preservation

### Page Index (7.3M docs)

```json
{
  "book_key": "622-1",
  "body": "بسم الله الرحمن الرحيم\n\nالفصل الأول...\n[full page text]",
  "author": "الحجاوي",
  "page": "42"
}
```

**Use for:**
- Main content for RAG
- Full Arabic text
- Page-level granularity

### Esnad Index (35K docs)

```json
{
  "book_key": "711-1",
  "hadeeth": "إنما الأعمال بالنيات",
  "esnad": "حدثنا عمر بن الخطاب..."
}
```

**Use for:**
- Hadith authentication
- Sanad/matn separation
- Cross-referencing

### Author Index (3K docs)

```json
{
  "author_id": "7",
  "body": "الإمام مسلم بن الحجاج..."
}
```

**Use for:**
- Author biographies
- Scholarly network analysis

---

## 🐛 Troubleshooting

### "Java not found"

Install Java JDK 11+:
```bash
# Download from: https://www.oracle.com/java/technologies/downloads/
```

### "Lucene JARs download failed"

Download manually:
```
https://repo1.maven.org/maven2/org/apache/lucene/lucene-core/9.12.0/
https://repo1.maven.org/maven2/org/apache/lucene/lucene-queryparser/9.12.0/
```

Save to: `lib/lucene/`

### "Out of memory"

Reduce JVM heap size:
```python
# In extract_all_lucene.py, change:
"-Xmx2g"  # to "-Xmx1g" if needed
```

### "Extraction too slow"

Increase batch size:
```bash
python scripts/extract_all_lucene.py --all --batch-size 1000000
```

---

## 💡 Tips

### Start Small
```bash
# Test with esnad first (fast, small)
python scripts/extract_all_lucene.py --index esnad

# Then try title (medium size)
python scripts/extract_all_lucene.py --index title

# Finally page (largest)
python scripts/extract_all_lucene.py --index page
```

### Run Overnight
```bash
# Start before sleeping
python scripts/extract_all_lucene.py --all

# Check progress in the morning
```

### Monitor Progress
Watch the output - it prints progress every 10K docs.

---

*Last updated: April 7, 2026*
