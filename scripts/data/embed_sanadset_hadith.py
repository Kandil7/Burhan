#!/usr/bin/env python3
"""
Sanadset Hadith Embedding Pipeline.

Processes all 650K+ hadith from Sanadset CSV and embeds them to Qdrant
with robust checkpointing and resume support.

Features:
- Checkpointing every 1000 hadith for crash recovery
- Resume from last checkpoint with --resume (default)
- Process from scratch with --no-resume
- Configurable batch size and limit for testing
- Progress bar with ETA
- Error tracking and logging

Usage:
    # Embed all hadith (with resume support)
    python scripts/data/embed_sanadset_hadith.py

    # Embed first N hadith (for testing)
    python scripts/data/embed_sanadset_hadith.py --limit 1000

    # Embed with custom batch size
    python scripts/data/embed_sanadset_hadith.py --batch-size 64

    # Start from scratch (ignore checkpoint)
    python scripts/data/embed_sanadset_hadith.py --no-resume

Author: Athar Engineering Team
"""

import argparse
import asyncio
import csv
import json
import re
import sys
import time
from pathlib import Path
from typing import Optional

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from scripts.utils import (
    get_project_root,
    get_data_dir,
    get_datasets_dir,
    setup_script_logger,
    ProgressBar,
    add_project_root_to_path,
    format_size,
    format_duration,
    ensure_dir,
)

add_project_root_to_path()

from src.indexing.embeddings.embedding_model import EmbeddingModel
from src.indexing.vectorstores.qdrant_store import VectorStore

logger = setup_script_logger("embed-sanadset")

# ── Configuration ────────────────────────────────────────────────────────

PROJECT_ROOT = get_project_root()
CHECKPOINT_FILE = get_data_dir("embeddings") / "sanadset_checkpoint.json"
SANADSET_CSV = (
    get_datasets_dir()
    / "Sanadset 368K Data on Hadith Narrators"
    / "Sanadset 368K Data on Hadith Narrators"
    / "sanadset.csv"
)
COLLECTION_NAME = "hadith_passages"
CHECKPOINT_INTERVAL = 1000  # Save checkpoint every N hadith


# ── Checkpoint Management ────────────────────────────────────────────────


def save_checkpoint(processed: int, errors: int) -> None:
    """
    Save processing checkpoint to disk.

    Args:
        processed: Number of successfully processed hadith.
        errors: Number of errors encountered.
    """
    ensure_dir(CHECKPOINT_FILE.parent)

    data = {
        "processed": processed,
        "errors": errors,
        "timestamp": time.time(),
        "collection": COLLECTION_NAME,
    }

    # Atomic write (write to temp, then rename)
    tmp_path = CHECKPOINT_FILE.with_suffix(".tmp")
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    tmp_path.replace(CHECKPOINT_FILE)

    logger.info("checkpoint_saved", processed=processed, errors=errors)


def load_checkpoint() -> dict:
    """
    Load last processing checkpoint.

    Returns:
        Dict with 'processed' and 'errors' counts, or defaults.
    """
    if not CHECKPOINT_FILE.exists():
        return {"processed": 0, "errors": 0}

    try:
        with open(CHECKPOINT_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        logger.info(
            "checkpoint_loaded",
            processed=data.get("processed", 0),
            errors=data.get("errors", 0),
        )
        return data
    except (json.JSONDecodeError, IOError) as e:
        logger.warning("checkpoint_load_error", error=str(e))
        return {"processed": 0, "errors": 0}


def clear_checkpoint() -> None:
    """Delete checkpoint file to force fresh start."""
    if CHECKPOINT_FILE.exists():
        CHECKPOINT_FILE.unlink()
        logger.info("checkpoint_cleared")


# ── Hadith Processing ────────────────────────────────────────────────────


def count_csv_rows(csv_path: Path) -> int:
    """
    Count total rows in CSV file (excluding header).

    Args:
        csv_path: Path to CSV file.

    Returns:
        Number of data rows.
    """
    count = 0
    with open(csv_path, "r", encoding="utf-8") as f:
        # Skip header
        next(f, None)
        for _ in f:
            count += 1
    return count


def clean_sanad(raw_sanad: str) -> str:
    """
    Clean sanad text by removing XML-like tags.

    Args:
        raw_sanad: Raw sanad string with potential tags.

    Returns:
        Cleaned sanad string.
    """
    return re.sub(r"<[^>]+>", "", raw_sanad).strip()


def build_hadith_doc(row: dict, chunk_index: int) -> dict:
    """
    Build a hadith document dict from a CSV row.

    Args:
        row: CSV row as dict.
        chunk_index: Sequential index for the document.

    Returns:
        Document dict ready for embedding.
    """
    sanad_clean = clean_sanad(row.get("Sanad", ""))
    matn = row.get("Matn", "").strip()
    book = row.get("Book", "").strip()

    # Build content: matn + sanad + book
    content_parts = []
    if matn:
        content_parts.append(matn)
    if sanad_clean and sanad_clean != "No SANAD":
        content_parts.append(sanad_clean)
    if book:
        content_parts.append(book)

    content = " | ".join(content_parts)

    return {
        "chunk_index": chunk_index,
        "content": content[:5000],  # Truncate very long content
        "metadata": {
            "type": "hadith",
            "book": book,
            "num_hadith": row.get("Num_hadith", ""),
            "matn": matn[:2000],
            "sanad": sanad_clean[:1000],
            "sanad_length": row.get("Sanad_Length", ""),
            "dataset": "sanadset_368k",
            "language": "ar",
        },
    }


# ── Main Pipeline ────────────────────────────────────────────────────────


async def embed_sanadset(
    limit: Optional[int] = None,
    batch_size: int = 32,
    resume: bool = True,
) -> dict:
    """
    Embed Sanadset hadith to Qdrant with checkpointing.

    Args:
        limit: Max hadith to process (None = all).
        batch_size: Batch size for embedding.
        resume: Resume from checkpoint.

    Returns:
        Stats dict with processing results.
    """
    start_time = time.time()

    # Verify CSV exists
    if not SANADSET_CSV.exists():
        logger.error("csv_not_found", path=str(SANADSET_CSV))
        print(f"  ✗ Sanadset CSV not found: {SANADSET_CSV}")
        return {"processed": 0, "errors": 0, "elapsed_seconds": 0}

    # Count total rows
    print(f"  Counting hadith records...")
    total_rows = count_csv_rows(SANADSET_CSV)
    actual_limit = min(limit, total_rows) if limit else total_rows
    print(f"  ✓ Total hadith: {total_rows:,}")
    if limit:
        print(f"  ✓ Processing limit: {limit:,}")

    # Load checkpoint
    checkpoint = {"processed": 0, "errors": 0}
    if resume:
        checkpoint = load_checkpoint()
        if checkpoint["processed"] > 0:
            print(f"  ✓ Resuming from checkpoint: {checkpoint['processed']:,} already processed")

    start_from = checkpoint["processed"]
    error_count = checkpoint["errors"]

    # Calculate remaining
    remaining = actual_limit - start_from
    if remaining <= 0:
        print(f"  ✓ All {actual_limit:,} hadith already processed!")
        return {"processed": start_from, "errors": error_count, "elapsed_seconds": 0}

    # Initialize components
    print(f"\n  Loading embedding model...")
    embedding_model = EmbeddingModel()
    await embedding_model.load_model()
    print(f"  ✓ Model: {embedding_model.MODEL_NAME} ({embedding_model.DIMENSION}d, {embedding_model.device})")

    print(f"  Connecting to Qdrant...")
    vector_store = VectorStore()
    await vector_store.initialize()
    print(f"  ✓ Connected\n")

    # Ensure collection exists
    await vector_store.ensure_collection(COLLECTION_NAME, dimension=embedding_model.DIMENSION)

    # Process CSV
    processed = start_from
    batch_docs: list[dict] = []
    batch_texts: list[str] = []

    with ProgressBar(total=remaining, desc="Embedding hadith", unit="hadith") as bar:
        with open(SANADSET_CSV, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)

            # Skip already processed rows
            for _ in range(start_from):
                try:
                    next(reader)
                except StopIteration:
                    break

            for row in reader:
                if processed >= actual_limit:
                    break

                try:
                    doc = build_hadith_doc(row, processed)
                    batch_docs.append(doc)
                    batch_texts.append(doc["content"][:2000])  # Limit for embedding

                    # Process batch
                    if len(batch_docs) >= batch_size:
                        embeddings = await embedding_model.encode(batch_texts)
                        count = await vector_store.upsert(COLLECTION_NAME, batch_docs, embeddings)
                        processed += count
                        bar.update(count)

                        # Save checkpoint periodically
                        if processed % CHECKPOINT_INTERVAL == 0:
                            save_checkpoint(processed, error_count)

                        batch_docs = []
                        batch_texts = []

                except Exception as e:
                    error_count += 1
                    if error_count % 100 == 0:
                        logger.warning("processing_errors", count=error_count, last_error=str(e))

            # Process remaining batch
            if batch_docs:
                try:
                    embeddings = await embedding_model.encode(batch_texts)
                    count = await vector_store.upsert(COLLECTION_NAME, batch_docs, embeddings)
                    processed += count
                    bar.update(count)
                except Exception as e:
                    error_count += len(batch_docs)
                    logger.error("final_batch_error", error=str(e))

    # Final checkpoint
    save_checkpoint(processed, error_count)

    # Get collection stats
    try:
        collection_stats = vector_store.get_collection_stats(COLLECTION_NAME)
        total_in_collection = collection_stats.get("vectors_count", "unknown")
    except Exception:
        total_in_collection = "unknown"

    elapsed = time.time() - start_time

    stats = {
        "processed": processed,
        "errors": error_count,
        "total_in_collection": total_in_collection,
        "elapsed_seconds": round(elapsed, 2),
    }

    logger.info("embedding_complete", **stats)
    return stats


# ── Main ─────────────────────────────────────────────────────────────────


def main():
    """CLI entry point with argument parsing."""
    parser = argparse.ArgumentParser(
        description="Embed Sanadset Hadith to Qdrant",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/data/embed_sanadset_hadith.py
  python scripts/data/embed_sanadset_hadith.py --limit 1000
  python scripts/data/embed_sanadset_hadith.py --batch-size 64
  python scripts/data/embed_sanadset_hadith.py --no-resume
        """,
    )
    parser.add_argument("--limit", type=int, default=None, help="Max hadith to process")
    parser.add_argument("--batch-size", type=int, default=32, help="Batch size (default: 32)")
    parser.add_argument("--no-resume", action="store_true", help="Don't resume from checkpoint")
    parser.add_argument("--clear-checkpoint", action="store_true", help="Clear checkpoint and start fresh")

    args = parser.parse_args()

    print(f"\n{'=' * 70}")
    print("  ATHAR SANADSET HADITH EMBEDDING PIPELINE")
    print(f"{'=' * 70}")
    print(f"  CSV:      {SANADSET_CSV}")
    print(f"  Batch:    {args.batch_size}")
    print(f"  Resume:   {'No' if args.no_resume else 'Yes'}")
    if args.limit:
        print(f"  Limit:    {args.limit:,}")
    print(f"{'=' * 70}\n")

    # Clear checkpoint if requested
    if args.clear_checkpoint:
        clear_checkpoint()
        print("  ✓ Checkpoint cleared\n")

    try:
        stats = asyncio.run(
            embed_sanadset(
                limit=args.limit,
                batch_size=args.batch_size,
                resume=not args.no_resume,
            )
        )

        # Print summary
        print(f"\n{'=' * 70}")
        print("  SANADSET EMBEDDING COMPLETE")
        print(f"{'=' * 70}")
        print(f"  Processed:       {stats['processed']:,}")
        print(f"  Errors:          {stats['errors']}")
        print(f"  In Collection:   {stats['total_in_collection']}")
        print(f"  Time:            {format_duration(stats['elapsed_seconds'])}")
        print(f"  Checkpoint:      {CHECKPOINT_FILE}")
        print(f"{'=' * 70}\n")

    except KeyboardInterrupt:
        print("\n\n  Interrupted by user. Checkpoint saved.")
        print("  Resume with: python scripts/data/embed_sanadset_hadith.py")
        sys.exit(1)
    except Exception as e:
        logger.error("fatal_error", error=str(e), exc_info=True)
        print(f"\nFatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
