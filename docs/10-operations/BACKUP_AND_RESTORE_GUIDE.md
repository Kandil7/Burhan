# 💾 Backup & Restore Guide - Athar Embeddings & Qdrant

**Purpose:** Save 5.7M embeddings and Qdrant data to HuggingFace for safe backup and sharing

---

## 📊 What Gets Backed Up

| Data Type | Original Size | Compressed | Files |
|-----------|--------------|------------|-------|
| **Embeddings (.npy)** | ~23 GB | ~7 GB (70% savings) | 10 files |
| **Qdrant Exports** | ~50 GB | ~15 GB (70% savings) | 10 files |
| **Metadata** | ~10 MB | ~3 MB | 3 files |
| **TOTAL** | **~73 GB** | **~22 GB** | **23 files** |

---

## 🚀 Backup Workflow

### Step 1: After Colab Embedding Completes

Once your Colab notebook finishes embedding all 10 collections:

1. **Download embeddings from Colab:**
   - Embeddings are saved to Google Drive
   - Download to local machine: `data/processed/embeddings/`

2. **Run backup script:**
```bash
# Backup everything and upload to HuggingFace
poetry run python scripts/backup_embeddings_and_qdrant.py --all --upload

# Backup only embeddings
poetry run python scripts/backup_embeddings_and_qdrant.py --embeddings-only --upload

# Backup only Qdrant
poetry run python scripts/backup_embeddings_and_qdrant.py --qdrant-only --upload
```

3. **Verify backup:**
```bash
poetry run python scripts/backup_embeddings_and_qdrant.py --verify
```

---

## 📥 Restore Workflow

### Option A: Restore to Local Machine

```bash
# Restore everything
poetry run python scripts/restore_from_huggingface.py --all

# Restore only embeddings
poetry run python scripts/restore_from_huggingface.py --embeddings

# Restore only Qdrant
poetry run python scripts/restore_from_huggingface.py --qdrant

# Verify restore
poetry run python scripts/restore_from_huggingface.py --verify
```

### Option B: Use in Another Colab Notebook

```python
from huggingface_hub import hf_hub_download
import numpy as np
import gzip

# Download embedding
filepath = hf_hub_download(
    repo_id="Kandil7/Athar-Embeddings",
    filename="embeddings/fiqh_passages_embeddings.npy.gz",
    repo_type="dataset"
)

# Decompress and load
with gzip.open(filepath, 'rb') as f:
    embeddings = np.load(f)

print(f"Loaded {len(embeddings):,} embeddings")
print(f"Shape: {embeddings.shape}")
```

---

## 💡 Why Backup to HuggingFace?

1. **Free unlimited storage** for public datasets
2. **Version control** - track changes over time
3. **Easy sharing** - team members can download
4. **Disaster recovery** - avoid re-embedding (saves 13+ hours)
5. **Reproducibility** - exact same embeddings for research

---

## 📁 File Structure After Backup

```
HuggingFace Repo: Kandil7/Athar-Embeddings
│
├── embeddings/
│   ├── README.md
│   ├── fiqh_passages_embeddings.npy.gz
│   ├── hadith_passages_embeddings.npy.gz
│   ├── quran_tafsir_embeddings.npy.gz
│   ├── ... (10 collections)
│   ├── fiqh_passages_passages.json.gz
│   └── ... (passage metadata)
│
└── qdrant_exports/
    ├── fiqh_passages_export.json
    ├── hadith_passages_export.json
    └── ... (10 collections)
```

---

## ⏱️ Time Estimates

| Operation | Time | Bandwidth |
|-----------|------|-----------|
| Compress embeddings | 30 min | Local |
| Upload embeddings (7 GB) | ~15 min (10 Mbps) | 7 GB |
| Export Qdrant | 1-2 hours | Local |
| Upload Qdrant (15 GB) | ~30 min (10 Mbps) | 15 GB |
| **TOTAL** | **~3 hours** | **22 GB** |

---

## 🎯 Use Cases

### 1. Team Collaboration
```bash
# Team member downloads
poetry run python scripts/restore_from_huggingface.py --embeddings
# Ready to use! No need to re-embed
```

### 2. Disaster Recovery
```bash
# Hard drive crashed? Restore from backup
poetry run python scripts/restore_from_huggingface.py --all
```

### 3. Migration to New Server
```bash
# New server setup
git clone https://github.com/Kandil7/Athar
poetry run python scripts/restore_from_huggingface.py --all
# Done! Same embeddings, no re-computation
```

---

## 🔧 Configuration

Add to `.env`:

```bash
# HuggingFace
HF_TOKEN=hf_your_token_here
HF_EMBEDDINGS_REPO_ID=Kandil7/Athar-Embeddings

# Qdrant
QDRANT_URL=http://localhost:6333
QDRANT_API_KEY=your-qdrant-key
```

---

## ⚠️ Important Notes

1. **Repository must be public** for free unlimited storage
2. **Large files** use Git LFS automatically
3. **Upload speed** depends on your internet connection
4. **Qdrant export** requires running Qdrant instance
5. **Compression** uses gzip (65-70% size reduction)

---

**Last updated:** April 8, 2026
