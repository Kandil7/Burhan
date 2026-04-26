# Dataset Preparation & Upload Guide

## Quick Reference

### 1. Prepare Datasets

```bash
python scripts/prepare_datasets_for_upload.py
```

**What it does:**
- ✅ Chunks extracted books into <500 MB archives
- ✅ Copies hadith CSV (if <5 GB)
- ✅ Prepares metadata files
- ✅ Creates README and dataset_info.json

**Output:** `data/Burhan-datasets/` directory with upload-ready files

**Expected Time:** 1-2 hours (compressing 16 GB of books)

**Progress:**
- Books: Split into ~32 chunks of 500 MB each
- Hadith: 1 file (1.3 GB, under 5 GB limit)
- Metadata: 3 JSON files

---

### 2. Upload to Hugging Face

**Option A: Use Colab Notebook (Recommended)**
```
1. Open notebooks/04_upload_to_huggingface.ipynb
2. Upload to Google Colab
3. Runtime → Change runtime type → T4 GPU (optional)
4. Runtime → Run all
5. Enter HF token when prompted
6. Wait 2-4 hours for upload
```

**Option B: Use Command Line**
```bash
# Install HF CLI
pip install huggingface_hub[cli]

# Login
huggingface-cli login

# Create repo
huggingface-cli repo create Kandil7/Athar-Datasets --type dataset

# Clone
git clone https://huggingface.co/datasets/Kandil7/Athar-Datasets
cd Athar-Datasets

# Copy files
cp -r ../data/Burhan-datasets/* .

# Commit with git-lfs
git lfs install
git add .
git commit -m "Upload Burhan datasets"
git push
```

---

### 3. Upload to Kaggle (Optional Backup)

```
1. Open notebooks/05_upload_to_kaggle.ipynb
2. Upload to Google Colab
3. Run all cells
4. Enter Kaggle credentials
5. Wait 1-2 hours
```

---

## Current Status

### ✅ Fixed Issues
- Hadith size detection now correct (1.3 GB)
- Auto-detects Sanadset directory structure
- Proper metadata copying

### ⏳ In Progress
- Book chunking (16 GB → ~32 chunks)

### 📊 Expected Output

```
data/Burhan-datasets/
├── README.md
├── dataset_info.json
├── extracted_books/
│   ├── extracted_books_part01.tar.gz  (500 MB)
│   ├── extracted_books_part02.tar.gz  (500 MB)
│   ├── ... (30 more chunks)
│   └── extracted_books_part32.tar.gz
├── hadith/
│   └── sanadset.csv                   (1.3 GB)
└── metadata/
    ├── categories.json
    ├── books.json
    └── authors.json
```

**Total Size:** ~17.3 GB

---

## Tips

### Speed Up Compression
- The script uses gzip compression which is CPU-intensive
- Can take 1-2 hours for 16 GB
- **Let it run in the background**

### Check Progress
The script shows progress as it creates each chunk:
```
✅ Created extracted_books_part01.tar.gz: 124.5 MB
✅ Created extracted_books_part02.tar.gz: ...
```

### Resume If Interrupted
If script is interrupted, the chunks already created are saved.
Just re-run the script - it will overwrite incomplete chunks.

### Upload Strategy
1. **Start with mini-dataset** (1.7 MB) to test upload process
2. **Then upload full dataset** when ready
3. **Use Colab** for faster upload speeds

---

## Troubleshooting

### "No space left on device"
- Clean up temp files
- Ensure enough disk space for both source + compressed files
- Need ~32 GB free space total

### Upload too slow
- Use Colab (better internet connection)
- Upload during off-peak hours
- Consider using Kaggle instead (faster upload)

### Git-LFS quota exceeded
- Hugging Face free tier has unlimited LFS storage
- If you hit limits, split into multiple repositories

---

*Last updated: April 7, 2026*
