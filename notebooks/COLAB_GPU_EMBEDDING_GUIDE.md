# 🚀 Colab GPU Embedding Setup Guide - Burhan Islamic QA System

## Complete Step-by-Step Instructions

This guide walks you through embedding 5.7M documents from 10 collections using Google Colab's free T4 GPU and uploading to Qdrant.

---

## 📋 Prerequisites

### What You Need:
1. ✅ Google account (for Colab)
2. ✅ HuggingFace account (for datasets)
3. ✅ Qdrant instance (local or cloud)
4. ✅ HF token (hf_...)
5. ✅ ~8 hours of Colab time

### Data Location Options:
- **Option A:** Download from HuggingFace (Kandil7/Burhan-Datasets)
- **Option B:** Upload from local machine (42.6 GB)
- **Option C:** Use Google Drive (upload first, then Colab)

---

## 🎯 Step 1: Open Colab Notebook

### Quick Start:
1. Go to: https://colab.research.google.com
2. Click: **File → Upload notebook**
3. Upload: `notebooks/02_upload_and_embed.ipynb`
4. Select runtime: **GPU (T4)**

### Runtime Settings:
- **Runtime type:** Python 3
- **Hardware accelerator:** GPU
- **GPU type:** T4 (free) or A100 (paid, faster)
- **RAM:** High RAM (if available)

---

## 📦 Step 2: Install Dependencies (5 minutes)

Run the first cell in notebook:

```python
# Install required packages
!pip install -q transformers torch qdrant-client datasets tqdm

# Verify GPU
import torch
print(f"GPU: {torch.cuda.get_device_name(0)}")
print(f"GPU Memory: {torch.cuda.get_device_properties(0).total_mem / 1e9:.1f} GB")
```

**Expected output:**
```
GPU: Tesla T4
GPU Memory: 15.8 GB
```

---

## 📥 Step 3: Get Collections Data (15-30 minutes)

### Option A: Download from HuggingFace (RECOMMENDED)

```python
from huggingface_hub import snapshot_download

# Download all collections
snapshot_download(
    repo_id="Kandil7/Burhan-Datasets",
    local_dir="/content/Burhan-collections",
    repo_type="dataset"
)

# Verify
!ls -lh /content/Burhan-collections/
```

### Option B: Upload from Google Drive

```python
from google.colab import drive
drive.mount('/content/drive')

# Copy to working directory
!cp -r /content/drive/MyDrive/Burhan-Collections /content/Burhan-collections
```

### Option C: Upload Directly

```python
from google.colab import files
uploaded = files.upload()  # Upload JSONL files one by one
```

---

## 🔧 Step 4: Configure Settings (2 minutes)

```python
# Collection names
COLLECTIONS = [
    "fiqh_passages",
    "hadith_passages",
    "quran_tafsir",
    "aqeedah_passages",
    "seerah_passages",
    "islamic_history_passages",
    "arabic_language_passages",
    "spirituality_passages",
    "general_islamic",
    "usul_fiqh",
]

# Paths
COLLECTIONS_DIR = "/content/Burhan-collections/collections"

# Qdrant configuration
QDRANT_URL = "http://your-qdrant-url:6333"
QDRANT_API_KEY = "your-api-key"

# Embedding settings
BATCH_SIZE = 1024  # Reduce if OOM
MAX_LENGTH = 8192  # BGE-M3 max tokens
```

---

## 🤖 Step 5: Load Embedding Model (3 minutes)

```python
from transformers import AutoModel, AutoTokenizer
import torch

print("Loading BAAI/bge-m3 model...")
tokenizer = AutoTokenizer.from_pretrained("BAAI/bge-m3")
model = AutoModel.from_pretrained("BAAI/bge-m3")

# Move to GPU
device = "cuda" if torch.cuda.is_available() else "cpu"
model.to(device)
model.eval()

print(f"✅ Model loaded on {device}")
```

---

## ⚡ Step 6: Embed Collections (6-8 hours)

### Process One Collection at a Time:

```python
import json
import time
from tqdm import tqdm

def embed_collection(collection_name):
    """Embed single collection and return (passages, embeddings)."""
    filepath = f"{COLLECTIONS_DIR}/{collection_name}.jsonl"
    
    # Load passages
    passages = []
    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            passages.append(json.loads(line))
    
    print(f"📚 {collection_name}: {len(passages):,} passages")
    
    # Embed in batches
    all_embeddings = []
    contents = [p.get('content', '') for p in passages]
    
    for i in tqdm(range(0, len(contents), BATCH_SIZE), 
                  desc=f"Embedding {collection_name}"):
        batch = contents[i:i + BATCH_SIZE]
        
        # Tokenize
        encoded = tokenizer(
            batch,
            padding=True,
            truncation=True,
            max_length=MAX_LENGTH,
            return_tensors='pt'
        ).to(device)
        
        # Embed
        with torch.no_grad():
            outputs = model(**encoded)
            embeddings = outputs.last_hidden_state[:, 0, :]
            embeddings = torch.nn.functional.normalize(embeddings, p=2, dim=1)
        
        all_embeddings.extend(embeddings.cpu().tolist())
    
    print(f"✅ {collection_name}: {len(all_embeddings):,} embeddings generated")
    return passages, all_embeddings

# Process all collections
for collection in COLLECTIONS:
    start = time.time()
    passages, embeddings = embed_collection(collection)
    elapsed = time.time() - start
    print(f"⏱️  Time: {elapsed/60:.1f} minutes")
    
    # Save embeddings for later upload
    import numpy as np
    np.save(f"/content/{collection}_embeddings.npy", embeddings)
    
    # Clear GPU memory
    torch.cuda.empty_cache()
```

**Expected Timeline:**

| Collection | Passages | Time |
|------------|----------|------|
| seerah | 100K | ~20 min |
| usul_fiqh | 150K | ~25 min |
| spirituality | 200K | ~30 min |
| aqeedah | 300K | ~40 min |
| arabic_language | 400K | ~50 min |
| quran_tafsir | 800K | ~1.5 hr |
| islamic_history | 900K | ~1.7 hr |
| general_islamic | 1M | ~2 hr |
| fiqh | 1.2M | ~2.2 hr |
| hadith | 2M | ~3.5 hr |
| **TOTAL** | **7.05M** | **~13 hours** |

---

## 💾 Step 7: Save to Google Drive (Backup)

```python
# Save embeddings to Drive (avoid losing progress)
from google.colab import drive
drive.mount('/content/drive')

import os
os.makedirs('/content/drive/MyDrive/Burhan-Embeddings', exist_ok=True)

for collection in COLLECTIONS:
    src = f"/content/{collection}_embeddings.npy"
    dst = f"/content/drive/MyDrive/Burhan-Embeddings/{collection}_embeddings.npy"
    if os.path.exists(src):
        !cp {src} {dst}
        print(f"✅ Saved {collection} embeddings")
```

---

## 📤 Step 8: Upload to Qdrant (1-2 hours)

```python
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct

# Connect to Qdrant
client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)

def upload_to_qdrant(collection_name, passages, embeddings):
    """Upload embeddings to Qdrant collection."""
    
    # Create collection if not exists
    try:
        client.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(size=1024, distance=Distance.COSINE)
        )
        print(f"✅ Created collection: {collection_name}")
    except Exception as e:
        print(f"⚠️  Collection exists: {e}")
    
    # Prepare points
    points = []
    for i, (passage, embedding) in enumerate(zip(passages, embeddings)):
        payload = {
            "content": passage.get("content", ""),
            "book_id": passage.get("book_id"),
            "title": passage.get("title", ""),
            "author": passage.get("author", ""),
            "author_death": passage.get("author_death"),
            "page": passage.get("page"),
            "chapter": passage.get("chapter", ""),
            "section": passage.get("section", ""),
            "category": passage.get("category", ""),
            "collection": collection_name,
        }
        
        points.append(PointStruct(
            id=i,
            vector=embedding,
            payload=payload
        ))
    
    # Upload in batches
    batch_size = 1000
    for i in tqdm(range(0, len(points), batch_size), desc="Uploading"):
        batch = points[i:i + batch_size]
        client.upsert(collection_name=collection_name, points=batch)
    
    print(f"✅ Uploaded {len(points):,} vectors to {collection_name}")

# Upload all collections
for collection in COLLECTIONS:
    # Load embeddings
    embeddings = np.load(f"/content/{collection}_embeddings.npy")
    passages = json.load(open(f"/content/{collection}_passages.json"))
    
    upload_to_qdrant(collection, passages, embeddings)
```

---

## ✅ Step 9: Verify Upload

```python
# Verify each collection
for collection in COLLECTIONS:
    info = client.get_collection(collection)
    print(f"📊 {collection}:")
    print(f"  Vectors: {info.points_count:,}")
    print(f"  Status: {info.status}")
    print(f"  Indexed vectors: {info.indexed_vectors_count:,}")
    print()
```

**Expected output:**
```
📊 fiqh_passages:
  Vectors: 1,200,000
  Status: green
  Indexed vectors: 1,200,000

📊 hadith_passages:
  Vectors: 2,000,000
  Status: green
  Indexed vectors: 2,000,000

... (all 10 collections)
```

---

## 🧪 Step 10: Test Retrieval

```python
# Test semantic search
def test_search(query, collection="fiqh_passages", top_k=5):
    """Test retrieval quality."""
    # Embed query
    encoded = tokenizer(query, return_tensors='pt').to(device)
    with torch.no_grad():
        outputs = model(**encoded)
        query_embedding = outputs.last_hidden_state[:, 0, :].cpu().tolist()[0]
    
    # Search Qdrant
    results = client.search(
        collection_name=collection,
        query_vector=query_embedding,
        limit=top_k
    )
    
    print(f"Query: {query}")
    print(f"Collection: {collection}")
    print(f"Results: {len(results)}\n")
    
    for i, result in enumerate(results):
        print(f"[{i+1}] Score: {result.score:.3f}")
        print(f"    Author: {result.payload.get('author')}")
        print(f"    Book: {result.payload.get('title')}")
        print(f"    Chapter: {result.payload.get('chapter')}")
        print(f"    Content: {result.payload['content'][:200]}...")
        print()

# Test queries
test_search("ما حكم صلاة الجماعة؟", "fiqh_passages")
test_search("حديث عن الصلاة", "hadith_passages")
test_search("التوحيد والإيمان", "aqeedah_passages")
```

---

## 💰 Cost Estimation

### Free Tier (T4 GPU):
- **Time:** 13 hours embedding + 2 hours upload = 15 hours
- **Colab limits:** 12-hour sessions (may need to resume)
- **Cost:** FREE

### Paid Tier (A100 GPU):
- **Time:** 3-4 hours (4x faster)
- **Cost:** ~$10-15 (Colab Pro)

### Qdrant Options:
- **Local:** Free (your hardware)
- **Qdrant Cloud:** Free tier (1 collection, 1GB)
- **Self-hosted:** ~$50/month (4GB RAM instance)

---

## ⚠️ Common Issues & Solutions

### Issue 1: Out of Memory (OOM)
**Solution:** Reduce batch size
```python
BATCH_SIZE = 512  # or 256
```

### Issue 2: Colab Disconnects
**Solution:** Save embeddings to Drive frequently
```python
# Save every 30 minutes
if time.time() - last_save > 1800:
    np.save(f"/content/drive/MyDrive/Burhan-Embeddings/{collection}_embeddings.npy", embeddings)
```

### Issue 3: Qdrant Upload Too Slow
**Solution:** Increase batch size
```python
batch_size = 5000  # Instead of 1000
```

### Issue 4: Download from HF Too Slow
**Solution:** Use Google Drive instead
```python
# Upload to Drive first, then mount in Colab
```

---

## 📊 Progress Tracking

Create a progress tracker:

```python
import json
from datetime import datetime

progress_file = "/content/embedding_progress.json"

def log_progress(collection, status, elapsed):
    progress = {
        "collection": collection,
        "status": status,  # "started", "embedded", "uploaded", "failed"
        "elapsed_minutes": elapsed / 60,
        "timestamp": datetime.now().isoformat()
    }
    
    with open(progress_file, 'a') as f:
        f.write(json.dumps(progress) + '\n')
    
    print(f"📝 Logged: {collection} - {status}")

# Check progress
!cat /content/embedding_progress.json | python -m json.tool
```

---

## 🎯 Next Steps After Completion

1. ✅ Verify all 10 collections in Qdrant
2. ✅ Test retrieval with sample queries
3. ✅ Update Burhan config to use Qdrant
4. ✅ Run integration tests
5. ✅ Deploy to production

---

## 📞 Support

If you encounter issues:
1. Check Colab GPU is enabled (Runtime → Change runtime type → GPU)
2. Verify HuggingFace token is valid
3. Ensure Qdrant is accessible from Colab
4. Check GPU memory usage: `!nvidia-smi`
5. Monitor disk space: `!df -h`

---

**Estimated Total Time:** 15 hours (free) or 4 hours (paid A100)  
**Estimated Cost:** FREE - $15  
**Expected Result:** 7M+ vectors across 10 collections in Qdrant
