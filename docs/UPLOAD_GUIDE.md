# 📤 Upload Guide - Free Cloud Storage for Athar Datasets

**Last Updated:** April 8, 2026  
**Status:** Scripts Ready, Awaiting Upload

---

## Overview

This guide covers uploading the processed Athar collections (~61 GB) to **FREE** cloud storage platforms for:
- **Sharing** with the community
- **Embedding** on Colab GPU
- **Backup** and disaster recovery
- **Version control** of datasets

---

## Recommended Platforms (All FREE)

| Platform | Storage Limit | Upload Time | Best For | Priority |
|----------|--------------|-------------|----------|----------|
| **Hugging Face** | Unlimited | ~3.5 hours | **Colab embedding, ML** | ⭐⭐⭐ MUST |
| **Kaggle** | 100 GB per dataset | ~5.5 hours | **Backup, discovery** | ⭐⭐ RECOMMENDED |
| **Archive.org** | Unlimited | ~8.5 hours | **Disaster recovery** | ⭐ OPTIONAL |

**Total Cost: FREE** (all platforms offer free storage)

---

## Quick Start

### Option A: Upload to All Three (Recommended)

```bash
# Step 1: Compress files (50-70% size reduction)
python scripts/compress_for_upload.py

# Step 2: Upload to Hugging Face (primary)
huggingface-cli login  # One-time setup
python scripts/upload_to_huggingface.py

# Step 3: Upload to Kaggle (backup)
pip install kaggle
# Download kaggle.json from https://www.kaggle.com/account
# Place in ~/.kaggle/kaggle.json
python scripts/upload_to_kaggle.py

# Step 4: Upload to Archive.org (disaster recovery)
pip install internetarchive
ia configure  # One-time setup
python scripts/upload_to_archive.py
```

### Option B: Hugging Face Only (Fastest)

```bash
# Compress and upload to Hugging Face only
python scripts/compress_for_upload.py
huggingface-cli login
python scripts/upload_to_huggingface.py
```

---

## Platform Setup

### 1. Hugging Face

**Setup:**
```bash
# Install
pip install huggingface_hub

# Login (get token from https://huggingface.co/settings/tokens)
huggingface-cli login

# Create repository
huggingface-cli repo create Athar-Datasets --type dataset
```

**Upload:**
```bash
# Full upload with progress tracking
python scripts/upload_to_huggingface.py

# Dry run (see what would be uploaded)
python scripts/upload_to_huggingface.py --dry-run

# Verify existing upload
python scripts/upload_to_huggingface.py --verify-only
```

**Access in Colab:**
```python
from datasets import load_dataset

# Load collection
ds = load_dataset(
    "json",
    data_files="hf://datasets/Kandil7/Athar-Datasets/collections/fiqh_passages.jsonl.gz",
    split="train"
)

print(f"Loaded {len(ds):,} documents")
```

---

### 2. Kaggle

**Setup:**
```bash
# Install
pip install kaggle

# Download API token from https://www.kaggle.com/account
# Place in ~/.kaggle/kaggle.json
chmod 600 ~/.kaggle/kaggle.json  # Linux/Mac
```

**Upload:**
```bash
# Prepare and upload
python scripts/upload_to_kaggle.py

# Dry run
python scripts/upload_to_kaggle.py --dry-run
```

**Access in Colab:**
```python
# Install Kaggle API
!pip install kaggle -q

# Download dataset
!kaggle datasets download -d YOUR_USERNAME/athar-islamic-collections

# Extract
!unzip athar-islamic-collections.zip
```

---

### 3. Archive.org

**Setup:**
```bash
# Install
pip install internetarchive

# Configure (get credentials from https://archive.org/account)
ia configure
```

**Upload:**
```bash
# Upload
python scripts/upload_to_archive.py

# Dry run
python scripts/upload_to_archive.py --dry-run
```

**Access:**
```
https://archive.org/details/athar-islamic-collections-2026
```

---

## Data Preparation

### Compression

The `compress_for_upload.py` script:
- Converts `.jsonl` → `.jsonl.gz` (gzip compression)
- Achieves **50-70% size reduction**
- Maintains original files for local use

```bash
# Compress all collections
python scripts/compress_for_upload.py

# Compress specific collections
python scripts/compress_for_upload.py --collections fiqh_passages hadith_passages

# Dry run (see estimated sizes)
python scripts/compress_for_upload.py --dry-run
```

**Expected Results:**

| Collection | Original | Compressed | Savings |
|------------|----------|------------|---------|
| hadith_passages | ~8.8 GB | ~3.1 GB | 65% |
| general_islamic | ~8.8 GB | ~3.1 GB | 65% |
| islamic_history_passages | ~8.8 GB | ~3.1 GB | 65% |
| fiqh_passages | ~8.8 GB | ~3.1 GB | 65% |
| quran_tafsir | ~8.8 GB | ~3.1 GB | 65% |
| Others | ~17 GB | ~6 GB | 65% |
| **Total** | **~61 GB** | **~21.5 GB** | **65%** |

---

## Upload Strategies

### Strategy 1: Single Repository (Simplest)

Upload all collections to one Hugging Face repository.

**Pros:**
- Simple management
- Single URL for all data
- Easy to update

**Cons:**
- Large single upload (~21.5 GB compressed)
- May take 3-5 hours

**Command:**
```bash
python scripts/upload_to_huggingface.py --repo Kandil7/Athar-Datasets
```

### Strategy 2: Split by Category (Most Reliable)

Split into multiple repositories by category type.

| Repository | Collections | Size |
|------------|-------------|------|
| `Athar-Fiqh-Hadith` | fiqh, hadith | ~6 GB |
| `Athar-Quran-Tafsir` | quran_tafsir | ~3 GB |
| `Athar-General` | general, history, arabic, spirituality, usul_fiqh | ~9 GB |
| `Athar-Aqeedah-Seerah` | aqeedah, seerah | ~3 GB |

**Pros:**
- Faster individual uploads
- Easier to retry failures
- Users can download only what they need

**Cons:**
- Multiple repositories to manage
- More complex URLs

---

## Troubleshooting

### Upload Too Slow

```bash
# Increase parallel uploads (if supported)
# Or split into smaller batches

python scripts/compress_for_upload.py --collections fiqh_passages
python scripts/upload_to_huggingface.py --collections fiqh_passages
```

### Upload Failed Midway

Both Hugging Face and Archive.org support **resuming**:
- Hugging Face: Re-run upload script, it skips existing files
- Archive.org: `ia upload` skips files that already exist

### Out of Disk Space

```bash
# Clean up compressed files after upload
rm data/processed/lucene_pages/upload_ready/*.gz

# Or use streaming upload (no intermediate files)
# Not implemented yet
```

### Memory Issues

The compression script uses streaming (line-by-line), so it uses minimal memory:
- Peak memory: ~100 MB
- Safe for most systems

---

## Verification

### After Upload

Run the verification notebook:
```bash
# Upload to Colab: notebooks/verify_upload.ipynb
```

Or test locally:
```python
from datasets import load_dataset

# Try loading a collection
ds = load_dataset(
    "json",
    data_files="hf://datasets/Kandil7/Athar-Datasets/collections/fiqh_passages.jsonl.gz",
    split="train"
)

print(f"✅ Loaded {len(ds):,} documents")
print(f"📄 Fields: {list(ds[0].keys())}")
```

---

## Cost Analysis

### Hugging Face

| Feature | Free Tier | Athar Usage | Cost |
|---------|-----------|-------------|------|
| Storage | Unlimited | ~21.5 GB (compressed) | **FREE** |
| Bandwidth | 1 TB/month | ~100 GB (initial) | **FREE** |
| API Requests | 100K/month | ~1K (embedding) | **FREE** |

### Kaggle

| Feature | Free Tier | Athar Usage | Cost |
|---------|-----------|-------------|------|
| Storage | 100 GB per dataset | ~21.5 GB (compressed) | **FREE** |
| Downloads | Unlimited | ~10K (estimated) | **FREE** |

### Archive.org

| Feature | Free Tier | Athar Usage | Cost |
|---------|-----------|-------------|------|
| Storage | Unlimited | ~21.5 GB (compressed) | **FREE** |
| Bandwidth | Unlimited | ~100 GB | **FREE** |

**Total Cost: $0.00/month**

---

## Next Steps After Upload

1. ✅ Upload collections (3-6 hours)
2. ✅ Verify uploads work (30 min)
3. ⏳ Embed on Colab GPU (3-5 hours)
4. ⏳ Import to Qdrant (1 hour)
5. ⏳ Test RAG retrieval (30 min)

---

## Scripts Reference

| Script | Purpose | Time |
|--------|---------|------|
| `compress_for_upload.py` | Compress JSONL → JSONL.gz | 1-2 hours |
| `upload_to_huggingface.py` | Upload to Hugging Face | 3-5 hours |
| `upload_to_kaggle.py` | Upload to Kaggle | 5-8 hours |
| `upload_to_archive.py` | Upload to Archive.org | 8-12 hours |
| `notebooks/verify_upload.ipynb` | Verify upload works | 30 min |

---

*Last updated: April 8, 2026*
