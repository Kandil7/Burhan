#!/usr/bin/env python3
"""
Batch Embedding Generation Script for Burhan Islamic QA System.

Generates embeddings for Islamic knowledge collections and upserts them
to Qdrant vector database.

Supported collections:
- fiqh_passages: Fiqh books, fatwas, rulings
- hadith_passages: Hadith collections
- quran_tafsir: Quran and tafsir passages
- aqeedah_passages: Aqeedah and creed texts
- seerah_passages: Prophet biography
- islamic_history_passages: Islamic history
- usul_fiqh_passages: Principles of jurisprudence
- arabic_language_passages: Arabic language texts
- general_islamic_passages: General Islamic knowledge
- duas_adhkar: Duas and adhkar
- all: Process all collections sequentially

Usage:
    python scripts/data/generate_embeddings.py --collection all
    python scripts/data/generate_embeddings.py --collection fiqh_passages --limit 1000
    python scripts/data/generate_embeddings.py --collection hadith_passages --batch-size 64
    python scripts/data/generate_embeddings.py --collection all --no-resume

Author: Burhan Engineering Team
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Optional

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from scripts.utils import (
    get_project_root,
    get_data_dir,
    setup_script_logger,
    ProgressBar,
    add_project_root_to_path,
    format_duration,
)

add_project_root_to_path()

from src.indexing.embeddings.embedding_model import EmbeddingModel
from src.indexing.vectorstores.qdrant_store import VectorStore
from src.config.logging_config import setup_logging

setup_logging()
logger = setup_script_logger("generate-embeddings")

# ── Configuration ────────────────────────────────────────────────────────

PROJECT_ROOT = get_project_root()
PROCESSED_DIR = get_data_dir("processed")
SEED_DIR = get_data_dir("seed")

# Category to Collection Mapping (All 40 Shamela categories)
CATEGORY_COLLECTION_MAP: dict[str, str] = {
    # Hadith-related (5 categories -> hadith_passages)
    "كتب السنة": "hadith_passages",
    "شروح الحديث": "hadith_passages",
    "علوم الحديث": "hadith_passages",
    "التخريج والأطراف": "hadith_passages",
    "العلل والسؤالات الحديثية": "hadith_passages",
    # Quran/Tafsir-related (3 categories -> quran_tafsir)
    "التفسير": "quran_tafsir",
    "علوم القرآن وأصول التفسير": "quran_tafsir",
    "التجويد والقراءات": "quran_tafsir",
    # Fiqh-related (9 categories -> fiqh_passages)
    "الفقه العام": "fiqh_passages",
    "مسائل فقهية": "fiqh_passages",
    "الفقه الحنفي": "fiqh_passages",
    "الفقه المالكي": "fiqh_passages",
    "الفقه الشافعي": "fiqh_passages",
    "الفقه الحنبلي": "fiqh_passages",
    "السياسة الشرعية والقضاء": "fiqh_passages",
    "الفرائض والوصايا": "fiqh_passages",
    "الفتاوى": "fiqh_passages",
    # Usul al-Fiqh (2 categories -> usul_fiqh_passages)
    "أصول الفقه": "usul_fiqh_passages",
    "علوم الفقه والقواعد الفقهية": "usul_fiqh_passages",
    # Aqeedah (2 categories -> aqeedah_passages)
    "العقيدة": "aqeedah_passages",
    "الفرق والردود": "aqeedah_passages",
    # Seerah/Biography (3 categories -> seerah_passages)
    "السيرة النبوية": "seerah_passages",
    "التراجم والطبقات": "seerah_passages",
    "الأنساب": "seerah_passages",
    # History (2 categories -> islamic_history_passages)
    "التاريخ": "islamic_history_passages",
    "البلدان والرحلات": "islamic_history_passages",
    # Arabic Language (7 categories -> arabic_language_passages)
    "كتب اللغة": "arabic_language_passages",
    "النحو والصرف": "arabic_language_passages",
    "الغريب والمعاجم": "arabic_language_passages",
    "البلاغة": "arabic_language_passages",
    "الأدب": "arabic_language_passages",
    "الدواوين الشعرية": "arabic_language_passages",
    "العروض والقوافي": "arabic_language_passages",
    # General Islamic (8 categories -> general_islamic_passages)
    "كتب عامة": "general_islamic_passages",
    "الرقائق والآداب والأذكار": "general_islamic_passages",
    "الجوامع": "general_islamic_passages",
    "فهارس الكتب والأدلة": "general_islamic_passages",
    "المنطق": "general_islamic_passages",
    "الطب": "general_islamic_passages",
    "علوم أخرى": "general_islamic_passages",
    "#": "general_islamic_passages",
}

# All available collections
ALL_COLLECTIONS = [
    "fiqh_passages",
    "hadith_passages",
    "quran_tafsir",
    "aqeedah_passages",
    "seerah_passages",
    "islamic_history_passages",
    "usul_fiqh_passages",
    "arabic_language_passages",
    "general_islamic_passages",
    "duas_adhkar",
]


# ── Routing ──────────────────────────────────────────────────────────────


def route_chunk_to_collection(chunk: dict) -> str:
    """
    Route a chunk to the appropriate collection based on metadata.

    Args:
        chunk: Document chunk with metadata.

    Returns:
        Collection name string.
    """
    metadata = chunk.get("metadata", {})
    chunk_type = metadata.get("type", "")
    category = metadata.get("category", "")

    if chunk_type == "hadith":
        return "hadith_passages"
    if chunk_type == "dua":
        return "duas_adhkar"
    if chunk_type == "islamic_book":
        return CATEGORY_COLLECTION_MAP.get(category, "general_islamic_passages")
    return "general_islamic_passages"


# ── Document Loading ─────────────────────────────────────────────────────


def load_documents(collection: str, limit: Optional[int] = None) -> list[dict]:
    """
    Load documents for a specific collection from processed data files.

    Args:
        collection: Collection name.
        limit: Maximum number of documents to load.

    Returns:
        List of document dicts.
    """
    documents: list[dict] = []

    if collection == "fiqh_passages":
        all_chunks_file = PROCESSED_DIR / "all_chunks.json"
        if all_chunks_file.exists():
            logger.info("loading_all_chunks", path=str(all_chunks_file))
            with open(all_chunks_file, "r", encoding="utf-8") as f:
                all_chunks = json.load(f)
                documents = [c for c in all_chunks if c.get("metadata", {}).get("type") == "islamic_book"]
                logger.info("filtered_chunks", total=len(all_chunks), fiqh=len(documents))

    elif collection == "hadith_passages":
        hadith_file = PROCESSED_DIR / "hadith_chunks.json"
        if hadith_file.exists():
            with open(hadith_file, "r", encoding="utf-8") as f:
                documents = json.load(f)
                logger.info("hadith_loaded", count=len(documents))
        else:
            logger.warning("hadith_file_not_found", path=str(hadith_file))

    elif collection in ("general_islamic", "general_islamic_passages"):
        all_chunks_file = PROCESSED_DIR / "all_chunks.json"
        if all_chunks_file.exists():
            with open(all_chunks_file, "r", encoding="utf-8") as f:
                all_chunks = json.load(f)
                general_categories = [
                    "كتب عامة",
                    "الرقائق والآداب والأذكار",
                    "الجوامع",
                    "فهارس الكتب والأدلة",
                    "المنطق",
                    "الطب",
                    "علوم أخرى",
                    "#",
                ]
                documents = [
                    c
                    for c in all_chunks
                    if c.get("metadata", {}).get("type") == "islamic_book"
                    and c.get("metadata", {}).get("category") in general_categories
                ]
                logger.info("general_loaded", total=len(all_chunks), general=len(documents))

    elif collection == "duas_adhkar":
        duas_file = SEED_DIR / "duas.json"
        if duas_file.exists():
            with open(duas_file, "r", encoding="utf-8") as f:
                duas = json.load(f)
                documents = [
                    {
                        "chunk_index": i,
                        "content": (
                            f"الدعاء: {dua.get('arabic_text', '')}\n\n"
                            f"الترجمة: {dua.get('translation', '')}\n\n"
                            f"المناسبة: {dua.get('occasion', '')}\n\n"
                            f"المصدر: {dua.get('source', '')}"
                        ),
                        "metadata": {
                            "type": "dua",
                            "category": dua.get("category", "general"),
                            "occasion": dua.get("occasion", ""),
                            "source": dua.get("source", ""),
                            "id": dua.get("id", i),
                        },
                    }
                    for i, dua in enumerate(duas)
                ]
                logger.info("duas_loaded", count=len(documents))
        else:
            logger.warning("duas_file_not_found", path=str(duas_file))

    elif collection == "all":
        for coll in ALL_COLLECTIONS:
            coll_docs = load_documents(coll, limit)
            documents.extend(coll_docs)
            if limit and len(documents) >= limit:
                documents = documents[:limit]
                break

    # Apply limit
    if limit and len(documents) > limit:
        documents = documents[:limit]

    logger.info("documents_loaded", collection=collection, count=len(documents))
    return documents


# ── Embedding Pipeline ───────────────────────────────────────────────────


async def generate_embeddings(
    collection: str,
    limit: Optional[int] = None,
    batch_size: int = 32,
) -> dict:
    """
    Generate embeddings for a collection and upsert to Qdrant.

    Args:
        collection: Collection name.
        limit: Maximum documents to process.
        batch_size: Batch size for embedding generation.

    Returns:
        Stats dict with embedded count, errors, and timing.
    """
    import time

    start_time = time.time()
    logger.info("generating_embeddings", collection=collection)

    # Load documents
    documents = load_documents(collection, limit)

    if not documents:
        logger.warning("no_documents", collection=collection)
        return {"collection": collection, "embedded": 0, "errors": 0, "elapsed_seconds": 0}

    # Initialize model and vector store
    print(f"  Loading embedding model...")
    model = EmbeddingModel()
    await model.load_model()
    print(f"  ✓ Model: {model.MODEL_NAME} ({model.DIMENSION}d, {model.device})")

    print(f"  Connecting to Qdrant...")
    vector_store = VectorStore()
    await vector_store.initialize()
    print(f"  ✓ Connected\n")

    # Process in batches with progress bar
    total_embedded = 0
    errors = 0
    total_batches = (len(documents) + batch_size - 1) // batch_size

    with ProgressBar(total=total_batches, desc=f"Embedding {collection}", unit="batch") as bar:
        for i in range(0, len(documents), batch_size):
            batch = documents[i : i + batch_size]

            try:
                texts = [doc.get("content", "") for doc in batch]

                # Generate embeddings
                embeddings = await model.encode(texts, batch_size=len(texts))

                # Upsert to Qdrant
                await vector_store.upsert(
                    collection=collection,
                    documents=batch,
                    embeddings=embeddings,
                )

                total_embedded += len(batch)

            except Exception as e:
                logger.error("batch_error", batch=i // batch_size, error=str(e))
                errors += len(batch)

            bar.update(1)

    elapsed = time.time() - start_time

    stats = {
        "collection": collection,
        "embedded": total_embedded,
        "errors": errors,
        "elapsed_seconds": round(elapsed, 2),
    }

    logger.info("embedding_complete", **stats)
    return stats


# ── Main ─────────────────────────────────────────────────────────────────


def main():
    """Main entry point with argument parsing."""
    parser = argparse.ArgumentParser(
        description="Generate Embeddings for Burhan collections",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/data/generate_embeddings.py --collection all
  python scripts/data/generate_embeddings.py --collection fiqh_passages --limit 1000
  python scripts/data/generate_embeddings.py --collection hadith_passages --batch-size 64
        """,
    )
    parser.add_argument(
        "--collection",
        choices=ALL_COLLECTIONS + ["all"],
        default="all",
        help="Collection to embed (default: all)",
    )
    parser.add_argument("--limit", type=int, default=None, help="Limit number of documents to process")
    parser.add_argument("--batch-size", type=int, default=32, help="Batch size for embedding generation")

    args = parser.parse_args()

    print(f"\n{'=' * 70}")
    print("  Burhan EMBEDDING GENERATOR")
    print(f"{'=' * 70}")
    print(f"  Collection: {args.collection}")
    if args.limit:
        print(f"  Limit:      {args.limit}")
    print(f"  Batch Size: {args.batch_size}")
    print(f"{'=' * 70}\n")

    import asyncio

    try:
        stats = asyncio.run(generate_embeddings(args.collection, args.limit, args.batch_size))

        # Print summary
        print(f"\n{'=' * 70}")
        print("  EMBEDDING GENERATION COMPLETE")
        print(f"{'=' * 70}")
        print(f"  Collection:  {stats['collection']}")
        print(f"  Documents:   {stats['embedded']}")
        print(f"  Errors:      {stats['errors']}")
        print(f"  Time:        {format_duration(stats['elapsed_seconds'])}")
        print(f"{'=' * 70}\n")

    except KeyboardInterrupt:
        print("\n\n  Interrupted by user.")
        sys.exit(1)
    except Exception as e:
        logger.error("fatal_error", error=str(e), exc_info=True)
        print(f"\nFatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
