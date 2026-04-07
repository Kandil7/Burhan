# 🤗 Hugging Face Datasets Setup Guide

Complete guide for uploading and accessing Athar datasets on Hugging Face.

---

## 🎯 Why Hugging Face?

| Feature | Hugging Face | Kaggle | Google Drive |
|---------|--------------|--------|--------------|
| Free Storage | Unlimited | 100 GB | 15 GB |
| Private Datasets | ❌ (Pro only) | ✅ Free | ✅ Free |
| Streaming Support | ✅ Yes | ❌ No | ❌ No |
| Colab Integration | ✅ Excellent | ✅ Good | ✅ Good |
| Version Control | ✅ Git-LFS | ❌ Limited | ❌ No |
| API Access | ✅ Easy | ✅ Moderate | ✅ Moderate |
| Public Demo | ✅ Perfect | ✅ Good | ❌ Limited |

**Recommendation:** Use Hugging Face for public datasets, Kaggle for private team work.

---

## 📋 Prerequisites

1. **Hugging Face Account**
   - Sign up: https://huggingface.co/join
   - Free tier is sufficient

2. **Hugging Face Token**
   - Go to: https://huggingface.co/settings/tokens
   - Create new token with "write" access
   - Copy token for later use

3. **Git-LFS** (for large files)
   - Install: https://git-lfs.com/
   - Or use Colab notebook (pre-installed)

---

## 📤 Upload Methods

### Method 1: Colab Notebook (Recommended)

**Best for:** Most users, no setup required

**Steps:**

1. **Open Notebook**
   - Go to: `notebooks/04_upload_to_huggingface.ipynb`
   - Or: https://colab.research.google.com

2. **Upload Notebook to Colab**
   - File → Upload notebook
   - Select the notebook file

3. **Run All Cells**
   - Runtime → Run all
   - Enter HF token when prompted
   - Wait for upload (2-4 hours)

**Pros:**
- ✅ No local setup
- ✅ GPU available if needed
- ✅ Progress tracking

**Cons:**
- ⚠️ 12-hour session limit
- ⚠️ Upload speed depends on Colab servers

---

### Method 2: Command Line

**Best for:** Developers with fast internet

**Steps:**

```bash
# 1. Install HF CLI
pip install huggingface_hub[cli]

# 2. Login
huggingface-cli login
# Enter your token

# 3. Initialize Git-LFS
git lfs install

# 4. Create dataset repository
huggingface-cli repo create Athar-Datasets --type dataset

# 5. Clone repository
git clone https://huggingface.co/datasets/Kandil7/Athar-Datasets
cd Athar-Datasets

# 6. Copy dataset files
cp -r /path/to/athar-datasets/* .

# 7. Add and commit
git add .
git commit -m "Upload Athar datasets"

# 8. Push (large files via LFS)
git push
```

**Pros:**
- ✅ Full control
- ✅ Resume interrupted uploads
- ✅ Version control

**Cons:**
- ⚠️ Requires git-lfs setup
- ⚠️ 5 GB max file size on free tier

---

### Method 3: Web Interface

**Best for:** Small files only (<50 MB)

**Steps:**

1. Go to: https://huggingface.co/datasets
2. Click "New Dataset"
3. Fill in details
4. Upload files via web interface

**Pros:**
- ✅ Simple
- ✅ No setup

**Cons:**
- ❌ Very slow for large files
- ❌ Max 50 MB per file
- ❌ No resume support

---

## 📂 Dataset Structure

### Required Structure

```
Athar-Datasets/
├── README.md                    # Dataset documentation
├── dataset_info.json            # Metadata
├── extracted_books/
│   ├── part01.tar.gz            # <5 GB chunks
│   ├── part02.tar.gz
│   ├── part03.tar.gz
│   └── part04.tar.gz
├── hadith/
│   └── sanadset.csv             # 1.43 GB
└── metadata/
    ├── categories.json
    ├── books_sample.json
    └── collection_stats.json
```

### File Size Limits

| File Type | Max Size (Free) | Solution |
|-----------|-----------------|----------|
| Regular files | 5 GB | Split into chunks |
| Git-LFS files | 5 GB | Use multiple parts |
| Total dataset | Unlimited | No limit! |

---

## 📥 Access Methods

### Method 1: Hugging Face `datasets` Library

```python
from datasets import load_dataset

# Load entire dataset (downloads first)
dataset = load_dataset("Kandil7/Athar-Datasets")

# Stream (no download needed)
dataset = load_dataset(
    "Kandil7/Athar-Datasets",
    streaming=True
)

# Access data
for item in dataset['train']:
    print(item['text'])
```

### Method 2: Direct Download

```python
from huggingface_hub import hf_hub_download

# Download specific file
file_path = hf_hub_download(
    repo_id="Kandil7/Athar-Datasets",
    filename="hadith/sanadset.csv",
    repo_type="dataset"
)

print(f"Downloaded to: {file_path}")
```

### Method 3: Download with Progress

```python
from huggingface_hub import hf_hub_download
from tqdm import tqdm

# Download with progress bar
files_to_download = [
    "metadata/categories.json",
    "metadata/books_sample.json",
    "hadith/sanadset.csv",
]

for filename in files_to_download:
    print(f"📥 Downloading: {filename}")
    path = hf_hub_download(
        repo_id="Kandil7/Athar-Datasets",
        filename=filename,
        repo_type="dataset"
    )
    print(f"   ✅ Saved to: {path}")
```

### Method 4: In Colab

```python
from huggingface_hub import login, hf_hub_download

# Login
login()  # Uses token from secrets

# Download
path = hf_hub_download(
    repo_id="Kandil7/Athar-Datasets",
    filename="hadith/sanadset.csv",
    repo_type="dataset"
)

# Use in pandas
import pandas as pd
df = pd.read_csv(path)
print(f"Loaded {len(df)} hadith")
```

---

## 🔧 Troubleshooting

### Upload Fails with "File Too Large"

**Problem:** Git rejects files >5 GB

**Solution:** Split files into smaller chunks:

```bash
# Split tar.gz into 4 GB parts
split -b 4G large_file.tar.gz large_file.tar.gz.part

# Upload each part
git add large_file.tar.gz.part*
git commit -m "Add chunked dataset"
git push
```

### Git-LFS Not Working

**Problem:** Files uploaded as pointers, not actual data

**Solution:**
```bash
# Install git-lfs
git lfs install

# Track large files
git lfs track "*.tar.gz"
git lfs track "*.csv"

# Re-add and commit
git add .
git commit -m "Fix LFS tracking"
git push
```

### Download is Slow

**Problem:** Slow download speeds

**Solution:** Use streaming instead of download:

```python
from datasets import load_dataset

# Stream data (no download)
dataset = load_dataset(
    "Kandil7/Athar-Datasets",
    streaming=True,
    split="train"
)

# Access data on-demand
for item in dataset:
    process(item)  # Data fetched as needed
```

### Authentication Error

**Problem:** "Invalid token" error

**Solution:**
1. Generate new token: https://huggingface.co/settings/tokens
2. Make sure token has "write" access
3. Login again:
   ```bash
   huggingface-cli login --token YOUR_TOKEN
   ```

---

## 💡 Best Practices

### 1. Chunk Large Files

```python
# Before upload, split into <5 GB chunks
import tarfile
import os

def create_chunks(source_dir, output_dir, chunk_size=4*1024**3):
    """Split directory into chunks."""
    files = list(source_dir.rglob('*.txt'))
    chunk_num = 0
    current_size = 0
    current_files = []
    
    for f in files:
        size = f.stat().st_size
        if current_size + size > chunk_size and current_files:
            # Write chunk
            chunk_path = output_dir / f"part{chunk_num:02d}.tar.gz"
            with tarfile.open(chunk_path, 'w:gz') as tar:
                for cf in current_files:
                    tar.add(cf)
            chunk_num += 1
            current_files = []
            current_size = 0
        
        current_files.append(f)
        current_size += size
    
    # Last chunk
    if current_files:
        chunk_path = output_dir / f"part{chunk_num:02d}.tar.gz"
        with tarfile.open(chunk_path, 'w:gz') as tar:
            for cf in current_files:
                tar.add(cf)
```

### 2. Use Streaming for Large Datasets

```python
from datasets import load_dataset

# Don't download everything
dataset = load_dataset(
    "Kandil7/Athar-Datasets",
    streaming=True
)

# Process without downloading
for book in dataset['extracted_books']:
    analyze(book['text'])
```

### 3. Version Your Datasets

```bash
# Tag releases
git tag -a v1.0.0 -m "Initial dataset release"
git push origin v1.0.0

# Use specific version
from datasets import load_dataset
dataset = load_dataset(
    "Kandil7/Athar-Datasets",
    revision="v1.0.0"  # Specific version
)
```

---

## 📊 Cost Comparison

| Platform | Storage | Bandwidth | Features | Cost |
|----------|---------|-----------|----------|------|
| **Hugging Face** | Unlimited | Unlimited | Streaming, Version Control | **Free** |
| Kaggle | 100 GB | Limited | Private Datasets | **Free** |
| Google Drive | 15 GB | Limited | Team Sharing | **Free** / $2/mo |
| AWS S3 | 5 GB free | $0.09/GB | Enterprise | **Pay per use** |
| GCP Storage | 5 GB free | $0.12/GB | Enterprise | **Pay per use** |

---

## 🔗 Quick Links

- **Hugging Face:** https://huggingface.co
- **Create Token:** https://huggingface.co/settings/tokens
- **Documentation:** https://huggingface.co/docs/hub
- **Datasets Guide:** https://huggingface.co/docs/datasets
- **Git-LFS:** https://git-lfs.com/

---

*Last updated: April 7, 2026*
