#!/usr/bin/env python3
"""Embed the bundled mini datasets and load them into Qdrant.

The Hub repository only carries precomputed embeddings for six collections.
This script covers the remaining collections from ``data/mini_dataset_v2`` so
every registered collection answers retrieval queries.

Usage:
    python scripts/data/embed_mini_v2_to_qdrant.py --collections fiqh_passages
    python scripts/data/embed_mini_v2_to_qdrant.py --collections fiqh_passages hadith_passages
    python scripts/data/embed_mini_v2_to_qdrant.py --all --recreate
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams

from src.config.settings import settings
from src.indexing.embeddings.embedding_model import EmbeddingModel

DATA_DIR = PROJECT_ROOT / "data" / "mini_dataset_v2"
DEFAULT_COLLECTIONS = (
    "fiqh_passages",
    "hadith_passages",
    "islamic_history_passages",
    "general_islamic",
)
UPSERT_BATCH = 256
PROGRESS_EVERY = 1024


def load_rows(collection: str, limit: int | None) -> list[dict]:
    path = DATA_DIR / f"{collection}.jsonl"
    if not path.exists():
        raise SystemExit(f"missing dataset: {path}")

    rows: list[dict] = []
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            row = json.loads(line)
            if not str(row.get("content") or "").strip():
                continue
            rows.append(row)
            if limit and len(rows) >= limit:
                break
    return rows


def ensure_collection(client: QdrantClient, collection: str, recreate: bool) -> None:
    exists = client.collection_exists(collection)
    if exists and not recreate:
        return
    if exists:
        client.delete_collection(collection)
    client.create_collection(
        collection_name=collection,
        vectors_config=VectorParams(size=1024, distance=Distance.COSINE, on_disk=True),
    )


async def embed_collection(
    client: QdrantClient,
    encoder: EmbeddingModel,
    collection: str,
    limit: int | None,
    recreate: bool,
) -> int:
    rows = load_rows(collection, limit)
    ensure_collection(client, collection, recreate)

    started = time.perf_counter()
    uploaded = 0
    for start in range(0, len(rows), UPSERT_BATCH):
        batch = rows[start : start + UPSERT_BATCH]
        texts = [str(row["content"]) for row in batch]
        vectors = await encoder.encode(texts, batch_size=64)

        points = [
            PointStruct(
                id=start + offset,
                vector=vector.tolist(),
                payload={key: value for key, value in row.items() if key != "content"}
                | {"content": str(row["content"])},
            )
            for offset, (row, vector) in enumerate(zip(batch, vectors, strict=True))
        ]
        client.upsert(collection_name=collection, points=points, wait=True)
        uploaded += len(points)

        if uploaded % PROGRESS_EVERY < UPSERT_BATCH or uploaded == len(rows):
            elapsed = time.perf_counter() - started
            rate = uploaded / elapsed if elapsed else 0.0
            print(f"  {collection}: {uploaded}/{len(rows)} ({rate:.1f}/s)", flush=True)

    count = client.count(collection_name=collection, exact=True).count
    print(f"{collection}: uploaded {uploaded}, stored {count}", flush=True)
    return count


async def main() -> None:
    parser = argparse.ArgumentParser(description="Embed mini datasets into Qdrant")
    parser.add_argument("--collections", nargs="+", default=list(DEFAULT_COLLECTIONS))
    parser.add_argument("--all", action="store_true", help="Use every default collection")
    parser.add_argument("--limit", type=int, default=None, help="Maximum rows per collection")
    parser.add_argument("--recreate", action="store_true", help="Drop and recreate each collection")
    parser.add_argument("--device", default="cpu", choices=["cpu", "cuda"])
    parser.add_argument("--half", action="store_true", help="Use float16 on CUDA for faster import")
    args = parser.parse_args()

    collections = list(DEFAULT_COLLECTIONS) if args.all else args.collections

    encoder = EmbeddingModel(cache_enabled=False)
    await encoder.load_model()
    if args.device == "cuda":
        import torch

        if not torch.cuda.is_available():
            raise SystemExit("CUDA requested but not available")
        encoder.model.to("cuda")
        if args.half:
            encoder.model.half()
        print("encoder moved to cuda", flush=True)
    print(f"encoder ready on {next(encoder.model.parameters()).device}", flush=True)

    client = QdrantClient(url=settings.qdrant_url, api_key=settings.qdrant_api_key, timeout=120)

    for collection in collections:
        await embed_collection(client, encoder, collection, args.limit, args.recreate)


if __name__ == "__main__":
    asyncio.run(main())
