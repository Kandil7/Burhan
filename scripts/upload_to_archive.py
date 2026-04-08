#!/usr/bin/env python3
"""
Upload collections to Archive.org (Internet Archive).

Archive.org offers FREE unlimited storage, perfect for disaster recovery.

Usage:
    python scripts/upload_to_archive.py
    python scripts/upload_to_archive.py --dry-run

Prerequisites:
    pip install internetarchive
    ia configure  # Set up credentials
"""

import argparse
import os
import subprocess
import sys
import time
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

UPLOAD_DIR = project_root / "data" / "processed" / "lucene_pages" / "upload_ready"
COLLECTIONS_DIR = project_root / "data" / "processed" / "lucene_pages" / "collections"

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

ARCHIVE_ID = "athar-islamic-collections-2026"


def format_size(size_bytes: int) -> str:
    """Format bytes to human-readable size."""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f} TB"


def upload_to_archive(dry_run: bool = False):
    """Upload files to Archive.org."""
    try:
        import internetarchive
    except ImportError:
        print("❌ internetarchive not installed. Run: pip install internetarchive")
        sys.exit(1)
    
    # Check if collection directory exists
    if not COLLECTIONS_DIR.exists():
        print(f"❌ Collection directory not found: {COLLECTIONS_DIR}")
        print("   Run: python scripts/compress_for_upload.py")
        sys.exit(1)
    
    # Collect files to upload
    files_to_upload = []
    total_size = 0
    
    for collection in COLLECTIONS:
        # Try compressed first
        gz_file = UPLOAD_DIR / f"{collection}.jsonl.gz"
        jsonl_file = COLLECTIONS_DIR / f"{collection}.jsonl"
        
        if gz_file.exists():
            files_to_upload.append(gz_file)
            total_size += gz_file.stat().st_size
        elif jsonl_file.exists():
            files_to_upload.append(jsonl_file)
            total_size += jsonl_file.stat().st_size
    
    # Add metadata files
    metadata_files = [
        "master_catalog.json",
        "category_mapping.json",
        "author_catalog.json",
        "README.md",
    ]
    
    for filename in metadata_files:
        filepath = UPLOAD_DIR / filename
        if filepath.exists():
            files_to_upload.append(filepath)
            total_size += filepath.stat().st_size
    
    print(f"\n📤 Files to upload: {len(files_to_upload)}")
    print(f"📊 Total size: {format_size(total_size)}")
    
    if dry_run:
        print("\n[DRY RUN] Files that would be uploaded:")
        for f in files_to_upload:
            print(f"  - {f.name} ({format_size(f.stat().st_size)})")
        return
    
    # Upload using ia CLI
    print(f"\n📤 Uploading to Archive.org (ID: {ARCHIVE_ID})...")
    print(f"   This may take several hours")
    
    try:
        # Build command
        cmd = ["ia", "upload", ARCHIVE_ID]
        
        for filepath in files_to_upload:
            cmd.append(str(filepath))
        
        # Add metadata
        cmd.extend(["--metadata", f"title:Athar Islamic Collections 2026"])
        cmd.extend(["--metadata", f"creator:Kandil7"])
        cmd.extend(["--metadata", f"description:Production-ready Islamic knowledge datasets from Shamela Library"])
        cmd.extend(["--metadata", f"date:2026-04"])
        cmd.extend(["--metadata", f"language:ara"])
        cmd.extend(["--metadata", f"subject:Islamic studies; Quran; Hadith; Fiqh; Arabic literature"])
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=86400,  # 24 hours timeout
        )
        
        if result.returncode == 0:
            print(f"\n✅ Upload successful!")
            print(f"   View at: https://archive.org/details/{ARCHIVE_ID}")
        else:
            print(f"\n❌ Upload failed:")
            print(result.stderr)
    except subprocess.TimeoutExpired:
        print(f"\n⏱️ Upload timed out (24 hours). Try again with faster connection.")
    except Exception as e:
        print(f"\n❌ Upload failed: {e}")


def main():
    parser = argparse.ArgumentParser(description="Upload to Archive.org")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be uploaded",
    )
    parser.add_argument(
        "--archive-id",
        type=str,
        default=ARCHIVE_ID,
        help="Archive.org identifier (default: athar-islamic-collections-2026)",
    )
    args = parser.parse_args()
    
    global ARCHIVE_ID
    ARCHIVE_ID = args.archive_id
    
    print("=" * 70)
    print("🕌 ATHAR - UPLOAD TO ARCHIVE.ORG")
    print("=" * 70)
    print(f"  Archive ID:      {ARCHIVE_ID}")
    print(f"  Dry run:         {args.dry_run}")
    print("=" * 70)
    
    upload_to_archive(args.dry_run)


if __name__ == "__main__":
    main()
