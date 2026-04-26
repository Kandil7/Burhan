# 🕌 Burhan Mini-Dataset for MVP

This mini-dataset contains representative samples from the full Burhan datasets,
optimized for GitHub (<50 MB) while demonstrating all system features.

---

## Dataset Overview

- **Total Documents:** 1,623
- **Estimated Size:** 1.7 MB
- **Collections:** 8
- **Source Books:** ~50 books from 41 categories
- **Hadith:** 300 from Sanadset (6 major collections)
- **Phase Status:** Phase 8 complete - Hybrid Intent Classifier active

---

## Collections

| Collection | Documents | Size (est.) | Source |
|------------|-----------|-------------|--------|
| fiqh_passages | 347 | ~350 KB | 8 fiqh books |
| hadith_passages | 126 | ~120 KB | Sanadset 368K |
| aqeedah_passages | 90 | ~80 KB | 5 aqeedah books |
| seerah_passages | 100 | ~100 KB | 4 seerah books |
| islamic_history | 270 | ~250 KB | 6 history books |
| arabic_language | 240 | ~220 KB | 8 language books |
| spirituality | 150 | ~140 KB | 5 spirituality books |
| general_islamic | 300 | ~300 KB | 10 general books |

---

## File Format

Each `.jsonl` file contains one JSON object per line:

```json
{
  "chunk_index": 0,
  "content": "Arabic text here...",
  "metadata": {
    "type": "fiqh",
    "book": "book_name.txt",
    "category": "الفقه العام",
    "language": "ar",
    "collection": "fiqh_passages"
  }
}
```

### Metadata Fields

| Field | Description |
|-------|-------------|
| `chunk_index` | Position of chunk in document |
| `content` | Arabic/English text content |
| `metadata.type` | Content type (fiqh, hadith, etc.) |
| `metadata.book` | Source book filename |
| `metadata.category` | Shamela category |
| `metadata.language` | Language code (ar/en) |
| `metadata.collection` | Target collection name |

---

## Usage

### Load in Python

```python
import json

# Load a collection
documents = []
with open('data/mini_dataset/fiqh_passages.jsonl', 'r', encoding='utf-8') as f:
    for line in f:
        documents.append(json.loads(line))

print(f"Loaded {len(documents)} documents")
```

### Embed with Burhan

```bash
# This mini-dataset can be embedded using the existing pipeline
python scripts/data/embed_all_collections.py --collection mini_dataset
```

### Use with Qdrant

```python
from qdrant_client import QdrantClient

client = QdrantClient("localhost", port=6333)

# Load and insert mini-dataset
# See scripts/data/seed_mvp_data.py for example
```

---

## Sampling Methodology

- **Books:** First 15-25 pages extracted from ~50 representative books
- **Hadith:** 300 hadith sampled from 6 major collections (50 each)
- **Chunks:** 250-500 characters with paragraph boundaries
- **Categories:** All 41 categories represented across 9 super-categories

### Super-Category Mapping

| Original (41) | Simplified (10) |
|----------------|-----------------|
| الفقه العام, فقه عبادات, فقه معاملات | fiqh_passages |
| الحديث, الصحيحات, السنن | hadith_passages |
| التوحيد، العقيدة | aqeedah_passages |
| السيرة النبوية | seerah_passages |
| التاريخ الإسلامي | islamic_history_passages |
| اللغة العربية، الصرف، النحو | arabic_language_passages |
| التصوف، الأخلاق | spirituality_passages |
| الثقافة العامة، الموسوعات | general_islamic |
| أصول الفقه | usul_fiqh |
| التفاسير | quran_tafsir |

---

## Full Datasets

This is a **sample** for MVP/demo purposes. Full datasets are available separately:

| Dataset | Size | Documents | Location |
|---------|------|-----------|----------|
| Shamela Library | 17.16 GB | 8,425 books | HuggingFace |
| Sanadset Hadith | 1.43 GB | 650,986 hadith | HuggingFace |
| Lucene Merge | 61 GB | 5,717,177 | HuggingFace |

### HuggingFace Repository

- **URL:** https://huggingface.co/datasets/Kandil7/Athar-Datasets
- **Size:** 42.6 GB (all 10 collections)
- **Status:** ✅ Fully uploaded

Full datasets are excluded from Git per `.gitignore`.

---

## Integration with Phase 8

As of **April 15, 2026**, the system now includes:

1. **Hybrid Intent Classifier** - Fast keyword-based intent detection
2. **New `/classify` endpoint** - Instant intent classification (<50ms)
3. **16 Intent Types** - Full coverage of Islamic query types

The mini-dataset works with the new classifier for testing purposes.

---

## License

Data sourced from:
- **Shamela Library** (public domain Islamic texts) - https://shamela.ws/
- **Sanadset Hadith Dataset** (open-source hadith collection)

---

## Related Documentation

- [docs/README.md](../docs/README.md) - Full documentation index
- [docs/6-data/MINI_DATASET_COMPLETE.md](../docs/6-data/MINI_DATASET_COMPLETE.md) - Complete dataset guide
- [scripts/README.md](../scripts/README.md) - Script documentation

---

**Created:** April 7, 2026  
**Updated:** April 15, 2026  
**Version:** 1.1  
**Purpose:** MVP demonstration and GitHub hosting

---

*Built with ❤️ for the Muslim community*