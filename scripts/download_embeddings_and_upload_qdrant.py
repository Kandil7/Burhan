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
    poetry run python scripts/download_embeddings_and_upload_qdrant.py --force
    poetry run python scripts/download_embeddings_and_upload_qdrant.py --collections seerah_passages --yes
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
    from qdrant_client.models import Distance, HnswConfigDiff, VectorParams, PointStruct

    HAS_QDRANT = True
except ImportError:
    print("❌ qdrant-client not installed")
    print("   Install: poetry add qdrant-client")
    sys.exit(1)

# Configuration
HF_REPO = "Kandil7/Athar-Embeddings"
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
VECTOR_DIM = 1024  # BAAI/bge-m3 output size


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
    """Estimate expected point counts from the embedding shard sizes on HF.

    Each shard stores float32 vectors of VECTOR_DIM, so one row is
    VECTOR_DIM * 4 bytes. Using the published file sizes avoids downloading
    every shard just to count rows.
    """
    print("Checking HuggingFace for expected counts...")
    api = HfApi()
    row_bytes = VECTOR_DIM * 4
    rows_by_collection: Dict[str, int] = {coll: 0 for coll in COLLECTIONS}

    for entry in api.list_repo_tree(repo_id=HF_REPO, repo_type="dataset", recursive=True):
        path = getattr(entry, "path", "") or ""
        size = getattr(entry, "size", None)
        if size is None or "_emb_" not in path or not path.endswith(".npy"):
            continue
        collection = path.split("/")[0]
        if collection not in rows_by_collection:
            continue
        # Each .npy carries a small header, so round per file instead of
        # summing bytes, which would accumulate one row per shard.
        rows = (size + row_bytes // 2) // row_bytes
        if abs(size - rows * row_bytes) > row_bytes:
            print(f"  [warn] {path}: size {size} does not fit the expected row layout")
        rows_by_collection[collection] += rows

    counts: Dict[str, int] = {}
    for collection, rows in rows_by_collection.items():
        counts[collection] = rows
        print(f"  {collection}: {rows:,} expected")
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


def list_collection_shards(collection_name: str) -> tuple[list[str], list[str]]:
    """Return the sorted embedding and metadata shard paths for a collection."""
    api = HfApi()
    all_files = api.list_repo_files(repo_id=HF_REPO, repo_type="dataset")
    prefix = f"{collection_name}/"
    coll_files = [f for f in all_files if f.startswith(prefix)]
    emb_files = sorted(f for f in coll_files if "_emb_" in f and f.endswith(".npy"))
    meta_files = sorted(f for f in coll_files if "_meta_" in f and f.endswith(".jsonl.gz"))
    return emb_files, meta_files


def read_meta_file(path: str) -> list[dict]:
    """Read one gzipped JSONL metadata shard into a list of dicts."""
    rows: list[dict] = []
    with gzip.open(path, "rt", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return rows


def iter_collection_shards(collection_name: str):
    """Download a collection one shard at a time.

    Yields (shard_index, shard_count, vectors, passages). Holding one shard
    keeps the process near 40 MB instead of several gigabytes.
    """
    emb_files, meta_files = list_collection_shards(collection_name)
    if not emb_files:
        print(f"  [warn] no embedding shards found for {collection_name}")
        return

    print(f"  Found {len(emb_files)} embedding shards, {len(meta_files)} metadata shards")
    if len(emb_files) != len(meta_files):
        print(f"  [warn] {len(emb_files)} embedding shards vs {len(meta_files)} metadata shards")

    total = min(len(emb_files), len(meta_files))
    for index in range(total):
        emb_path = hf_hub_download(
            repo_id=HF_REPO,
            filename=emb_files[index],
            repo_type="dataset",
            local_dir=str(DOWNLOAD_DIR),
            force_download=False,
        )
        meta_path = hf_hub_download(
            repo_id=HF_REPO,
            filename=meta_files[index],
            repo_type="dataset",
            local_dir=str(DOWNLOAD_DIR),
            force_download=False,
        )

        vectors = np.load(emb_path, mmap_mode="r")
        passages = read_meta_file(meta_path)
        if vectors.shape[0] != len(passages):
            count = min(vectors.shape[0], len(passages))
            print(
                f"  [warn] {emb_files[index]}: {vectors.shape[0]} vectors vs {len(passages)} rows, trimming to {count}"
            )
            vectors = vectors[:count]
            passages = passages[:count]

        yield index, total, vectors, passages


def upload_to_qdrant(
    collection_name: str,
    shards,
    batch_size: int = QDRANT_BATCH_SIZE,
    force: bool = False,
) -> dict:
    """Upload shards to Qdrant with on-disk storage and a deferred HNSW index.

    Vectors and payload stay on disk so a bulk load does not grow RAM in step
    with the collection, and HNSW is disabled during the upload so every batch
    does not build its own index. The index is built once at the end.
    """
    print(f"\n{'=' * 70}")
    print(f"Uploading to Qdrant: {collection_name}")
    print(f"{'=' * 70}")

    client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY, timeout=120)

    existing_count = 0
    collection_exists = client.collection_exists(collection_name)
    if collection_exists:
        existing_count = client.get_collection(collection_name).points_count or 0
        print(f"  Collection exists ({existing_count:,} existing points)")

    recreate = force or not collection_exists or existing_count == 0
    if recreate:
        if collection_exists:
            print("  Recreating collection (force mode)...")
            client.delete_collection(collection_name)
        else:
            print(f"  Creating collection: {collection_name} (dim={VECTOR_DIM})")
        client.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(size=VECTOR_DIM, distance=Distance.COSINE, on_disk=True),
            on_disk_payload=True,
            hnsw_config=HnswConfigDiff(m=0),
        )
        start_id = 0
    else:
        print(f"  Appending after {existing_count:,} existing points...")
        start_id = existing_count

    total_points = 0
    rows_seen = 0
    next_id = start_id
    started = time.time()

    for shard_index, shard_count, vectors, passages in shards:
        if vectors.shape[1] != VECTOR_DIM:
            raise ValueError(
                f"{collection_name}: shard {shard_index} has {vectors.shape[1]} dimensions, expected {VECTOR_DIM}"
            )

        if rows_seen + len(passages) <= start_id:
            rows_seen += len(passages)
            continue

        skip = max(0, start_id - rows_seen)
        for start in range(skip, len(passages), batch_size):
            end = min(start + batch_size, len(passages))
            batch_vectors = vectors[start:end].tolist()

            points = []
            for idx in range(end - start):
                pas = passages[start + idx]
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
                points.append(PointStruct(id=next_id, vector=batch_vectors[idx], payload=payload))
                next_id += 1

            client.upsert(collection_name=collection_name, points=points)
            total_points += len(points)

        rows_seen += len(passages)
        elapsed = time.time() - started
        rate = total_points / elapsed if elapsed else 0.0
        print(
            f"  shard {shard_index + 1}/{shard_count}: {rows_seen:,} rows, {total_points:,} uploaded ({rate:.0f} pts/s)"
        )

    elapsed = time.time() - started
    print(f"  Uploaded {total_points:,} points in {elapsed:.1f}s")

    print("  Enabling HNSW index...")
    client.update_collection(
        collection_name=collection_name,
        hnsw_config=HnswConfigDiff(m=16, ef_construct=100),
    )

    return {
        "collection": collection_name,
        "points": total_points,
        "existing": existing_count,
        "elapsed": elapsed,
    }


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
    parser.add_argument("--yes", action="store_true", help="Skip the confirmation prompt")

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
    if upload_count > 0 and not args.yes:
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

        if coll_status["action"] == "skip" and not args.force:
            print(f"\nSkipping {coll} ({coll_status['reason']})")
            continue

        coll_start = time.time()
        try:
            result = upload_to_qdrant(
                coll,
                iter_collection_shards(coll),
                batch_size,
                force=args.force,
            )
        except Exception as exc:
            print(f"  [error] {coll}: {exc}")
            continue

        result["total_time"] = time.time() - coll_start
        results.append(result)
        print(f"  Total time for {coll}: {result['total_time']:.1f}s")

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
