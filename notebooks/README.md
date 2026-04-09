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
| **02_upload_and_embed.ipynb** | Upload + Embed + Import | ~13 hours | ✅ **MAIN - USE THIS** |
| **verify_upload.ipynb** | Verify uploads work | 10 min | ✅ Verification |
| **COLAB_GPU_EMBEDDING_GUIDE.md** | Complete setup guide | - | ✅ Documentation |
| README.md | This guide | - | ✅ Current |

### Archived (Not Recommended)

| Notebook | Why Archived | Location |
|----------|--------------|----------|
| 01_embed_all_collections.ipynb | Uses old model (Qwen3 instead of BGE-M3) | `archive/` |
| 04_upload_to_huggingface.ipynb | Duplicates Python scripts | `archive/` |
| 05_upload_to_kaggle.ipynb | Kaggle is backup option only | `archive/` |
| setup_colab_env.ipynb | Superseded by main notebook | Deleted |

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

**Time:** ~13 hours (free T4) or ~4 hours (paid A100)
**Cost:** FREE (T4 GPU) or ~$10-15 (A100)

1. Open Google Colab: https://colab.research.google.com
2. Upload: `notebooks/02_upload_and_embed.ipynb`
3. Set your `HF_TOKEN` in the notebook
4. Select T4 GPU: Runtime → Change runtime type → GPU
5. Run all cells (takes ~13 hours)
6. Embeddings auto-save to Google Drive every 30 min

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
| Download from HF | 15-30 min | Free |
| Embed 10 collections (5.7M docs) | ~13 hours | Free |
| Upload to Qdrant | 1-2 hours | Free |
| Verify | 10 min | Free |
| **Total** | **~15-16 hours** | **FREE** |

### Colab Pro A100 ($10/month)

| Task | Time | Cost |
|------|------|------|
| Embed 10 collections | ~3-4 hours | ~$0.15 |
| Upload to Qdrant | 30 min | ~$0.05 |
| **Total** | **~4-5 hours** | **~$0.20** |

**Recommendation:** Free T4 works fine for overnight runs. A100 is 4x faster if you need results quickly.

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
