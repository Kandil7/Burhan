#!/usr/bin/env python3
"""
Complete HuggingFace Upload with Resume Capability.

Uploads 10 collections from Kandil7/Athar-Datasets with:
- One collection at a time (avoids memory issues)
- Resume capability (skips already uploaded)
- Progress tracking
- Compression with gzip
- Verification after each upload

Usage:
    poetry run python scripts/upload_to_huggingface_complete.py
    poetry run python scripts/upload_to_huggingface_complete.py --collection hadith_passages
    poetry run python scripts/upload_to_huggingface_complete.py --verify
    poetry run python scripts/upload_to_huggingface_complete.py --resume
"""

import argparse
import gzip
import json
import os
import sys
import time
from pathlib import Path
from datetime import datetime

# Load .env
from dotenv import load_dotenv
load_dotenv()

try:
    from huggingface_hub import HfApi, login, HfFileSystem
    HAS_HF = True
except ImportError:
    print("❌ huggingface_hub not installed")
    print("   Install: poetry add huggingface_hub")
    sys.exit(1)

# Configuration
PROJECT_ROOT = Path(__file__).parent.parent
COLLECTIONS_DIR = PROJECT_ROOT / "data" / "processed" / "lucene_pages" / "collections"
UPLOAD_DIR = PROJECT_ROOT / "data" / "processed" / "lucene_pages" / "upload_ready"
PROGRESS_FILE = PROJECT_ROOT / "data" / "processed" / "upload_progress.json"

REPO_ID = os.environ.get("HF_REPO_ID", "Kandil7/Athar-Datasets")
HF_TOKEN = os.environ.get("HF_TOKEN")

COLLECTIONS = [
    "seerah_passages",           # 0.8 GB (smallest first)
    "usul_fiqh",                 # 0.9 GB
    "spirituality_passages",     # 1.1 GB
    "aqeedah_passages",          # 1.8 GB
    "arabic_language_passages",  # 2.3 GB
    "quran_tafsir",              # 5.2 GB
    "islamic_history_passages",  # 6.0 GB
    "general_islamic",           # 6.5 GB
    "fiqh_passages",             # 7.0 GB
    "hadith_passages",           # 11.0 GB (largest last)
]

METADATA_FILES = [
    "master_catalog.json",
    "category_mapping.json",
    "author_catalog.json",
]


def format_size(size_bytes: int) -> str:
    """Format bytes to human-readable size."""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} PB"


def load_progress() -> dict:
    """Load upload progress from file."""
    if PROGRESS_FILE.exists():
        try:
            with open(PROGRESS_FILE, 'r') as f:
                return json.load(f)
        except:
            return {"uploaded": [], "metadata_uploaded": False, "started_at": None}
    return {"uploaded": [], "metadata_uploaded": False, "started_at": None}


def save_progress(progress: dict):
    """Save progress to file."""
    PROGRESS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(PROGRESS_FILE, 'w') as f:
        json.dump(progress, f, indent=2)


def get_uploaded_files(api: HfApi) -> list:
    """Get list of files already in repo."""
    try:
        return api.list_repo_files(repo_id=REPO_ID, repo_type="dataset")
    except Exception as e:
        print(f"⚠️  Could not list repo files: {e}")
        return []


def compress_collection(filepath: Path, output_dir: Path) -> Path:
    """Compress a single collection file."""
    output_file = output_dir / f"{filepath.stem}.jsonl.gz"

    if output_file.exists():
        return output_file

    print(f"  📦 Compressing {filepath.name}...")
    start = time.time()

    with open(filepath, 'rb') as f_in:
        with gzip.open(output_file, 'wb', compresslevel=6) as f_out:
            import shutil
            shutil.copyfileobj(f_in, f_out)

    original_size = filepath.stat().st_size
    compressed_size = output_file.stat().st_size
    elapsed = time.time() - start
    ratio = compressed_size / original_size

    print(f"    {format_size(original_size)} → {format_size(compressed_size)} ({ratio:.1%}) [{elapsed:.1f}s]")

    return output_file


def upload_file_with_retry(api: HfApi, filepath: Path, repo_path: str, max_retries: int = 3):
    """Upload file with retry logic."""
    size = filepath.stat().st_size

    for attempt in range(1, max_retries + 1):
        try:
            print(f"  📤 Uploading {filepath.name} ({format_size(size)})... [Attempt {attempt}]")
            start = time.time()

            api.upload_file(
                path_or_fileobj=str(filepath),
                path_in_repo=repo_path,
                repo_id=REPO_ID,
                repo_type="dataset",
            )

            elapsed = time.time() - start
            speed = size / 1e6 / elapsed if elapsed > 0 else 0
            print(f"  ✅ Uploaded ({speed:.1f} MB/s, {elapsed:.0f}s)")
            return True

        except Exception as e:
            print(f"  ❌ Attempt {attempt} failed: {e}")
            if attempt < max_retries:
                wait_time = 2 ** attempt  # Exponential backoff
                print(f"  ⏳ Waiting {wait_time}s before retry...")
                time.sleep(wait_time)
            else:
                print(f"  ❌ Failed after {max_retries} attempts")
                return False

    return False


def upload_all(api: HfApi, compress: bool = False, resume: bool = False, single_collection: str = None):
    """Upload all collections with resume capability."""

    # Load progress
    progress = load_progress()
    if progress["started_at"] is None:
        progress["started_at"] = datetime.now().isoformat()
        save_progress(progress)

    uploaded = set(progress["uploaded"])

    # Get files already in repo
    existing_files = get_uploaded_files(api)
    existing_files_set = set(existing_files)

    # Determine which collections to upload
    if single_collection:
        if single_collection not in COLLECTIONS:
            print(f"❌ Unknown collection: {single_collection}")
            print(f"Available: {', '.join(COLLECTIONS)}")
            sys.exit(1)
        collections_to_upload = [single_collection]
        print(f"📚 Single collection mode: {single_collection}")
    elif resume:
        # Skip already uploaded
        collections_to_upload = [c for c in COLLECTIONS if c not in uploaded]
        print(f"🔄 Resume mode: {len(collections_to_upload)} collections remaining")
    else:
        collections_to_upload = COLLECTIONS
        print(f"📤 Fresh upload: {len(collections_to_upload)} collections")

    if not collections_to_upload:
        print("✅ All collections already uploaded!")
        return

    # Create upload directory
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

    print(f"\n{'='*70}")
    print(f"📤 UPLOADING TO HUGGING FACE")
    print(f"  Repository: {REPO_ID}")
    print(f"  Collections: {len(collections_to_upload)}")
    print(f"  Compress: {compress}")
    print(f"  Resume: {resume}")
    print(f"{'='*70}")

    total_start = time.time()
    total_uploaded = 0
    total_size = 0

    for i, collection in enumerate(collections_to_upload, 1):
        print(f"\n{'='*70}")
        print(f"[{i}/{len(collections_to_upload)}] {collection}")
        print(f"{'='*70}")

        coll_start = time.time()

        # Find source file
        source_file = COLLECTIONS_DIR / f"{collection}.jsonl"
        if not source_file.exists():
            print(f"  ⚠️  Source file not found: {source_file}")
            continue

        # Compress if requested
        if compress:
            upload_file = compress_collection(source_file, UPLOAD_DIR)
        else:
            # Check if compressed version exists
            compressed = UPLOAD_DIR / f"{collection}.jsonl.gz"
            if compressed.exists():
                upload_file = compressed
            else:
                # Compress on the fly
                upload_file = compress_collection(source_file, UPLOAD_DIR)

        # Check if already uploaded
        repo_path = f"collections/{upload_file.name}"
        if repo_path in existing_files_set:
            print(f"  ✅ Already uploaded: {upload_file.name}")
            if collection not in uploaded:
                uploaded.add(collection)
                progress["uploaded"] = list(uploaded)
                save_progress(progress)
            continue

        # Upload
        success = upload_file_with_retry(api, upload_file, repo_path)

        if success:
            uploaded.add(collection)
            progress["uploaded"] = list(uploaded)
            save_progress(progress)
            total_uploaded += 1
            total_size += upload_file.stat().st_size

        elapsed = time.time() - coll_start
        print(f"  ⏱️  Time: {elapsed/60:.1f} minutes")

    # Upload metadata
    print(f"\n{'='*70}")
    print(f"📤 UPLOADING METADATA")
    print(f"{'='*70}")

    for filename in METADATA_FILES:
        filepath = PROJECT_ROOT / "data" / "processed" / filename
        if filepath.exists():
            repo_path = f"metadata/{filename}"
            if repo_path not in existing_files_set:
                upload_file_with_retry(api, filepath, repo_path)
            else:
                print(f"  ✅ Already uploaded: {filename}")

    progress["metadata_uploaded"] = True
    progress["completed_at"] = datetime.now().isoformat()
    save_progress(progress)

    # Final summary
    total_elapsed = time.time() - total_start
    print(f"\n{'='*70}")
    print(f"✅ UPLOAD SESSION COMPLETE")
    print(f"{'='*70}")
    print(f"  Collections uploaded this session: {total_uploaded}")
    print(f"  Total data uploaded: {format_size(total_size)}")
    print(f"  Total time: {total_elapsed/60:.1f} minutes")
    print(f"  Average speed: {total_size / 1e6 / max(total_elapsed, 1):.1f} MB/s")
    print(f"\n🔗 View at: https://huggingface.co/datasets/{REPO_ID}")


def verify_upload():
    """Verify all files are uploaded."""
    if not HF_TOKEN:
        print("❌ HF_TOKEN not set")
        sys.exit(1)

    api = HfApi()
    login(token=HF_TOKEN)

    try:
        files = api.list_repo_files(repo_id=REPO_ID, repo_type="dataset")
        files_set = set(files)

        print(f"📋 Repository: {REPO_ID}")
        print(f"📁 Total files: {len(files)}")
        print()

        # Check collections
        print("📚 Collections:")
        for collection in COLLECTIONS:
            # Check both compressed and uncompressed
            compressed = f"collections/{collection}.jsonl.gz"
            uncompressed = f"collections/{collection}.jsonl"

            if compressed in files_set:
                print(f"  ✅ {collection} (compressed)")
            elif uncompressed in files_set:
                print(f"  ✅ {collection} (uncompressed)")
            else:
                print(f"  ❌ {collection} - NOT UPLOADED")

        # Check metadata
        print("\n📁 Metadata:")
        for filename in METADATA_FILES:
            repo_path = f"metadata/{filename}"
            if repo_path in files_set:
                print(f"  ✅ {filename}")
            else:
                print(f"  ❌ {filename} - NOT UPLOADED")

        # Summary
        uploaded_collections = sum(1 for c in COLLECTIONS
                                  if f"collections/{c}.jsonl.gz" in files_set
                                  or f"collections/{c}.jsonl" in files_set)
        uploaded_metadata = sum(1 for f in METADATA_FILES
                               if f"metadata/{f}" in files_set)

        print(f"\n{'='*70}")
        print(f"📊 SUMMARY")
        print(f"{'='*70}")
        print(f"  Collections: {uploaded_collections}/{len(COLLECTIONS)}")
        print(f"  Metadata: {uploaded_metadata}/{len(METADATA_FILES)}")
        print(f"  Status: {'✅ COMPLETE' if uploaded_collections == len(COLLECTIONS) else '⏳ INCOMPLETE'}")

    except Exception as e:
        print(f"❌ Failed to verify: {e}")
        print("   Repository may not exist or token is invalid")


def main():
    parser = argparse.ArgumentParser(description="Upload Athar Collections to HuggingFace")
    parser.add_argument("--upload", action="store_true", help="Upload collections")
    parser.add_argument("--compress", action="store_true", help="Compress before upload")
    parser.add_argument("--resume", action="store_true", help="Resume from last position")
    parser.add_argument("--verify", action="store_true", help="Verify upload")
    parser.add_argument("--collection", type=str, help="Upload single collection")
    parser.add_argument("--progress", action="store_true", help="Show upload progress")

    args = parser.parse_args()

    if not any([args.upload, args.verify, args.progress]):
        print("Usage:")
        print("  python scripts/upload_to_huggingface_complete.py --upload --compress --resume")
        print("  python scripts/upload_to_huggingface_complete.py --verify")
        print("  python scripts/upload_to_huggingface_complete.py --collection hadith_passages")
        print("  python scripts/upload_to_huggingface_complete.py --progress")
        return

    # Check token
    if not HF_TOKEN:
        print("❌ HF_TOKEN not set in .env")
        print("   Add to .env: HF_TOKEN=hf_your_token_here")
        sys.exit(1)

    if args.progress:
        progress = load_progress()
        print(f"📊 Upload Progress:")
        print(f"  Started: {progress.get('started_at', 'Never')}")
        print(f"  Completed: {progress.get('completed_at', 'Not yet')}")
        print(f"  Uploaded: {len(progress.get('uploaded', []))}/{len(COLLECTIONS)}")
        print(f"  Collections: {', '.join(progress.get('uploaded', []))}")
        print(f"  Metadata: {'✅' if progress.get('metadata_uploaded') else '❌'}")
        return

    if args.verify:
        verify_upload()
        return

    if args.upload:
        api = HfApi()
        login(token=HF_TOKEN)

        upload_all(
            api,
            compress=args.compress,
            resume=args.resume,
            single_collection=args.collection
        )


if __name__ == "__main__":
    main()
