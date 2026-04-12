# 🕌 Fix Fiqh Passages Embedding

**Problem:** `fiqh_passages` in Qdrant has corrupted UTF-8 data (literary criticism instead of Islamic fiqh)  
**Source:** `fiqh_passages.jsonl` on disk has CORRECT UTF-8 (7 GB, 2.4M documents)  
**Solution:** Re-embed with BGE-M3 on GPU, upload to Qdrant

---

## Option A: Modal Pipeline (Recommended - Fast)

**Estimated time:** ~20-30 minutes  
**Estimated cost:** ~$3-5 (L4 GPU)

```bash
# Install Modal if needed
pip install modal

# Setup Modal authentication
modal setup

# Run the fix
modal run modal/fix_fiqh_passages.py
```

This will:
1. Load 2.4M passages from local JSONL (correct UTF-8)
2. Embed with BGE-M3 on L4 GPU (~20 min)
3. Upload to Qdrant (~5 min)
4. Verify the collection

---

## Option B: Colab GPU (Free - Slower)

**Estimated time:** ~4-6 hours (T4 free tier)  
**Estimated cost:** $0

### Steps:

1. **Open Colab:** https://colab.research.google.com
2. **Upload notebook:** `notebooks/fix_fiqh_passages.ipynb`
3. **Set GPU:** Runtime → Change runtime type → GPU (T4)
4. **Run all cells**

The notebook will:
1. Download `fiqh_passages.jsonl.gz` from HuggingFace (1.43 GB compressed)
2. Decompress and parse (2.4M passages)
3. Embed with BGE-M3 on T4 GPU
4. Upload to Qdrant via API
5. Verify the collection

**Note:** You need a Qdrant instance accessible from Colab (ngrok tunnel or cloud instance).

---

## What Gets Fixed

| Before | After |
|--------|-------|
| 10,132 corrupted points | 2,397,988 correct points |
| Garbled UTF-8 (mojibake) | Clean Arabic text |
| Literary criticism content | Islamic fiqh content |
| Wrong sources (Taha Hussein) | Correct sources (fiqh books) |

---

## Verification

After running, verify:

```bash
# Check collection
curl -s http://localhost:6333/collections/fiqh_passages | python -m json.tool

# Test query
curl -s -X POST http://localhost:8002/api/v1/query \
  -H "Content-Type: application/json" \
  -d '{"query": "حكم الصيام"}' | python -m json.tool
```

Expected result: LLM returns proper fiqh answer about fasting ruling.

---

## Why This Happened

The original fiqh_passages embeddings were generated on Colab with an incorrect file encoding. The source JSONL file on disk has perfect UTF-8 Arabic text, but the embedding pipeline processed corrupted data.

The other 5 large collections (aqeedah, arabic_language, spirituality, seerah, quran_tafsir) were embedded later with correct encoding and work perfectly.
