#!/usr/bin/env python3
"""
Prepare datasets for upload to Hugging Face / Kaggle.

Chunks large files into <5 GB pieces for git-lfs compatibility,
creates metadata files, and generates upload-ready structure.

Usage:
    python scripts/prepare_datasets_for_upload.py

Output:
    data/Burhan-datasets/
    ├── README.md                           # Dataset documentation
    ├── dataset_info.json                   # Dataset metadata
    ├── extracted_books/
    │   ├── part01.tar.gz                   # <5 GB chunks
    │   ├── part02.tar.gz
    │   └── ...
    ├── hadith/
    │   └── sanadset.csv                    # 1.43 GB (<5 GB, no split needed)
    └── metadata/
        ├── categories.json
        ├── books_sample.json
        └── collection_stats.json
"""
import json
import os
import shutil
import tarfile
from pathlib import Path

# Configuration
DATASETS_DIR = Path("datasets")
OUTPUT_DIR = Path("data/Burhan-datasets")
MAX_FILE_SIZE = 4 * 1024**3  # 4 GB (safe under 5 GB git-lfs limit)
CHUNK_SIZE = 500 * 1024**2  # 500 MB per archive chunk


def get_directory_size(path: Path) -> int:
    """Get total size of directory in bytes."""
    total = 0
    for f in path.rglob('*'):
        if f.is_file():
            total += f.stat().st_size
    return total


def format_size(size_bytes: int) -> str:
    """Format bytes to human-readable size."""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f} TB"


def create_tar_chunks(source_dir: Path, output_dir: Path, prefix: str, max_chunk_size: int = CHUNK_SIZE):
    """
    Create tar.gz archives split into chunks.
    
    Args:
        source_dir: Directory to archive
        output_dir: Where to save archives
        prefix: Filename prefix
        max_chunk_size: Maximum size per chunk
    """
    print(f"\n📦 Creating {prefix} archives...")
    print(f"   Source: {source_dir}")
    print(f"   Max chunk size: {format_size(max_chunk_size)}")
    
    # Get all files
    files = [f for f in source_dir.rglob('*.txt') if f.is_file()]
    total_size = sum(f.stat().st_size for f in files)
    
    print(f"   Files: {len(files):,}")
    print(f"   Total size: {format_size(total_size)}")
    
    # Create chunks
    chunk_num = 0
    current_size = 0
    current_files = []
    chunk_output = output_dir / f"{prefix}_part01.tar.gz"
    
    for file_path in files:
        file_size = file_path.stat().st_size
        
        # Check if adding this file exceeds chunk size
        if current_size + file_size > max_chunk_size and current_files:
            # Write current chunk
            with tarfile.open(chunk_output, 'w:gz') as tar:
                for f in current_files:
                    tar.add(f, arcname=f.relative_to(source_dir.parent))
            
            print(f"   ✅ Created {chunk_output.name}: {format_size(chunk_output.stat().st_size)}")
            
            # Start new chunk
            chunk_num += 1
            current_size = 0
            current_files = []
            chunk_output = output_dir / f"{prefix}_part{chunk_num + 1:02d}.tar.gz"
        
        current_files.append(file_path)
        current_size += file_size
    
    # Write last chunk
    if current_files:
        with tarfile.open(chunk_output, 'w:gz') as tar:
            for f in current_files:
                tar.add(f, arcname=f.relative_to(source_dir.parent))
        
        print(f"   ✅ Created {chunk_output.name}: {format_size(chunk_output.stat().st_size)}")
    
    print(f"   📊 Total chunks: {chunk_num + 1}")


def prepare_metadata():
    """Prepare metadata files for dataset."""
    print("\n📋 Preparing metadata...")
    
    metadata = {
        "name": "Burhan Islamic QA System Datasets",
        "description": "Comprehensive Islamic scholarly texts for QA system",
        "version": "1.0.0",
        "license": "MIT",
        "homepage": "https://github.com/Kandil7/Burhan",
        "sources": {
            "shamela_library": {
                "description": "8,425 Islamic books from Shamela",
                "size": "17.16 GB",
                "format": "TXT (extracted)",
                "language": "Arabic",
            },
            "sanadset_hadith": {
                "description": "650,986 hadith with sanad/matan",
                "size": "1.43 GB",
                "format": "CSV",
                "language": "Arabic",
            }
        },
        "collections": {
            "fiqh_passages": {"description": "Islamic jurisprudence", "estimated_docs": 10000},
            "hadith_passages": {"description": "Prophetic traditions", "estimated_docs": 650986},
            "quran_tafsir": {"description": "Quran interpretation", "estimated_docs": 6236},
            "aqeedah_passages": {"description": "Islamic creed", "estimated_docs": 5000},
            "seerah_passages": {"description": "Prophet biography", "estimated_docs": 5000},
            "islamic_history": {"description": "Islamic history", "estimated_docs": 8000},
            "arabic_language": {"description": "Arabic language", "estimated_docs": 6000},
            "spirituality": {"description": "Spirituality & ethics", "estimated_docs": 4000},
            "general_islamic": {"description": "General Islamic knowledge", "estimated_docs": 5000},
            "duas_adhkar": {"description": "Supplications & remembrance", "estimated_docs": 1000},
        },
        "usage": {
            "citation": "@misc{Burhan2026, title={Burhan Islamic QA System Datasets}, author={Burhan Team}, year={2026}}",
            "acknowledgment": "Data sourced from Shamela Library and Sanadset Hadith Dataset",
        }
    }
    
    return metadata


def main():
    """Main preparation function."""
    print("="*70)
    print("🕌 Burhan - PREPARE DATASETS FOR UPLOAD")
    print("="*70)
    
    # Create output directory
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    # Calculate source sizes
    books_dir = DATASETS_DIR / "data" / "extracted_books"
    
    # Auto-detect Sanadset directory (handles various naming)
    sanadset_base = DATASETS_DIR / "Sanadset 368K Data on Hadith Narrators"
    hadith_dir = None
    if sanadset_base.exists():
        # Try nested directory
        hadith_dir = sanadset_base / "Sanadset 368K Data on Hadith Narrators"
        if not hadith_dir.exists():
            # Try direct CSV
            for csv_file in sanadset_base.rglob("sanadset.csv"):
                hadith_dir = csv_file.parent
                break
    
    metadata_dir = DATASETS_DIR / "data" / "metadata"

    print(f"\n📊 Source Data:")
    print(f"   Books: {format_size(get_directory_size(books_dir))} ({sum(1 for _ in books_dir.glob('*.txt')):,} files)")
    
    if hadith_dir and hadith_dir.exists():
        hadith_size = get_directory_size(hadith_dir)
        print(f"   Hadith: {format_size(hadith_size)} (in {hadith_dir.name})")
    else:
        print(f"   Hadith: Not found")
        hadith_dir = None
    
    print(f"   Metadata: {format_size(get_directory_size(metadata_dir))}")
    
    # Create directory structure
    (OUTPUT_DIR / "extracted_books").mkdir(exist_ok=True)
    (OUTPUT_DIR / "hadith").mkdir(exist_ok=True)
    (OUTPUT_DIR / "metadata").mkdir(exist_ok=True)
    
    # 1. Chunk extracted books
    if books_dir.exists():
        create_tar_chunks(books_dir, OUTPUT_DIR / "extracted_books", "extracted_books")
    else:
        print(f"\n⚠️  Books directory not found: {books_dir}")
    
    # 2. Copy hadith CSV (if <5 GB, no chunking needed)
    sanadset_csv = None
    if hadith_dir:
        # Find sanadset.csv
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
            print(f"\n⚠️  Hadith CSV too large ({format_size(csv_size)}), needs chunking")
            # TODO: Implement CSV chunking if needed
    else:
        print(f"\n⚠️  Hadith CSV not found")
        print(f"   Expected in: {hadith_dir if hadith_dir else 'Unknown'}")
    
    # 3. Prepare metadata
    metadata = prepare_metadata()
    
    # Save dataset info
    dataset_info = OUTPUT_DIR / "dataset_info.json"
    with open(dataset_info, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)
    print(f"\n✅ Created {dataset_info}")
    
    # Copy essential metadata files
    essential_metadata = [
        "categories.json",
        "books.json",
        "authors.json"
    ]
    
    for meta_file in essential_metadata:
        src = metadata_dir / meta_file
        dst = OUTPUT_DIR / "metadata" / meta_file
        if src.exists():
            shutil.copy2(src, dst)
            print(f"   ✅ Copied {meta_file}")
    
    # 4. Create README
    readme_content = f"""# 🕌 Burhan Islamic QA System - Datasets

Comprehensive Islamic scholarly texts for the Burhan QA system.

## Dataset Overview

- **Total Size:** ~19 GB
- **Books:** 8,425 from Shamela Library (17.16 GB)
- **Hadith:** 650,986 from Sanadset (1.43 GB)
- **Language:** Arabic
- **License:** MIT

## Files

| File | Description | Size |
|------|-------------|------|
| `extracted_books/part*.tar.gz` | Shamela books (chunked) | ~17 GB |
| `hadith/sanadset.csv` | Hadith with sanad/matan | 1.43 GB |
| `metadata/` | Categories, authors, books | <1 MB |

## Usage

### Python

```python
from huggingface_hub import hf_hub_download
import tarfile

# Download and extract
download_path = hf_hub_download(
    repo_id="Kandil7/Athar-Datasets",
    filename="extracted_books/part01.tar.gz"
)

with tarfile.open(download_path, 'r:gz') as tar:
    tar.extractall(path='./extracted_books')
```

### Colab

```python
from huggingface_hub import login, hf_hub_download

login()  # Authenticate

# Download chunk
path = hf_hub_download(
    repo_id="Kandil7/Athar-Datasets",
    filename="extracted_books/part01.tar.gz"
)
```

## Collections

| Collection | Books | Estimated Docs |
|------------|-------|----------------|
| Fiqh | 1,519 | ~10,000 |
| Hadith | 2,135 | ~650,986 |
| History | 1,072 | ~8,000 |
| Aqeedah | 945 | ~5,000 |
| Arabic Language | 904 | ~6,000 |
| Quran & Tafsir | 725 | ~6,236 |
| Spirituality | 619 | ~4,000 |

## Citation

```
@misc{{Burhan2026,
  title={{Burhan Islamic QA System Datasets}},
  author={{Burhan Team}},
  year={{2026}},
  url={{https://huggingface.co/datasets/Kandil7/Athar-Datasets}}
}}
```

## Acknowledgments

- Shamela Library for Islamic texts
- Sanadset Hadith Dataset
"""
    
    readme_path = OUTPUT_DIR / "README.md"
    with open(readme_path, 'w', encoding='utf-8') as f:
        f.write(readme_content)
    print(f"\n✅ Created {readme_path}")
    
    # Summary
    total_size = get_directory_size(OUTPUT_DIR)
    num_files = sum(1 for _ in OUTPUT_DIR.rglob('*') if _.is_file())
    
    print(f"\n{'='*70}")
    print(f"✅ DATASET PREPARATION COMPLETE")
    print(f"{'='*70}")
    print(f"\n📊 Summary:")
    print(f"   Output directory: {OUTPUT_DIR}")
    print(f"   Total size: {format_size(total_size)}")
    print(f"   Files: {num_files}")
    print(f"\n📁 Directory structure:")
    for f in sorted(OUTPUT_DIR.rglob('*')):
        if f.is_file():
            rel_path = f.relative_to(OUTPUT_DIR)
            size = format_size(f.stat().st_size)
            print(f"   {rel_path:40s} {size}")
    
    print(f"\n🚀 Next steps:")
    print(f"   1. Review files in {OUTPUT_DIR}")
    print(f"   2. Run: python scripts/upload_to_huggingface.py")
    print(f"   3. Or use: notebooks/04_upload_to_huggingface.ipynb")


if __name__ == "__main__":
    main()
