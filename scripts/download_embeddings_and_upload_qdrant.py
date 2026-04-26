#!/usr/bin/env python3
"""
Download embeddings from HuggingFace and upload to Qdrant.

This script intelligently handles incremental updates:
1. Checks current Qdrant collection counts
2. Gets expected counts from HuggingFace
3. Only downloads/uploads what's missing
4. Supports resume and incremental updates

Usage:
    poetry run python scripts/download_embeddings_and_upload_qdrant.py
    poetry run python scripts/download_embeddings_and_upload_qdrant.py --collections hadith_passages
    poetry run python scripts/download_embeddings_and_upload_qdrant.py --verify-only
    poetry run python scripts/download_embeddings_and_upload_qdrant.py --dry-run
    poetry run python scripts/download_embeddings_and_upload_qdrant.py --force-reupload
"""

import os
import sys
import json
import gzip
import time
import argparse
import numpy as np
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, List, Tuple

# Fix Windows console encoding for emojis
if sys.platform == "win32":
    import io

    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

from dotenv import load_dotenv

load_dotenv()

# HuggingFace
try:
    from huggingface_hub import hf_hub_download, HfApi, login

    HAS_HF = True
except ImportError:
    print("❌ huggingface_hub not installed")
    print("   Install: poetry add huggingface_hub")
    sys.exit(1)

# Qdrant
try:
    from qdrant_client import QdrantClient
    from qdrant_client.models import Distance, VectorParams, PointStruct

    HAS_QDRANT = True
except ImportError:
    print("❌ qdrant-client not installed")
    print("   Install: poetry add qdrant-client")
    sys.exit(1)

# Configuration
HF_REPO = "Kandil7/Burhan-Embeddings"
HF_TOKEN = os.environ.get("HF_TOKEN")

QDRANT_URL = os.environ.get("QDRANT_URL", "http://localhost:6333")
QDRANT_API_KEY = os.environ.get("QDRANT_API_KEY")

COLLECTIONS = [
    "seerah_passages",
    "usul_fiqh",
    "spirituality_passages",
    "aqeedah_passages",
    "arabic_language_passages",
    "quran_tafsir",
    "islamic_history_passages",
    "general_islamic",
    "fiqh_passages",
    "hadith_passages",
    "duas_adhkar",
]

DOWNLOAD_DIR = Path("data/processed/hf_embeddings")
QDRANT_BATCH_SIZE = 500  # Points per upload batch


def format_size(size_bytes: int) -> str:
    """Format bytes to human-readable size."""
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} PB"


def get_qdrant_counts() -> Dict[str, int]:
    """Get current point counts from all Qdrant collections."""
    print("📊 Checking Qdrant collections...")
    client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY, timeout=30)

    counts = {}
    try:
        collections = client.get_collections()
        for coll in collections.collections:
            info = client.get_collection(coll.name)
            counts[coll.name] = info.points_count or 0
    except Exception as e:
        print(f"  ⚠️  Error getting Qdrant info: {e}")

    return counts


def get_hf_counts() -> Dict[str, int]:
    """Get expected point counts from HuggingFace metadata files."""
    print("📡 Checking HuggingFace for expected counts...")
    api = HfApi()

    counts = {}
    for coll in COLLECTIONS:
        try:
            all_files = api.list_repo_files(repo_id=HF_REPO, repo_type="dataset")
            coll_files = [f for f in all_files if f.startswith(f"{coll}/")]
            meta_files = [f for f in coll_files if "_meta_" in f and f.endswith(".jsonl.gz")]

            if not meta_files:
                print(f"  ⚠️  No metadata files for {coll}")
                counts[coll] = 0
                continue

            # Only download first metadata file to get count estimate
            meta_file = meta_files[0]
            filepath = hf_hub_download(
                repo_id=HF_REPO,
                filename=meta_file,
                repo_type="dataset",
                local_dir=str(DOWNLOAD_DIR / coll),
                force_download=False,
            )

            with gzip.open(filepath, "rt", encoding="utf-8") as f:
                count = sum(1 for line in f if line.strip())

            counts[coll] = count
            print(f"  ✅ {coll}: {count:,} expected")
        except Exception as e:
            print(f"  ⚠️  Error for {coll}: {e}")
            counts[coll] = 0

    return counts


def analyze_sync_status(qdrant_counts: Dict[str, int], hf_counts: Dict[str, int]) -> Dict[str, dict]:
    """Analyze which collections need updating."""
    status = {}

    for coll in COLLECTIONS:
        qdrant_count = qdrant_counts.get(coll, 0)
        hf_count = hf_counts.get(coll, 0)

        if hf_count == 0:
            status[coll] = {"action": "skip", "reason": "No data on HuggingFace", "qdrant": qdrant_count, "hf": 0}
        elif qdrant_count == 0:
            status[coll] = {"action": "upload", "reason": "Missing in Qdrant", "qdrant": 0, "hf": hf_count}
        elif qdrant_count >= hf_count:
            status[coll] = {
                "action": "skip",
                "reason": f"Already synced ({qdrant_count:,} >= {hf_count:,})",
                "qdrant": qdrant_count,
                "hf": hf_count,
            }
        else:
            status[coll] = {
                "action": "update",
                "reason": f"Need {hf_count - qdrant_count:,} more points",
                "qdrant": qdrant_count,
                "hf": hf_count,
            }

    return status


def print_sync_plan(status: Dict[str, dict]):
    """Print the synchronization plan."""
    print("\n" + "═" * 80)
    print("📋  SYNC PLAN")
    print("═" * 80)

    upload_count = sum(1 for s in status.values() if s["action"] == "upload")
    update_count = sum(1 for s in status.values() if s["action"] == "update")
    skip_count = sum(1 for s in status.values() if s["action"] == "skip")

    for coll, s in status.items():
        if s["action"] == "upload":
            print(f"  🔼 {coll:<35} Upload {s['hf']:,} points  │ {s['reason']}")
        elif s["action"] == "update":
            print(f"  🔄 {coll:<35} Update +{s['hf'] - s['qdrant']:,}  │ {s['reason']}")
        else:
            print(f"  ⏭️  {coll:<35} Skipped       │ {s['reason']}")

    print("─" * 80)
    print(f"  📤 Will upload: {upload_count} collections")
    print(f"  🔄 Will update: {update_count} collections")
    print(f"  ⏭️  Will skip:  {skip_count} collections")
    print("═" * 80)


def download_embeddings_for_collection(collection_name: str, skip_existing: bool = True) -> Optional[tuple]:
    """
    Download all embedding chunks and metadata for a collection from HuggingFace.
    Returns: (embeddings_array, passages_list)
    """
    print(f"\n{'=' * 70}")
    print(f"📥 Downloading: {collection_name}")
    print(f"{'=' * 70}")

    DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)
    coll_dir = DOWNLOAD_DIR / collection_name
    coll_dir.mkdir(exist_ok=True)

    # List files in collection directory on HF
    api = HfApi()
    all_files = api.list_repo_files(repo_id=HF_REPO, repo_type="dataset")
    coll_files = [f for f in all_files if f.startswith(f"{collection_name}/")]

    emb_files = sorted([f for f in coll_files if "_emb_" in f and f.endswith(".npy")])
    meta_files = sorted([f for f in coll_files if "_meta_" in f and f.endswith(".jsonl.gz")])

    print(f"  Found {len(emb_files)} embedding files")
    print(f"  Found {len(meta_files)} metadata files")

    # Check for cached local files
    cached_emb = list(coll_dir.glob("*_emb_*.npy"))
    if skip_existing and cached_emb:
        print(f"  💾 Found {len(cached_emb)} cached embedding files, using cache")
        all_embeddings = []
        for f in cached_emb:
            emb = np.load(f)
            all_embeddings.append(emb)
        embeddings_array = np.concatenate(all_embeddings, axis=0) if all_embeddings else None
    else:
        # Download and concatenate all embedding chunks
        all_embeddings = []
        for i, emb_file in enumerate(emb_files, 1):
            filepath = hf_hub_download(
                repo_id=HF_REPO,
                filename=emb_file,
                repo_type="dataset",
                local_dir=str(DOWNLOAD_DIR),
                force_download=False,
            )

            embeddings = np.load(filepath)
            all_embeddings.append(embeddings)

            if i % 10 == 0 or i == len(emb_files):
                print(f"    Downloaded {i}/{len(emb_files)} embedding files")

        # Concatenate all embedding chunks
        if all_embeddings:
            embeddings_array = np.concatenate(all_embeddings, axis=0)
        else:
            print(f"  ⚠️  No embeddings found for {collection_name}")
            return None

    print(f"  ✅ Embeddings shape: {embeddings_array.shape}")

    # Download metadata (always download as it's smaller)
    passages = []
    for i, meta_file in enumerate(meta_files, 1):
        filepath = hf_hub_download(
            repo_id=HF_REPO, filename=meta_file, repo_type="dataset", local_dir=str(DOWNLOAD_DIR), force_download=False
        )

        with gzip.open(filepath, "rt", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        passages.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue

        if i % 10 == 0 or i == len(meta_files):
            print(f"    Downloaded {i}/{len(meta_files)} metadata files ({len(passages):,} passages)")

    print(f"  ✅ Total passages: {len(passages):,}")

    # Sanity check
    if len(embeddings_array) != len(passages):
        print(f"  ⚠️  MISMATCH: {len(embeddings_array)} embeddings vs {len(passages)} passages")
        print(f"  Using minimum count: {min(len(embeddings_array), len(passages))}")
        min_count = min(len(embeddings_array), len(passages))
        embeddings_array = embeddings_array[:min_count]
        passages = passages[:min_count]

    return embeddings_array, passages


def upload_to_qdrant(
    collection_name: str,
    embeddings: np.ndarray,
    passages: list,
    batch_size: int = QDRANT_BATCH_SIZE,
    force: bool = False,
) -> dict:
    """Upload embeddings and passages to Qdrant."""
    print(f"\n{'=' * 70}")
    print(f"📤 Uploading to Qdrant: {collection_name}")
    print(f"{'=' * 70}")

    # Connect to Qdrant
    print(f"  Connecting to Qdrant: {QDRANT_URL}")
    client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY, timeout=120)

    # Create collection if not exists
    vector_size = embeddings.shape[1]
    existing_count = 0

    if client.collection_exists(collection_name):
        info = client.get_collection(collection_name)
        existing_count = info.points_count or 0
        print(f"  ℹ️  Collection exists ({existing_count:,} existing points)")

        if not force and existing_count > 0:
            print(f"  🔄 Appending {len(passages)} new points...")
            # Use offset to continue from existing
            start_id = existing_count
        else:
            print(f"  🗑️  Recreating collection (force mode)...")
            client.delete_collection(collection_name)
            client.create_collection(
                collection_name=collection_name, vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE)
            )
            start_id = 0
    else:
        print(f"  Creating collection: {collection_name} (dim={vector_size})")
        client.create_collection(
            collection_name=collection_name, vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE)
        )
        start_id = 0

    # Upload in batches
    total_points = len(passages)
    t0 = time.time()
    uploaded = 0

    for start in range(0, total_points, batch_size):
        end = min(start + batch_size, total_points)
        batch_emb = embeddings[start:end]
        batch_pas = passages[start:end]

        points = []
        for idx, pas in enumerate(batch_pas):
            payload = {
                "content": pas.get("content", ""),
                "book_id": pas.get("book_id"),
                "title": pas.get("title", ""),
                "author": pas.get("author", ""),
                "author_death": pas.get("author_death"),
                "page": pas.get("page"),
                "chapter": pas.get("chapter", ""),
                "section": pas.get("section", ""),
                "category": pas.get("category", ""),
                "collection": collection_name,
                "content_type": pas.get("content_type"),
                "book_title": pas.get("book_title"),
                "page_number": pas.get("page_number"),
                "section_title": pas.get("section_title"),
            }

            points.append(PointStruct(id=start_id + start + idx, vector=batch_emb[idx].tolist(), payload=payload))

        client.upsert(collection_name=collection_name, points=points)

        uploaded += len(points)
        if uploaded % 5000 == 0 or uploaded == total_points:
            elapsed = time.time() - t0
            speed = uploaded / elapsed
            print(f"    Uploaded {uploaded:,}/{total_points:,} points ({elapsed:.1f}s, {speed:.0f} pts/sec)")

    elapsed = time.time() - t0
    print(f"\n  ✅ Uploaded {uploaded:,} points in {elapsed:.1f}s ({uploaded / elapsed:.0f} pts/sec)")

    return {"collection": collection_name, "points": uploaded, "existing": existing_count, "elapsed": elapsed}


def verify_qdrant(collections: list) -> dict:
    """Verify all collections in Qdrant."""
    print(f"\n{'=' * 70}")
    print(f"📊 Qdrant Collections Verification")
    print(f"{'=' * 70}")

    client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY, timeout=30)

    total_vectors = 0
    results = {}

    for coll in collections:
        try:
            info = client.get_collection(coll)
            count = info.points_count or 0
            total_vectors += count
            results[coll] = {"count": count, "status": str(info.status)}
            print(f"  ✅ {coll:<40} {count:>10,} vectors  │  {info.status}")
        except Exception as e:
            results[coll] = {"count": 0, "status": f"ERROR: {e}"}
            print(f"  ❌ {coll:<40} ERROR: {e}")

    print(f"{'─' * 70}")
    print(f"  {'TOTAL':<40} {total_vectors:>10,} vectors")
    print(f"{'=' * 70}")

    return {"total_vectors": total_vectors, "collections": results}


def main():
    parser = argparse.ArgumentParser(description="Download embeddings from HF and upload to Qdrant")
    parser.add_argument("--collections", nargs="+", default=None, help="Specific collections to process (default: all)")
    parser.add_argument("--verify-only", action="store_true", help="Only verify Qdrant collections, no download/upload")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be done without actually doing it")
    parser.add_argument("--batch-size", type=int, default=QDRANT_BATCH_SIZE, help="Qdrant upload batch size")
    parser.add_argument("--force", action="store_true", help="Force reupload even if collection exists")
    parser.add_argument(
        "--skip-cached", action="store_true", default=True, help="Skip downloading if files are cached locally"
    )

    args = parser.parse_args()

    # Use provided batch size or default
    batch_size = args.batch_size

    # Verify HF token
    if not HF_TOKEN:
        print("❌ HF_TOKEN not set in .env")
        print("   Add your HuggingFace token to .env file")
        sys.exit(1)

    # Login to HuggingFace
    print("🔐 Logging in to HuggingFace...")
    login(token=HF_TOKEN)
    print("✅ Logged in")

    # Select collections
    collections = args.collections if args.collections else COLLECTIONS

    # Verify-only mode
    if args.verify_only:
        verify_qdrant(collections)
        return

    # Get Qdrant and HF counts
    qdrant_counts = get_qdrant_counts()
    hf_counts = get_hf_counts()

    # Analyze sync status
    status = analyze_sync_status(qdrant_counts, hf_counts)

    # Print plan
    print_sync_plan(status)

    # Dry-run mode - just show plan
    if args.dry_run:
        print("\n🛑 Dry run complete - no changes made")
        return

    # Ask for confirmation if there are uploads/updates
    upload_count = sum(1 for s in status.values() if s["action"] in ["upload", "update"])
    if upload_count > 0:
        confirm = input(f"\nProceed with {upload_count} collections? [Y/n]: ")
        if confirm.lower() not in ["", "y", "Y"]:
            print("❌ Aborted")
            return

    print("\n" + "═" * 70)
    print("🕌  Burhan - Download Embeddings & Upload to Qdrant (Smart Sync)")
    print("═" * 70)
    print(f"  HF Repo: {HF_REPO}")
    print(f"  Qdrant: {QDRANT_URL}")
    print(f"  Batch size: {batch_size}")
    print("═" * 70)

    total_start = time.time()
    results = []

    for coll in collections:
        coll_status = status.get(coll, {"action": "skip"})

        if coll_status["action"] == "skip":
            print(f"\n⏭️  Skipping {coll} ({coll_status['reason']})")
            continue

        coll_start = time.time()

        # Download
        data = download_embeddings_for_collection(coll, skip_existing=args.skip_cached)

        if data is None:
            print(f"  ⚠️  No data for {coll}, skipping")
            continue

        embeddings, passages = data
        download_time = time.time() - coll_start
        print(f"  ⏱️  Download time: {download_time:.1f}s")

        # Upload to Qdrant
        upload_start = time.time()
        result = upload_to_qdrant(coll, embeddings, passages, batch_size, force=args.force)
        upload_time = time.time() - upload_start

        result["download_time"] = download_time
        result["upload_time"] = upload_time
        results.append(result)

        # Clean up memory
        del embeddings
        del passages
        import gc

        gc.collect()

        coll_total = time.time() - coll_start
        print(f"  ⏱️  Total time for {coll}: {coll_total:.1f}s")

    # Summary
    total_elapsed = time.time() - total_start
    total_points = sum(r["points"] for r in results)

    print("\n" + "═" * 70)
    print("🎉  SYNC COMPLETE")
    print("═" * 70)
    print(f"  Collections processed: {len(results)}/{len([s for s in status.values() if s['action'] != 'skip'])}")
    print(f"  Total points uploaded: {total_points:,}")
    print(f"  Total time: {total_elapsed / 60:.1f} minutes")
    print("═" * 70)

    # Verify
    print("\n🔍  Verifying Qdrant collections...")
    verify_qdrant(collections)


if __name__ == "__main__":
    main()
