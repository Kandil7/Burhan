#!/usr/bin/env python3
"""
Upload Athar Collections to Hugging Face.

Based on data analysis:
- Upload: 42.6 GB collections + 8 MB metadata = 42.6 GB total
- Skip: 118.7 GB regenerable files

Usage:
    python scripts/final_upload.py --upload
    python scripts/final_upload.py --upload --compress  # Compress first (15 GB)
    python scripts/final_upload.py --verify
    python scripts/final_upload.py --summary

Prerequisites:
    pip install huggingface_hub
    huggingface-cli login
"""

import argparse
import gzip
import json
import os
import shutil
import sys
import time
from pathlib import Path

# Load .env file
from dotenv import load_dotenv
load_dotenv()

try:
    from huggingface_hub import HfApi, login
    HAS_HF = True
except ImportError:
    HAS_HF = False

# Paths
PROJECT_ROOT = Path(__file__).parent.parent
COLLECTIONS_DIR = PROJECT_ROOT / "data" / "processed" / "lucene_pages" / "collections"
UPLOAD_DIR = PROJECT_ROOT / "data" / "processed" / "lucene_pages" / "upload_ready"
METADATA_DIR = PROJECT_ROOT / "data" / "processed"

# Configuration
REPO_ID = os.environ.get("HF_REPO_ID", "Kandil7/Athar-Datasets")
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
    """Format bytes to human-readable size."""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f} PB"


def get_summary():
    """Print data summary."""
    print("=" * 70)
    print("📊 ATHAR DATA SUMMARY")
    print("=" * 70)
    
    # Collections
    total_collection_size = 0
    
    print("\n📁 Collections (UPLOAD THESE):")
    for collection in COLLECTIONS:
        filepath = COLLECTIONS_DIR / f"{collection}.jsonl"
        if filepath.exists():
            size = filepath.stat().st_size
            total_collection_size += size
            print(f"  ✓ {collection}.jsonl: {format_size(size)}")
    
    print(f"\n  Total: {format_size(total_collection_size)}")
    
    # Metadata
    total_metadata_size = 0
    print("\n📁 Metadata (UPLOAD THESE):")
    for filename in METADATA_FILES:
        filepath = METADATA_DIR / filename
        if filepath.exists():
            size = filepath.stat().st_size
            total_metadata_size += size
            print(f"  ✓ {filename}: {format_size(size)}")
    
    print(f"\n  Total: {format_size(total_metadata_size)}")
    
    # Grand total
    grand_total = total_collection_size + total_metadata_size
    print(f"\n{'=' * 70}")
    print(f"📦 TOTAL UPLOAD SIZE: {format_size(grand_total)}")
    print(f"{'=' * 70}")
    
    # Compressed estimate
    compressed_estimate = grand_total * 0.35  # 65% compression
    print(f"📦 Compressed (estimated): {format_size(compressed_estimate)}")
    print(f"💡 Space savings: 65%")


def compress_for_upload():
    """Compress collections for upload."""
    print("\n📦 COMPRESSING COLLECTIONS...")
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    
    total_original = 0
    total_compressed = 0
    
    for collection in COLLECTIONS:
        input_file = COLLECTIONS_DIR / f"{collection}.jsonl"
        output_file = UPLOAD_DIR / f"{collection}.jsonl.gz"
        
        if not input_file.exists():
            print(f"  ⚠️ {collection}.jsonl not found")
            continue
        
        print(f"  Compressing {collection}...")
        start = time.time()
        
        with open(input_file, 'rb') as f_in:
            with gzip.open(output_file, 'wb', compresslevel=6) as f_out:
                shutil.copyfileobj(f_in, f_out)
        
        original_size = input_file.stat().st_size
        compressed_size = output_file.stat().st_size
        total_original += original_size
        total_compressed += compressed_size
        
        duration = time.time() - start
        ratio = compressed_size / original_size
        
        print(f"    {format_size(original_size)} → {format_size(compressed_size)} ({ratio:.1%}) [{duration:.1f}s]")
    
    # Copy metadata
    print("\n  Copying metadata...")
    for filename in METADATA_FILES:
        src = METADATA_DIR / filename
        dst = UPLOAD_DIR / filename
        if src.exists():
            shutil.copy2(src, dst)
            print(f"    ✓ {filename}")
    
    # Summary
    print(f"\n{'=' * 70}")
    print(f"📊 COMPRESSION SUMMARY")
    print(f"{'=' * 70}")
    print(f"  Original:  {format_size(total_original)}")
    print(f"  Compressed: {format_size(total_compressed)}")
    print(f"  Savings:    {(1 - total_compressed/total_original)*100:.1f}%")
    print(f"  Output:     {UPLOAD_DIR}")


def upload_to_huggingface(compress: bool = False):
    """Upload to Hugging Face."""
    if not HAS_HF:
        print("❌ huggingface_hub not installed. Run: pip install huggingface_hub")
        sys.exit(1)
    
    # Check token
    token = os.environ.get("HF_TOKEN")
    if not token:
        print("❌ HF_TOKEN not set")
        print("   Run: huggingface-cli login")
        print("   Or: set HF_TOKEN=your_token")
        sys.exit(1)
    
    api = HfApi()
    login(token=token)
    
    # Compress if requested
    if compress:
        compress_for_upload()
        source_dir = UPLOAD_DIR
    else:
        source_dir = COLLECTIONS_DIR
    
    print(f"\n📤 UPLOADING TO HUGGING FACE")
    print(f"  Repository: {REPO_ID}")
    print(f"  Source: {source_dir}")
    print("=" * 70)
    
    # Upload collections
    for i, collection in enumerate(COLLECTIONS, 1):
        if compress:
            filepath = source_dir / f"{collection}.jsonl.gz"
        else:
            filepath = source_dir / f"{collection}.jsonl"
        
        if not filepath.exists():
            print(f"\n  ⚠️ {filepath.name} not found")
            continue
        
        size = filepath.stat().st_size
        print(f"\n[{i}/{len(COLLECTIONS)}] Uploading {filepath.name} ({format_size(size)})...")
        
        try:
            start = time.time()
            api.upload_file(
                path_or_fileobj=str(filepath),
                path_in_repo=f"collections/{filepath.name}",
                repo_id=REPO_ID,
                repo_type="dataset",
            )
            elapsed = time.time() - start
            speed = size / 1e6 / elapsed if elapsed > 0 else 0
            print(f"  ✅ Uploaded ({speed:.1f} MB/s, {elapsed:.0f}s)")
        except Exception as e:
            print(f"  ❌ Failed: {e}")
    
    # Upload metadata
    print(f"\n📤 Uploading metadata...")
    for filename in METADATA_FILES:
        filepath = source_dir / filename
        if filepath.exists():
            try:
                api.upload_file(
                    path_or_fileobj=str(filepath),
                    path_in_repo=f"metadata/{filename}",
                    repo_id=REPO_ID,
                    repo_type="dataset",
                )
                print(f"  ✅ {filename}")
            except Exception as e:
                print(f"  ❌ {filename}: {e}")
    
    print(f"\n{'=' * 70}")
    print(f"✅ UPLOAD COMPLETE")
    print(f"{'=' * 70}")
    print(f"🔗 View at: https://huggingface.co/datasets/{REPO_ID}")


def verify_upload():
    """Verify upload by listing repo files."""
    if not HAS_HF:
        print("❌ huggingface_hub not installed")
        sys.exit(1)
    
    api = HfApi()
    
    try:
        files = api.list_repo_files(repo_id=REPO_ID, repo_type="dataset")
        print(f"📋 Repository: {REPO_ID}")
        print(f"📁 Files ({len(files)}):")
        
        total_size = 0
        for f in sorted(files):
            print(f"  - {f}")
        
        print(f"\n✅ Repository exists and is accessible")
    except Exception as e:
        print(f"❌ Failed to verify: {e}")
        print("   Repository may not exist yet")


def main():
    parser = argparse.ArgumentParser(description="Upload Athar Collections to Hugging Face")
    parser.add_argument("--upload", action="store_true", help="Upload collections")
    parser.add_argument("--compress", action="store_true", help="Compress before upload")
    parser.add_argument("--verify", action="store_true", help="Verify upload")
    parser.add_argument("--summary", action="store_true", help="Show data summary")
    parser.add_argument("--repo", type=str, default=None, help="Repository ID")
    args = parser.parse_args()
    
    if args.repo:
        global REPO_ID
        REPO_ID = args.repo
    
    if not any([args.upload, args.verify, args.summary]):
        parser.print_help()
        return
    
    if args.summary:
        get_summary()
    
    if args.upload:
        upload_to_huggingface(compress=args.compress)
    
    if args.verify:
        verify_upload()


if __name__ == "__main__":
    main()
