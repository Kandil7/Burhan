#!/usr/bin/env python3
"""
Revert README.md to original full dataset version.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

from huggingface_hub import HfApi

# Configuration
REPO_ID = "Kandil7/Athar-Datasets"
LOCAL_TOKEN = os.getenv("HF_TOKEN") or os.getenv("HF_HUB_TOKEN")

# Original README content (full 15.7M dataset)
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
pretty_name: Athar Islamic QA Datasets
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
    num_bytes: 42600000000
    num_examples: 5700000
  download_size: 4300000000
  dataset_size: 42600000000
---

# 🕌 Athar Islamic QA Datasets

> **15.7M passages from 8,425 classical Islamic books spanning 1,400 years of scholarship**

A comprehensive collection of Islamic texts covering Quran, Hadith, Fiqh, Tafsir, Aqeedah, Seerah, and more — sourced from the Shamela library and enriched with scholarly metadata for RAG-based Islamic QA systems.

**Based on the Fanar-Sadiq Architecture** for grounded, citation-backed Islamic question answering.

---

## 📊 Dataset Summary

| Metric | Value |
|--------|-------|
| **Total Passages** | 15,700,000+ |
| **Total Source Books** | 8,425 |
| **Total Scholars** | 3,146 |
| **Time Span** | 0-1400 AH (7th-21st century CE) |
| **Original Size** | 42.6 GB |
| **Compressed Size** | ~4.3 GB |
| **Collections** | 10 |
| **Languages** | Arabic (primary), English (metadata) |

---

## 📚 Collections

### 1. `hadith_passages` (2M passages, 11 GB)

Prophetic traditions from the six canonical hadith collections (Kutub al-Sittah) plus Musnad collections.

| Feature | Details |
|---------|---------|
| Source Books | Sahih Bukhari, Sahih Muslim, Sunan Abu Dawud, Jami' al-Tirmidhi, Sunan al-Nasa'i, Sunan Ibn Majah |
| Includes | Sanad (chain of narrators) and Matn (text) |
| Authenticity Data | ✅ Esnad chain data available |
| Time Period | 0-300 AH |

**Schema:**
```json
{
  "content": "حديث: عن أبي هريرة رضي الله عنه قال...",
  "book_id": 627,
  "title": "صحيح البخاري",
  "author": "Imam Bukhari",
  "author_death": 256,
  "page": 45,
  "chapter": "كتاب الصلاة",
  "section": "باب الأذان",
  "category": "صحيح",
  "collection": "hadith_passages"
}
```

---

### 2. `fiqh_passages` (1.2M passages, 7 GB)

Islamic jurisprudence from all four major Sunni schools (Hanafi, Maliki, Shafi'i, Hanbali).

| Feature | Details |
|---------|---------|
| Schools Covered | Hanafi, Maliki, Shafi'i, Hanbali |
| Topics | Worship, Transactions, Family Law, Criminal Law |
| Time Period | 150-1300 AH |
| Source Books | 2,000+ fiqh texts |

---

### 3. `general_islamic` (1M passages, 6.5 GB)

General Islamic knowledge including spirituality, ethics, dua, and daily life guidance.

| Feature | Details |
|---------|---------|
| Topics | Spirituality, Ethics, Dua, Adab, Daily Life |
| Time Period | 0-1400 AH |
| Source Books | 1,500+ texts |

---

### 4. `islamic_history_passages` (900K passages, 6 GB)

Islamic history from the Prophetic era through the Ottoman period.

| Feature | Details |
|---------|---------|
| Periods | Prophetic, Rashidun, Umayyad, Abbasid, Ottoman |
| Topics | Battles, Biographies, Dynasties, Events |
| Time Period | 0-1400 AH |

---

### 5. `quran_tafsir` (800K passages, 5.2 GB)

Quranic exegesis from classical tafsir works.

| Feature | Details |
|---------|---------|
| Tafsir Works | Tabari, Qurtubi, Ibn Kathir, Jalalayn, etc. |
| Coverage | All 114 surahs, 6,236 verses |
| Languages | Classical Arabic |
| Time Period | 200-900 AH |

---

### 6. `arabic_language_passages` (400K passages, 2.3 GB)

Arabic grammar, linguistics, rhetoric, and language sciences.

| Feature | Details |
|---------|---------|
| Topics | Nahw, Sarf, Balaghah, Arabic Lexicons |
| Time Period | 150-1300 AH |

---

### 7. `aqeedah_passages` (300K passages, 1.8 GB)

Islamic creed and theology from various theological schools.

| Feature | Details |
|---------|---------|
| Schools | Ash'ari, Maturidi, Athari |
| Topics | Tawhid, Attributes of Allah, Prophethood, Afterlife |
| Time Period | 200-1300 AH |

---

### 8. `spirituality_passages` (200K passages, 1.1 GB)

Islamic spirituality, purification of the heart, and Sufi works.

| Feature | Details |
|---------|---------|
| Topics | Tasawwuf, Tazkiyah, Adab, Dhikr |
| Time Period | 200-1300 AH |

---

### 9. `usul_fiqh` (150K passages, 0.9 GB)

Principles of Islamic jurisprudence and legal theory.

| Feature | Details |
|---------|---------|
| Topics | Usul al-Fiqh, Qawa'id Fiqhiyyah, Maqasid al-Shari'ah |
| Time Period | 200-1200 AH |

---

### 10. `seerah_passages` (100K passages, 0.8 GB)

Prophet Muhammad's ﷺ biography and related studies.

| Feature | Details |
|---------|---------|
| Sources | Ibn Hisham, Ibn Kathir, Al-Rahiq al-Makhtum |
| Topics | Birth, Prophethood, Migration, Battles, Death ﷺ |
| Time Period | 200-1400 AH |

---

## 📁 File Structure

```
Athar-Datasets/
├── collections/
│   ├── fiqh_passages.jsonl.gz        # 7.0 GB compressed
│   ├── hadith_passages.jsonl.gz       # 11.0 GB compressed
│   ├── quran_tafsir.jsonl.gz          # 5.2 GB compressed
│   ├── aqeedah_passages.jsonl.gz      # 1.8 GB compressed
│   ├── seerah_passages.jsonl.gz       # 0.8 GB compressed
│   ├── islamic_history_passages.jsonl.gz  # 6.0 GB compressed
│   ├── arabic_language_passages.jsonl.gz  # 2.3 GB compressed
│   ├── spirituality_passages.jsonl.gz # 1.1 GB compressed
│   ├── general_islamic.jsonl.gz       # 6.5 GB compressed
│   └── usul_fiqh.jsonl.gz             # 0.9 GB compressed
│
└── metadata/
    ├── master_catalog.json            # 8,425 books catalog
    ├── category_mapping.json          # 41→10 category mapping
    └── author_catalog.json            # 3,146 scholars
```

---

## 🔍 How to Load

### Python (using huggingface_hub)

```python
from huggingface_hub import hf_hub_download
import json

# Download a collection
filepath = hf_hub_download(
    repo_id="Kandil7/Athar-Datasets",
    filename="collections/fiqh_passages.jsonl.gz",
    repo_type="dataset"
)

# Load passages
import gzip
passages = []
with gzip.open(filepath, 'rt', encoding='utf-8') as f:
    for line in f:
        passages.append(json.loads(line))

print(f"Loaded {len(passages):,} passages")
```

### Load with metadata

```python
# Load metadata
master_catalog = hf_hub_download(
    repo_id="Kandil7/Athar-Datasets",
    filename="metadata/master_catalog.json",
    repo_type="dataset"
)

author_catalog = hf_hub_download(
    repo_id="Kandil7/Athar-Datasets",
    filename="metadata/author_catalog.json",
    repo_type="dataset"
)

# Enrich passages with additional metadata
with open(author_catalog, 'r') as f:
    authors = json.load(f)
```

---

## 💡 Usage Examples

### Example 1: Semantic Search

```python
from sentence_transformers import SentenceTransformer

# Load model
model = SentenceTransformer('BAAI/bge-m3')

# Embed query
query = "ما حكم صلاة الجماعة؟"
query_embedding = model.encode(query)

# Search in collection (requires vector DB like Qdrant)
# See: https://github.com/Kandil7/Athar
```

### Example 2: Faceted Search

```python
# Filter by era and collection
classical_passages = [
    p for p in passages
    if 200 <= p.get('author_death', 0) <= 500  # Classical era
    and p.get('collection') == 'fiqh_passages'
]

# Filter by author
bukhari_hadith = [
    p for p in hadith_passages
    if 'Bukhari' in p.get('author', '')
]
```

### Example 3: Citation-Enhanced QA

```python
# Build a RAG pipeline
from Athar import FiqhAgent

agent = FiqhAgent()
result = await agent.execute(
    query="ما حكم صلاة الجماعة؟",
    filters={"era": "classical"},
    hierarchical=True
)

# Result includes rich citations:
print(result.citations[0].source)
# "Imam Bukhari - Sahih al-Bukhari, Chapter of Prayer"
print(result.citations[0].metadata['hadith_grade'])
# "sahih"
```

---

## 🏗️ Scholarly Eras

| Era | Range (AH) | Range (CE) | Description |
|-----|-----------|-----------|-------------|
| **Prophetic** | 0-100 | 622-718 | Companions of Prophet ﷺ |
| **Tabi'un** | 100-200 | 718-815 | Successors |
| **Classical** | 200-500 | 815-1106 | Golden age of Islamic scholarship |
| **Medieval** | 500-900 | 1106-1496 | Post-classical period |
| **Ottoman** | 900-1300 | 1496-1883 | Ottoman era |
| **Modern** | 1300+ | 1883+ | Modern period |

---

## 📖 Source: ElShamela Library (المكتبة الشاملة)

This dataset is derived from **ElShamela Library** (المكتبة الشاملة) — the largest comprehensive digital library of Islamic texts, containing **8,425 books** across **41 categories** spanning **1,400 years of Islamic scholarship**.

### About ElShamela Library

**ElShamela** (المكتبة الشاملة) is a free, open-access digital library that has been digitizing and preserving classical Islamic texts for over two decades. It is widely considered the most comprehensive collection of Islamic heritage works, including:

- **Quran and Tafsir** — Complete Quran text with major classical commentaries
- **Hadith Collections** — Six canonical hadith books (Kutub al-Sittah) plus Musnad works
- **Fiqh** — Jurisprudence from all four major Sunni schools (Hanafi, Maliki, Shafi'i, Hanbali)
- **Aqeedah** — Islamic theology and creed from various schools
- **Seerah** — Prophet Muhammad's ﷺ biography
- **Arabic Language** — Grammar, linguistics, rhetoric, and lexicons
- **Islamic History** — Historical accounts from the Prophetic era through the Ottoman period
- **Spirituality** — Tasawwuf, ethics, and purification of the heart
- **Usul Fiqh** — Principles of Islamic jurisprudence and legal theory

**Website:** https://shamela.ws/

### Processing Pipeline

1. **Extracted** 8,425 books from ElShamela Library format
2. **Converted** from proprietary Shamela format to plain text
3. **Split** into pages and passages for granular retrieval
4. **Enriched** with metadata:
   - Author names and death years (Hijri calendar)
   - Book titles and categories
   - Chapter and section headings
   - Page numbers
5. **Organized** into 10 scholarly collections based on subject matter
6. **Added** hadith chain (esnad) data where available
7. **Compressed** with gzip for efficient storage and transfer

### ElShamela Statistics

| Metric | Value |
|--------|-------|
| Total Books | 8,425 |
| Total Categories | 41 |
| Total Authors | 3,146 |
| Time Span | 0-1400+ AH (7th-21st century CE) |
| Original Size | 17.16 GB (extracted text) |
| Languages | Classical Arabic (primary) |

---

## 📊 Statistics

### Passages per Collection

| Collection | Passages | Size (GB) | % of Total |
|------------|----------|-----------|------------|
| hadith_passages | ~2,000,000 | 11.0 | 35% |
| fiqh_passages | ~1,200,000 | 7.0 | 21% |
| general_islamic | ~1,000,000 | 6.5 | 18% |
| islamic_history_passages | ~900,000 | 6.0 | 16% |
| quran_tafsir | ~800,000 | 5.2 | 14% |
| arabic_language_passages | ~400,000 | 2.3 | 7% |
| aqeedah_passages | ~300,000 | 1.8 | 5% |
| spirituality_passages | ~200,000 | 1.1 | 4% |
| usul_fiqh | ~150,000 | 0.9 | 3% |
| seerah_passages | ~100,000 | 0.8 | 2% |

### Scholar Distribution

| Era | Scholars | Books | Passages |
|-----|----------|-------|----------|
| Prophetic | 150 | 12 | 50,000 |
| Tabi'un | 280 | 85 | 200,000 |
| Classical | 1,200 | 2,800 | 2,500,000 |
| Medieval | 800 | 3,200 | 1,800,000 |
| Ottoman | 500 | 1,800 | 900,000 |
| Modern | 216 | 528 | 250,000 |

---

## 🤝 Related Projects

- **[Athar](https://github.com/Kandil7/Athar)** — The parent project: A production-ready Islamic QA system using these datasets
- **[Fanar-Sadiq Architecture](docs/Fanar-Sadiq%20A%20Multi-Agent%20Architecture%20for%20Grounded%20Islamic%20QA.pdf)** — Research paper that inspired this system
- **[Quran.com](https://quran.com)** — Quran text reference
- **[Sunnah.com](https://sunnah.com)** — Hadith collections reference

---

## 📝 Citation

If you use this dataset in your research, please cite:

```bibtex
@misc{athar-datasets-2026,
  title={Athar: A Multi-Agent Architecture for Grounded Islamic QA},
  author={Kandil, [Author Name]},
  year={2026},
  url={https://huggingface.co/datasets/Kandil7/Athar-Datasets},
  note={Based on the Fanar-Sadiq architecture}
}
```

---

## ⚠️ Usage Notes

1. **Scholarly Context:** These texts represent classical Islamic scholarship. Always consult qualified scholars for religious rulings.

2. **Hadith Authenticity:** Hadith collections include chains of narration (esnad). Use the authenticity grading system to evaluate reliability.

3. **Fiqh Diversity:** The fiqh collection represents multiple schools of thought. Present all views when answering questions.

4. **Language:** Primary content is in Classical Arabic. Metadata includes English translations.

5. **Licensing:** MIT License — free for research and commercial use. Please attribute appropriately.

---

## 📞 Contact & Support

- **GitHub:** https://github.com/Kandil7/Athar
- **Issues:** https://github.com/Kandil7/Athar/issues
- **HuggingFace:** https://huggingface.co/Kandil7

---

<div align="center">

**Built with ❤️ for the Muslim community**

🕌 Athar Islamic QA Datasets • 5.7M passages • 8,425 books • 1,400 years of scholarship

</div>
"""


def main():
    if not LOCAL_TOKEN:
        print("ERROR: HF_TOKEN not found in environment!")
        print("Please add HF_TOKEN to your .env file")
        return

    print("=" * 60)
    print("Reverting README.md to original full dataset version")
    print("=" * 60)

    api = HfApi(token=LOCAL_TOKEN)

    # Upload the original README
    api.upload_file(
        path_or_fileobj=README_CONTENT.encode("utf-8"),
        path_in_repo="README.md",
        repo_id=REPO_ID,
        repo_type="dataset",
        commit_message="Revert README to full dataset documentation (15.7M passages)",
    )

    print("\n" + "=" * 60)
    print("README Reverted Successfully!")
    print("=" * 60)
    print(f"\nDataset URL: https://huggingface.co/datasets/{REPO_ID}")


if __name__ == "__main__":
    main()
