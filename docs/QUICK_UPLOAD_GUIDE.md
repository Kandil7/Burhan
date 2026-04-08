# 🚀 Quick Upload Guide - Athar Datasets

**Goal:** Upload 10.46 GB of collections to FREE cloud storage  
**Time:** 1-2 hours  
**Cost:** FREE

---

## Option 1: Hugging Face (RECOMMENDED - Fastest & Best for ML)

### Prerequisites (5 minutes)

```bash
# 1. Install HF CLI
pip install huggingface_hub

# 2. Login (get token from https://huggingface.co/settings/tokens)
huggingface-cli login

# 3. Create dataset repo
huggingface-cli repo create Athar-Datasets --type dataset
```

### Upload (1-2 hours)

**Method A: Direct Upload (Simple)**

```bash
# Upload entire collections directory
huggingface-cli upload Kandil7/Athar-Datasets data/processed/lucene_pages/collections/ collections/ --repo-type dataset

# This will upload all 10 JSONL files (~10.46 GB)
```

**Method B: Python Script (Better Progress)**

```python
from huggingface_hub import HfApi
from pathlib import Path
import time

api = HfApi()
collections_dir = Path("data/processed/lucene_pages/collections")

COLLECTIONS = [
    "fiqh_passages", "hadith_passages", "quran_tafsir",
    "aqeedah_passages", "seerah_passages", "islamic_history_passages",
    "arabic_language_passages", "spirituality_passages",
    "general_islamic", "usul_fiqh"
]

for collection in COLLECTIONS:
    filepath = collections_dir / f"{collection}.jsonl"
    if filepath.exists():
        size_mb = filepath.stat().st_size / 1e6
        print(f"📤 Uploading {collection} ({size_mb:.1f} MB)...")
        
        start = time.time()
        api.upload_file(
            path_or_fileobj=str(filepath),
            path_in_repo=f"collections/{filepath.name}",
            repo_id="Kandil7/Athar-Datasets",
            repo_type="dataset",
        )
        
        elapsed = time.time() - start
        speed = size_mb / elapsed if elapsed > 0 else 0
        print(f"  ✅ Done! ({speed:.1f} MB/s, {elapsed:.0f}s)")
```

**Method C: Colab Notebook (Easiest)**

1. Open: `notebooks/02_upload_and_embed.ipynb` in Colab
2. Set your HF_TOKEN
3. Run all cells
4. Done! (Uploads + Embeds + Imports to Qdrant)

### Verify Upload

```python
from datasets import load_dataset

# Test loading
ds = load_dataset(
    "json",
    data_files="hf://datasets/Kandil7/Athar-Datasets/collections/fiqh_passages.jsonl",
    split="train"
)

print(f"✅ Loaded {len(ds):,} documents")
```

---

## Option 2: Kaggle (Backup - 100 GB Free)

### Setup (5 minutes)

```bash
# Install Kaggle CLI
pip install kaggle

# Download API token from https://www.kaggle.com/account
# Place in ~/.kaggle/kaggle.json
```

### Upload

```bash
# Create dataset directory
mkdir -p kaggle-upload
cp data/processed/lucene_pages/collections/*.jsonl kaggle-upload/
cp data/processed/master_catalog.json kaggle-upload/
cp data/processed/category_mapping.json kaggle-upload/
cp data/processed/author_catalog.json kaggle-upload/

# Create dataset-metadata.json
cat > kaggle-upload/dataset-metadata.json << 'EOF'
{
  "title": "Athar Islamic Collections",
  "id": "YOUR_USERNAME/athar-islamic-collections",
  "licenses": [{"name": "MIT"}],
  "subtitle": "5.7M Islamic knowledge documents from Shamela Library"
}
EOF

# Upload
cd kaggle-upload
kaggle datasets create -p .
```

---

## Option 3: Google Drive (15 GB Free, Need to Split)

Since collections are 10.46 GB total and Google Drive gives 15 GB free:

```python
from google.colab import drive
drive.mount('/content/drive')

import shutil
from pathlib import Path

# Copy to Google Drive
src = Path("data/processed/lucene_pages/collections")
dst = Path("/content/drive/MyDrive/Athar-Datasets")
dst.mkdir(parents=True, exist_ok=True)

for f in src.glob("*.jsonl"):
    print(f"📤 Uploading {f.name}...")
    shutil.copy(f, dst / f.name)
    print(f"  ✅ Done")
```

---

## Option 4: MEGA.nz (20 GB Free)

```bash
# Install mega-cmd
# https://mega.nz/cmd

# Login
mega-login your@email.com password

# Upload
mega-put data/processed/lucene_pages/collections/*.jsonl /Athar-Datasets/
```

---

## Estimated Upload Times

| Platform | Size | Speed | Time |
|----------|------|-------|------|
| Hugging Face | 10.46 GB | ~5 MB/s | ~35 min |
| Kaggle | 10.46 GB | ~3 MB/s | ~58 min |
| Google Drive | 10.46 GB | ~10 MB/s | ~18 min |
| MEGA.nz | 10.46 GB | ~8 MB/s | ~22 min |

---

## Recommended Strategy

**Upload to ALL platforms for redundancy:**

1. **Primary:** Hugging Face (best for ML/Colab integration)
2. **Backup:** Kaggle (easy to discover)
3. **Archive:** Google Drive (accessible everywhere)

**Total Time:** ~2 hours  
**Total Cost:** FREE  
**Total Storage:** 10.46 GB × 3 = 31.38 GB (all free)

---

## After Upload

### Use in Colab for Embedding

```python
from datasets import load_dataset
from FlagEmbedding import BGEM3FlagModel

# Load collection directly from HF
ds = load_dataset(
    "Kandil7/Athar-Datasets",
    data_files="collections/fiqh_passages.jsonl",
    split="train"
)

# Embed with BGE-M3
model = BGEM3FlagModel('BAAI/bge-m3', use_fp16=True)

# Process in batches...
```

### Use in Athar API

```python
# src/config/settings.py
EMBEDDING_MODEL = "BAAI/bge-m3"
HF_DATASET_REPO = "Kandil7/Athar-Datasets"
```

---

## Quick Commands Summary

```bash
# Hugging Face (RECOMMENDED)
huggingface-cli login
huggingface-cli upload Kandil7/Athar-Datasets data/processed/lucene_pages/collections/ collections/ --repo-type dataset

# Verify
python -c "from datasets import load_dataset; ds = load_dataset('json', data_files='hf://datasets/Kandil7/Athar-Datasets/collections/fiqh_passages.jsonl', split='train'); print(f'✅ {len(ds):,} docs')"
```

---

*Last updated: April 8, 2026*
