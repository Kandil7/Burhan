#!/usr/bin/env python3
"""
Backup Embeddings and Qdrant Data to HuggingFace.

After embedding 5.7M documents on Colab GPU, this script:
1. Compresses embeddings (.npy → .npy.gz, ~70% savings)
2. Exports Qdrant collections to JSON
3. Uploads everything to HuggingFace
4. Creates restore script for later use

Saves:
- 10 embedding files (~7GB compressed, down from ~23GB)
- 10 Qdrant export files (~15GB compressed, down from ~50GB)
- Metadata and restore instructions

Usage:
    python scripts/backup_embeddings_and_qdrant.py --embeddings-only
    python scripts/backup_embeddings_and_qdrant.py --qdrant-only
    python scripts/backup_embeddings_and_qdrant.py --all
    python scripts/backup_embeddings_and_qdrant.py --verify
"""

import argparse
import gzip
import json
import os
import shutil
import sys
import time
from pathlib import Path

from dotenv import load_dotenv
load_dotenv()

try:
    from huggingface_hub import HfApi, login
    HAS_HF = True
except ImportError:
    print("❌ huggingface_hub not installed")
    print("   Install: poetry add huggingface_hub")
    sys.exit(1)

# Configuration
PROJECT_ROOT = Path(__file__).parent.parent
EMBEDDINGS_DIR = PROJECT_ROOT / "data" / "processed" / "embeddings"
QDRANT_EXPORT_DIR = PROJECT_ROOT / "data" / "processed" / "qdrant_exports"
BACKUP_DIR = PROJECT_ROOT / "data" / "processed" / "hf_backup"

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


def compress_file(input_path: Path, output_path: Path) -> int:
    """Compress file with gzip and return compressed size."""
    if output_path.exists():
        print(f"  ⏭️  Already compressed: {output_path.name}")
        return output_path.stat().st_size

    print(f"  📦 Compressing {input_path.name}...")
    start = time.time()

    with open(input_path, 'rb') as f_in:
        with gzip.open(output_path, 'wb', compresslevel=6) as f_out:
            shutil.copyfileobj(f_in, f_out)

    original_size = input_path.stat().st_size
    compressed_size = output_path.stat().st_size
    elapsed = time.time() - start
    ratio = compressed_size / original_size

    print(f"    {format_size(original_size)} → {format_size(compressed_size)} ({ratio:.1%}) [{elapsed:.1f}s]")

    return compressed_size


def backup_embeddings():
    """Backup embedding files to HuggingFace."""
    print("\n" + "=" * 70)
    print("📦 BACKING UP EMBEDDINGS")
    print("=" * 70)

    if not EMBEDDINGS_DIR.exists():
        print(f"❌ Embeddings directory not found: {EMBEDDINGS_DIR}")
        print("   Run Colab notebook first to generate embeddings")
        return False

    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    embeddings_backup_dir = BACKUP_DIR / "embeddings"
    embeddings_backup_dir.mkdir(exist_ok=True)

    total_original = 0
    total_compressed = 0
    files_processed = 0

    for collection in COLLECTIONS:
        # Check for embedding file
        npy_file = EMBEDDINGS_DIR / f"{collection}_embeddings.npy"

        if not npy_file.exists():
            print(f"  ⚠️  Not found: {npy_file.name}")
            continue

        # Compress
        gz_file = embeddings_backup_dir / f"{collection}_embeddings.npy.gz"
        compressed_size = compress_file(npy_file, gz_file)
        original_size = npy_file.stat().st_size

        total_original += original_size
        total_compressed += compressed_size
        files_processed += 1

        # Also save passages metadata
        json_file = EMBEDDINGS_DIR / f"{collection}_passages.json"
        if json_file.exists():
            gz_json = embeddings_backup_dir / f"{collection}_passages.json.gz"
            compress_file(json_file, gz_json)

    if files_processed == 0:
        print("❌ No embeddings found to backup")
        return False

    # Create README for embeddings
    readme_content = f"""# 🕌 Athar Embeddings

**5.7M document embeddings from 10 Islamic text collections**

Embedded using BAAI/bge-m3 model (1024 dimensions) on Colab GPU.

## Files

| Collection | Original | Compressed | Documents |
|------------|----------|------------|-----------|
"""

    for collection in COLLECTIONS:
        npy_file = EMBEDDINGS_DIR / f"{collection}_embeddings.npy"
        if npy_file.exists():
            # Load to get document count
            import numpy as np
            embeddings = np.load(npy_file)
            size = npy_file.stat().st_size
            print(f"| {collection} | {format_size(size)} | - | {len(embeddings):,} |")
            readme_content += f"| {collection} | {format_size(size)} | - | {len(embeddings):,} |\n"

    readme_content += f"""
## Total

- **Original Size:** {format_size(total_original)}
- **Compressed Size:** {format_size(total_compressed)}
- **Savings:** {(1 - total_compressed/max(total_original,1))*100:.1f}%
- **Collections:** {files_processed}/10

## How to Restore

```python
from huggingface_hub import hf_hub_download
import numpy as np
import gzip

# Download embedding
filepath = hf_hub_download(
    repo_id="{REPO_ID}",
    filename="embeddings/fiqh_passages_embeddings.npy.gz",
    repo_type="dataset"
)

# Decompress
with gzip.open(filepath, 'rb') as f:
    embeddings = np.load(f)

print(f"Loaded {len(embeddings):,} embeddings")
print(f"Shape: {embeddings.shape}")
```

## Model Info

- **Model:** BAAI/bge-m3
- **Dimensions:** 1024
- **Device:** GPU (Colab T4/A100)
- **Batch Size:** 512
- **Max Length:** 8192 tokens

---

Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}
"""

    with open(embeddings_backup_dir / "README.md", 'w', encoding='utf-8') as f:
        f.write(readme_content)

    print(f"\n{'='*70}")
    print(f"📊 EMBEDDINGS BACKUP SUMMARY")
    print(f"{'='*70}")
    print(f"  Files processed: {files_processed}")
    print(f"  Original size: {format_size(total_original)}")
    print(f"  Compressed size: {format_size(total_compressed)}")
    print(f"  Savings: {(1 - total_compressed/max(total_original,1))*100:.1f}%")
    print(f"  Output: {embeddings_backup_dir}")

    return True


def backup_qdrant_collections():
    """Export Qdrant collections to JSON for backup."""
    print("\n" + "=" * 70)
    print("📦 BACKING UP QDRANT DATA")
    print("=" * 70)

    try:
        from qdrant_client import QdrantClient
    except ImportError:
        print("❌ qdrant-client not installed")
        print("   Install: poetry add qdrant-client")
        return False

    QDRANT_URL = os.environ.get("QDRANT_URL", "http://localhost:6333")
    QDRANT_API_KEY = os.environ.get("QDRANT_API_KEY")

    try:
        client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)
    except Exception as e:
        print(f"❌ Cannot connect to Qdrant: {e}")
        print("   Make sure Qdrant is running and accessible")
        return False

    QDRANT_EXPORT_DIR.mkdir(parents=True, exist_ok=True)

    total_points = 0

    for collection in COLLECTIONS:
        try:
            # Get collection info
            info = client.get_collection(collection)
            points_count = info.points_count

            if points_count == 0:
                print(f"  ⚠️  Empty collection: {collection}")
                continue

            print(f"\n  📚 Exporting {collection} ({points_count:,} points)...")
            start = time.time()

            # Export in batches
            export_file = QDRANT_EXPORT_DIR / f"{collection}_export.json"
            points = []

            offset = None
            while True:
                batch = client.scroll(
                    collection_name=collection,
                    limit=1000,
                    offset=offset,
                    with_payload=True,
                    with_vectors=True
                )

                for point in batch[0]:
                    points.append({
                        "id": point.id,
                        "vector": point.vector,
                        "payload": point.payload
                    })

                if len(batch[0]) < 1000:
                    break
                offset = batch[-1][0].id

            # Save to JSON
            with open(export_file, 'w', encoding='utf-8') as f:
                json.dump({
                    "collection": collection,
                    "points_count": len(points),
                    "exported_at": time.strftime('%Y-%m-%d %H:%M:%S'),
                    "points": points
                }, f, ensure_ascii=False)

            elapsed = time.time() - start
            file_size = export_file.stat().st_size
            total_points += len(points)

            print(f"  ✅ Exported {len(points):,} points ({format_size(file_size)}) [{elapsed/60:.1f} min]")

        except Exception as e:
            print(f"  ❌ Failed to export {collection}: {e}")

    print(f"\n{'='*70}")
    print(f"📊 QDRANT BACKUP SUMMARY")
    print(f"{'='*70}")
    print(f"  Total points exported: {total_points:,}")
    print(f"  Output: {QDRANT_EXPORT_DIR}")

    return total_points > 0


def upload_to_huggingface(api: HfApi, source_dir: Path, repo_path_prefix: str):
    """Upload backup directory to HuggingFace."""
    if not source_dir.exists():
        print(f"❌ Directory not found: {source_dir}")
        return False

    print(f"\n📤 Uploading {source_dir.name} to HuggingFace...")
    print(f"  Repository: {REPO_ID}")
    print(f"  Path: {repo_path_prefix}/")

    files = list(source_dir.rglob("*"))
    files = [f for f in files if f.is_file()]

    for i, filepath in enumerate(sorted(files), 1):
        rel_path = filepath.relative_to(source_dir.parent)
        repo_path = f"{repo_path_prefix}/{rel_path.as_posix()}"

        size = filepath.stat().st_size
        print(f"  [{i}/{len(files)}] Uploading {rel_path.name} ({format_size(size)})...")

        try:
            start = time.time()
            api.upload_file(
                path_or_fileobj=str(filepath),
                path_in_repo=repo_path,
                repo_id=REPO_ID,
                repo_type="dataset",
            )
            elapsed = time.time() - start
            speed = size / 1e6 / max(elapsed, 0.001)
            print(f"    ✅ ({speed:.1f} MB/s)")
        except Exception as e:
            print(f"    ❌ Failed: {e}")
            return False

    return True


def verify_backup():
    """Verify backup on HuggingFace."""
    if not HF_TOKEN:
        print("❌ HF_TOKEN not set")
        return

    api = HfApi()
    login(token=HF_TOKEN)

    try:
        files = api.list_repo_files(repo_id=REPO_ID, repo_type="dataset")
        print(f"📋 Repository: {REPO_ID}")
        print(f"📁 Files: {len(files)}")
        print()

        for f in sorted(files)[:20]:
            print(f"  - {f}")

        if len(files) > 20:
            print(f"  ... and {len(files) - 20} more files")

    except Exception as e:
        print(f"❌ Failed to verify: {e}")


def main():
    parser = argparse.ArgumentParser(description="Backup embeddings and Qdrant to HuggingFace")
    parser.add_argument("--embeddings-only", action="store_true", help="Backup only embeddings")
    parser.add_argument("--qdrant-only", action="store_true", help="Backup only Qdrant exports")
    parser.add_argument("--all", action="store_true", help="Backup everything")
    parser.add_argument("--verify", action="store_true", help="Verify backup on HF")
    parser.add_argument("--upload", action="store_true", help="Upload to HuggingFace")

    args = parser.parse_args()

    if not any([args.embeddings_only, args.qdrant_only, args.all, args.verify]):
        args.all = True  # Default to all

    if not HF_TOKEN:
        print("❌ HF_TOKEN not set in .env")
        sys.exit(1)

    api = HfApi()
    login(token=HF_TOKEN)

    if args.verify:
        verify_backup()
        return

    # Backup embeddings
    if args.embeddings_only or args.all:
        success = backup_embeddings()
        if success and args.upload:
            upload_to_huggingface(
                api,
                BACKUP_DIR / "embeddings",
                "embeddings"
            )

    # Backup Qdrant
    if args.qdrant_only or args.all:
        success = backup_qdrant_collections()
        if success and args.upload:
            upload_to_huggingface(
                api,
                QDRANT_EXPORT_DIR,
                "qdrant_exports"
            )

    print("\n" + "=" * 70)
    print("✅ BACKUP COMPLETE")
    print("=" * 70)
    print(f"\n🔗 View at: https://huggingface.co/datasets/{REPO_ID}")


if __name__ == "__main__":
    main()
