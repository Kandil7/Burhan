#!/usr/bin/env python3
"""
Download embeddings from HuggingFace and upload to Qdrant.

This script:
1. Downloads embedding chunks from Kandil7/Athar-Embeddings
2. Downloads metadata (passages) from the same repo
3. Creates Qdrant collections if they don't exist
4. Uploads all embeddings with metadata to Qdrant

Usage:
    poetry run python scripts/download_embeddings_and_upload_qdrant.py
    poetry run python scripts/download_embeddings_and_upload_qdrant.py --collections fiqh_passages hadith_passages
    poetry run python scripts/download_embeddings_and_upload_qdrant.py --verify-only
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
]

DOWNLOAD_DIR = Path("data/processed/hf_embeddings")
QDRANT_BATCH_SIZE = 500  # Points per upload batch


def format_size(size_bytes: int) -> str:
    """Format bytes to human-readable size."""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} PB"


def download_embeddings_for_collection(collection_name: str) -> tuple:
    """
    Download all embedding chunks and metadata for a collection from HuggingFace.
    Returns: (embeddings_array, passages_list)
    """
    print(f"\n{'='*70}")
    print(f"📥 Downloading: {collection_name}")
    print(f"{'='*70}")
    
    DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)
    coll_dir = DOWNLOAD_DIR / collection_name
    coll_dir.mkdir(exist_ok=True)
    
    # List files in collection directory on HF
    api = HfApi()
    all_files = api.list_repo_files(repo_id=HF_REPO, repo_type="dataset")
    coll_files = [f for f in all_files if f.startswith(f"{collection_name}/")]
    
    emb_files = sorted([f for f in coll_files if '_emb_' in f and f.endswith('.npy')])
    meta_files = sorted([f for f in coll_files if '_meta_' in f and f.endswith('.jsonl.gz')])
    
    print(f"  Found {len(emb_files)} embedding files")
    print(f"  Found {len(meta_files)} metadata files")
    
    # Download and concatenate all embedding chunks
    all_embeddings = []
    for i, emb_file in enumerate(emb_files, 1):
        filepath = hf_hub_download(
            repo_id=HF_REPO,
            filename=emb_file,
            repo_type="dataset",
            local_dir=str(DOWNLOAD_DIR)
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
        return None, None
    
    print(f"  ✅ Embeddings shape: {embeddings_array.shape}")
    
    # Download and concatenate all metadata chunks
    passages = []
    for i, meta_file in enumerate(meta_files, 1):
        filepath = hf_hub_download(
            repo_id=HF_REPO,
            filename=meta_file,
            repo_type="dataset",
            local_dir=str(DOWNLOAD_DIR)
        )
        
        with gzip.open(filepath, 'rt', encoding='utf-8') as f:
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


def upload_to_qdrant(collection_name: str, embeddings: np.ndarray, passages: list) -> dict:
    """Upload embeddings and passages to Qdrant."""
    print(f"\n{'='*70}")
    print(f"📤 Uploading to Qdrant: {collection_name}")
    print(f"{'='*70}")
    
    # Connect to Qdrant
    print(f"  Connecting to Qdrant: {QDRANT_URL}")
    client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY, timeout=120)
    
    # Create collection if not exists
    vector_size = embeddings.shape[1]
    if not client.collection_exists(collection_name):
        print(f"  Creating collection: {collection_name} (dim={vector_size})")
        client.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE)
        )
        print(f"  ✅ Collection created")
    else:
        info = client.get_collection(collection_name)
        print(f"  ℹ️  Collection exists ({info.points_count:,} points)")
        print(f"  🔄 Upserting new points...")
    
    # Upload in batches
    total_points = len(passages)
    t0 = time.time()
    uploaded = 0
    
    for start in range(0, total_points, QDRANT_BATCH_SIZE):
        end = min(start + QDRANT_BATCH_SIZE, total_points)
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
            
            points.append(PointStruct(
                id=start + idx,
                vector=batch_emb[idx].tolist(),
                payload=payload
            ))
        
        client.upsert(
            collection_name=collection_name,
            points=points
        )
        
        uploaded += len(points)
        if uploaded % 5000 == 0 or uploaded == total_points:
            elapsed = time.time() - t0
            speed = uploaded / elapsed
            print(f"    Uploaded {uploaded:,}/{total_points:,} points ({elapsed:.1f}s, {speed:.0f} pts/sec)")
    
    elapsed = time.time() - t0
    print(f"\n  ✅ Uploaded {uploaded:,} points in {elapsed:.1f}s ({uploaded/elapsed:.0f} pts/sec)")
    
    return {
        "collection": collection_name,
        "points": uploaded,
        "elapsed": elapsed
    }


def verify_qdrant(collections: list) -> dict:
    """Verify all collections in Qdrant."""
    print(f"\n{'='*70}")
    print(f"📊 Qdrant Collections Verification")
    print(f"{'='*70}")
    
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
    
    print(f"{'─'*70}")
    print(f"  {'TOTAL':<40} {total_vectors:>10,} vectors")
    print(f"{'='*70}")
    
    return {"total_vectors": total_vectors, "collections": results}


def main():
    parser = argparse.ArgumentParser(description="Download embeddings from HF and upload to Qdrant")
    parser.add_argument("--collections", nargs="+", default=None, help="Specific collections to process (default: all)")
    parser.add_argument("--verify-only", action="store_true", help="Only verify Qdrant collections, no download/upload")
    parser.add_argument("--batch-size", type=int, default=QDRANT_BATCH_SIZE, help="Qdrant upload batch size")
    
    args = parser.parse_args()
    
    global QDRANT_BATCH_SIZE
    QDRANT_BATCH_SIZE = args.batch_size
    
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
    
    if args.verify_only:
        verify_qdrant(collections)
        return
    
    print("\n" + "═"*70)
    print("🕌  ATHAR - Download Embeddings & Upload to Qdrant")
    print("═"*70)
    print(f"  HF Repo: {HF_REPO}")
    print(f"  Qdrant: {QDRANT_URL}")
    print(f"  Collections: {len(collections)}")
    print(f"  Batch size: {QDRANT_BATCH_SIZE}")
    print("═"*70)
    
    total_start = time.time()
    results = []
    
    for coll in collections:
        coll_start = time.time()
        
        # Download
        embeddings, passages = download_embeddings_for_collection(coll)
        
        if embeddings is None or passages is None:
            print(f"  ⏭️  Skipped {coll} (no data)")
            continue
        
        download_time = time.time() - coll_start
        print(f"  ⏱️  Download time: {download_time:.1f}s")
        
        # Upload to Qdrant
        upload_start = time.time()
        result = upload_to_qdrant(coll, embeddings, passages)
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
    
    print("\n" + "═"*70)
    print("🎉  UPLOAD COMPLETE")
    print("═"*70)
    print(f"  Collections processed: {len(results)}/{len(collections)}")
    print(f"  Total points uploaded: {total_points:,}")
    print(f"  Total time: {total_elapsed/60:.1f} minutes")
    print("═"*70)
    
    # Verify
    print("\n🔍  Verifying Qdrant collections...")
    verify_qdrant(collections)


if __name__ == "__main__":
    main()
