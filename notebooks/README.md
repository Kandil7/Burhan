# 🕌 Athar - Complete Notebooks Guide

**Last Updated:** April 8, 2026  
**Status:** Production-Ready  
**Phase:** 7 Complete (Lucene Merge), Phase 8 (Upload & Embedding)

---

## Overview

Production-ready Google Colab notebooks for:
1. **Uploading** 5.7M Islamic documents to Hugging Face
2. **Embedding** all collections with BGE-M3 on GPU
3. **Importing** to Qdrant vector database
4. **Verifying** everything works

---

## Available Notebooks

| Notebook | Purpose | GPU Time | Status |
|----------|---------|----------|--------|
| **02_upload_and_embed.ipynb** | Upload + Embed + Import | ~2 hours | ✅ Complete |
| **verify_upload.ipynb** | Verify uploads work | 10 min | ✅ Complete |
| setup_colab_env.ipynb | Environment setup | 5 min | ⏳ Outdated |
| 01_embed_all_collections.ipynb | Old embedding script | ~3 hours | ⏳ Outdated |
| 04_upload_to_huggingface.ipynb | Old upload script | ~2 hours | ⏳ Outdated |
| 05_upload_to_kaggle.ipynb | Kaggle upload | ~3 hours | ⏳ Outdated |
| google_drive_setup.md | Drive setup guide | - | ✅ Reference |
| README.md | This guide | - | ✅ Current |

---

## Quick Start (Recommended Flow)

### Step 1: Upload Data to Hugging Face (Local Machine)

**Time:** ~1.5 hours  
**Cost:** FREE

```bash
# Already running on your machine!
# PID: 18364

# Check progress
dir data\processed\lucene_pages\upload_ready\*.gz

# Verify when done
poetry run python scripts/final_upload.py --verify --repo Kandil7/Athar-Datasets
```

### Step 2: Embed on Colab GPU

**Time:** ~1 hour  
**Cost:** FREE (T4 GPU)

1. Open Google Colab: https://colab.research.google.com
2. Upload: `notebooks/02_upload_and_embed.ipynb`
3. Set your `HF_TOKEN` in the notebook
4. Select T4 GPU: Runtime → Change runtime type → GPU
5. Run all cells

### Step 3: Verify Everything Works

**Time:** 10 minutes

1. Upload: `notebooks/verify_upload.ipynb`
2. Run all cells
3. Check all collections load correctly

---

## Notebook Details

### 02_upload_and_embed.ipynb (MAIN NOTEBOOK)

**Purpose:** Complete pipeline from upload to embedding to Qdrant import

**Steps:**
1. Setup environment (install packages)
2. Login to Hugging Face
3. Compress collections (optional)
4. Upload to Hugging Face
5. Verify upload
6. Embed all collections with BGE-M3
7. Import to Qdrant
8. Test retrieval

**Requirements:**
- Google Colab with T4 GPU (free)
- Hugging Face token
- ~2 hours runtime

**Outputs:**
- Collections on Hugging Face
- Embeddings (.npy files)
- Qdrant collections populated
- Working RAG retrieval

---

### verify_upload.ipynb

**Purpose:** Verify uploaded datasets work correctly

**Steps:**
1. Load each collection from Hugging Face
2. Check document counts
3. Verify data quality
4. Show sample documents

**Requirements:**
- Google Colab (CPU is fine)
- 10 minutes runtime

**Outputs:**
- Verification report
- Collection statistics
- Sample documents

---

## Google Drive Setup

### For Local Data Upload (RECOMMENDED)

Keep data on your local machine, upload via scripts:

```bash
# Upload to Hugging Face
poetry run python scripts/final_upload.py --upload --compress

# Verify
poetry run python scripts/final_upload.py --verify
```

**Pros:**
- No need to upload to Google Drive first
- Direct upload to Hugging Face
- Faster (no double upload)

### For Google Drive Storage (OPTIONAL)

If you want to store data on Google Drive:

```
Google Drive/
└── MyDrive/
    └── Athar/
        ├── collections/
        │   ├── fiqh_passages.jsonl
        │   ├── hadith_passages.jsonl
        │   └── ... (10 files)
        ├── metadata/
        │   ├── master_catalog.json
        │   ├── category_mapping.json
        │   └── author_catalog.json
        └── output/
            ├── embeddings/
            └── qdrant/
```

**Upload to Drive:**
```bash
# Install Google Drive CLI
# Or use Google Drive Desktop app
# Copy data/processed/lucene_pages/collections/ to Drive
```

---

## Cost Analysis

### Free Tier (T4 GPU)

| Task | Time | Cost |
|------|------|------|
| Setup | 5 min | Free |
| Verify upload | 10 min | Free |
| Embed 10 collections | ~1 hour | Free |
| Import to Qdrant | 30 min | Free |
| **Total** | **~2 hours** | **FREE** |

### Colab Pro ($10/month)

| Task | Time | Cost |
|------|------|------|
| Embed 10 collections | ~20 min | $0.06 |
| Import to Qdrant | 10 min | $0.03 |
| **Total** | **~30 min** | **$0.09** |

**Recommendation:** Free tier is sufficient for this workload

---

## Current Status

### Upload Progress

```
Repository: Kandil7/Athar-Datasets
Status: Created ✅
Upload: Running (PID: 18364)

Collections to upload:
  ✓ hadith_passages.jsonl (11.0 GB)
  ✓ fiqh_passages.jsonl (7.0 GB)
  ✓ general_islamic.jsonl (6.5 GB)
  ✓ islamic_history_passages.jsonl (6.0 GB)
  ✓ quran_tafsir.jsonl (5.2 GB)
  ✓ arabic_language_passages.jsonl (2.3 GB)
  ✓ aqeedah_passages.jsonl (1.8 GB)
  ✓ usul_fiqh.jsonl (0.9 GB)
  ✓ spirituality_passages.jsonl (1.1 GB)
  ✓ seerah_passages.jsonl (0.8 GB)
  
Total: 42.6 GB → ~15 GB compressed
```

### Next Steps

1. ⏳ **Wait for upload to complete** (~1 hour)
2. ⏳ **Verify upload** (`scripts/final_upload.py --verify`)
3. ⏳ **Open Colab** (notebooks/02_upload_and_embed.ipynb)
4. ⏳ **Embed collections** (~1 hour on T4)
5. ⏳ **Import to Qdrant** (30 min)
6. ⏳ **Test retrieval** (10 min)

---

## Troubleshooting

### Upload Stuck

```powershell
# Check if running
tasklist | findstr python

# If stuck, restart
poetry run python scripts/final_upload.py --upload --compress
```

### Colab GPU Not Available

**Solution:**
1. Try again later (free GPUs get busy)
2. Use CPU (slower but works): Change `device='cuda'` to `device='cpu'`
3. Upgrade to Colab Pro ($10/month)

### Out of Memory on Colab

**Solution:**
```python
# Reduce batch size
BATCH_SIZE = 8  # Change from 32 to 8
```

### Hugging Face Authentication

**Solution:**
```python
# Get token from https://huggingface.co/settings/tokens
# In Colab, use:
from huggingface_hub import login
login(token="hf_YOUR_TOKEN_HERE")
```

---

## Resources

- **Hugging Face Repo:** https://huggingface.co/datasets/Kandil7/Athar-Datasets
- **Colab:** https://colab.research.google.com
- **BGE-M3 Model:** https://huggingface.co/BAAI/bge-m3
- **Athar GitHub:** https://github.com/Kandil7/Athar
- **Qdrant Docs:** https://qdrant.tech/documentation

---

*Last updated: April 8, 2026*
