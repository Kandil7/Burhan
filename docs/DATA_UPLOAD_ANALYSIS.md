# 📊 Complete Data Analysis - What to Upload

**Analysis Date:** April 8, 2026  
**Total Processed Data:** 161.3 GB  
**Recommended for Upload:** 42.6 GB (26.4%)

---

## Complete Data Inventory

### Directory Breakdown

| Directory | Size | Files | Purpose | Upload? |
|-----------|------|-------|---------|---------|
| **collections/** | **42.6 GB** | 10 | ✅ **Final enriched collections** | **YES - PRIMARY** |
| **chunks/** | 43.3 GB | 10 | Hierarchical chunks | ❌ Regenerable |
| **temp_book_pages/** | 34.7 GB | 8,423 | Temp working files | ❌ Delete after |
| **raw/** | 17.7 GB | 25 | Batch extraction files | ❌ Regenerable |
| **pages/** | 17.1 GB | 8,423 | Per-book page JSONL | ❌ Regenerable |
| **lucene_*.json** | 17.4 GB | 12 | Raw Lucene output | ❌ Regenerable |
| **titles/** | 342 MB | 8,358 | Per-book title JSONL | ❌ Regenerable |
| **books/** | 9 MB | 8,425 | Per-book metadata | ❌ In master_catalog |
| **esnad/** | 3 MB | 10 | Hadith chain JSONL | ❌ Included in collections |
| **master_catalog.json** | 5 MB | 1 | 8,425 books metadata | **YES - METADATA** |
| **category_mapping.json** | 2 MB | 1 | 40→10 mapping | **YES - METADATA** |
| **author_catalog.json** | 0.5 MB | 1 | 3,146 authors | **YES - METADATA** |

**Total:** 161.3 GB  
**Upload Only:** 42.6 GB (collections) + 8 MB (metadata) = **42.6 GB**

---

## What MUST Be Uploaded (42.6 GB)

### 1. Collections (42.6 GB) - **ESSENTIAL**

These are the final, enriched, merged documents ready for embedding:

| File | Size | Documents | Content |
|------|------|-----------|---------|
| hadith_passages.jsonl | 11.0 GB | 1,551,964 | Hadith collections |
| fiqh_passages.jsonl | 7.0 GB | 676,577 | Islamic jurisprudence |
| general_islamic.jsonl | 6.5 GB | 1,193,626 | General knowledge |
| islamic_history_passages.jsonl | 6.0 GB | 1,186,189 | Islamic history |
| quran_tafsir.jsonl | 5.2 GB | 550,989 | Quran interpretation |
| arabic_language_passages.jsonl | 2.3 GB | 147,498 | Arabic language |
| aqeedah_passages.jsonl | 1.8 GB | 183,086 | Islamic creed |
| usul_fiqh.jsonl | 0.9 GB | 73,043 | Jurisprudence principles |
| spirituality_passages.jsonl | 1.1 GB | 79,233 | Spirituality |
| seerah_passages.jsonl | 0.8 GB | 74,972 | Prophet biography |
| **TOTAL** | **42.6 GB** | **5,717,177** | **All collections** |

**Why upload these:**
- ✅ Final enriched data with full metadata
- ✅ Cannot be regenerated without 3+ hours of processing
- ✅ Required for embedding phase
- ✅ 5.7M documents of verified Islamic knowledge

### 2. Metadata Files (8 MB) - **ESSENTIAL**

| File | Size | Contents |
|------|------|----------|
| master_catalog.json | 5 MB | 8,425 books with metadata |
| category_mapping.json | 2 MB | 41→10 collection mapping |
| author_catalog.json | 0.5 MB | 3,146 authors with death years |

**Why upload these:**
- ✅ Book metadata for context
- ✅ Category mappings for organization
- ✅ Author information for citations
- ✅ Tiny size (8 MB total)

---

## What NOT to Upload (118.7 GB) - Can Be Regenerated

### ❌ Chunks (43.3 GB)

**Why skip:** Can be regenerated from collections in ~1 hour
```bash
python scripts/data/lucene/merge_lucene_with_master.py --process-all-pages
```

### ❌ Temporary Files (34.7 GB)

**Why skip:** `temp_book_pages/` is intermediate processing data
```bash
# Safe to delete
rm -rf data/processed/lucene_pages/temp_book_pages/
```

### ❌ Raw Batch Files (17.7 GB)

**Why skip:** Can be regenerated from Lucene indexes
```bash
python scripts/extract_all_lucene_pipeline.py
```

### ❌ Per-Book Pages (17.1 GB)

**Why skip:** Intermediate format, already merged into collections

### ❌ Raw Lucene Output (17.4 GB)

**Why skip:** `lucene_page.json` (17.4 GB) is raw extraction, already processed

### ❌ Titles (342 MB)

**Why skip:** Already included in collections with enrichment

### ❌ Books Metadata (9 MB)

**Why skip:** Already in `master_catalog.json`

### ❌ Esnad (3 MB)

**Why skip:** Already included in hadith_passages collection

---

## Upload Strategy

### Option A: Upload Collections Only (RECOMMENDED)

**Upload Size:** 42.6 GB + 8 MB metadata = **42.6 GB**

```bash
# Hugging Face
huggingface-cli upload Kandil7/Athar-Datasets \
  data/processed/lucene_pages/collections/ collections/ \
  --repo-type dataset

# Upload metadata
huggingface-cli upload Kandil7/Athar-Datasets \
  data/processed/master_catalog.json metadata/ \
  --repo-type dataset

huggingface-cli upload Kandil7/Athar-Datasets \
  data/processed/category_mapping.json metadata/ \
  --repo-type dataset

huggingface-cli upload Kandil7/Athar-Datasets \
  data/processed/author_catalog.json metadata/ \
  --repo-type dataset
```

**Estimated Time:** ~2.5 hours at 5 MB/s

### Option B: Compress Then Upload (Better)

**Compress to ~65%:** 42.6 GB → **~15 GB**

```bash
# Compress collections
python scripts/compress_for_upload.py

# Upload compressed (~15 GB)
huggingface-cli upload Kandil7/Athar-Datasets \
  data/processed/lucene_pages/upload_ready/ collections/ \
  --repo-type dataset
```

**Estimated Time:** ~1 hour compression + ~50 min upload = **~1.5 hours total**

### Option C: Upload Everything (NOT RECOMMENDED)

**Upload Size:** 161.3 GB  
**Why not:** Wastes time/space, most files are regenerable

---

## Recommended Upload Structure on Hugging Face

```
Kandil7/Athar-Datasets/
├── README.md                          # Dataset description
├── collections/
│   ├── fiqh_passages.jsonl.gz        # ~2.5 GB compressed
│   ├── hadith_passages.jsonl.gz      # ~3.9 GB
│   ├── general_islamic.jsonl.gz      # ~2.3 GB
│   ├── islamic_history_passages.jsonl.gz  # ~2.1 GB
│   ├── quran_tafsir.jsonl.gz         # ~1.8 GB
│   ├── arabic_language_passages.jsonl.gz  # ~0.8 GB
│   ├── aqeedah_passages.jsonl.gz     # ~0.6 GB
│   ├── usul_fiqh.jsonl.gz            # ~0.3 GB
│   ├── spirituality_passages.jsonl.gz # ~0.4 GB
│   └── seerah_passages.jsonl.gz      # ~0.3 GB
├── metadata/
│   ├── master_catalog.json           # 5 MB
│   ├── category_mapping.json         # 2 MB
│   └── author_catalog.json           # 0.5 MB
└── chunks/ (OPTIONAL - regenerable)
    ├── fiqh_passages_chunks.jsonl.gz
    └── ... (10 files total)
```

**Total Upload Size:** ~15 GB compressed (collections + metadata)

---

## After Upload: Verification

```python
from datasets import load_dataset

# Test loading collection
ds = load_dataset(
    "json",
    data_files="hf://datasets/Kandil7/Athar-Datasets/collections/fiqh_passages.jsonl.gz",
    split="train"
)
print(f"✅ Loaded {len(ds):,} documents")

# Test loading metadata
import json
from huggingface_hub import hf_hub_download

# Download master catalog
master_file = hf_hub_download(
    repo_id="Kandil7/Athar-Datasets",
    filename="metadata/master_catalog.json",
    repo_type="dataset"
)
with open(master_file) as f:
    master_catalog = json.load(f)
print(f"✅ Master catalog: {len(master_catalog)} books")
```

---

## Cleanup After Successful Upload

Once upload is verified, you can safely delete regenerable files:

```bash
# Safe to delete (118.7 GB)
rm -rf data/processed/lucene_pages/temp_book_pages/  # 34.7 GB
rm -rf data/processed/lucene_pages/raw/              # 17.7 GB
rm -rf data/processed/lucene_pages/pages/            # 17.1 GB
rm data/processed/lucene_page.json                   # 17.4 GB
rm -rf data/processed/lucene_pages/chunks/           # 43.3 GB (regenerable)

# Space saved: ~130 GB
```

**Keep only:**
- `data/processed/lucene_pages/collections/` (42.6 GB)
- `data/processed/master_catalog.json` (5 MB)
- `data/processed/category_mapping.json` (2 MB)
- `data/processed/author_catalog.json` (0.5 MB)

**Total kept:** 42.6 GB

---

## Summary

| Category | Size | Action |
|----------|------|--------|
| **Collections (upload)** | **42.6 GB** | ✅ **UPLOAD NOW** |
| **Metadata (upload)** | **8 MB** | ✅ **UPLOAD NOW** |
| Chunks (regenerable) | 43.3 GB | ❌ Skip or optional |
| Temporary files | 34.7 GB | ❌ Delete after upload |
| Raw batches | 17.7 GB | ❌ Regenerable |
| Per-book pages | 17.1 GB | ❌ Regenerable |
| Raw Lucene output | 17.4 GB | ❌ Regenerable |
| Titles/Books/Esناد | 354 MB | ❌ Included in collections |

**Upload Now:** 42.6 GB (collections + metadata)  
**Can Delete Later:** 118.7 GB (regenerable)  
**Net Savings After Cleanup:** 118.7 GB freed

---

*Analysis completed: April 8, 2026*
