#!/usr/bin/env python3
"""
Compress collection JSONL files for upload to Hugging Face/Kaggle.

Converts JSONL → JSONL.gz (gzip compression, ~50-70% size reduction)
Maintains original files for local use.

Usage:
    python scripts/compress_for_upload.py --collections all
    python scripts/compress_for_upload.py --collections fiqh_passages hadith_passages
    python scripts/compress_for_upload.py --dry-run
"""

import argparse
import gzip
import json
import os
import shutil
import sys
import time
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

COLLECTIONS_DIR = project_root / "data" / "processed" / "lucene_pages" / "collections"
OUTPUT_DIR = project_root / "data" / "processed" / "lucene_pages" / "upload_ready"

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


def compress_file(input_file: Path, output_file: Path, dry_run: bool = False) -> dict:
    """Compress a single JSONL file to JSONL.gz with stats."""
    original_size = input_file.stat().st_size
    
    if dry_run:
        # Estimate compression ratio (typically 0.3-0.5 for Arabic text)
        estimated_ratio = 0.35
        estimated_size = int(original_size * estimated_ratio)
        return {
            "original_size": original_size,
            "compressed_size": estimated_size,
            "ratio": estimated_ratio,
            "status": "estimated",
        }
    
    start_time = time.time()
    line_count = 0
    
    with open(input_file, 'rb') as f_in:
        with gzip.open(output_file, 'wb', compresslevel=6) as f_out:
            shutil.copyfileobj(f_in, f_out)
            # Count lines by seeking
            f_in.seek(0)
            for _ in f_in:
                line_count += 1
    
    compressed_size = output_file.stat().st_size
    duration = time.time() - start_time
    ratio = compressed_size / original_size if original_size > 0 else 1.0
    
    return {
        "original_size": original_size,
        "compressed_size": compressed_size,
        "ratio": ratio,
        "line_count": line_count,
        "duration": duration,
        "status": "compressed",
    }


def copy_metadata(output_dir: Path):
    """Copy metadata files to upload directory."""
    metadata_files = [
        "master_catalog.json",
        "category_mapping.json",
        "author_catalog.json",
    ]
    
    metadata_dir = project_root / "data" / "processed"
    
    for filename in metadata_files:
        src = metadata_dir / filename
        if src.exists():
            dst = output_dir / filename
            shutil.copy2(src, dst)
            print(f"  ✓ Copied {filename}")


def create_readme(output_dir: Path, collections: list):
    """Create README.md for the upload package."""
    readme = f"""# Athar Islamic Datasets

> Production-ready Islamic knowledge datasets extracted from Shamela's Lucene indexes.

**Total Documents:** 5,717,177  
**Collections:** {len(collections)}  
**Source:** Shamela Library (8,425 books, 11.3M+ Lucene documents)

---

## Collections

| File | Documents | Category |
|------|-----------|----------|
"""
    
    for collection in collections:
        jsonl_file = COLLECTIONS_DIR / f"{collection}.jsonl"
        if jsonl_file.exists():
            # Count lines
            with open(jsonl_file, 'r', encoding='utf-8') as f:
                line_count = sum(1 for _ in f)
            
            category = collection.replace('_passages', '').replace('_', ' ').title()
            readme += f"| {collection}.jsonl.gz | {line_count:,} | {category} |\n"
    
    readme += f"""
---

## File Format

- **Format:** JSONL (JSON Lines), gzipped
- **Encoding:** UTF-8
- **Schema:** See schema.json

## Schema

Each line is a JSON object with:
- `book_id`: Book identifier
- `title`: Book title (Arabic)
- `author`: Author name (Arabic)
- `author_death`: Author death year (Hijri)
- `category`: Shamela category (Arabic)
- `collection`: RAG collection name
- `page`: Page number
- `chapter`: Chapter title (Arabic)
- `content`: Page content (Arabic)
- `doc_id`: Unique document ID

## Metadata

- `master_catalog.json`: 8,425 books with full metadata
- `category_mapping.json`: 41 Shamela → 10 RAG collections mapping
- `author_catalog.json`: 3,146 authors with death years

## Usage

### Python
```python
import gzip
import json

# Load compressed collection
with gzip.open('fiqh_passages.jsonl.gz', 'rt', encoding='utf-8') as f:
    for line in f:
        doc = json.loads(line)
        print(doc['content'])
```

### Hugging Face Datasets
```python
from datasets import load_dataset

ds = load_dataset('json', data_files='fiqh_passages.jsonl.gz')
```

## Source

- **Project:** Athar Islamic QA System
- **GitHub:** https://github.com/Kandil7/Athar
- **Extraction Date:** April 2026

## License

MIT License
"""
    
    readme_file = output_dir / "README.md"
    with open(readme_file, 'w', encoding='utf-8') as f:
        f.write(readme)
    
    print(f"\n  ✓ Created README.md")


def main():
    parser = argparse.ArgumentParser(description="Compress collections for upload")
    parser.add_argument(
        "--collections",
        nargs="+",
        default=["all"],
        help="Collections to compress (default: all)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show estimated sizes without compressing",
    )
    args = parser.parse_args()
    
    # Determine collections
    if "all" in args.collections:
        collections = COLLECTIONS
    else:
        collections = args.collections
    
    # Create output directory
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    print("=" * 70)
    print("🕌 ATHAR - COMPRESS COLLECTIONS FOR UPLOAD")
    print("=" * 70)
    print(f"  Collections:     {len(collections)}")
    print(f"  Output dir:      {OUTPUT_DIR}")
    print(f"  Dry run:         {args.dry_run}")
    print("=" * 70)
    
    total_original = 0
    total_compressed = 0
    results = {}
    
    for collection in collections:
        input_file = COLLECTIONS_DIR / f"{collection}.jsonl"
        output_file = OUTPUT_DIR / f"{collection}.jsonl.gz"
        
        if not input_file.exists():
            print(f"\n  ✗ {collection}: File not found")
            continue
        
        print(f"\n  Compressing {collection}...")
        result = compress_file(input_file, output_file, args.dry_run)
        results[collection] = result
        
        total_original += result["original_size"]
        total_compressed += result["compressed_size"]
        
        original_mb = result["original_size"] / (1024 * 1024)
        compressed_mb = result["compressed_size"] / (1024 * 1024)
        ratio = result["ratio"]
        
        if args.dry_run:
            print(f"    Original:   {original_mb:.1f} MB (estimated)")
            print(f"    Compressed: {compressed_mb:.1f} MB (estimated)")
        else:
            duration = result.get("duration", 0)
            line_count = result.get("line_count", 0)
            print(f"    Original:   {original_mb:.1f} MB")
            print(f"    Compressed: {compressed_mb:.1f} MB ({ratio:.1%})")
            print(f"    Lines:      {line_count:,}")
            print(f"    Time:       {duration:.1f}s")
    
    # Copy metadata
    if not args.dry_run:
        print("\n  Copying metadata...")
        copy_metadata(OUTPUT_DIR)
        create_readme(OUTPUT_DIR, collections)
    
    # Summary
    total_original_mb = total_original / (1024 * 1024)
    total_compressed_mb = total_compressed / (1024 * 1024)
    overall_ratio = total_compressed / total_original if total_original > 0 else 1.0
    savings = (1 - overall_ratio) * 100
    
    print("\n" + "=" * 70)
    print("📊 COMPRESSION SUMMARY")
    print("=" * 70)
    print(f"  Original size:     {total_original_mb:.1f} MB ({total_original_mb / 1024:.2f} GB)")
    print(f"  Compressed size:   {total_compressed_mb:.1f} MB ({total_compressed_mb / 1024:.2f} GB)")
    print(f"  Compression ratio: {overall_ratio:.1%}")
    print(f"  Space savings:     {savings:.1f}%")
    print("=" * 70)
    
    if args.dry_run:
        print("\n  💡 Run without --dry-run to actually compress files")
    else:
        print(f"\n  ✓ Upload-ready files saved to: {OUTPUT_DIR}")
        print(f"  💡 Use scripts/upload_to_huggingface.py to upload")


if __name__ == "__main__":
    main()
