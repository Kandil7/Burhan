# 📓 Comprehensive Notebook Review & Action Plan

**Review Date:** April 8, 2026  
**Total Notebooks:** 6  
**Status:** Mixed - Some outdated, some current

---

## 📊 Notebook Inventory

| # | Notebook | Lines | Purpose | Status | Recommendation |
|---|----------|-------|---------|--------|----------------|
| 1 | **02_upload_and_embed.ipynb** | 637 | Complete pipeline (HF → Embed → Qdrant) | ✅ **CURRENT** | **USE THIS** |
| 2 | **verify_upload.ipynb** | 219 | Verify HF uploads | ✅ **CURRENT** | Keep |
| 3 | **01_embed_all_collections.ipynb** | 311 | Old embedding script | ⚠️ **OUTDATED** | Delete or archive |
| 4 | **04_upload_to_huggingface.ipynb** | 289 | Old HF upload | ⚠️ **OUTDATED** | Delete or archive |
| 5 | **05_upload_to_kaggle.ipynb** | 275 | Kaggle upload | ⚠️ **BACKUP ONLY** | Keep as optional |
| 6 | **setup_colab_env.ipynb** | ? | Environment setup | ⚠️ **OUTDATED** | Delete or update |

---

## ✅ MAIN NOTEBOOK: 02_upload_and_embed.ipynb (KEEP & USE)

### Strengths
- ✅ Uses BAAI/bge-m3 (correct model)
- ✅ 12-step complete pipeline
- ✅ Google Drive backup integration
- ✅ Progress tracking with JSON logging
- ✅ Resume capability
- ✅ Error handling per collection
- ✅ Qdrant upload included
- ✅ Test queries included

### Weaknesses
- ⚠️ Very long (637 lines)
- ⚠️ Some redundant comments
- ⚠️ Could be split into 2 notebooks (upload vs embed)

### Issues Found
1. **Line 4**: Says "13 hours (T4 free)" but should clarify this is for ALL collections
2. **Line 76**: HF download might fail for large files (42.6 GB)
3. **Line 133**: BATCH_SIZE = 1024 might be too large for T4 (should be 512)
4. **Line 201**: No check if embeddings already exist before re-embedding
5. **Line 301**: Qdrant upload might timeout for large collections

### Recommended Fixes
```python
# Fix 1: Add file size check before download
import os
if not os.path.exists(filepath):
    snapshot_download(...)

# Fix 2: Reduce batch size for T4
BATCH_SIZE = 512  # Instead of 1024

# Fix 3: Add resume check
if os.path.exists(f"{EMBEDDINGS_DIR}/{collection}_embeddings.npy"):
    print(f"✅ {collection} already embedded, skipping")
    continue
```

---

## ✅ VERIFICATION NOTEBOOK: verify_upload.ipynb (KEEP)

### Strengths
- ✅ Simple and focused
- ✅ Tests all 10 collections
- ✅ Quick execution (10 min)
- ✅ Good for post-upload verification

### Issues
- ⚠️ Only loads from HF, doesn't check local files
- ⚠️ No metadata verification

---

## ⚠️ OUTDATED NOTEBOOKS (SHOULD BE REMOVED)

### 01_embed_all_collections.ipynb
**Why Outdated:**
- Uses old model (Qwen3-Embedding-0.6B instead of BGE-M3)
- Different directory structure
- No HF integration
- No progress tracking

**Action:** DELETE or move to `archive/` folder

### 04_upload_to_huggingface.ipynb
**Why Outdated:**
- Duplicates `scripts/final_upload.py`
- Less robust than Python script version
- No resume capability
- No compression

**Action:** DELETE (use Python script instead)

### 05_upload_to_kaggle.ipynb
**Why Outdated:**
- Kaggle is backup option only
- HuggingFace is primary
- Adds confusion

**Action:** KEEP but move to `archive/` folder

### setup_colab_env.ipynb
**Why Outdated:**
- Old package references
- Superseded by cell 2 in main notebook

**Action:** DELETE

---

## 🎯 RECOMMENDED ACTION PLAN

### Immediate (Before Running Notebooks)

1. **Delete outdated notebooks:**
```bash
rm notebooks/01_embed_all_collections.ipynb
rm notebooks/04_upload_to_huggingface.ipynb
rm notebooks/setup_colab_env.ipynb
```

2. **Archive Kaggle notebook:**
```bash
mkdir -p notebooks/archive
mv notebooks/05_upload_to_kaggle.ipynb notebooks/archive/
```

3. **Fix main notebook issues:**
   - Reduce BATCH_SIZE to 512
   - Add resume checks
   - Add file size warnings

### After Cleanup

**Final Structure:**
```
notebooks/
├── README.md                          # ✅ Guide
├── 02_upload_and_embed.ipynb          # ✅ MAIN (fix & use)
├── verify_upload.ipynb                # ✅ Verification
├── COLAB_GPU_EMBEDDING_GUIDE.md      # ✅ Documentation
├── UPLOAD_STATUS.md                   # ✅ Status tracking
├── google_drive_setup.md             # ✅ Reference
└── archive/
    └── 05_upload_to_kaggle.ipynb      # ⚠️ Backup only
```

---

## 🔧 CRITICAL FIXES FOR 02_upload_and_embed.ipynb

### Fix 1: Reduce Batch Size (Prevents OOM)

**Current (Line ~133):**
```python
BATCH_SIZE = 1024
```

**Should be:**
```python
BATCH_SIZE = 512  # T4 has 16GB VRAM, 1024 may OOM
```

### Fix 2: Add Resume Check (Saves Time)

**Add before embedding loop:**
```python
import os

# Check if already embedded
embedding_file = f"{EMBEDDINGS_DIR}/{collection}_embeddings.npy"
if os.path.exists(embedding_file):
    print(f"✅ {collection} already embedded, loading from disk")
    embeddings = np.load(embedding_file)
    passages = json.load(open(f"{EMBEDDINGS_DIR}/{collection}_passages.json"))
    continue
```

### Fix 3: Better HF Download Error Handling

**Current:** Just calls `snapshot_download()`
**Should be:**
```python
from huggingface_hub import hf_hub_download
import os

# Download collection by collection
for collection in COLLECTIONS:
    filepath = f"{COLLECTIONS_DIR}/{collection}.jsonl.gz"
    if not os.path.exists(filepath):
        try:
            hf_hub_download(
                repo_id=REPO_ID,
                filename=f"collections/{collection}.jsonl.gz",
                repo_type="dataset",
                local_dir="/content/athar-collections"
            )
        except Exception as e:
            print(f"⚠️ Failed to download {collection}: {e}")
            continue
```

### Fix 4: Qdrant Upload Retry Logic

**Current:** No retry
**Should be:**
```python
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
def upload_to_qdrant_with_retry(points, collection_name):
    client.upsert(collection_name=collection_name, points=points)
```

---

## 📋 WORKFLOW RECOMMENDATIONS

### Current Workflow (Confusing)
```
User sees 6 notebooks
→ Doesn't know which to use
→ Might use outdated one
→ Gets errors or wrong model
```

### Recommended Workflow (Clear)
```
User opens notebooks/
→ Sees README.md first
→ Reads "Quick Start" section
→ Opens 02_upload_and_embed.ipynb
→ Runs cells in order
→ Done!
```

---

## 💡 ADDITIONAL RECOMMENDATIONS

### 1. Split Main Notebook (Optional)

**Current:** One huge notebook (637 lines)
**Better:** Two notebooks

**Notebook A:** `01_upload_and_prepare.ipynb`
- Download from HF
- Verify files
- Setup environment
- ~30 minutes

**Notebook B:** `02_embed_and_upload_to_qdrant.ipynb`
- Load model
- Embed collections
- Upload to Qdrant
- Test retrieval
- ~13 hours

**Benefit:** Users can stop/resume between steps

### 2. Add Progress Visualization

```python
# Add this to embedding cell
from tqdm.notebook import tqdm
import matplotlib.pyplot as plt

# Show progress bar
for collection in tqdm(COLLECTIONS, desc="Collections"):
    embed_collection(collection)

# Show completion chart
plt.barh(COLLECTIONS, times)
plt.xlabel("Time (minutes)")
plt.title("Embedding Time per Collection")
plt.show()
```

### 3. Add Cost Calculator

```python
# At the beginning of notebook
print("💰 Cost Estimator")
print(f"Collections: {len(COLLECTIONS)}")
print(f"Total passages: 5.7M")
print(f"Estimated time: 13 hours (T4 free)")
print(f"Estimated cost: $0 (free tier) or $10-15 (A100)")
```

---

## 🎯 FINAL RECOMMENDATION

### DO THIS NOW:

1. **Fix 02_upload_and_embed.ipynb:**
   - Change BATCH_SIZE to 512
   - Add resume checks
   - Add better error handling

2. **Delete outdated notebooks:**
   - 01_embed_all_collections.ipynb
   - 04_upload_to_huggingface.ipynb
   - setup_colab_env.ipynb

3. **Archive Kaggle notebook:**
   - Move to notebooks/archive/

4. **Update README.md:**
   - Clear "which notebook to use" section
   - Remove references to deleted notebooks
   - Add troubleshooting section

### THEN:

5. **Run the fixed notebook on Colab**
6. **Monitor embedding progress**
7. **Verify with verify_upload.ipynb**

---

## 📊 Summary of Issues

| Issue | Severity | Notebook | Fix |
|-------|----------|----------|-----|
| Outdated model | 🔴 High | 01_embed_all_collections | DELETE |
| Wrong batch size | 🟡 Medium | 02_upload_and_embed | Change to 512 |
| No resume checks | 🟡 Medium | 02_upload_and_embed | Add os.path.exists |
| No retry logic | 🟡 Medium | 02_upload_and_embed | Add tenacity |
| Duplicate functionality | 🟢 Low | 04_upload_to_huggingface | DELETE |
| No progress viz | 🟢 Low | 02_upload_and_embed | Add matplotlib |

---

**Bottom Line:** Focus on `02_upload_and_embed.ipynb`, delete the rest, fix the 4 critical issues, then run it on Colab. 🚀
