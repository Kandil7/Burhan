#!/usr/bin/env python3
"""
Upload compressed collections to Kaggle Datasets.

Kaggle offers FREE 100 GB per dataset, perfect for our 61 GB collections.

Usage:
    python scripts/upload_to_kaggle.py --title "Athar Islamic Collections"
    python scripts/upload_to_kaggle.py --dry-run

Prerequisites:
    pip install kaggle
    # Download kaggle.json from https://www.kaggle.com/account
    # Place in ~/.kaggle/kaggle.json
"""

import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

UPLOAD_DIR = project_root / "data" / "processed" / "lucene_pages" / "upload_ready"
KAGGLE_DIR = project_root / "data" / "athar-datasets-kaggle"

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


def create_dataset_metadata(output_dir: Path, title: str):
    """Create kaggle.json dataset metadata."""
    metadata = {
        "title": title,
        "id": os.environ.get("KAGGLE_DATASET_ID", "YOUR_USERNAME/athar-islamic-collections"),
        "licenses": [{"name": "MIT"}],
        "subtitle": "Production-ready Islamic knowledge datasets from Shamela Library",
        "description": """# Athar Islamic Collections

Production-ready Islamic knowledge datasets extracted from Shamela's Lucene indexes.

## Statistics
- **Total Documents:** 5,717,177
- **Collections:** 10
- **Source:** Shamela Library (8,425 books, 11.3M+ Lucene documents)
- **Extraction Date:** April 2026

## Collections

| File | Description |
|------|-------------|
| fiqh_passages.jsonl.gz | Islamic jurisprudence texts |
| hadith_passages.jsonl.gz | Prophetic traditions |
| quran_tafsir.jsonl.gz | Quran interpretation |
| aqeedah_passages.jsonl.gz | Islamic creed and theology |
| seerah_passages.jsonl.gz | Prophet biography |
| islamic_history_passages.jsonl.gz | Islamic historical texts |
| arabic_language_passages.jsonl.gz | Arabic language and literature |
| spirituality_passages.jsonl.gz | Spirituality and ethics |
| general_islamic.jsonl.gz | General Islamic knowledge |
| usul_fiqh.jsonl.gz | Principles of jurisprudence |

## Metadata Files
- `master_catalog.json`: 8,425 books with full metadata
- `category_mapping.json`: 41 Shamela → 10 RAG collections mapping
- `author_catalog.json`: 3,146 authors with death years

## Usage

```python
import gzip
import json

with gzip.open('fiqh_passages.jsonl.gz', 'rt', encoding='utf-8') as f:
    for line in f:
        doc = json.loads(line)
        print(doc['content'])
```

## Source
- **Project:** Athar Islamic QA System
- **GitHub:** https://github.com/Kandil7/Athar

## License
MIT License
""",
        "tags": [
            "islamic",
            "quran",
            "hadith",
            "fiqh",
            "arabic",
            "rag",
            "nlp",
        ],
    }
    
    metadata_file = output_dir / "dataset-metadata.json"
    with open(metadata_file, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)
    
    print(f"  ✓ Created dataset-metadata.json")


def prepare_kaggle_upload(collections: list):
    """Prepare Kaggle upload directory with symlinks (no copying)."""
    KAGGLE_DIR.mkdir(parents=True, exist_ok=True)
    
    print(f"\n📦 Preparing Kaggle upload directory...")
    
    files_copied = 0
    total_size = 0
    
    # Copy compressed collection files
    for collection in collections:
        gz_file = UPLOAD_DIR / f"{collection}.jsonl.gz"
        if gz_file.exists():
            dest = KAGGLE_DIR / gz_file.name
            if not dest.exists():
                # Use symlink to avoid copying (saves time and disk)
                os.symlink(str(gz_file), str(dest))
                print(f"  ✓ Linked {collection}.jsonl.gz")
                files_copied += 1
                total_size += gz_file.stat().st_size
        else:
            print(f"  ✗ {collection}.jsonl.gz not found")
    
    # Copy metadata
    metadata_files = [
        "master_catalog.json",
        "category_mapping.json",
        "author_catalog.json",
    ]
    
    for filename in metadata_files:
        src = UPLOAD_DIR / filename
        if src.exists():
            dest = KAGGLE_DIR / filename
            if not dest.exists():
                os.symlink(str(src), str(dest))
                print(f"  ✓ Linked {filename}")
                files_copied += 1
    
    # Create dataset metadata
    create_dataset_metadata(
        KAGGLE_DIR,
        title="Athar Islamic Collections"
    )
    
    return files_copied, total_size


def main():
    parser = argparse.ArgumentParser(description="Upload to Kaggle")
    parser.add_argument(
        "--title",
        type=str,
        default="Athar Islamic Collections",
        help="Dataset title",
    )
    parser.add_argument(
        "--collections",
        nargs="+",
        default=["all"],
        help="Collections to upload (default: all)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be uploaded",
    )
    args = parser.parse_args()
    
    # Determine collections
    if "all" in args.collections:
        collections = COLLECTIONS
    else:
        collections = args.collections
    
    print("=" * 70)
    print("🕌 ATHAR - UPLOAD TO KAGGLE")
    print("=" * 70)
    print(f"  Title:           {args.title}")
    print(f"  Collections:     {len(collections)}")
    print(f"  Dry run:         {args.dry_run}")
    print("=" * 70)
    
    # Check if Kaggle CLI is installed
    try:
        subprocess.run(["kaggle", "--version"], capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("\n❌ Kaggle CLI not installed. Run: pip install kaggle")
        print("   Then download API token from https://www.kaggle.com/account")
        sys.exit(1)
    
    # Check if upload directory exists
    if not UPLOAD_DIR.exists():
        print(f"\n⚠️ Upload directory not found: {UPLOAD_DIR}")
        print("   Run: python scripts/compress_for_upload.py")
        sys.exit(1)
    
    # Prepare Kaggle directory
    files_count, total_size = prepare_kaggle_upload(collections)
    
    total_mb = total_size / (1024 * 1024)
    print(f"\n📊 Prepared {files_count} files ({total_mb:.1f} MB / {total_mb / 1024:.2f} GB)")
    
    if args.dry_run:
        print("\n💡 Run without --dry-run to actually upload")
        return
    
    # Upload using Kaggle CLI
    print(f"\n📤 Uploading to Kaggle...")
    print(f"   This may take a while ({total_mb / 1024:.2f} GB)")
    
    try:
        result = subprocess.run(
            ["kaggle", "datasets", "create", "-p", str(KAGGLE_DIR), "--quiet"],
            capture_output=True,
            text=True,
            timeout=36000,  # 10 hours timeout
        )
        
        if result.returncode == 0:
            print("\n✅ Upload successful!")
            print(f"   View at: https://www.kaggle.com/datasets/")
        else:
            print(f"\n❌ Upload failed:")
            print(result.stderr)
    except subprocess.TimeoutExpired:
        print("\n⏱️ Upload timed out (10 hours). Try again with faster connection.")
    except Exception as e:
        print(f"\n❌ Upload failed: {e}")


if __name__ == "__main__":
    main()
