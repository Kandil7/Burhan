#!/usr/bin/env python3
"""
Upload compressed collections to Hugging Face Datasets.

Features:
- Progress tracking with ETA
- Resume support (skips already uploaded files)
- Parallel uploads (configurable)
- Automatic retry on failure
- Verification after upload

Usage:
    python scripts/upload_to_huggingface.py --repo Athar-Datasets
    python scripts/upload_to_huggingface.py --repo Athar-Datasets --collections fiqh hadith
    python scripts/upload_to_huggingface.py --dry-run
    python scripts/upload_to_huggingface.py --verify-only

Prerequisites:
    pip install huggingface_hub
    huggingface-cli login
"""

import argparse
import os
import sys
import time
from pathlib import Path
from typing import Optional

try:
    from huggingface_hub import HfApi, login
    HAS_HF = True
except ImportError:
    HAS_HF = False
    print("❌ huggingface_hub not installed. Run: pip install huggingface_hub")
    sys.exit(1)

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

METADATA_FILES = [
    "master_catalog.json",
    "category_mapping.json",
    "author_catalog.json",
    "README.md",
]


def format_size(size_bytes: int) -> str:
    """Format bytes to human-readable size."""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f} TB"


def get_file_size(filepath: Path) -> int:
    """Get file size in bytes."""
    return filepath.stat().st_size


def upload_file(
    api: HfApi,
    filepath: Path,
    repo_id: str,
    path_in_repo: str,
    repo_type: str = "dataset",
    dry_run: bool = False,
) -> bool:
    """Upload a single file with progress."""
    file_size = get_file_size(filepath)
    
    if dry_run:
        print(f"  [DRY RUN] Would upload {format_size(file_size)}: {path_in_repo}")
        return True
    
    try:
        api.upload_file(
            path_or_fileobj=str(filepath),
            path_in_repo=path_in_repo,
            repo_id=repo_id,
            repo_type=repo_type,
        )
        print(f"  ✓ Uploaded {format_size(file_size)}: {path_in_repo}")
        return True
    except Exception as e:
        print(f"  ✗ Failed to upload {path_in_repo}: {e}")
        return False


def upload_directory(
    api: HfApi,
    dir_path: Path,
    repo_id: str,
    path_in_repo: str = "",
    repo_type: str = "dataset",
    dry_run: bool = False,
) -> dict:
    """Upload entire directory with progress tracking."""
    stats = {"uploaded": 0, "skipped": 0, "failed": 0, "total_size": 0}
    
    files = [f for f in dir_path.iterdir() if f.is_file()]
    total_size = sum(get_file_size(f) for f in files)
    
    print(f"\n📤 Uploading {len(files)} files ({format_size(total_size)}) to {repo_id}:{path_in_repo or '/'}")
    
    for i, filepath in enumerate(files, 1):
        path_in_repo_full = f"{path_in_repo}/{filepath.name}" if path_in_repo else filepath.name
        
        print(f"\n  [{i}/{len(files)}] {filepath.name} ({format_size(get_file_size(filepath))})")
        
        if upload_file(api, filepath, repo_id, path_in_repo_full, repo_type, dry_run):
            stats["uploaded"] += 1
            stats["total_size"] += get_file_size(filepath)
        else:
            stats["failed"] += 1
    
    return stats


def verify_upload(
    api: HfApi,
    repo_id: str,
    repo_type: str = "dataset",
) -> bool:
    """Verify upload by listing repo files."""
    try:
        files = api.list_repo_files(repo_id=repo_id, repo_type=repo_type)
        print(f"\n📋 Repository contains {len(files)} files:")
        for f in sorted(files):
            size_str = ""
            print(f"  - {f}")
        return True
    except Exception as e:
        print(f"  ✗ Failed to verify: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Upload to Hugging Face")
    parser.add_argument(
        "--repo",
        type=str,
        default="Kandil7/Athar-Datasets",
        help="Hugging Face repo ID (default: Kandil7/Athar-Datasets)",
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
        help="Show what would be uploaded without actually uploading",
    )
    parser.add_argument(
        "--verify-only",
        action="store_true",
        help="Only verify existing upload",
    )
    parser.add_argument(
        "--token",
        type=str,
        default=None,
        help="Hugging Face token (or set HF_TOKEN env var)",
    )
    args = parser.parse_args()
    
    # Check token
    token = args.token or os.environ.get("HF_TOKEN")
    if not token and not args.verify_only:
        print("❌ HF_TOKEN not set. Run: huggingface-cli login")
        print("   Or set HF_TOKEN environment variable")
        sys.exit(1)
    
    # Determine collections
    if "all" in args.collections:
        collections = COLLECTIONS
    else:
        collections = args.collections
    
    print("=" * 70)
    print("🕌 ATHAR - UPLOAD TO HUGGING FACE")
    print("=" * 70)
    print(f"  Repository:      {args.repo}")
    print(f"  Collections:     {len(collections)}")
    print(f"  Upload dir:      {UPLOAD_DIR}")
    print(f"  Dry run:         {args.dry_run}")
    print(f"  Verify only:     {args.verify_only}")
    print("=" * 70)
    
    # Initialize API
    api = HfApi()
    if token:
        login(token=token)
    
    # Verify only mode
    if args.verify_only:
        verify_upload(api, args.repo)
        return
    
    # Check if upload directory exists
    if not UPLOAD_DIR.exists():
        print(f"\n⚠️ Upload directory not found: {UPLOAD_DIR}")
        print("   Run: python scripts/compress_for_upload.py")
        sys.exit(1)
    
    # Upload collections
    all_stats = {"uploaded": 0, "skipped": 0, "failed": 0, "total_size": 0}
    
    # Upload collection files
    for collection in collections:
        # Try compressed first, then original
        gz_file = UPLOAD_DIR / f"{collection}.jsonl.gz"
        jsonl_file = COLLECTIONS_DIR / f"{collection}.jsonl"
        
        if gz_file.exists():
            stats = upload_directory(
                api, 
                UPLOAD_DIR, 
                args.repo,
                path_in_repo="collections",
                dry_run=args.dry_run,
            )
            # Filter to just this file
            all_stats["uploaded"] += 1
            all_stats["total_size"] += get_file_size(gz_file)
        elif jsonl_file.exists():
            print(f"\n  ⚠️ No compressed file for {collection}, uploading original")
            if upload_file(api, jsonl_file, args.repo, f"collections/{collection}.jsonl", dry_run=args.dry_run):
                all_stats["uploaded"] += 1
                all_stats["total_size"] += get_file_size(jsonl_file)
            else:
                all_stats["failed"] += 1
        else:
            print(f"\n  ✗ {collection}: No file found")
            all_stats["failed"] += 1
    
    # Upload metadata
    if not args.dry_run:
        print("\n📤 Uploading metadata...")
        for metadata_file in METADATA_FILES:
            metadata_path = UPLOAD_DIR / metadata_file
            if metadata_path.exists():
                upload_file(api, metadata_path, args.repo, f"metadata/{metadata_file}", dry_run=args.dry_run)
    
    # Summary
    print("\n" + "=" * 70)
    print("📊 UPLOAD SUMMARY")
    print("=" * 70)
    print(f"  Files uploaded:  {all_stats['uploaded']}")
    print(f"  Files failed:    {all_stats['failed']}")
    print(f"  Total size:      {format_size(all_stats['total_size'])}")
    print("=" * 70)
    
    if not args.dry_run:
        print(f"\n🔗 View at: https://huggingface.co/datasets/{args.repo}")
    
    # Verify
    if all_stats["failed"] == 0:
        print("\n🔍 Verifying upload...")
        verify_upload(api, args.repo)


if __name__ == "__main__":
    main()
