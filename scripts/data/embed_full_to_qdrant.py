#!/usr/bin/env python3
"""Embed the full text corpora from the Hub and load them into Qdrant.

The Hub carries precomputed embeddings for six collections only. The other
four (fiqh, hadith, islamic history, general Islamic) exist as full text in
``Kandil7/Athar-Datasets`` under ``collections/<name>.jsonl.gz``, so this
script embeds them locally with the same encoder the query path uses and
uploads them with the same collection layout as the six preloaded ones.

The same encoder and the same pooling are used on both sides, so vectors
from this script and vectors from the Hub are comparable.

Usage:
    python scripts/data/embed_full_to_qdrant.py --collection fiqh_passages --recreate
    python scripts/data/embed_full_to_qdrant.py --all --device cuda --half
    python scripts/data/embed_full_to_qdrant.py --collection hadith_passages --start-row 0 --end-row 50000
"""

from __future__ import annotations

import argparse
import asyncio
import gzip
import json
import os
import sys
import time
from pathlib import Path
from typing import Any, Iterator

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

import httpx
from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    HnswConfigDiff,
    OptimizersConfigDiff,
    PointStruct,
    VectorParams,
)

from src.config.settings import settings
from src.indexing.embeddings.embedding_model import EmbeddingModel

HF_REPO = "Kandil7/Athar-Datasets"
HF_ENDPOINT = "https://huggingface.co"
RAW_DIR = Path(os.environ.get("HF_RAW_DIR", r"D:\AI\Models\HuggingFace\raw"))
DEFAULT_COLLECTIONS = (
    "fiqh_passages",
    "hadith_passages",
    "islamic_history_passages",
    "general_islamic",
)
VECTOR_DIM = 1024
UPSERT_BATCH = 256
ENCODE_BATCH = 32
PROGRESS_EVERY = 2048
GRPC_PORT = 6334
DOWNLOAD_CHUNK = 1 << 20


def remote_size(repo: str, filename: str) -> int | None:
    """Return the size of a file in a dataset repository, if the API knows it."""
    try:
        from huggingface_hub import HfApi

        info = HfApi().repo_info(repo, repo_type="dataset", files_metadata=True)
    except Exception as exc:  # noqa: BLE001 - the size is an optimisation
        print(f"  could not read the file size: {exc}", flush=True)
        return None
    for sibling in info.siblings:
        if sibling.rfilename == filename:
            return sibling.size
    return None


def download_collection(collection: str) -> Path:
    """Fetch the gzipped corpus for one collection and return its local path.

    The hub client downloads through the Xet content store, which failed
    midway on this workstation with a decoding error and left nothing behind.
    A plain streamed request with a Range header resumes instead, and the
    file lands under the model root, not in the repository.
    """
    filename = f"collections/{collection}.jsonl.gz"
    target = RAW_DIR / "Athar-Datasets" / filename
    target.parent.mkdir(parents=True, exist_ok=True)

    expected = remote_size(HF_REPO, filename)
    if target.exists() and (expected is None or target.stat().st_size == expected):
        print(f"  {target} already downloaded ({target.stat().st_size / 1e6:.1f} MB)", flush=True)
        return target

    url = f"{HF_ENDPOINT}/datasets/{HF_REPO}/resolve/main/{filename}"
    partial = target.with_suffix(target.suffix + ".part")
    have = partial.stat().st_size if partial.exists() else 0

    headers: dict[str, str] = {}
    token = os.environ.get("HF_TOKEN") or settings.hf_token
    if token:
        headers["Authorization"] = f"Bearer {token}"
    if have:
        headers["Range"] = f"bytes={have}-"

    print(f"  downloading {filename} to {target}", flush=True)
    with httpx.stream("GET", url, headers=headers, follow_redirects=True, timeout=300.0) as response:
        if have and response.status_code == 200:
            # The server ignored the range request, so start over.
            have = 0
        response.raise_for_status()
        mode = "ab" if have else "wb"
        downloaded = have
        last_report = time.time()
        with partial.open(mode) as handle:
            for chunk in response.iter_bytes(DOWNLOAD_CHUNK):
                handle.write(chunk)
                downloaded += len(chunk)
                if time.time() - last_report > 30:
                    rate = (downloaded - have) / max(time.time() - last_report, 0.001)
                    print(
                        f"    {downloaded / 1e6:.0f} MB of {(expected or 0) / 1e6:.0f} MB ({rate / 1e6:.1f} MB/s)",
                        flush=True,
                    )
                    last_report = time.time()

    if expected is not None and partial.stat().st_size != expected:
        print(
            f"  size mismatch: {partial.stat().st_size} of {expected} bytes, retrying later",
            flush=True,
        )
        return partial

    partial.replace(target)
    print(f"  downloaded {target.stat().st_size / 1e6:.1f} MB", flush=True)
    return target


def iter_rows(path: Path, start_row: int, end_row: int | None) -> Iterator[tuple[int, dict[str, Any]]]:
    """Yield (absolute id, row) pairs for the requested row window.

    The id is the index of the row inside the corpus, so re-running a window
    rewrites the same points instead of appending duplicates.
    """
    with gzip.open(path, "rt", encoding="utf-8") as handle:
        for index, line in enumerate(handle):
            if index < start_row:
                continue
            if end_row is not None and index >= end_row:
                break
            line = line.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            if not str(row.get("content") or "").strip():
                continue
            yield index, row


def build_payload(row: dict[str, Any]) -> dict[str, Any]:
    """Build the Qdrant payload for one row.

    Every field except the body is kept so citations can name the book, the
    author, the category, and the page. Lists are preserved, scalars are
    stringified to match the layout of the six preloaded collections.
    """
    payload: dict[str, Any] = {"content": str(row["content"])}
    for key, value in row.items():
        if key == "content":
            continue
        if isinstance(value, (list, dict)):
            payload[key] = value
        elif value is None:
            payload[key] = "None"
        else:
            payload[key] = str(value)
    return payload


def ensure_collection(client: QdrantClient, collection: str, recreate: bool) -> None:
    """Create the collection with the layout the preloaded collections use."""
    exists = client.collection_exists(collection)
    if exists and recreate:
        print(f"  dropping existing collection {collection}", flush=True)
        client.delete_collection(collection)
        exists = False
    if exists:
        return
    client.create_collection(
        collection_name=collection,
        vectors_config=VectorParams(size=VECTOR_DIM, distance=Distance.COSINE, on_disk=True),
        on_disk_payload=True,
        hnsw_config=HnswConfigDiff(m=0),
    )
    print(f"  created collection {collection} (dim={VECTOR_DIM}, hnsw m=0 during upload)", flush=True)


async def embed_collection(
    client: QdrantClient,
    encoder: EmbeddingModel,
    collection: str,
    corpus_path: Path,
    start_row: int,
    end_row: int | None,
    recreate: bool,
    limit: int | None,
) -> int:
    """Embed one collection and upsert it into Qdrant."""
    ensure_collection(client, collection, recreate)

    # Segment merges copy every vector in the merged segment. During a bulk
    # load that can exceed the free space on the Docker volume, so
    # optimization stays paused until the upload finishes.
    client.update_collection(
        collection_name=collection,
        optimizers_config=OptimizersConfigDiff(max_optimization_threads=0),
    )

    started = time.time()
    uploaded = 0
    batch_rows: list[tuple[int, dict[str, Any]]] = []

    async def flush() -> None:
        nonlocal uploaded, batch_rows
        if not batch_rows:
            return
        texts = [str(row["content"]) for _, row in batch_rows]
        vectors = await encoder.encode(texts, batch_size=ENCODE_BATCH)
        points = [
            PointStruct(
                id=index,
                vector=vector.tolist(),
                payload=build_payload(row),
            )
            for (index, row), vector in zip(batch_rows, vectors, strict=True)
        ]
        for attempt in range(1, 4):
            try:
                client.upsert(collection_name=collection, points=points)
                break
            except Exception as exc:  # noqa: BLE001 - transient transport errors
                if attempt == 3:
                    raise
                print(f"  [retry] upsert attempt {attempt} failed: {type(exc).__name__}: {exc}", flush=True)
                time.sleep(3 * attempt)
        uploaded += len(points)
        batch_rows = []

    for index, row in iter_rows(corpus_path, start_row, end_row):
        batch_rows.append((index, row))
        if len(batch_rows) >= UPSERT_BATCH:
            await flush()
            if uploaded % PROGRESS_EVERY < UPSERT_BATCH:
                elapsed = time.time() - started
                rate = uploaded / elapsed if elapsed else 0.0
                print(f"  {collection}: {uploaded:,} rows embedded ({rate:.1f}/s)", flush=True)
            if limit and uploaded >= limit:
                break

    await flush()

    elapsed = time.time() - started
    count = client.count(collection_name=collection, exact=True).count
    print(f"  {collection}: uploaded {uploaded:,} in {elapsed:.0f}s, stored {count:,}", flush=True)

    print("  building the HNSW index (m=16, ef_construct=100) ...", flush=True)
    client.update_collection(
        collection_name=collection,
        hnsw_config=HnswConfigDiff(m=16, ef_construct=100),
        optimizers_config=OptimizersConfigDiff(max_optimization_threads=1),
    )
    print(f"  {collection}: index ready", flush=True)
    return count


async def main() -> None:
    parser = argparse.ArgumentParser(description="Embed full corpora into Qdrant")
    parser.add_argument("--collections", nargs="+", default=list(DEFAULT_COLLECTIONS))
    parser.add_argument("--all", action="store_true", help="Use every default collection")
    parser.add_argument("--collection", help="Single collection to load")
    parser.add_argument("--recreate", action="store_true", help="Drop the collection before loading")
    parser.add_argument("--device", default="cpu", choices=["cpu", "cuda"])
    parser.add_argument("--half", action="store_true", help="Use float16 on CUDA for faster import")
    parser.add_argument("--start-row", type=int, default=0, help="First corpus row to embed")
    parser.add_argument("--end-row", type=int, default=None, help="Stop before this corpus row")
    parser.add_argument("--limit", type=int, default=None, help="Maximum rows to embed")
    args = parser.parse_args()

    if args.collection:
        collections = [args.collection]
    elif args.all:
        collections = list(DEFAULT_COLLECTIONS)
    else:
        collections = list(args.collections)

    encoder = EmbeddingModel(cache_enabled=False)
    await encoder.load_model()
    if args.device == "cuda":
        import torch

        if not torch.cuda.is_available():
            raise SystemExit("CUDA requested but not available")
        encoder.model.to("cuda")
        if args.half:
            encoder.model.half()
    print(f"encoder ready on {next(encoder.model.parameters()).device}", flush=True)

    client = QdrantClient(
        url=settings.qdrant_url,
        api_key=settings.qdrant_api_key,
        timeout=300,
        grpc_port=GRPC_PORT,
        prefer_grpc=True,
    )

    for collection in collections:
        print(f"\n=== {collection} ===", flush=True)
        corpus_path = download_collection(collection)
        await embed_collection(
            client,
            encoder,
            collection,
            corpus_path,
            args.start_row,
            args.end_row,
            args.recreate,
            args.limit,
        )


if __name__ == "__main__":
    asyncio.run(main())
