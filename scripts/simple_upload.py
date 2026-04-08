#!/usr/bin/env python3
"""
Simple upload script for Hugging Face.
Uploads collections one by one with progress tracking.

Usage:
    poetry run python scripts/simple_upload.py
"""

import os
import time
from pathlib import Path

from dotenv import load_dotenv
load_dotenv()

from huggingface_hub import HfApi, login

# Configuration
HF_TOKEN = os.environ.get("HF_TOKEN")
REPO_ID = "Kandil7/Athar-Datasets"
COLLECTIONS_DIR = Path("data/processed/lucene_pages/collections")
UPLOAD_DIR = Path("data/processed/lucene_pages/upload_ready")
METADATA_DIR = Path("data/processed")

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

METADATA_FILES = [
    "master_catalog.json",
    "category_mapping.json",
    "author_catalog.json",
]


def format_size(size_bytes: int) -> str:
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f} TB"


def compress_file(input_path: Path, output_path: Path) -> bool:
    """Compress a single file with gzip."""
    import gzip
    import shutil
    
    if output_path.exists() and output_path.stat().st_size > 0:
        print(f"  ✓ Already exists: {output_path.name} ({format_size(output_path.stat().st_size)})")
        return True
    
    print(f"  Compressing {input_path.name}...")
    start = time.time()
    
    try:
        with open(input_path, 'rb') as f_in:
            with gzip.open(output_path, 'wb', compresslevel=6) as f_out:
                shutil.copyfileobj(f_in, f_out)
        
        elapsed = time.time() - start
        original = input_path.stat().st_size
        compressed = output_path.stat().st_size
        ratio = compressed / original
        
        print(f"  ✓ Done: {format_size(original)} → {format_size(compressed)} ({ratio:.1%}) [{elapsed:.0f}s]")
        return True
    except Exception as e:
        print(f"  ✗ Failed: {e}")
        return False


def upload_file(api: HfApi, filepath: Path, path_in_repo: str) -> bool:
    """Upload a single file."""
    if not filepath.exists():
        print(f"  ✗ Not found: {filepath}")
        return False
    
    size = filepath.stat().st_size
    print(f"  Uploading {filepath.name} ({format_size(size)})...")
    
    try:
        start = time.time()
        api.upload_file(
            path_or_fileobj=str(filepath),
            path_in_repo=path_in_repo,
            repo_id=REPO_ID,
            repo_type="dataset",
        )
        elapsed = time.time() - start
        speed = size / 1e6 / elapsed if elapsed > 0 else 0
        print(f"  ✅ Uploaded ({speed:.1f} MB/s, {elapsed:.0f}s)")
        return True
    except Exception as e:
        print(f"  ✗ Failed: {e}")
        return False


def main():
    print("=" * 70)
    print("🕌 ATHAR - UPLOAD TO HUGGING FACE")
    print("=" * 70)
    print(f"  Repository: {REPO_ID}")
    print(f"  Token: {'✅ Set' if HF_TOKEN else '❌ Not set'}")
    print("=" * 70)
    
    if not HF_TOKEN:
        print("❌ HF_TOKEN not set in .env file")
        return
    
    # Login
    login(token=HF_TOKEN)
    api = HfApi()
    
    # Create upload directory
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    
    # Compress and upload collections
    print("\n📦 COLLECTIONS:")
    for i, collection in enumerate(COLLECTIONS, 1):
        print(f"\n[{i}/{len(COLLECTIONS)}] {collection}")
        
        # Compress
        input_file = COLLECTIONS_DIR / f"{collection}.jsonl"
        output_file = UPLOAD_DIR / f"{collection}.jsonl.gz"
        
        if input_file.exists():
            compress_file(input_file, output_file)
        else:
            print(f"  ⚠️ Not found: {input_file}")
            continue
        
        # Upload
        upload_file(api, output_file, f"collections/{output_file.name}")
    
    # Upload metadata
    print("\n📁 METADATA:")
    for filename in METADATA_FILES:
        filepath = METADATA_DIR / filename
        if filepath.exists():
            upload_file(api, filepath, f"metadata/{filename}")
    
    print("\n" + "=" * 70)
    print("✅ UPLOAD COMPLETE")
    print("=" * 70)
    print(f"🔗 https://huggingface.co/datasets/{REPO_ID}")


if __name__ == "__main__":
    main()
