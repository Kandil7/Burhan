#!/usr/bin/env python3
"""
Prepare datasets for upload to Hugging Face / Kaggle (v2 - with hierarchical chunking).

Uses the new hierarchical chunking system for optimal RAG performance:
- Preserves chapter/page boundaries
- Enriches chunks with full metadata
- Maps to 11 RAG collections
- Handles special cases (fatwas, hadith, tafsir)

Usage:
    python scripts/prepare_datasets_for_upload_v2.py

Output:
    data/athar-datasets/
    ├── README.md                           # Dataset documentation
    ├── dataset_info.json                   # Dataset metadata
    ├── hierarchical_chunks/                # OPTIMIZED CHUNKS (recommended)
    │   ├── fiqh_passages.jsonl             # ~1,581 books → chunks
    │   ├── hadith_passages.jsonl           # ~2,358 books → chunks
    │   ├── aqeedah_passages.jsonl          # ~945 books → chunks
    │   └── ... (11 collections)
    │
    ├── raw_books/                          # RAW BOOKS (for reference)
    │   ├── part01.tar.gz                   # <500 MB chunks
    │   ├── part02.tar.gz
    │   └── ...
    ├── hadith/
    │   └── sanadset.csv                    # 1.43 GB
    └── metadata/
        ├── category_mapping.json
        ├── books_sample.json
        └── collection_stats.json
"""

import json
import os
import shutil
import tarfile
from pathlib import Path
from typing import Dict, List, Optional

# Import hierarchical chunking
try:
    from src.indexing.chunking.hierarchical_chunker import HierarchicalChunker, BookMetadata
    from scripts.utils import setup_script_logger, get_project_root, get_data_dir, get_datasets_dir

    HAS_CHUNKER = True
except ImportError as e:
    print(f"⚠️  Warning: Could not import hierarchical chunker: {e}")
    print("   Falling back to basic preparation mode")
    HAS_CHUNKER = False

# Configuration
DATASETS_DIR = Path("datasets")
OUTPUT_DIR = Path("data/athar-datasets-v2")
MAX_FILE_SIZE = 4 * 1024**3  # 4 GB (safe under 5 GB git-lfs limit)
CHUNK_SIZE = 500 * 1024**2  # 500 MB per archive chunk


def get_directory_size(path: Path) -> int:
    """Get total size of directory in bytes."""
    total = 0
    for f in path.rglob("*"):
        if f.is_file():
            total += f.stat().st_size
    return total


def format_size(size_bytes: int) -> str:
    """Format bytes to human-readable size."""
    for unit in ["B", "KB", "MB", "GB"]:
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f} TB"


def create_hierarchical_chunks(output_dir: Path, books_dir: Path, metadata_dir: Path):
    """
    Create hierarchically chunked datasets organized by collection.

    This is the KEY improvement over v1 - uses semantic boundaries and full metadata.
    """
    print("\n" + "=" * 70)
    print("📚 CREATING HIERARCHICAL CHUNKS (v2)")
    print("=" * 70)

    if not HAS_CHUNKER:
        print("❌ Hierarchical chunker not available")
        print("   Install dependencies or use v1 script")
        return False

    # Initialize chunker
    chunker = HierarchicalChunker()

    # Load category mapping
    category_mapping_file = Path("data/processed/category_mapping.json")
    if category_mapping_file.exists():
        with open(category_mapping_file) as f:
            category_mapping = json.load(f)
        print(f"✅ Loaded category mapping ({len(category_mapping['books'])} books)")
    else:
        print("⚠️  Category mapping not found, running creation script...")
        import subprocess

        subprocess.run(["python", "scripts/create_category_mapping.py"])
        with open(category_mapping_file) as f:
            category_mapping = json.load(f)

    # Create output directory
    chunks_dir = output_dir / "hierarchical_chunks"
    chunks_dir.mkdir(parents=True, exist_ok=True)

    # Get all book files
    book_files = sorted(books_dir.glob("*.txt"))
    print(f"\n📊 Processing {len(book_files):,} books")

    # Open JSONL files for each collection
    jsonl_files = {}
    collection_counts = {}

    # Process books
    processed = 0
    errors = 0
    total_chunks = 0

    for book_file in book_files:
        try:
            # Extract book ID from filename
            book_id = int(book_file.stem.split("_")[0])

            # Get metadata
            book_meta = category_mapping["books"].get(str(book_id))
            if not book_meta:
                continue

            # Read book content
            with open(book_file, "r", encoding="utf-8") as f:
                content = f.read()

            # Create BookMetadata object
            book_metadata = BookMetadata(
                book_id=book_id,
                book_title=book_meta.get("title", book_file.stem),
                author=book_meta.get("author", "Unknown"),
                author_death=book_meta.get("author_death"),
                category=book_meta.get("category", ""),
                category_en=book_meta.get("category_en", ""),
            )

            # Chunk the book
            chunks = chunker.chunk_text(content, book_metadata)

            # Write to appropriate collection JSONL files
            for chunk in chunks:
                chunk_dict = chunk.to_dict()

                # Determine collection
                collection = chunk_dict.get("collection", "general_islamic")

                # Open JSONL file if not already open
                if collection not in jsonl_files:
                    jsonl_path = chunks_dir / f"{collection}.jsonl"
                    jsonl_files[collection] = open(jsonl_path, "w", encoding="utf-8")
                    collection_counts[collection] = 0

                # Write chunk
                jsonl_files[collection].write(json.dumps(chunk_dict, ensure_ascii=False) + "\n")
                collection_counts[collection] += 1
                total_chunks += 1

            processed += 1

            # Progress update every 100 books
            if processed % 100 == 0:
                print(f"   📖 Processed {processed:,} books → {total_chunks:,} chunks")

        except Exception as e:
            errors += 1
            if errors <= 10:  # Only show first 10 errors
                print(f"   ⚠️  Error processing {book_file.name}: {e}")

    # Close all JSONL files
    for f in jsonl_files.values():
        f.close()

    # Print summary
    print(f"\n{'=' * 70}")
    print(f"✅ HIERARCHICAL CHUNKING COMPLETE")
    print(f"{'=' * 70}")
    print(f"\n📊 Summary:")
    print(f"   Books processed: {processed:,}")
    print(f"   Total chunks: {total_chunks:,}")
    print(f"   Errors: {errors}")
    print(f"\n📁 Collections:")
    for collection, count in sorted(collection_counts.items(), key=lambda x: -x[1]):
        jsonl_path = chunks_dir / f"{collection}.jsonl"
        size = jsonl_path.stat().st_size if jsonl_path.exists() else 0
        print(f"   {collection:30s}: {count:6,} chunks ({format_size(size)})")

    return True


def create_tar_chunks(source_dir: Path, output_dir: Path, prefix: str, max_chunk_size: int = CHUNK_SIZE):
    """Create tar.gz archives split into chunks (for raw books backup)."""
    print(f"\n📦 Creating {prefix} archives...")
    print(f"   Source: {source_dir}")
    print(f"   Max chunk size: {format_size(max_chunk_size)}")

    files = [f for f in source_dir.rglob("*.txt") if f.is_file()]
    total_size = sum(f.stat().st_size for f in files)

    print(f"   Files: {len(files):,}")
    print(f"   Total size: {format_size(total_size)}")

    chunk_num = 0
    current_size = 0
    current_files = []
    chunk_output = output_dir / f"{prefix}_part01.tar.gz"

    for file_path in files:
        file_size = file_path.stat().st_size

        if current_size + file_size > max_chunk_size and current_files:
            with tarfile.open(chunk_output, "w:gz") as tar:
                for f in current_files:
                    tar.add(f, arcname=f.relative_to(source_dir.parent))

            print(f"   ✅ Created {chunk_output.name}: {format_size(chunk_output.stat().st_size)}")

            chunk_num += 1
            current_size = 0
            current_files = []
            chunk_output = output_dir / f"{prefix}_part{chunk_num + 1:02d}.tar.gz"

        current_files.append(file_path)
        current_size += file_size

    if current_files:
        with tarfile.open(chunk_output, "w:gz") as tar:
            for f in current_files:
                tar.add(f, arcname=f.relative_to(source_dir.parent))

        print(f"   ✅ Created {chunk_output.name}: {format_size(chunk_output.stat().st_size)}")

    print(f"   📊 Total chunks: {chunk_num + 1}")


def prepare_metadata():
    """Prepare comprehensive metadata for dataset."""
    print("\n📋 Preparing metadata...")

    metadata = {
        "name": "Athar Islamic QA System Datasets (v2)",
        "description": "Comprehensive Islamic scholarly texts with hierarchical chunking for optimal RAG",
        "version": "2.0.0",
        "license": "MIT",
        "homepage": "https://github.com/Kandil7/Athar",
        "chunking_strategy": {
            "type": "hierarchical",
            "levels": ["book_metadata", "chapter_boundaries", "page_boundaries", "content_split"],
            "target_chunk_size": "300-600 tokens",
            "overlap": "50-75 tokens",
            "metadata_enrichment": True,
        },
        "sources": {
            "shamela_library": {
                "description": "8,425 Islamic books from Shamela",
                "size": "16.4 GB",
                "format": "TXT (extracted)",
                "language": "Arabic (Classical)",
            },
            "sanadset_hadith": {
                "description": "650,986 hadith with sanad/matan",
                "size": "1.43 GB",
                "format": "CSV",
                "language": "Arabic",
            },
        },
        "collections": {
            "fiqh_passages": {"description": "Islamic jurisprudence", "estimated_books": 1581},
            "hadith_passages": {"description": "Prophetic traditions", "estimated_books": 2358},
            "quran_tafsir": {"description": "Quran interpretation", "estimated_books": 725},
            "aqeedah_passages": {"description": "Islamic creed", "estimated_books": 945},
            "seerah_passages": {"description": "Prophet biography", "estimated_books": 184},
            "islamic_history": {"description": "Islamic history", "estimated_books": 888},
            "arabic_language": {"description": "Arabic language", "estimated_books": 500},
            "spirituality": {"description": "Spirituality & ethics", "estimated_books": 619},
            "general_islamic": {"description": "General Islamic knowledge", "estimated_books": 137},
            "comparative_religion": {"description": "Comparative religion", "estimated_books": 151},
            "medicine_science": {"description": "Islamic medicine & science", "estimated_books": 40},
        },
        "usage": {
            "citation": "@misc{athar2026, title={Athar Islamic QA System Datasets}, author={Athar Team}, year={2026}, version={2.0}}",
            "acknowledgment": "Data sourced from Shamela Library and Sanadset Hadith Dataset",
        },
    }

    return metadata


def main():
    """Main preparation function."""
    print("=" * 70)
    print("🕌 ATHAR - PREPARE DATASETS FOR UPLOAD (v2 - Hierarchical)")
    print("=" * 70)

    # Create output directory
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Calculate source sizes
    books_dir = DATASETS_DIR / "data" / "extracted_books"
    sanadset_base = DATASETS_DIR / "Sanadset 368K Data on Hadith Narrators"
    hadith_dir = None
    if sanadset_base.exists():
        hadith_dir = sanadset_base / "Sanadset 368K Data on Hadith Narrators"
        if not hadith_dir.exists():
            for csv_file in sanadset_base.rglob("sanadset.csv"):
                hadith_dir = csv_file.parent
                break

    metadata_dir = DATASETS_DIR / "data" / "metadata"

    print(f"\n📊 Source Data:")
    print(f"   Books: {format_size(get_directory_size(books_dir))} ({sum(1 for _ in books_dir.glob('*.txt')):,} files)")

    if hadith_dir and hadith_dir.exists():
        hadith_size = get_directory_size(hadith_dir)
        print(f"   Hadith: {format_size(hadith_size)}")
    else:
        print(f"   Hadith: Not found")
        hadith_dir = None

    print(f"   Metadata: {format_size(get_directory_size(metadata_dir))}")

    # ==========================================
    # STEP 1: Create hierarchical chunks (KEY IMPROVEMENT)
    # ==========================================
    hierarchical_success = False
    if HAS_CHUNKER:
        hierarchical_success = create_hierarchical_chunks(OUTPUT_DIR, books_dir, metadata_dir)

    # ==========================================
    # STEP 2: Create raw books backup (tar chunks)
    # ==========================================
    print(f"\n{'=' * 70}")
    print("📦 CREATING RAW BOOKS BACKUP")
    print(f"{'=' * 70}")

    raw_books_dir = OUTPUT_DIR / "raw_books"
    raw_books_dir.mkdir(exist_ok=True)

    if books_dir.exists():
        create_tar_chunks(books_dir, raw_books_dir, "extracted_books")

    # ==========================================
    # STEP 3: Copy hadith CSV
    # ==========================================
    (OUTPUT_DIR / "hadith").mkdir(exist_ok=True)

    sanadset_csv = None
    if hadith_dir:
        for csv_file in hadith_dir.rglob("sanadset.csv"):
            sanadset_csv = csv_file
            break

    if sanadset_csv and sanadset_csv.exists():
        csv_size = sanadset_csv.stat().st_size
        if csv_size < MAX_FILE_SIZE:
            print(f"\n📋 Copying hadith CSV ({format_size(csv_size)})...")
            shutil.copy2(sanadset_csv, OUTPUT_DIR / "hadith" / "sanadset.csv")
            print(f"   ✅ Copied successfully")
        else:
            print(f"\n⚠️  Hadith CSV too large ({format_size(csv_size)})")
    else:
        print(f"\n⚠️  Hadith CSV not found")

    # ==========================================
    # STEP 4: Prepare metadata
    # ==========================================
    metadata = prepare_metadata()

    dataset_info = OUTPUT_DIR / "dataset_info.json"
    with open(dataset_info, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)
    print(f"\n✅ Created {dataset_info}")

    # Copy category mapping
    category_mapping_file = Path("data/processed/category_mapping.json")
    if category_mapping_file.exists():
        (OUTPUT_DIR / "metadata").mkdir(exist_ok=True)
        shutil.copy2(category_mapping_file, OUTPUT_DIR / "metadata" / "category_mapping.json")
        print(f"   ✅ Copied category_mapping.json")

    # Copy essential metadata
    essential_metadata = ["categories.json", "books.json"]
    for meta_file in essential_metadata:
        src = metadata_dir / meta_file
        dst = OUTPUT_DIR / "metadata" / meta_file
        if src.exists():
            shutil.copy2(src, dst)
            print(f"   ✅ Copied {meta_file}")

    # ==========================================
    # STEP 5: Create README
    # ==========================================
    chunks_info = ""
    if hierarchical_success:
        chunks_info = """
## Hierarchical Chunks (Recommended for RAG)

These chunks use **hierarchical semantic chunking** for optimal retrieval:

- **Chapter boundaries**: Preserved from `<span data-type="title">` markers
- **Page boundaries**: Respected from `[Page N]` markers
- **Target size**: 300-600 tokens per chunk
- **Metadata enrichment**: Every chunk includes book_id, title, author, category, page
- **Collection mapping**: 41 categories → 11 RAG collections

### Usage Example

```python
import json

# Load fiqh chunks
with open('fiqh_passages.jsonl') as f:
    chunks = [json.loads(line) for line in f]

# Each chunk has full metadata
print(chunks[0]['book_title'])
print(chunks[0]['category'])
print(chunks[0]['page_number'])
```
"""

    readme_content = f"""# 🕌 Athar Islamic QA System - Datasets (v2)

Comprehensive Islamic scholarly texts with hierarchical chunking for optimal RAG performance.

## Dataset Overview

- **Total Size:** ~18 GB (chunks + raw books + hadith)
- **Books:** 8,425 from Shamela Library (16.4 GB)
- **Hadith:** 650,986 from Sanadset (1.43 GB)
- **Chunking:** Hierarchical semantic boundaries
- **Language:** Arabic (Classical)
- **License:** MIT

## Files

| Directory | Description | Size |
|-----------|-------------|------|
| `hierarchical_chunks/` | **OPTIMIZED** chunks for RAG (recommended) | ~2-3 GB |
| `raw_books/` | Original books (tar.gz chunks) | ~16 GB |
| `hadith/` | Hadith CSV | 1.43 GB |
| `metadata/` | Category mappings, book metadata | <50 MB |
{chunks_info}

## Collections

| Collection | Books | Description |
|------------|-------|-------------|
| Fiqh | ~1,581 | Islamic jurisprudence |
| Hadith | ~2,358 | Prophetic traditions |
| Aqeedah | ~945 | Islamic creed |
| Tafsir/Quran | ~725 | Quran interpretation |
| Seerah/History | ~1,072 | Biography & history |
| Arabic Language | ~500 | Grammar, morphology, rhetoric |
| Spirituality | ~619 | Ethics & devotion |
| General | ~137 | Miscellaneous |
| Comparative Religion | ~151 | Sects & refutations |
| Medicine/Science | ~40 | Historical sciences |

## Citation

```
@misc{{athar2026,
  title={{Athar Islamic QA System Datasets}},
  author={{Athar Team}},
  year={{2026}},
  url={{https://huggingface.co/datasets/Kandil7/Athar-Datasets}},
  version={{2.0}}
}}
```

## Acknowledgments

- Shamela Library for Islamic texts
- Sanadset Hadith Dataset
"""

    readme_path = OUTPUT_DIR / "README.md"
    with open(readme_path, "w", encoding="utf-8") as f:
        f.write(readme_content)
    print(f"\n✅ Created {readme_path}")

    # ==========================================
    # FINAL SUMMARY
    # ==========================================
    total_size = get_directory_size(OUTPUT_DIR)
    num_files = sum(1 for _ in OUTPUT_DIR.rglob("*") if _.is_file())

    print(f"\n{'=' * 70}")
    print(f"✅ DATASET PREPARATION COMPLETE (v2)")
    print(f"{'=' * 70}")
    print(f"\n📊 Summary:")
    print(f"   Output directory: {OUTPUT_DIR}")
    print(f"   Total size: {format_size(total_size)}")
    print(f"   Files: {num_files}")
    print(f"\n📁 Directory structure:")
    for f in sorted(OUTPUT_DIR.rglob("*")):
        if f.is_file():
            rel_path = f.relative_to(OUTPUT_DIR)
            size = format_size(f.stat().st_size)
            print(f"   {rel_path:45s} {size}")

    print(f"\n🚀 Next steps:")
    print(f"   1. Review files in {OUTPUT_DIR}")
    print(f"   2. Upload to Hugging Face:")
    print(f"      python notebooks/04_upload_to_huggingface.ipynb")
    print(f"   3. Or upload to Kaggle:")
    print(f"      python notebooks/05_upload_to_kaggle.ipynb")


if __name__ == "__main__":
    main()
