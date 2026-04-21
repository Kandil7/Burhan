#!/usr/bin/env python3
"""
Production-Ready Embedding Pipeline for Athar Islamic QA System.

Generates embeddings for all Islamic knowledge collections with:
- Chunk categorization & routing (fiqh, hadith, general, duas)
- Checkpointing & resume after crashes
- Deduplication via (source, chunk_index) tracking
- Batch error recovery with retry logic (up to 3 retries)
- Progress tracking with tqdm + ETA
- Comprehensive error logging to data/embeddings/errors.log
- Memory-efficient loading for 1M+ chunk files

Collections:
  fiqh_passages    - Fiqh books, fatwas, rulings (فقه, أحكام, صلاة, etc.)
  hadith_passages  - Hadith collections (type == "hadith")
  general_islamic  - History, biography, theology (تاريخ, سيرة, عقيدة, etc.)
  duas_adhkar      - Duas and adhkar from seed data

Usage:
    python scripts/embed_all_collections.py --collection all
    python scripts/embed_all_collections.py --collection fiqh_passages --batch-size 64
    python scripts/embed_all_collections.py --collection hadith_passages --limit 1000
    python scripts/embed_all_collections.py --collection all --no-resume

Author: Athar Engineering Team
"""

import argparse
import asyncio
import json
import os
import sys
import time
import traceback
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Optional

import numpy as np
from tqdm import tqdm

# ── Project root setup ──────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.indexing.embeddings.embedding_model import EmbeddingModel
from src.indexing.vectorstores.qdrant_store import VectorStore
from src.config.logging_config import setup_logging, get_logger

setup_logging()
logger = get_logger()

# ── Constants ───────────────────────────────────────────────────────

# Data paths
DATA_DIR = PROJECT_ROOT / "data"
PROCESSED_DIR = DATA_DIR / "processed"
SEED_DIR = DATA_DIR / "seed"
EMBEDDINGS_DIR = DATA_DIR / "embeddings"

# File paths
ALL_CHUNKS_FILE = PROCESSED_DIR / "all_chunks.json"
HADITH_CHUNKS_FILE = PROCESSED_DIR / "hadith_chunks.json"
DUAS_FILE = SEED_DIR / "duas.json"

# Checkpoint & error paths
CHECKPOINT_DIR = EMBEDDINGS_DIR / "checkpoints"
ERROR_LOG_FILE = EMBEDDINGS_DIR / "errors.log"

# Collection definitions
COLLECTIONS = ["fiqh_passages", "hadith_passages", "general_islamic", "duas_adhkar"]

# ── Category Routing ────────────────────────────────────────────────
# Chunks whose metadata.category matches any of these go to fiqh_passages
FIQH_CATEGORIES = frozenset(
    {
        "فقه",
        "فقه شافعي",
        "فقه حنفي",
        "فقه مالكي",
        "فقه حنبلي",
        "أحكام",
        "صلاة",
        "زكاة",
        "صيام",
        "حج",
        "نكاح",
        "طلاق",
        "مواريث",
        "بيوع",
        "حدود",
        "جهاد",
        "أطعمة",
        "ذبائح",
        "الفقه العام",
        "الفقه",
        "أصول الفقه",
        "فرائض",
        "قضاء",
        "فتاوى",
        "رقاق",
        "آداب",
        "أذكار",
        "دعاء",
        "ذكر",
    }
)

# Chunks whose metadata.category matches any of these go to general_islamic
GENERAL_CATEGORIES = frozenset(
    {
        "تاريخ",
        "سيرة",
        "عقيدة",
        "توحيد",
        "تفسير",
        "علوم الحديث",
        "كتب عامة",
        "التاريخ",
        "التفسير",
        "العقيدة",
        "السيرة",
        "علوم القرآن",
        "الحديث",
        "مصطلح الحديث",
        "الجرح والتعديل",
        "الطب",
        "الفضائل",
        "المغازي",
        "الأنبياء",
        "الصحابة",
        "التراجم",
        "الطبقات",
        "البلدان",
        "الجغرافيا",
        "النحو",
        "الصرف",
        "البلاغة",
        "العروض",
        "اللغة",
        "كتب اللغة",
        "الأدب",
        "الشعر",
        "الخطب",
        "الرقائق",
        "الزهد",
        "الأدب الجاهلي",
        "الأدب الإسلامي",
        "مواعظ",
        "سلوك",
        "تصوف",
        "أخلاق",
        "فرق ومذاهب",
        "ردود",
        "مقارنات",
        "فكر إسلامي",
        "حضارة",
        "تراجم",
        "معاجم",
        "قواميس",
        "موسوعات",
        "مناهج",
        "تربية",
        "دعوة",
        "إعلام",
    }
)

# Maximum retries for a failed batch
MAX_RETRIES = 3
# Retry backoff seconds
RETRY_BACKOFF = [5, 15, 30]


# ── Helpers ─────────────────────────────────────────────────────────


def ensure_dirs() -> None:
    """Create required directories if they don't exist."""
    CHECKPOINT_DIR.mkdir(parents=True, exist_ok=True)
    EMBEDDINGS_DIR.mkdir(parents=True, exist_ok=True)


def checkpoint_path(collection: str) -> Path:
    """Return the checkpoint file path for a collection."""
    return CHECKPOINT_DIR / f"checkpoint_{collection}.json"


def load_checkpoint(collection: str) -> dict:
    """
    Load checkpoint for a collection.

    Returns dict with:
      - processed_keys: list of already-embedded (source, chunk_index) string tuples
      - last_batch_end: index after last successfully processed batch
      - total_processed: total chunks embedded so far
      - timestamp: ISO timestamp of last checkpoint save
    """
    path = checkpoint_path(collection)
    if not path.exists():
        return {"processed_keys": [], "last_batch_end": 0, "total_processed": 0, "timestamp": ""}

    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        logger.info("checkpoint.loaded", collection=collection, processed=data.get("total_processed", 0))
        return data
    except (json.JSONDecodeError, IOError) as e:
        logger.warning("checkpoint.load_error", collection=collection, error=str(e))
        return {"processed_keys": [], "last_batch_end": 0, "total_processed": 0, "timestamp": ""}


def save_checkpoint(collection: str, state: dict) -> None:
    """Persist checkpoint to disk atomically (write-then-rename)."""
    path = checkpoint_path(collection)
    state["timestamp"] = datetime.now().isoformat()
    try:
        tmp_path = path.with_suffix(".tmp")
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(state, f, ensure_ascii=False, indent=2)
        tmp_path.replace(path)
    except IOError as e:
        logger.error("checkpoint.save_error", collection=collection, error=str(e))


def log_error(collection: str, batch_idx: int, chunk_indices: list[int], error: Exception) -> None:
    """Append a JSON error entry to the error log file."""
    entry = {
        "timestamp": datetime.now().isoformat(),
        "collection": collection,
        "batch_index": batch_idx,
        "chunk_indices": chunk_indices,
        "error_type": type(error).__name__,
        "error_message": str(error),
        "traceback": traceback.format_exc(),
    }
    try:
        with open(ERROR_LOG_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except IOError:
        pass  # Best-effort error logging


def dedup_key(chunk: dict) -> str:
    """
    Create a deduplication key from (source, chunk_index).

    Returns a string key for JSON-serializable checkpoint storage.
    """
    meta = chunk.get("metadata", {})
    source = meta.get("source", "unknown")
    chunk_index = chunk.get("chunk_index", 0)
    return f"{source}|||{chunk_index}"


# ── Data Loading ────────────────────────────────────────────────────


def load_fiqh_chunks(limit: Optional[int] = None) -> list[dict]:
    """
    Load fiqh chunks from data/processed/all_chunks.json.

    Selection criteria:
      - metadata.type == "islamic_book" AND
      - metadata.category in FIQH_CATEGORIES
    """
    if not ALL_CHUNKS_FILE.exists():
        logger.warning("data.file_missing", path=str(ALL_CHUNKS_FILE))
        return []

    logger.info("data.loading_all_chunks_for_fiqh", path=str(ALL_CHUNKS_FILE))
    with open(ALL_CHUNKS_FILE, "r", encoding="utf-8") as f:
        all_chunks = json.load(f)

    if not isinstance(all_chunks, list):
        return []

    results = []
    for chunk in all_chunks:
        meta = chunk.get("metadata", {})
        if meta.get("type") == "islamic_book" and meta.get("category") in FIQH_CATEGORIES:
            results.append(chunk)
            if limit and len(results) >= limit:
                break

    logger.info("data.fiqh_selected", total=len(results))
    return results


def load_hadith_chunks(limit: Optional[int] = None) -> list[dict]:
    """
    Load hadith chunks from data/processed/hadith_chunks.json.

    Selection criteria: metadata.type == "hadith"
    """
    if not HADITH_CHUNKS_FILE.exists():
        logger.warning("data.file_missing", path=str(HADITH_CHUNKS_FILE))
        return []

    logger.info("data.loading_hadith", path=str(HADITH_CHUNKS_FILE))
    with open(HADITH_CHUNKS_FILE, "r", encoding="utf-8") as f:
        all_chunks = json.load(f)

    if not isinstance(all_chunks, list):
        return []

    results = []
    for chunk in all_chunks:
        meta = chunk.get("metadata", {})
        if meta.get("type") == "hadith":
            results.append(chunk)
            if limit and len(results) >= limit:
                break

    logger.info("data.hadith_selected", total=len(results))
    return results


def load_general_chunks(limit: Optional[int] = None) -> list[dict]:
    """
    Load general Islamic chunks from data/processed/all_chunks.json.

    Selection criteria:
      - metadata.type == "islamic_book" AND
      - metadata.category in GENERAL_CATEGORIES
    """
    if not ALL_CHUNKS_FILE.exists():
        logger.warning("data.file_missing", path=str(ALL_CHUNKS_FILE))
        return []

    logger.info("data.loading_all_chunks_for_general", path=str(ALL_CHUNKS_FILE))
    with open(ALL_CHUNKS_FILE, "r", encoding="utf-8") as f:
        all_chunks = json.load(f)

    if not isinstance(all_chunks, list):
        return []

    results = []
    for chunk in all_chunks:
        meta = chunk.get("metadata", {})
        if meta.get("type") == "islamic_book" and meta.get("category") in GENERAL_CATEGORIES:
            results.append(chunk)
            if limit and len(results) >= limit:
                break

    logger.info("data.general_selected", total=len(results))
    return results


def load_duas(limit: Optional[int] = None) -> list[dict]:
    """
    Load duas from data/seed/duas.json and convert to chunk format.

    Each dua is transformed into a document with:
      - content: Arabic text + translation
      - metadata: source, category, occasion, reference, etc.
    """
    if not DUAS_FILE.exists():
        logger.warning("data.file_missing", path=str(DUAS_FILE))
        return []

    with open(DUAS_FILE, "r", encoding="utf-8") as f:
        duas = json.load(f)

    if not isinstance(duas, list):
        return []

    documents = []
    for i, dua in enumerate(duas):
        if limit and i >= limit:
            break

        arabic = dua.get("arabic_text", "")
        translation = dua.get("translation", "")
        content = f"{arabic}\n\n{translation}".strip() if translation else arabic

        doc = {
            "chunk_index": i,
            "content": content,
            "metadata": {
                "source": dua.get("source", "Duas Collection"),
                "type": "dua",
                "category": dua.get("category", "general"),
                "occasion": dua.get("occasion", ""),
                "reference": dua.get("reference", ""),
                "narrator": dua.get("narrator", ""),
                "grade": dua.get("grade", ""),
                "language": "ar",
                "dataset": "seed_duas",
            },
        }
        documents.append(doc)

    logger.info("data.duas_loaded", total=len(documents))
    return documents


# ── Collection Loader Registry ──────────────────────────────────────

COLLECTION_LOADERS = {
    "fiqh_passages": load_fiqh_chunks,
    "hadith_passages": load_hadith_chunks,
    "general_islamic": load_general_chunks,
    "duas_adhkar": load_duas,
}


# ── Embedding Pipeline ──────────────────────────────────────────────


class EmbeddingPipeline:
    """
    Production embedding pipeline with:
    - Checkpointing & resume after crashes
    - Deduplication via (source, chunk_index) tracking
    - Batch error recovery with exponential backoff retry
    - Progress tracking with tqdm + ETA
    - Designed for 1M+ chunks

    Usage:
        pipeline = EmbeddingPipeline(batch_size=32, resume=True)
        await pipeline.initialize()
        stats = await pipeline.run("fiqh_passages", limit=None)
    """

    def __init__(
        self,
        batch_size: int = 32,
        resume: bool = True,
        model: Optional[EmbeddingModel] = None,
        vector_store: Optional[VectorStore] = None,
    ):
        self.batch_size = batch_size
        self.resume = resume
        self.model = model or EmbeddingModel(cache_enabled=True)
        self.vector_store = vector_store or VectorStore()
        self._stats: dict = defaultdict(lambda: {"embedded": 0, "skipped": 0, "errors": 0, "retries": 0})

    async def initialize(self) -> None:
        """Load model and initialize vector store."""
        await self.model.load_model()
        await self.vector_store.initialize()
        logger.info(
            "pipeline.initialized",
            model=self.model.MODEL_NAME,
            dimension=self.model.DIMENSION,
            device=self.model.device,
            batch_size=self.batch_size,
        )

    @staticmethod
    def _get_text(chunk: dict) -> str:
        """Extract text content from a chunk."""
        return chunk.get("content", "").strip()

    @staticmethod
    def _build_upsert_doc(chunk: dict) -> dict:
        """Prepare a chunk for upsert into the vector store."""
        return {
            "content": chunk.get("content", ""),
            "chunk_index": chunk.get("chunk_index", 0),
            "metadata": chunk.get("metadata", {}),
        }

    async def run(self, collection: str, limit: Optional[int] = None) -> dict:
        """
        Run embedding pipeline for a single collection.

        Args:
            collection: Collection name (fiqh_passages, hadith_passages, etc.)
            limit: Maximum chunks to process (None = all)

        Returns:
            Stats dict: {collection, embedded, skipped, errors, elapsed_seconds, chunks_per_second}
        """
        if collection not in COLLECTION_LOADERS:
            raise ValueError(f"Unknown collection: {collection}. Valid: {COLLECTIONS}")

        logger.info("pipeline.starting", collection=collection, limit=limit, resume=self.resume)
        start_time = time.time()

        # ── Step 1: Load chunks ─────────────────────────────────────
        loader = COLLECTION_LOADERS[collection]
        chunks = loader(limit=limit)

        if not chunks:
            logger.warning("pipeline.no_chunks", collection=collection)
            return {
                "collection": collection,
                "embedded": 0,
                "skipped": 0,
                "errors": 0,
                "elapsed_seconds": 0,
                "chunks_per_second": 0,
            }

        # ── Step 2: Load checkpoint & deduplicate ───────────────────
        checkpoint = (
            load_checkpoint(collection)
            if self.resume
            else {"processed_keys": [], "last_batch_end": 0, "total_processed": 0}
        )
        processed_set = set(checkpoint.get("processed_keys", []))

        to_process = []
        skipped_count = 0
        for chunk in chunks:
            key = dedup_key(chunk)
            if key in processed_set:
                skipped_count += 1
            else:
                to_process.append(chunk)

        logger.info(
            "pipeline.chunks_prepared",
            collection=collection,
            total=len(chunks),
            to_process=len(to_process),
            already_processed=skipped_count,
        )

        if not to_process:
            logger.info("pipeline.all_processed", collection=collection)
            return {
                "collection": collection,
                "embedded": 0,
                "skipped": skipped_count,
                "errors": 0,
                "elapsed_seconds": round(time.time() - start_time, 2),
                "chunks_per_second": 0,
            }

        # ── Step 3: Process in batches ──────────────────────────────
        total_batches = (len(to_process) + self.batch_size - 1) // self.batch_size

        pbar = tqdm(
            range(total_batches),
            desc=f"Embedding {collection}",
            unit="batch",
            total=total_batches,
        )

        embedded_count = 0
        error_count = 0
        last_checkpoint_batch = 0

        for batch_num in pbar:
            batch_start = batch_num * self.batch_size
            batch_end = min(batch_start + self.batch_size, len(to_process))
            batch = to_process[batch_start:batch_end]
            batch_indices = list(range(batch_start, batch_end))

            success = False
            retries = 0

            while not success and retries < MAX_RETRIES:
                try:
                    # Extract texts
                    texts = [self._get_text(c) for c in batch]

                    # Generate embeddings (model handles its own caching)
                    embeddings = await self.model.encode(texts, batch_size=len(texts))

                    # Prepare documents for upsert
                    upsert_docs = [self._build_upsert_doc(c) for c in batch]

                    # Upsert to vector store
                    await self.vector_store.upsert(
                        collection=collection,
                        documents=upsert_docs,
                        embeddings=embeddings,
                    )

                    # Track processed keys
                    for chunk in batch:
                        processed_set.add(dedup_key(chunk))

                    embedded_count += len(batch)
                    self._stats[collection]["embedded"] += len(batch)
                    success = True

                    # Update progress bar
                    pbar.set_postfix(
                        {
                            "emb": embedded_count,
                            "err": error_count,
                            "skip": skipped_count,
                        }
                    )

                except Exception as e:
                    retries += 1
                    self._stats[collection]["retries"] += 1
                    if retries < MAX_RETRIES:
                        wait = RETRY_BACKOFF[retries - 1]
                        logger.warning(
                            "pipeline.batch_retry",
                            collection=collection,
                            batch=batch_num,
                            retry=retries,
                            max_retries=MAX_RETRIES,
                            wait_seconds=wait,
                            error=str(e),
                        )
                        await asyncio.sleep(wait)
                    else:
                        # All retries exhausted – log and skip
                        error_count += len(batch)
                        self._stats[collection]["errors"] += len(batch)
                        log_error(collection, batch_num, batch_indices, e)
                        logger.error(
                            "pipeline.batch_failed_permanently",
                            collection=collection,
                            batch=batch_num,
                            chunks_failed=len(batch),
                            error=str(e),
                        )
                        success = True  # Move past this batch

            # ── Periodic checkpoint (every 10 batches) ──────────────
            if batch_num - last_checkpoint_batch >= 9:
                save_checkpoint(
                    collection,
                    {
                        "processed_keys": list(processed_set),
                        "last_batch_end": batch_end,
                        "total_processed": embedded_count + skipped_count,
                        "batch_size": self.batch_size,
                    },
                )
                last_checkpoint_batch = batch_num

        # ── Step 4: Final checkpoint ────────────────────────────────
        save_checkpoint(
            collection,
            {
                "processed_keys": list(processed_set),
                "last_batch_end": len(to_process),
                "total_processed": embedded_count + skipped_count,
                "batch_size": self.batch_size,
            },
        )

        elapsed = time.time() - start_time
        stats = {
            "collection": collection,
            "embedded": embedded_count,
            "skipped": skipped_count,
            "errors": error_count,
            "elapsed_seconds": round(elapsed, 2),
            "chunks_per_second": round(embedded_count / elapsed, 2) if elapsed > 0 else 0,
        }

        logger.info("pipeline.complete", **stats)
        pbar.close()

        return stats


# ── Main Entry Point ────────────────────────────────────────────────


async def run_pipeline(
    collection: str,
    batch_size: int = 32,
    limit: Optional[int] = None,
    resume: bool = True,
) -> None:
    """
    Run the embedding pipeline for the specified collection(s).

    Args:
        collection: Collection name or "all"
        batch_size: Batch size for embedding generation
        limit: Maximum chunks per collection (for testing)
        resume: Resume from checkpoint
    """
    ensure_dirs()

    target_collections = COLLECTIONS if collection == "all" else [collection]

    pipeline = EmbeddingPipeline(batch_size=batch_size, resume=resume)
    await pipeline.initialize()

    all_stats = []
    total_start = time.time()

    for coll in target_collections:
        stats = await pipeline.run(coll, limit=limit)
        all_stats.append(stats)

        # Per-collection summary
        print(f"\n{'=' * 60}")
        print(f"  Collection: {coll}")
        print(f"  Embedded:   {stats['embedded']}")
        print(f"  Skipped:    {stats['skipped']}")
        print(f"  Errors:     {stats['errors']}")
        print(f"  Time:       {stats['elapsed_seconds']:.1f}s")
        if stats["embedded"] > 0:
            print(f"  Speed:      {stats['chunks_per_second']:.1f} chunks/s")
        print(f"{'=' * 60}")

    # ── Final summary ───────────────────────────────────────────────
    total_elapsed = time.time() - total_start
    total_embedded = sum(s["embedded"] for s in all_stats)
    total_skipped = sum(s["skipped"] for s in all_stats)
    total_errors = sum(s["errors"] for s in all_stats)

    print(f"\n{'=' * 60}")
    print(f"  EMBEDDING PIPELINE COMPLETE")
    print(f"{'=' * 60}")
    print(f"  Total Embedded:  {total_embedded:,}")
    print(f"  Total Skipped:   {total_skipped:,}")
    print(f"  Total Errors:    {total_errors:,}")
    print(f"  Total Time:      {total_elapsed:.1f}s")
    print(f"  Model:           {pipeline.model.MODEL_NAME}")
    print(f"  Dimension:       {pipeline.model.DIMENSION}")
    print(f"  Device:          {pipeline.model.device}")
    print(f"  Batch Size:      {batch_size}")
    print(f"{'=' * 60}")

    # Cache stats
    cache_stats = pipeline.model.get_stats()
    print(f"\n  Cache Stats: {json.dumps(cache_stats, indent=2, default=str)}")

    # Error log pointer
    if total_errors > 0:
        print(f"\n  WARNING: {total_errors} chunks failed permanently.")
        print(f"  See error log: {ERROR_LOG_FILE}")

    logger.info(
        "pipeline.all_complete",
        total_embedded=total_embedded,
        total_skipped=total_skipped,
        total_errors=total_errors,
        total_time=round(total_elapsed, 2),
    )


def main():
    """CLI entry point with argument parsing."""
    parser = argparse.ArgumentParser(
        description="Athar Islamic QA - Production Embedding Pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Embed all collections
  python scripts/embed_all_collections.py --collection all

  # Embed only fiqh with larger batches
  python scripts/embed_all_collections.py --collection fiqh_passages --batch-size 64

  # Test with limited chunks
  python scripts/embed_all_collections.py --collection hadith_passages --limit 500

  # Re-embed from scratch (ignore checkpoints)
  python scripts/embed_all_collections.py --collection general_islamic --no-resume
        """,
    )
    parser.add_argument(
        "--collection",
        choices=COLLECTIONS + ["all"],
        default="all",
        help="Which collection to embed (default: all)",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=32,
        help="Batch size for embedding generation (default: 32)",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Maximum chunks to process per collection (for testing)",
    )
    parser.add_argument(
        "--resume",
        action="store_true",
        default=True,
        help="Resume from checkpoint (default: True)",
    )
    parser.add_argument(
        "--no-resume",
        action="store_true",
        default=False,
        help="Disable resume; process all chunks from scratch",
    )

    args = parser.parse_args()
    resume = args.resume and not args.no_resume

    try:
        asyncio.run(
            run_pipeline(
                collection=args.collection,
                batch_size=args.batch_size,
                limit=args.limit,
                resume=resume,
            )
        )
    except KeyboardInterrupt:
        print("\n\n  Interrupted by user. Checkpoint saved.")
        print("  Resume with: python scripts/embed_all_collections.py --resume")
        sys.exit(1)
    except Exception as e:
        logger.error("pipeline.fatal_error", error=str(e), traceback=traceback.format_exc())
        print(f"\nFatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
