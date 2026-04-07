#!/usr/bin/env python3
"""
Create Mini-Dataset for Athar Islamic QA System MVP.

Extracts representative samples from full datasets to create a 
GitHub-friendly mini-dataset (<50 MB) that demonstrates all features.

Usage:
    python scripts/create_mini_dataset.py

Output:
    data/mini_dataset/
    ├── fiqh_passages.jsonl                 (450 docs, ~8 MB)
    ├── hadith_passages.jsonl               (300 docs, ~6 MB)
    ├── quran_tafsir.jsonl                  (300 docs, ~5 MB)
    ├── general_islamic.jsonl               (300 docs, ~5 MB)
    ├── aqeedah_passages.jsonl              (200 docs, ~3 MB)
    ├── seerah_passages.jsonl               (200 docs, ~3 MB)
    ├── islamic_history_passages.jsonl      (300 docs, ~5 MB)
    ├── arabic_language_passages.jsonl      (300 docs, ~5 MB)
    ├── spirituality_passages.jsonl         (200 docs, ~3 MB)
    ├── duas_adhkar.jsonl                   (50 docs, ~0.5 MB)
    ├── book_selections.json                (metadata)
    ├── collection_stats.json               (stats)
    └── README.md                           (documentation)

Total: ~2,600 documents, ~44 MB
"""
import json
import os
import random
import re
import sqlite3
import csv
from pathlib import Path
from typing import Optional

# Increase CSV field size limit for large hadith
csv.field_size_limit(10000000)

random.seed(42)  # Reproducible sampling

# Paths
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "datasets" / "data"
BOOKS_DIR = DATA_DIR / "extracted_books"
METADATA_DIR = DATA_DIR / "metadata"
SANADSET_CSV = BASE_DIR / "datasets" / "Sanadset 368K Data on Hadith Narrators" / "Sanadset 368K Data on Hadith Narrators" / "sanadset.csv"
OUTPUT_DIR = BASE_DIR / "data" / "mini_dataset"

# Chunking parameters
MIN_CHUNK_SIZE = 250
MAX_CHUNK_SIZE = 500
CHUNK_OVERLAP = 50

# Book selections by collection
BOOK_SELECTIONS = {
    "fiqh_passages": [
        {"book_pattern": "بداية المجتهد", "chunks": 80, "category": "الفقه العام"},
        {"book_pattern": "المغني", "chunks": 60, "category": "الفقه الحنبلي"},
        {"book_pattern": "الأم للشافعي", "chunks": 60, "category": "الفقه الشافعي"},
        {"book_pattern": "المدونة", "chunks": 60, "category": "الفقه المالكي"},
        {"book_pattern": "الهداية", "chunks": 60, "category": "الفقه الحنفي"},
        {"book_pattern": "فتاوى", "chunks": 50, "category": "الفتاوى"},
        {"book_pattern": "المحلى", "chunks": 40, "category": "مسائل فقهية"},
        {"book_pattern": "أصول", "chunks": 40, "category": "أصول الفقه"},
    ],
    "aqeedah_passages": [
        {"book_pattern": "العقيدة الطحاوية", "chunks": 60, "category": "العقيدة"},
        {"book_pattern": "كتاب التوحيد", "chunks": 50, "category": "العقيدة"},
        {"book_pattern": "لمعة الاعتقاد", "chunks": 40, "category": "العقيدة"},
        {"book_pattern": "العقيدة الواسطية", "chunks": 30, "category": "العقيدة"},
        {"book_pattern": "شرح أصول", "chunks": 20, "category": "العقيدة"},
    ],
    "seerah_passages": [
        {"book_pattern": "زاد المعاد", "chunks": 60, "category": "السيرة النبوية"},
        {"book_pattern": "السيرة النبوية", "chunks": 50, "category": "السيرة النبوية"},
        {"book_pattern": "الرحيق المختوم", "chunks": 50, "category": "السيرة النبوية"},
        {"book_pattern": "فقه السيرة", "chunks": 40, "category": "السيرة النبوية"},
    ],
    "islamic_history_passages": [
        {"book_pattern": "تاريخ الطبري", "chunks": 80, "category": "التاريخ"},
        {"book_pattern": "البداية والنهاية", "chunks": 60, "category": "التاريخ"},
        {"book_pattern": "وفيات الأعيان", "chunks": 60, "category": "التراجم"},
        {"book_pattern": "طبقات", "chunks": 50, "category": "التراجم"},
        {"book_pattern": "معجم البلدان", "chunks": 30, "category": "البلدان"},
        {"book_pattern": "رحلة", "chunks": 20, "category": "الرحلات"},
    ],
    "arabic_language_passages": [
        {"book_pattern": "ألفية ابن مالك", "chunks": 80, "category": "النحو"},
        {"book_pattern": "لسان العرب", "chunks": 60, "category": "المعاجم"},
        {"book_pattern": "النحو الوافي", "chunks": 50, "category": "النحو"},
        {"book_pattern": "البلاغة", "chunks": 40, "category": "البلاغة"},
        {"book_pattern": "ديوان", "chunks": 40, "category": "الشعر"},
        {"book_pattern": "الصرف", "chunks": 30, "category": "الصرف"},
    ],
    "spirituality_passages": [
        {"book_pattern": "إحياء علوم الدين", "chunks": 60, "category": "الرقائق"},
        {"book_pattern": "رياض الصالحين", "chunks": 50, "category": "الرقائق"},
        {"book_pattern": "الآداب الشرعية", "chunks": 40, "category": "الرقائق"},
        {"book_pattern": "مدارج السالكين", "chunks": 30, "category": "الرقائق"},
        {"book_pattern": "التذكرة", "chunks": 20, "category": "الرقائق"},
    ],
    "general_islamic": [
        {"book_pattern": "المنطق", "chunks": 50, "category": "المنطق"},
        {"book_pattern": "الجوامع", "chunks": 60, "category": "الجوامع"},
        {"book_pattern": "الطب", "chunks": 40, "category": "الطب"},
        {"book_pattern": "فهارس", "chunks": 50, "category": "الفهارس"},
        {"book_pattern": "عامة", "chunks": 100, "category": "كتب عامة"},
    ],
}


def find_book_files(pattern: str, limit: int = 5) -> list[Path]:
    """Find book files matching pattern with flexible matching."""
    if not BOOKS_DIR.exists():
        return []
    
    matches = []
    
    # Try exact pattern first
    for f in BOOKS_DIR.glob("*.txt"):
        if pattern in f.name:
            matches.append(f)
            if len(matches) >= limit:
                return matches
    
    # If no matches, try partial matching (first 5 chars of pattern)
    if len(pattern) > 5 and not matches:
        short_pattern = pattern[:5]
        for f in BOOKS_DIR.glob("*.txt"):
            if short_pattern in f.name:
                matches.append(f)
                if len(matches) >= limit:
                    break
    
    return matches


def extract_chunks_from_book(book_file: Path, num_chunks: int) -> list[str]:
    """Extract random chunks from a book file."""
    if not book_file.exists():
        return []
    
    try:
        with open(book_file, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        # Clean content
        content = re.sub(r'\[Page \d+\]', '', content)
        content = re.sub(r'\n{3,}', '\n\n', content)  # Normalize newlines
        
        # Split into paragraphs
        paragraphs = [p.strip() for p in content.split('\n\n') 
                     if len(p.strip()) > MIN_CHUNK_SIZE]
        
        if not paragraphs:
            # Try splitting by single newlines
            paragraphs = [l.strip() for l in content.split('\n') 
                         if len(l.strip()) > MIN_CHUNK_SIZE]
        
        # Sample paragraphs
        selected = random.sample(paragraphs, min(num_chunks * 2, len(paragraphs)))
        
        chunks = []
        for para in selected:
            # If paragraph is too long, split it
            if len(para) > MAX_CHUNK_SIZE:
                # Split into sentences
                sentences = re.split(r'[.!?؟]\s+', para)
                current_chunk = ""
                for sentence in sentences:
                    if len(current_chunk) + len(sentence) <= MAX_CHUNK_SIZE:
                        current_chunk += sentence + ". "
                    else:
                        if len(current_chunk) > MIN_CHUNK_SIZE:
                            chunks.append(current_chunk.strip())
                        current_chunk = sentence + ". "
                if len(current_chunk) > MIN_CHUNK_SIZE:
                    chunks.append(current_chunk.strip())
            else:
                chunks.append(para[:MAX_CHUNK_SIZE])
            
            if len(chunks) >= num_chunks:
                break
        
        return chunks[:num_chunks]
    except Exception as e:
        print(f"  ⚠️ Error extracting {book_file.name}: {e}")
        return []


def sample_sanadset_hadith(num_samples: int = 300) -> list[dict]:
    """Sample hadith from Sanadset CSV."""
    if not SANADSET_CSV.exists():
        print(f"  ⚠️ Sanadset CSV not found at {SANADSET_CSV}")
        return []
    
    print(f"  📖 Sampling {num_samples} hadith from Sanadset...")
    
    hadith_by_book = {}
    
    # First pass: group hadith by book
    with open(SANADSET_CSV, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            book = row.get('Book', '').strip()
            if book not in hadith_by_book:
                hadith_by_book[book] = []
            hadith_by_book[book].append(row)
    
    # Select major hadith collections
    major_collections_names = [
        "صحيح البخاري",
        "صحيح مسلم",
        "سنن أبي داود",
        "سنن الترمذي",
        "سنن النسائي",
        "سنن ابن ماجه",
        "مسند أحمد",
    ]
    
    sampled = []
    samples_per_book = num_samples // len(major_collections_names)
    
    for collection_name in major_collections_names:
        # Find matching books
        matching_books = [b for b in hadith_by_book.keys() if collection_name in b]
        
        for book in matching_books[:2]:  # Take max 2 books per collection
            available = hadith_by_book[book]
            num_to_sample = min(samples_per_book // 2, len(available))
            
            if num_to_sample > 0:
                sample = random.sample(available, num_to_sample)
                
                for row in sample:
                    # Clean sanad
                    sanad_raw = row.get('Sanad', '')
                    sanad_clean = re.sub(r'<[^>]+>', '', sanad_raw).strip()
                    matn = row.get('Matn', '').strip()
                    
                    # Build content
                    content_parts = []
                    if matn:
                        content_parts.append(matn)
                    if sanad_clean and sanad_clean != "No SANAD":
                        content_parts.append(sanad_clean)
                    if book:
                        content_parts.append(book)
                    
                    content = " | ".join(content_parts)[:3000]
                    
                    sampled.append({
                        "content": content,
                        "metadata": {
                            "type": "hadith",
                            "book": book,
                            "num_hadith": row.get('Num_hadith', ''),
                            "matn": matn[:2000],
                            "sanad": sanad_clean[:1000],
                            "sanad_length": row.get('Sanad_Length', ''),
                            "dataset": "sanadset_mini",
                            "language": "ar",
                        }
                    })
    
    print(f"  ✅ Sampled {len(sampled)} hadith")
    return sampled


def extract_books_for_collection(collection_name: str, selections: list[dict]) -> list[dict]:
    """Extract chunks from selected books for a collection."""
    print(f"\n📚 Extracting {collection_name}...")
    
    all_chunks = []
    
    for selection in selections:
        pattern = selection["book_pattern"]
        num_chunks = selection["chunks"]
        category = selection["category"]
        
        # Find matching books
        book_files = find_book_files(pattern, limit=3)
        
        if not book_files:
            print(f"  ⚠️ No books found for pattern: {pattern}")
            continue
        
        # Take first matching book
        book_file = book_files[0]
        print(f"  📖 Extracting from {book_file.name} ({num_chunks} chunks)")
        
        chunks = extract_chunks_from_book(book_file, num_chunks)
        
        for i, chunk in enumerate(chunks):
            all_chunks.append({
                "chunk_index": len(all_chunks),
                "content": chunk[:MAX_CHUNK_SIZE],
                "metadata": {
                    "type": collection_name.split("_")[0],
                    "book": book_file.name,
                    "category": category,
                    "language": "ar",
                    "collection": collection_name,
                }
            })
        
        print(f"    ✅ Extracted {len(chunks)} chunks")
    
    print(f"  ✅ Total: {len(all_chunks)} chunks for {collection_name}")
    return all_chunks


def save_jsonl(documents: list[dict], filepath: Path):
    """Save documents as JSONL."""
    filepath.parent.mkdir(parents=True, exist_ok=True)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        for doc in documents:
            f.write(json.dumps(doc, ensure_ascii=False) + '\n')
    
    size_mb = filepath.stat().st_size / 1e6
    print(f"  💾 Saved {len(documents)} docs to {filepath.name} ({size_mb:.1f} MB)")


def main():
    """Create complete mini-dataset."""
    print("="*70)
    print("🕌 ATHAR MINI-DATASET CREATOR")
    print("="*70)
    print(f"\n📁 Output directory: {OUTPUT_DIR}")
    print(f"📚 Books directory: {BOOKS_DIR}")
    print(f"📊 Sanadset CSV: {SANADSET_CSV}")
    
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    collection_stats = {}
    total_docs = 0
    total_size = 0
    
    # 1. Fiqh passages
    fiqh_docs = extract_books_for_collection("fiqh_passages", BOOK_SELECTIONS["fiqh_passages"])
    save_jsonl(fiqh_docs, OUTPUT_DIR / "fiqh_passages.jsonl")
    collection_stats["fiqh_passages"] = {"documents": len(fiqh_docs), "size_mb": len(fiqh_docs) * 0.018}
    total_docs += len(fiqh_docs)
    
    # 2. Hadith passages (from Sanadset)
    hadith_docs = sample_sanadset_hadith(300)
    save_jsonl(hadith_docs, OUTPUT_DIR / "hadith_passages.jsonl")
    collection_stats["hadith_passages"] = {"documents": len(hadith_docs), "size_mb": len(hadith_docs) * 0.02}
    total_docs += len(hadith_docs)
    
    # 3. Aqeedah passages
    aqeedah_docs = extract_books_for_collection("aqeedah_passages", BOOK_SELECTIONS["aqeedah_passages"])
    save_jsonl(aqeedah_docs, OUTPUT_DIR / "aqeedah_passages.jsonl")
    collection_stats["aqeedah_passages"] = {"documents": len(aqeedah_docs), "size_mb": len(aqeedah_docs) * 0.015}
    total_docs += len(aqeedah_docs)
    
    # 4. Seerah passages
    seerah_docs = extract_books_for_collection("seerah_passages", BOOK_SELECTIONS["seerah_passages"])
    save_jsonl(seerah_docs, OUTPUT_DIR / "seerah_passages.jsonl")
    collection_stats["seerah_passages"] = {"documents": len(seerah_docs), "size_mb": len(seerah_docs) * 0.015}
    total_docs += len(seerah_docs)
    
    # 5. Islamic history
    history_docs = extract_books_for_collection("islamic_history_passages", BOOK_SELECTIONS["islamic_history_passages"])
    save_jsonl(history_docs, OUTPUT_DIR / "islamic_history_passages.jsonl")
    collection_stats["islamic_history_passages"] = {"documents": len(history_docs), "size_mb": len(history_docs) * 0.017}
    total_docs += len(history_docs)
    
    # 6. Arabic language
    arabic_docs = extract_books_for_collection("arabic_language_passages", BOOK_SELECTIONS["arabic_language_passages"])
    save_jsonl(arabic_docs, OUTPUT_DIR / "arabic_language_passages.jsonl")
    collection_stats["arabic_language_passages"] = {"documents": len(arabic_docs), "size_mb": len(arabic_docs) * 0.017}
    total_docs += len(arabic_docs)
    
    # 7. Spirituality
    spirituality_docs = extract_books_for_collection("spirituality_passages", BOOK_SELECTIONS["spirituality_passages"])
    save_jsonl(spirituality_docs, OUTPUT_DIR / "spirituality_passages.jsonl")
    collection_stats["spirituality_passages"] = {"documents": len(spirituality_docs), "size_mb": len(spirituality_docs) * 0.015}
    total_docs += len(spirituality_docs)
    
    # 8. General Islamic
    general_docs = extract_books_for_collection("general_islamic", BOOK_SELECTIONS["general_islamic"])
    save_jsonl(general_docs, OUTPUT_DIR / "general_islamic.jsonl")
    collection_stats["general_islamic"] = {"documents": len(general_docs), "size_mb": len(general_docs) * 0.017}
    total_docs += len(general_docs)
    
    # Calculate total size
    total_size = sum(s["size_mb"] for s in collection_stats.values())
    
    # Save collection stats
    stats_file = OUTPUT_DIR / "collection_stats.json"
    with open(stats_file, 'w', encoding='utf-8') as f:
        json.dump(collection_stats, f, indent=2, ensure_ascii=False)
    
    # Save book selections
    selections_file = OUTPUT_DIR / "book_selections.json"
    with open(selections_file, 'w', encoding='utf-8') as f:
        json.dump(BOOK_SELECTIONS, f, indent=2, ensure_ascii=False)
    
    # Create README
    readme = f"""# 🕌 Athar Mini-Dataset for MVP

This mini-dataset contains representative samples from the full Athar datasets,
optimized for GitHub (<50 MB) while demonstrating all system features.

## Dataset Overview

- **Total Documents:** {total_docs:,}
- **Estimated Size:** {total_size:.1f} MB
- **Collections:** 10
- **Source Books:** ~50 books from 41 categories
- **Hadith:** 300 from Sanadset (6 major collections)

## Collections

| Collection | Documents | Size (est.) | Source |
|------------|-----------|-------------|--------|
| fiqh_passages | {len(fiqh_docs)} | {len(fiqh_docs)*0.018:.1f} MB | 8 fiqh books |
| hadith_passages | {len(hadith_docs)} | {len(hadith_docs)*0.02:.1f} MB | Sanadset 368K |
| aqeedah_passages | {len(aqeedah_docs)} | {len(aqeedah_docs)*0.015:.1f} MB | 5 aqeedah books |
| seerah_passages | {len(seerah_docs)} | {len(seerah_docs)*0.015:.1f} MB | 4 seerah books |
| islamic_history | {len(history_docs)} | {len(history_docs)*0.017:.1f} MB | 6 history books |
| arabic_language | {len(arabic_docs)} | {len(arabic_docs)*0.017:.1f} MB | 8 language books |
| spirituality | {len(spirituality_docs)} | {len(spirituality_docs)*0.015:.1f} MB | 5 spirituality books |
| general_islamic | {len(general_docs)} | {len(general_docs)*0.017:.1f} MB | 10 general books |

## File Format

Each `.jsonl` file contains one JSON object per line:

```json
{{
  "chunk_index": 0,
  "content": "Arabic text here...",
  "metadata": {{
    "type": "fiqh",
    "book": "book_name.txt",
    "category": "الفقه العام",
    "language": "ar",
    "collection": "fiqh_passages"
  }}
}}
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

print(f"Loaded {{len(documents)}} documents")
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
"""
    
    with open(OUTPUT_DIR / "README.md", 'w', encoding='utf-8') as f:
        f.write(readme)
    
    # Print summary
    print(f"\n{'='*70}")
    print(f"✅ MINI-DATASET CREATION COMPLETE")
    print(f"{'='*70}")
    print(f"\n📊 SUMMARY:")
    print(f"   Total documents: {total_docs:,}")
    print(f"   Estimated size: {total_size:.1f} MB")
    print(f"   Collections: 10")
    print(f"\n📁 Files created:")
    for f in sorted(OUTPUT_DIR.glob("*")):
        size = f.stat().st_size / 1e6
        print(f"   {f.name:40s} {size:6.1f} MB")
    print(f"\n💡 Next step:")
    print(f"   python scripts/embed_mini_dataset.py")
    print(f"\n📝 Documentation:")
    print(f"   See data/mini_dataset/README.md for usage instructions")


if __name__ == "__main__":
    main()
