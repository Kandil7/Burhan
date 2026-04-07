# 🕌 Athar Mini-Dataset for MVP

This mini-dataset contains representative samples from the full Athar datasets,
optimized for GitHub (<50 MB) while demonstrating all system features.

## Dataset Overview

- **Total Documents:** 1,623
- **Estimated Size:** 27.6 MB
- **Collections:** 10
- **Source Books:** ~50 books from 41 categories
- **Hadith:** 300 from Sanadset (6 major collections)

## Collections

| Collection | Documents | Size (est.) | Source |
|------------|-----------|-------------|--------|
| fiqh_passages | 347 | 6.2 MB | 8 fiqh books |
| hadith_passages | 126 | 2.5 MB | Sanadset 368K |
| aqeedah_passages | 90 | 1.3 MB | 5 aqeedah books |
| seerah_passages | 100 | 1.5 MB | 4 seerah books |
| islamic_history | 270 | 4.6 MB | 6 history books |
| arabic_language | 240 | 4.1 MB | 8 language books |
| spirituality | 150 | 2.2 MB | 5 spirituality books |
| general_islamic | 300 | 5.1 MB | 10 general books |

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

### Embed with Athar
```bash
# This mini-dataset can be embedded using the existing pipeline
python scripts/embed_mini_dataset.py
```

## Sampling Methodology

- **Books:** First 15-25 pages extracted from ~50 representative books
- **Hadith:** 300 hadith sampled from 6 major collections (50 each)
- **Chunks:** 250-500 characters with paragraph boundaries
- **Categories:** All 41 categories represented across 9 super-categories

## Full Datasets

This is a **sample** for MVP/demo purposes. Full datasets are available separately:
- **Shamela Library:** 8,425 books (17.16 GB)
- **Sanadset Hadith:** 650,986 hadith (1.43 GB)

Full datasets are excluded from Git per `.gitignore`.

## License

Data sourced from:
- Shamela Library (public domain Islamic texts)
- Sanadset Hadith Dataset (open-source hadith collection)

---

**Created:** April 7, 2026  
**Version:** 1.0  
**Purpose:** MVP demonstration and GitHub hosting
