#!/usr/bin/env python3
"""
Restore Embeddings and Qdrant Data from HuggingFace Backup.

Downloads compressed embeddings and Qdrant exports from HuggingFace
and restores them for use in the Athar RAG system.

Usage:
    python scripts/restore_from_huggingface.py --embeddings
    python scripts/restore_from_huggingface.py --qdrant
    python scripts/restore_from_huggingface.py --all
    python scripts/restore_from_huggingface.py --verify
"""

import argparse
import gzip
import json
import os
import sys
import time
from pathlib import Path

from dotenv import load_dotenv
load_dotenv()

try:
    from huggingface_hub import hf_hub_download, HfApi, login
    HAS_HF = True
except ImportError:
    print("❌ huggingface_hub not installed")
    sys.exit(1)

try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    print("❌ numpy not installed")
    sys.exit(1)

# Configuration
PROJECT_ROOT = Path(__file__).parent.parent
EMBEDDINGS_DIR = PROJECT_ROOT / "data" / "processed" / "embeddings"
QDRANT_EXPORT_DIR = PROJECT_ROOT / "data" / "processed" / "qdrant_exports"

REPO_ID = os.environ.get("HF_EMBEDDINGS_REPO_ID", "Kandil7/Athar-Embeddings")
HF_TOKEN = os.environ.get("HF_TOKEN")

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


def format_size(size_bytes: int) -> str:
    """Format bytes to human-readable size."""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} PB"


def restore_embeddings():
    """Download and decompress embeddings from HuggingFace."""
    print("\n" + "=" * 70)
    print("📥 RESTORING EMBEDDINGS")
    print("=" * 70)

    EMBEDDINGS_DIR.mkdir(parents=True, exist_ok=True)

    restored = 0

    for collection in COLLECTIONS:
        filename = f"{collection}_embeddings.npy.gz"
        output_file = EMBEDDINGS_DIR / f"{collection}_embeddings.npy"

        if output_file.exists():
            print(f"  ✅ Already exists: {output_file.name}")
            restored += 1
            continue

        print(f"\n  📥 Downloading {collection}...")
        start = time.time()

        try:
            # Download
            filepath = hf_hub_download(
                repo_id=REPO_ID,
                filename=f"embeddings/{filename}",
                repo_type="dataset"
            )

            # Decompress
            with gzip.open(filepath, 'rb') as f_in:
                with open(output_file, 'wb') as f_out:
                    f_out.write(f_in.read())

            # Verify
            embeddings = np.load(output_file)
            size = output_file.stat().st_size
            elapsed = time.time() - start

            print(f"  ✅ {collection}: {len(embeddings):,} embeddings ({format_size(size)}) [{elapsed:.1f}s]")
            print(f"     Shape: {embeddings.shape}")
            restored += 1

        except Exception as e:
            print(f"  ❌ Failed: {e}")

    print(f"\n{'='*70}")
    print(f"📊 RESTORE SUMMARY")
    print(f"{'='*70}")
    print(f"  Restored: {restored}/{len(COLLECTIONS)} collections")

    return restored == len(COLLECTIONS)


def restore_qdrant():
    """Restore Qdrant collections from HuggingFace export."""
    print("\n" + "=" * 70)
    print("📥 RESTORING QDRANT DATA")
    print("=" * 70)

    try:
        from qdrant_client import QdrantClient
        from qdrant_client.models import Distance, VectorParams, PointStruct
    except ImportError:
        print("❌ qdrant-client not installed")
        return False

    QDRANT_URL = os.environ.get("QDRANT_URL", "http://localhost:6333")
    QDRANT_API_KEY = os.environ.get("QDRANT_API_KEY")

    try:
        client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)
    except Exception as e:
        print(f"❌ Cannot connect to Qdrant: {e}")
        return False

    QDRANT_EXPORT_DIR.mkdir(parents=True, exist_ok=True)

    restored = 0

    for collection in COLLECTIONS:
        filename = f"{collection}_export.json"
        export_file = QDRANT_EXPORT_DIR / filename

        print(f"\n  📚 Restoring {collection}...")

        # Download if not exists
        if not export_file.exists():
            try:
                filepath = hf_hub_download(
                    repo_id=REPO_ID,
                    filename=f"qdrant_exports/{filename}",
                    repo_type="dataset"
                )
                # Copy to local dir
                import shutil
                shutil.copy2(filepath, export_file)
            except Exception as e:
                print(f"  ❌ Download failed: {e}")
                continue

        # Load export
        try:
            with open(export_file, 'r', encoding='utf-8') as f:
                export_data = json.load(f)

            points = export_data.get("points", [])
            points_count = len(points)

            if points_count == 0:
                print(f"  ⚠️  No points in export")
                continue

            # Create collection
            try:
                client.create_collection(
                    collection_name=collection,
                    vectors_config=VectorParams(size=1024, distance=Distance.COSINE)
                )
                print(f"  ✅ Created collection: {collection}")
            except Exception as e:
                print(f"  ⚠️  Collection may exist: {e}")

            # Upload points
            batch_size = 1000
            for i in range(0, points_count, batch_size):
                batch_points = points[i:i+batch_size]

                qdrant_points = []
                for point in batch_points:
                    qdrant_points.append(PointStruct(
                        id=point["id"],
                        vector=point["vector"],
                        payload=point["payload"]
                    ))

                client.upsert(
                    collection_name=collection,
                    points=qdrant_points
                )

            elapsed = time.time() - start if 'start' in dir() else 0
            print(f"  ✅ Restored {points_count:,} points")
            restored += 1

        except Exception as e:
            print(f"  ❌ Failed: {e}")

    print(f"\n{'='*70}")
    print(f"📊 RESTORE SUMMARY")
    print(f"{'='*70}")
    print(f"  Restored: {restored}/{len(COLLECTIONS)} collections")

    return restored == len(COLLECTIONS)


def verify_restore():
    """Verify restored embeddings and Qdrant collections."""
    print("\n" + "=" * 70)
    print("✅ VERIFYING RESTORE")
    print("=" * 70)

    # Check embeddings
    print("\n📊 Embeddings:")
    for collection in COLLECTIONS:
        npy_file = EMBEDDINGS_DIR / f"{collection}_embeddings.npy"
        if npy_file.exists():
            embeddings = np.load(npy_file)
            print(f"  ✅ {collection}: {len(embeddings):,} vectors, shape {embeddings.shape}")
        else:
            print(f"  ❌ {collection}: NOT FOUND")

    # Check Qdrant
    try:
        from qdrant_client import QdrantClient
        QDRANT_URL = os.environ.get("QDRANT_URL", "http://localhost:6333")
        QDRANT_API_KEY = os.environ.get("QDRANT_API_KEY")
        client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)

        print("\n📊 Qdrant Collections:")
        for collection in COLLECTIONS:
            try:
                info = client.get_collection(collection)
                print(f"  ✅ {collection}: {info.points_count:,} points")
            except:
                print(f"  ❌ {collection}: NOT FOUND")
    except Exception as e:
        print(f"\n⚠️  Could not check Qdrant: {e}")


def main():
    parser = argparse.ArgumentParser(description="Restore from HuggingFace backup")
    parser.add_argument("--embeddings", action="store_true", help="Restore embeddings only")
    parser.add_argument("--qdrant", action="store_true", help="Restore Qdrant only")
    parser.add_argument("--all", action="store_true", help="Restore everything")
    parser.add_argument("--verify", action="store_true", help="Verify restore")

    args = parser.parse_args()

    if not any([args.embeddings, args.qdrant, args.all, args.verify]):
        args.all = True

    if not HF_TOKEN:
        print("❌ HF_TOKEN not set")
        sys.exit(1)

    login(token=HF_TOKEN)

    if args.verify:
        verify_restore()
        return

    if args.embeddings or args.all:
        restore_embeddings()

    if args.qdrant or args.all:
        restore_qdrant()


if __name__ == "__main__":
    main()
