#!/usr/bin/env python3
"""Embed the dua seed files into the ``duas_adhkar`` collection.

The dua tool answers from ``data/seed/duas.json`` and
``data/seed/azkar_imported.json``. Those files are also the only content behind
the registered ``duas_adhkar`` collection, which otherwise stays empty and
returns nothing from ``/api/v1/search/simple?collection=duas_adhkar``.

Payload fields follow the other collections (``book_title``, ``page_number``,
``content``) so the citation builder can render a dua the same way it renders a
book page.

Usage:
    python scripts/data/embed_duas_to_qdrant.py
    python scripts/data/embed_duas_to_qdrant.py --device cuda --half
    python scripts/data/embed_duas_to_qdrant.py --recreate
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams

from src.config.constants import CollectionNames
from src.config.settings import settings
from src.indexing.embeddings.embedding_model import EmbeddingModel

SEED_DIR = PROJECT_ROOT / "data" / "seed"
DUAS_PATH = SEED_DIR / "duas.json"
AZKAR_PATH = SEED_DIR / "azkar_imported.json"
COLLECTION = CollectionNames.DUA
VECTOR_SIZE = 1024
UPSERT_BATCH = 64

# (path, book title, content type)
DATASETS: tuple[tuple[Path, str], ...] = (
    (DUAS_PATH, "حصن المسلم"),
    (AZKAR_PATH, "الأذكار"),
)


def load_entries() -> list[dict[str, Any]]:
    """Build embeddable rows from both seed files."""
    rows: list[dict[str, Any]] = []

    for path, book_title in DATASETS:
        if not path.exists():
            print(f"skipping missing seed file: {path}", flush=True)
            continue

        with path.open(encoding="utf-8") as handle:
            entries = json.load(handle)
        if not isinstance(entries, list):
            raise SystemExit(f"unexpected payload in {path}: expected a list")

        for entry in entries:
            arabic_text = str(entry.get("arabic_text") or "").strip()
            if not arabic_text:
                continue

            translation = str(entry.get("translation") or "").strip()
            reference = str(entry.get("reference") or "").strip()
            content_parts = [arabic_text]
            if translation:
                content_parts.append(translation)
            if reference:
                content_parts.append(f"({reference})")

            rows.append(
                {
                    "content": "\n".join(content_parts),
                    "content_type": "dua",
                    "book_title": book_title,
                    "page_number": int(entry.get("id") or len(rows) + 1),
                    "section_title": str(entry.get("occasion") or "general"),
                    "category": str(entry.get("category_ar") or entry.get("category") or "general"),
                    "reference": reference,
                    "hadith_source": str(entry.get("source") or ""),
                    "grade": str(entry.get("grade") or ""),
                    "repeat_count": int(entry.get("repeat_count") or 1),
                    "collection": COLLECTION,
                }
            )

    return rows


def ensure_collection(client: QdrantClient, recreate: bool) -> None:
    exists = client.collection_exists(COLLECTION)
    if exists and not recreate:
        return
    if exists:
        client.delete_collection(COLLECTION)
    client.create_collection(
        collection_name=COLLECTION,
        vectors_config=VectorParams(size=VECTOR_SIZE, distance=Distance.COSINE, on_disk=True),
    )


async def embed(rows: list[dict[str, Any]], device: str, half: bool, recreate: bool) -> int:
    encoder = EmbeddingModel(cache_enabled=False)
    await encoder.load_model()

    if device == "cuda":
        import torch

        if not torch.cuda.is_available():
            raise SystemExit("CUDA requested but not available")
        encoder.model.to("cuda")
        if half:
            encoder.model.half()

    client = QdrantClient(url=settings.qdrant_url, api_key=settings.qdrant_api_key, timeout=120)
    ensure_collection(client, recreate)

    uploaded = 0
    for start in range(0, len(rows), UPSERT_BATCH):
        batch = rows[start : start + UPSERT_BATCH]
        vectors = await encoder.encode([row["content"] for row in batch], batch_size=UPSERT_BATCH)
        points = [
            PointStruct(
                id=start + offset,
                vector=vector.tolist(),
                payload=row,
            )
            for offset, (row, vector) in enumerate(zip(batch, vectors, strict=True))
        ]
        client.upsert(collection_name=COLLECTION, points=points, wait=True)
        uploaded += len(points)
        print(f"  {COLLECTION}: {uploaded}/{len(rows)}", flush=True)

    stored = client.count(collection_name=COLLECTION, exact=True).count
    print(f"{COLLECTION}: uploaded {uploaded}, stored {stored}", flush=True)
    return stored


async def main() -> None:
    parser = argparse.ArgumentParser(description="Embed dua seed files into Qdrant")
    parser.add_argument("--device", default="cpu", choices=["cpu", "cuda"])
    parser.add_argument("--half", action="store_true", help="Use float16 on CUDA")
    parser.add_argument("--recreate", action="store_true", help="Drop and recreate the collection")
    args = parser.parse_args()

    rows = load_entries()
    if not rows:
        raise SystemExit("No dua entries found; run scripts/ingestion/import_azkar_db.py first.")

    print(f"loaded {len(rows)} entries", flush=True)
    await embed(rows, device=args.device, half=args.half, recreate=args.recreate)


if __name__ == "__main__":
    asyncio.run(main())
