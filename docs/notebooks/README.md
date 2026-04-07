# 🕌 Athar - Google Colab Notebooks

GPU-accelerated notebooks for embedding, data processing, and analysis.

---

## 📋 Overview

These notebooks enable running computationally intensive tasks on Google Colab's free GPU tier, providing **13-150x speedup** compared to CPU processing.

### Available Notebooks

| Notebook | Purpose | GPU Time | CPU Time | Savings |
|----------|---------|----------|----------|---------|
| `setup_colab_env.ipynb` | Environment setup | 5 min | 5 min | N/A |
| `01_embed_all_collections.ipynb` | Embed all 10 collections | ~3 hours | ~40 hours | **13x** |
| `02_process_sanadset_hadith.ipynb` | Process 650K hadith | ~6 hours | ~900 hours | **150x** |
| `03_analyze_and_chunk_books.ipynb` | Analyze & chunk books | ~2 hours | ~20 hours | **10x** |

---

## 🚀 Quick Start

### Step 1: Open in Colab

Click one of the links below or upload the notebook:

1. **Start Here:** [setup_colab_env.ipynb](setup_colab_env.ipynb)
   - Opens in Colab
   - Installs dependencies
   - Mounts Google Drive
   - Tests GPU

2. **Embed Collections:** [01_embed_all_collections.ipynb](01_embed_all_collections.ipynb)
   - Embeds all 10 collections
   - Outputs: `.npy` embedding files

3. **Process Hadith:** [02_process_sanadset_hadith.ipynb](02_process_sanadset_hadith.ipynb)
   - Processes 650K Sanadset hadith
   - Outputs: Chunked JSONL files

4. **Analyze Books:** [03_analyze_and_chunk_books.ipynb](03_analyze_and_chunk_books.ipynb)
   - Analyzes 8,425 books
   - Outputs: Chunked data ready for embedding

### Step 2: Select GPU

1. Go to **Runtime → Change runtime type**
2. Select **T4 GPU** (free tier)
3. Click **Save**

### Step 3: Run All Cells

1. Open `setup_colab_env.ipynb` first
2. Click **Runtime → Run all**
3. Wait for setup to complete (~5 minutes)
4. Open the notebook you need
5. Run all cells

---

## 📂 Google Drive Setup

### Folder Structure

Create this structure in your Google Drive:

```
Google Drive/
└── MyDrive/
    └── Athar/
        ├── datasets/
        │   ├── extracted_books/     # 8,425 books (17.16 GB)
        │   ├── sanadset.csv         # 650K hadith (1.43 GB)
        │   └── metadata/            # Small JSON/DB files
        └── output/
            ├── embeddings/          # Generated embeddings
            └── chunked_data/        # Processed chunks
```

### Upload Datasets

**Option 1: Google Drive Desktop App** (Recommended)
1. Install Google Drive for Desktop
2. Copy datasets to `Google Drive/MyDrive/Athar/datasets/`
3. Wait for sync to complete

**Option 2: Web Upload**
1. Go to https://drive.google.com
2. Navigate to `MyDrive/Athar/datasets/`
3. Upload files/folders
4. Wait for upload to complete

---

## 💰 Cost Estimates

### Free Tier (T4 GPU)

| Task | Time | Cost |
|------|------|------|
| Setup | 5 min | Free |
| Embed 10 collections | ~3 hours | Free |
| Process 650K hadith | ~6 hours | Free |
| Analyze & chunk books | ~2 hours | Free |
| **Total per session** | **~11 hours** | **Free** |

**Limitations:**
- 12-hour session timeout
- May disconnect if idle
- T4 GPU (16 GB VRAM)

### Colab Pro ($10/month)

| Task | Time | Cost |
|------|------|------|
| Embed 10 collections | ~1 hour | $0.17 |
| Process 650K hadith | ~2 hours | $0.33 |
| Analyze & chunk books | ~45 min | $0.13 |
| **Total** | **~4 hours** | **$0.63** |

**Benefits:**
- A100 GPU (40 GB VRAM)
- 24-hour sessions
- Priority access
- More memory

---

## 📊 Expected Outputs

### After Embedding

```
output/embeddings/
├── fiqh_passages_embeddings.npy       # 10,132 × 1024 matrix
├── fiqh_passages_meta.json            # Metadata
├── hadith_passages_embeddings.npy     # 650,986 × 1024 matrix
├── hadith_passages_meta.json
├── ... (10 collections total)
└── embeddings.zip                     # All files
```

### After Processing Hadith

```
output/chunked_data/
├── sanadset_chunked.jsonl             # 650K hadith
└── sanadset_stats.json                # Statistics
```

### After Analyzing Books

```
output/chunked_data/
├── all_chunks.json                    # All chunked books
├── chunks_by_collection/
│   ├── fiqh_passages.jsonl
│   ├── aqeedah_passages.jsonl
│   └── ... (10 collections)
└── analysis_report.json               # Statistics
```

---

## 🔧 Troubleshooting

### GPU Not Available

**Problem:** Notebook shows "No GPU detected"

**Solution:**
1. Go to **Runtime → Change runtime type**
2. Select **T4 GPU**
3. Re-run the setup cell

### Session Timeout

**Problem:** Colab disconnects after 12 hours

**Solution:**
1. Save your progress frequently
2. Outputs are saved to Google Drive automatically
3. Re-run the notebook when you reconnect
4. It will resume from where it left off

### Out of Memory

**Problem:** "CUDA out of memory" error

**Solution:**
1. Reduce batch size in the notebook:
   ```python
   BATCH_SIZE = 64  # Change from 128 to 64
   ```
2. Or upgrade to Colab Pro for A100 GPU

### HuggingFace Authentication

**Problem:** Can't download embedding model

**Solution:**
1. Get token from https://huggingface.co/settings/tokens
2. In Colab: **Secrets** → Add `HF_TOKEN`
3. Enable "Notebook access"

---

## 📈 Performance Comparison

| Task | Local CPU | Colab T4 | Colab A100 |
|------|-----------|----------|------------|
| Embed 650K hadith | 900 hours | 6 hours | 2 hours |
| Embed 10 collections | 40 hours | 3 hours | 1 hour |
| Process 8,425 books | 20 hours | 2 hours | 45 min |
| **Total** | **960 hours** | **11 hours** | **4 hours** |

---

## 🔗 Resources

- **Colab Homepage:** https://colab.research.google.com
- **Colab Pro:** https://colab.research.google.com/signup
- **Athar Repository:** https://github.com/Kandil7/Athar
- **HuggingFace:** https://huggingface.co/Qwen/Qwen3-Embedding-0.6B

---

## 💡 Tips

1. **Save Progress Frequently**
   - Colab can disconnect unexpectedly
   - All outputs are saved to Google Drive

2. **Use Free Tier First**
   - Test with mini-dataset (1,623 docs)
   - Upgrade to Pro only if needed

3. **Schedule Long Tasks**
   - Start embedding before sleeping
   - Check progress in the morning

4. **Download Results**
   - Zip files are in Google Drive
   - Download to local machine for Qdrant import

---

*Last updated: April 7, 2026*
