#!/usr/bin/env python3
"""
Update README.md on HuggingFace dataset repository.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

from huggingface_hub import HfApi

# Configuration
REPO_ID = "Kandil7/Athar-Datasets"
LOCAL_TOKEN = os.getenv("HF_TOKEN") or os.getenv("HF_HUB_TOKEN")

# New README content
README_CONTENT = """---
language:
- ar
- en
license: mit
task_categories:
- question-answering
- text-generation
- text-retrieval
- fill-mask
pretty_name: Burhan Islamic QA Datasets
tags:
- islamic-studies
- quran
- hadith
- fiqh
- arabic
- rag
- multi-agent
- citation-grounded
dataset_info:
  features:
  - name: content
    dtype: string
  - name: content_type
    dtype: string
  - name: book_id
    dtype: int64
  - name: book_title
    dtype: string
  - name: category
    dtype: string
  - name: author
    dtype: string
  - name: author_death
    dtype: int64
  - name: collection
    dtype: string
  - name: page_number
    dtype: int64
  - name: section_title
    dtype: string
  - name: hierarchy
    sequence: string
  - name: title
    dtype: string
  - name: chapter
    dtype: string
  - name: section
    dtype: string
  - name: page
    dtype: int64
  splits:
  - name: train
    num_examples: 100000
  config:
  - name: default
    data_files:
    - path: aqeedah_passages.jsonl
    - path: arabic_language_passages.jsonl
    - path: fiqh_passages.jsonl
    - path: general_islamic.jsonl
    - path: hadith_passages.jsonl
    - path: islamic_history_passages.jsonl
    - path: quran_tafsir.jsonl
    - path: seerah_passages.jsonl
    - path: spirituality_passages.jsonl
    - path: usul_fiqh.jsonl
---

# 🕌 Burhan Islamic QA Datasets (Mini Dataset v2)

> **100,000 passages from 10 classical Islamic collections — a sampling of 1.4M years of scholarship**

A streamlined subset of the full Burhan Islamic QA dataset, containing 10,000 passages per collection across 10 major Islamic disciplines. Perfect for testing, development, and prototyping RAG-based Islamic QA systems.

**Based on the Fanar-Sadiq Architecture** for grounded, citation-backed Islamic question answering.

---

## 📊 Dataset Summary

| Metric | Value |
|--------|-------|
| **Total Passages** | 100,000 |
| **Samples per Collection** | 10,000 |
| **Collections** | 10 |
| **Languages** | Arabic (primary), English (metadata) |
| **Format** | JSONL |
| **Size** | ~235 MB |

---

## 📚 Collections

| # | Collection | Passages | Description |
|---|------------|----------|-------------|
| 1 | `aqeedah_passages` | 10,000 | Islamic creed and theology |
| 2 | `arabic_language_passages` | 10,000 | Arabic grammar and linguistics |
| 3 | `fiqh_passages` | 10,000 | Islamic jurisprudence |
| 4 | `general_islamic` | 10,000 | General Islamic knowledge |
| 5 | `hadith_passages` | 10,000 | Prophetic traditions |
| 6 | `islamic_history_passages` | 10,000 | Islamic history |
| 7 | `quran_tafsir` | 10,000 | Quranic exegesis |
| 8 | `seerah_passages` | 10,000 | Prophet Muhammad's biography |
| 9 | `spirituality_passages` | 10,000 | Islamic spirituality and Sufism |
| 10 | `usul_fiqh` | 10,000 | Principles of Islamic jurisprudence |

---

## 📋 Schema

Each passage contains the following fields:

| Field | Type | Description |
|-------|------|-------------|
| `content` | string | Main passage text (Arabic) |
| `content_type` | string | Type of content |
| `book_id` | int64 | Unique book identifier |
| `book_title` | string | Title of the source book |
| `category` | string | Category (e.g., "العقيدة", "الفقه") |
| `author` | string | Author name |
| `author_death` | int64 | Author's death year (Hijri) |
| `collection` | string | Collection name |
| `page_number` | int64 | Page number in source |
| `section_title` | string | Section heading |
| `hierarchy` | list | Hierarchical path [book, chapter, section] |
| `title` | string | Passage title |
| `chapter` | string | Chapter name |
| `section` | string | Section name |
| `page` | int64 | Page number |

### Example Entry

```json
{
  "content": "الحمد لله نحمده ونستعينه ونستغفره، ونعوذ بالله من شرور أنفسنا...",
  "book_id": 1234,
  "book_title": "الفوائد العذاب في الرد على من لم يحكم السنة والكتاب",
  "category": "العقيدة",
  "author": "حمد بن ناصر آل معمر",
  "author_death": 1225,
  "collection": "aqeedah_passages",
  "page_number": 1,
  "section_title": "مقدمة المحقق",
  "hierarchy": ["الفوائد العذاب", "مقدمة المحقق"],
  "title": "مقدمة المحقق",
  "chapter": null,
  "section": null,
  "page": 1
}
```

---

## 🔧 How to Load

### Using HuggingFace Datasets

```python
from datasets import load_dataset

# Load the full dataset (all collections)
ds = load_dataset("Kandil7/Athar-Datasets")

# Load a specific collection
ds = load_dataset("Kandil7/Athar-Datasets", split="train")

# Access specific collection
for row in ds:
    if row['collection'] == 'fiqh_passages':
        print(row['content'][:100])
        break
```

### Using JSONL Files Directly

```python
import json

# Load a specific collection file
with open('fiqh_passages.jsonl', 'r', encoding='utf-8') as f:
    passages = [json.loads(line) for line in f]

print(f"Loaded {len(passages):,} fiqh passages")
```

### Streaming Mode (Memory Efficient)

```python
from datasets import load_dataset

# Stream data without downloading
ds = load_dataset("Kandil7/Athar-Datasets", split="train", streaming=True)

for i, passage in enumerate(ds):
    if i >= 5:
        break
    print(f"{passage['collection']}: {passage['title']}")
```

---

## 💡 Usage Examples

### Example 1: Basic QA with RAG

```python
from sentence_transformers import SentenceTransformer
import numpy as np

# Load embedding model
model = SentenceTransformer('BAAI/bge-m3')

# Load a sample collection
with open('fiqh_passages.jsonl', 'r', encoding='utf-8') as f:
    passages = [json.loads(line) for line in f]

# Create embeddings
texts = [p['content'] for p in passages[:1000]]
embeddings = model.encode(texts)

# Search
query = "ما حكم صلاة الجماعة؟"
query_embedding = model.encode([query])[0]

# Find most similar
scores = np.dot(embeddings, query_embedding)
top_idx = np.argsort(scores)[-5:][::-1]

for idx in top_idx:
    print(f"Score: {scores[idx]:.3f}")
    print(passages[idx]['content'][:200])
    print("---")
```

### Example 2: Filter by Collection

```python
from datasets import load_dataset

ds = load_dataset("Kandil7/Athar-Datasets", split="train")

# Get only hadith passages
hadith_only = ds.filter(lambda x: x['collection'] == 'hadith_passages')
print(f"Hadith passages: {len(hadith_only):,}")

# Get only Aqeedah passages
aqeedah_only = ds.filter(lambda x: x['collection'] == 'aqeedah_passages')
print(f"Aqeedah passages: {len(aqeedah_only):,}")
```

### Example 3: Analyze Author Distribution

```python
from datasets import load_dataset
from collections import Counter

ds = load_dataset("Kandil7/Athar-Datasets", split="train")

# Count authors per collection
author_counts = Counter()
for row in ds:
    author_counts[row['collection']] += 1

for coll, count in author_counts.most_common():
    print(f"{coll}: {count:,} passages")
```

---

## 📊 Collection Statistics

| Collection | Records | Size (MB) |
|------------|---------|-----------|
| aqeedah_passages | 10,000 | ~25 MB |
| arabic_language_passages | 10,000 | ~24 MB |
| fiqh_passages | 10,000 | ~27 MB |
| general_islamic | 10,000 | ~22 MB |
| hadith_passages | 10,000 | ~29 MB |
| islamic_history_passages | 10,000 | ~19 MB |
| quran_tafsir | 10,000 | ~18 MB |
| seerah_passages | 10,000 | ~23 MB |
| spirituality_passages | 10,000 | ~24 MB |
| usul_fiqh | 10,000 | ~25 MB |
| **Total** | **100,000** | **~235 MB** |

---

## 🔗 Related Datasets

### Full Dataset (15.7M passages)

The complete Burhan dataset with 15.7M passages from 8,425 books:

- **URL:** https://huggingface.co/datasets/Kandil7/Athar-Datasets
- **Size:** ~4.3 GB compressed
- **Passages:** 15,700,000+

### This Mini Dataset

A balanced subset for development and testing:

- **URL:** https://huggingface.co/datasets/Kandil7/Athar-Datasets
- **Size:** ~235 MB
- **Passages:** 100,000 (10K per collection)

---

## 🏗️ Parent Project: Burhan

Burhan is a production-ready Islamic QA system built on this dataset:

- **GitHub:** https://github.com/Kandil7/Burhan
- **Architecture:** Fanar-Sadiq Multi-Agent System
- **Features:**
  - Grounded, citation-backed answers
  - Multi-collection retrieval
  - Hadith grading and verification
  - Quote validation

### Key Papers

- [Fanar-Sadiq: A Multi-Agent Architecture for Grounded Islamic QA](docs/Fanar-Sadiq%20A%20Multi-Agent%20Architecture%20for%20Grounded%20Islamic%20QA.pdf)

---

## 📝 Citation

If you use this dataset, please cite:

```bibtex
@misc{Burhan-mini-dataset-v2-2026,
  title={Burhan Islamic QA Datasets (Mini Dataset v2)},
  author={Kandil, Ahmed},
  year={2026},
  url={https://huggingface.co/datasets/Kandil7/Athar-Datasets},
  note={100K passages from 10 Islamic collections}
}
```

---

## ⚠️ Usage Notes

1. **Scholarly Context:** These texts represent classical Islamic scholarship. Always consult qualified scholars for religious rulings.

2. **Hadith Authenticity:** Hadith passages include chains of narration. Use authenticity grading to evaluate reliability.

3. **Fiqh Diversity:** The fiqh collection represents multiple schools of thought (Hanafi, Maliki, Shafi'i, Hanbali).

4. **Language:** Primary content is in Classical Arabic. Metadata includes English translations.

5. **Licensing:** MIT License — free for research and commercial use.

---

## 📁 File Structure

```
Kandil7/Athar-Datasets/
├── aqeedah_passages.jsonl           # 10,000 passages
├── arabic_language_passages.jsonl    # 10,000 passages
├── fiqh_passages.jsonl               # 10,000 passages
├── general_islamic.jsonl             # 10,000 passages
├── hadith_passages.jsonl             # 10,000 passages
├── islamic_history_passages.jsonl    # 10,000 passages
├── quran_tafsir.jsonl                # 10,000 passages
├── seerah_passages.jsonl             # 10,000 passages
├── spirituality_passages.jsonl       # 10,000 passages
├── usul_fiqh.jsonl                   # 10,000 passages
└── stats.json                        # Dataset statistics
```

---

## 📞 Contact & Support

- **GitHub:** https://github.com/Kandil7/Burhan
- **HuggingFace:** https://huggingface.co/Kandil7

---

<div align="center">

**Built with ❤️ for the Muslim community**

🕌 Burhan Islamic QA • 100K passages • 10 collections • 1,400 years of scholarship

</div>
"""


def main():
    if not LOCAL_TOKEN:
        print("ERROR: HF_TOKEN not found in environment!")
        print("Please add HF_TOKEN to your .env file")
        return

    print("=" * 60)
    print("Updating README.md on HuggingFace")
    print("=" * 60)

    api = HfApi(token=LOCAL_TOKEN)

    # Upload the README
    api.upload_file(
        path_or_fileobj=README_CONTENT.encode("utf-8"),
        path_in_repo="README.md",
        repo_id=REPO_ID,
        repo_type="dataset",
        commit_message="Update README with Mini Dataset v2 documentation (100K passages)",
    )

    print("\n" + "=" * 60)
    print("README Updated Successfully!")
    print("=" * 60)
    print(f"\nDataset URL: https://huggingface.co/datasets/{REPO_ID}")


if __name__ == "__main__":
    main()
