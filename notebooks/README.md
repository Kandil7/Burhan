# 🕌 Athar - Complete Notebooks Guide

**Last Updated:** April 15, 2026  
**Status:** Phase 8 Complete - Ready for GPU Embedding  
**Phase:** Hybrid Intent Classifier Active

---

## Overview

Production-ready Google Colab notebooks for:
1. **Uploading** 5.7M Islamic documents to Hugging Face ✅ COMPLETE
2. **Embedding** all collections with BGE-m3 on GPU
3. **Importing** to Qdrant vector database
4. **Verifying** everything works

---

## 🎉 Phase 8 Complete: Hybrid Intent Classifier Active

As of **April 15, 2026**, the system now includes:

- ✅ **Fast keyword-based classification** (no LLM required)
- ✅ **New `/classify` endpoint** for instant intent detection (<50ms)
- ✅ **10 priority levels** for conflict resolution
- ✅ **Quran sub-intent detection** (4 types)

This means the API is ready to route queries while we wait for the embedding pipeline to complete.

---

## Available Notebooks

| Notebook | Purpose | GPU Time | Status |
|----------|---------|----------|--------|
| **02_upload_and_embed.ipynb** | Complete pipeline (Upload → Embed → Import) | ~13 hours (T4) | ✅ Ready |
| **verify_upload.ipynb** | Verify HuggingFace uploads | 10 min | ✅ Ready |
| **COLAB_GPU_EMBEDDING_GUIDE.md** | Complete setup guide | - | ✅ Documentation |

### Recommended Workflow

```
1. HuggingFace Upload ✅ COMPLETE (42.6 GB)
       ↓
2. Run Colab GPU Embedding ⏳ PENDING (~13 hours)
       ↓
3. Import to Qdrant ⏳ PENDING (auto in notebook)
       ↓
4. Verify & Test ⏳ PENDING
```

---

## Quick Start (Recommended Flow)

### Step 1: Verify HuggingFace Upload (Already Done ✅)

The data has been uploaded to HuggingFace:

```bash
# Verify uploads
poetry run python scripts/final_upload.py --verify --repo Kandil7/Athar-Datasets
```

**Status:** ✅ All 10 collections uploaded (42.6 GB total)

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
2. Login to HuggingFace
3. Download collections from HuggingFace
4. Load BGE-m3 embedding model
5. Embed all collections with GPU
6. Import to Qdrant
7. Test retrieval

**Requirements:**
- Google Colab with T4 GPU (free)
- HuggingFace token
- ~13 hours runtime

**Outputs:**
- Collections on HuggingFace (already done)
- Embeddings (.npy files)
- Qdrant collections populated
- Working RAG retrieval

### verify_upload.ipynb

**Purpose:** Verify uploaded datasets work correctly

**Steps:**
1. Load each collection from HuggingFace
2. Check document counts
3. Verify data quality
4. Show sample documents

**Requirements:**
- Google Colab (CPU is fine)
- 10 minutes runtime

---

## Current Status

### Upload Progress ✅ COMPLETE

```
Repository: Kandil7/Athar-Datasets
Status: Complete ✅

Collections uploaded:
  ✅ hadith_passages.jsonl (11.0 GB)
  ✅ fiqh_passages.jsonl (7.0 GB)
  ✅ general_islamic.jsonl (6.5 GB)
  ✅ islamic_history_passages.jsonl (6.0 GB)
  ✅ quran_tafsir.jsonl (5.2 GB)
  ✅ arabic_language_passages.jsonl (2.3 GB)
  ✅ aqeedah_passages.jsonl (1.8 GB)
  ✅ usul_fiqh.jsonl (0.9 GB)
  ✅ spirituality_passages.jsonl (1.1 GB)
  ✅ seerah_passages.jsonl (0.8 GB)
   
Total: 42.6 GB ✅ COMPLETE
```

### Embedding Progress ⏳ PENDING

| Collection | Documents | Embedding Time (T4) |
|------------|-----------|-------------------|
| hadith_passages | 1,551,964 | ~3.5 hours |
| general_islamic | 1,193,626 | ~2 hours |
| islamic_history_passages | 1,186,189 | ~1.7 hours |
| fiqh_passages | 676,577 | ~2.2 hours |
| quran_tafsir | 550,989 | ~1.5 hours |
| aqeedah_passages | 183,086 | ~40 min |
| arabic_language_passages | 147,498 | ~30 min |
| spirituality_passages | 79,233 | ~20 min |
| seerah_passages | 74,972 | ~20 min |
| usul_fiqh | 73,043 | ~20 min |
| **Total** | **5,717,177** | **~13 hours** |

---

## Google Drive Setup

### For Local Data Upload (RECOMMENDED)

Keep data on your local machine, upload via scripts:

```bash
# Upload to HuggingFace
poetry run python scripts/final_upload.py --upload --compress

# Verify
poetry run python scripts/final_upload.py --verify
```

**Pros:**
- No need to upload to Google Drive first
- Direct upload to HuggingFace
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

## Next Steps

### Immediate

1. ⏳ **Open Colab:** https://colab.research.google.com
2. ⏳ **Upload notebook:** `notebooks/02_upload_and_embed.ipynb`
3. ⏳ **Set HF_TOKEN** in notebook
4. ⏳ **Select T4 GPU:** Runtime → Change runtime type → GPU
5. ⏳ **Run all cells** (~13 hours on T4)
6. ⏳ **Verify:** `notebooks/verify_upload.ipynb`

### After Embedding

1. ⏳ **Import to Qdrant** (notebook does this automatically)
2. ⏳ **Test retrieval** (notebook includes tests)
3. ⏳ **Update API** to use BGE-m3 embeddings
4. ⏳ **Deploy to production**

---

## Troubleshooting

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
- **BGE-m3 Model:** https://huggingface.co/BAAI/bge-m3
- **Athar GitHub:** https://github.com/Kandil7/Athar
- **Qdrant Docs:** https://qdrant.tech/documentation
- **Phase 8 Details:** [docs/10-operations/LUCENE_MERGE_COMPLETE.md](/docs/10-operations/LUCENE_MERGE_COMPLETE.md)

---

## 📊 Phase Progress

| Phase | Status | Key Achievement |
|-------|--------|-----------------|
| Phase 7 | ✅ Complete | 11.3M Lucene documents merged |
| **Phase 8** | ✅ **Complete** | **Hybrid Intent Classifier** |
| Phase 9 | ⏳ Pending | GPU Embedding & Qdrant Import |

---

*Last updated: April 15, 2026*

*Built with ❤️ for the Muslim community*