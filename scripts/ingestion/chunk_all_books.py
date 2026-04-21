#!/usr/bin/env python3
"""
Batch chunking script for all Shamela books.

Processes all 8,424+ books from datasets/data/extracted_books/,
applies hierarchical chunking, and saves to JSONL format.

Features:
- Progress bars with real-time statistics
- Error handling with per-book error logging
- Resume from checkpoint (skips already-processed books)
- Statistics report at completion
- Memory-efficient streaming output

Usage:
    python scripts/chunk_all_books.py
    python scripts/chunk_all_books.py --resume
    python scripts/chunk_all_books.py --limit 100
    python scripts/chunk_all_books.py --book-id 27107

Output:
    data/processed/hierarchical_chunks.jsonl
    data/processed/chunking_stats.json
    data/processed/.chunking_checkpoint.json
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path
from typing import Any

# Add project root to path for src imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.utils import (
    ProgressBar,
    ensure_dir,
    format_duration,
    format_size,
    get_data_dir,
    get_datasets_dir,
    get_project_root,
    get_script_logger,
    progress_iter,
)

# ── Configuration ────────────────────────────────────────────────────────

BOOKS_JSON_PATH = get_datasets_dir("data/metadata/books.json")
EXTRACTED_DIR = get_datasets_dir("data/extracted_books")
OUTPUT_FILE = get_data_dir("processed/hierarchical_chunks.jsonl")
STATS_FILE = get_data_dir("processed/chunking_stats.json")
CHECKPOINT_FILE = get_data_dir("processed/.chunking_checkpoint.json")

logger = get_script_logger("chunk-all-books")


# ── Checkpoint Management ────────────────────────────────────────────────


def load_checkpoint() -> dict[str, Any]:
    """Load checkpoint file with already-processed book IDs."""
    if CHECKPOINT_FILE.exists():
        with open(CHECKPOINT_FILE, encoding="utf-8") as f:
            return json.load(f)
    return {"processed_books": [], "total_chunks": 0, "errors": []}


def save_checkpoint(checkpoint: dict[str, Any]) -> None:
    """Save checkpoint atomically."""
    tmp_path = CHECKPOINT_FILE.with_suffix(".tmp")
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(checkpoint, f, ensure_ascii=False, indent=2)
    tmp_path.replace(CHECKPOINT_FILE)


# ── Metadata Loading ─────────────────────────────────────────────────────


def load_books_metadata() -> tuple[list[dict], dict[int, dict]]:
    """
    Load books.json and return list of books + ID-indexed dict.

    Returns:
        Tuple of (books_list, books_by_id_dict).
    """
    logger.info(f"Loading books metadata from {BOOKS_JSON_PATH}")
    with open(BOOKS_JSON_PATH, encoding="utf-8") as f:
        data = json.load(f)

    books = data.get("books", [])
    books_by_id = {b["id"]: b for b in books}
    logger.info(f"Loaded {len(books)} books")
    return books, books_by_id


# ── Chunking Pipeline ────────────────────────────────────────────────────


def chunk_book_file(
    book_entry: dict[str, Any],
    chunker: Any,
) -> tuple[list[dict], int]:
    """
    Chunk a single book file.

    Args:
        book_entry: Book metadata dict from books.json.
        chunker: HierarchicalChunker instance.

    Returns:
        Tuple of (chunks_as_dicts, file_size_bytes).
    """
    from src.indexing.chunking.hierarchical_chunker import BookMetadata

    book_id = book_entry["id"]
    file_name = book_entry.get("file")
    extracted = book_entry.get("extracted", False)

    if not extracted or not file_name:
        return [], 0

    file_path = EXTRACTED_DIR / file_name
    if not file_path.exists():
        logger.warning(f"Book file not found: {file_path} (ID={book_id})")
        return [], 0

    file_size = file_path.stat().st_size

    # Read file
    with open(file_path, encoding="utf-8", errors="replace") as f:
        text = f.read()

    if not text.strip():
        return [], file_size

    # Build metadata
    metadata = BookMetadata.from_books_json_entry(book_entry)

    # Chunk
    chunks = chunker.chunk_book(text, metadata)

    return [c.to_dict() for c in chunks], file_size


def run_chunking(
    resume: bool = True,
    limit: int = 0,
    book_ids: list[int] | None = None,
) -> dict[str, Any]:
    """
    Run the full chunking pipeline.

    Args:
        resume: Whether to resume from checkpoint.
        limit: Maximum number of books to process (0 = no limit).
        book_ids: Specific book IDs to process (None = all).

    Returns:
        Statistics dict.
    """
    start_time = time.time()

    # Load metadata
    books, books_by_id = load_books_metadata()

    # Filter books
    if book_ids:
        books_to_process = [books_by_id[bid] for bid in book_ids if bid in books_by_id]
        logger.info(f"Processing {len(books_to_process)} specific books")
    else:
        books_to_process = books

    # Load checkpoint
    checkpoint = {"processed_books": [], "total_chunks": 0, "errors": []}
    if resume:
        checkpoint = load_checkpoint()
        processed_ids = set(checkpoint.get("processed_books", []))
        books_to_process = [b for b in books_to_process if b["id"] not in processed_ids]
        logger.info(f"Resuming: {len(processed_ids)} books already processed, {len(books_to_process)} remaining")

    # Apply limit
    if limit > 0:
        books_to_process = books_to_process[:limit]
        logger.info(f"Limited to {limit} books")

    if not books_to_process:
        logger.info("No books to process")
        return checkpoint

    # Ensure output directory exists
    ensure_dir(OUTPUT_FILE.parent)

    # Initialize chunker
    from src.indexing.chunking.hierarchical_chunker import HierarchicalChunker

    chunker = HierarchicalChunker()

    # Statistics
    stats = {
        "total_books_queued": len(books_to_process),
        "books_processed": 0,
        "books_skipped": 0,
        "books_errored": 0,
        "total_chunks": checkpoint.get("total_chunks", 0),
        "total_bytes_processed": 0,
        "category_stats": {},
        "chunk_type_stats": {},
        "size_distribution": {"tiny": 0, "small": 0, "medium": 0, "large": 0, "xlarge": 0},
        "errors": checkpoint.get("errors", []),
    }

    # Open output file in append mode
    mode = "a" if (resume and checkpoint.get("processed_books")) else "w"
    total_processed_so_far = len(checkpoint.get("processed_books", []))

    logger.info(f"Starting chunking (mode={'append' if mode == 'a' else 'write'})")
    logger.info(f"Output: {OUTPUT_FILE}")

    with open(OUTPUT_FILE, mode, encoding="utf-8") as out_f:
        with ProgressBar(
            total=len(books_to_process),
            desc="Chunking books",
            unit="books",
        ) as bar:
            for book_entry in books_to_process:
                book_id = book_entry["id"]
                book_title = book_entry.get("title", "unknown")[:50]
                category = book_entry.get("cat_name", "unknown")

                try:
                    chunks, file_size = chunk_book_file(book_entry, chunker)

                    # Write chunks
                    for chunk in chunks:
                        out_f.write(json.dumps(chunk, ensure_ascii=False) + "\n")

                    # Update stats
                    stats["books_processed"] += 1
                    stats["total_chunks"] += len(chunks)
                    stats["total_bytes_processed"] += file_size

                    # Category stats
                    if category not in stats["category_stats"]:
                        stats["category_stats"][category] = {
                            "books": 0,
                            "chunks": 0,
                            "bytes": 0,
                        }
                    stats["category_stats"][category]["books"] += 1
                    stats["category_stats"][category]["chunks"] += len(chunks)
                    stats["category_stats"][category]["bytes"] += file_size

                    # Chunk type stats
                    for chunk in chunks:
                        ct = chunk.get("chunk_type", "unknown")
                        stats["chunk_type_stats"][ct] = stats["chunk_type_stats"].get(ct, 0) + 1

                        # Size distribution
                        cl = chunk.get("content_length", 0)
                        if cl < 200:
                            stats["size_distribution"]["tiny"] += 1
                        elif cl < 600:
                            stats["size_distribution"]["small"] += 1
                        elif cl < 1200:
                            stats["size_distribution"]["medium"] += 1
                        elif cl < 1800:
                            stats["size_distribution"]["large"] += 1
                        else:
                            stats["size_distribution"]["xlarge"] += 1

                    # Update checkpoint
                    checkpoint["processed_books"].append(book_id)
                    checkpoint["total_chunks"] = stats["total_chunks"]
                    if stats["books_processed"] % 50 == 0:
                        save_checkpoint(checkpoint)

                    bar.set_postfix(
                        chunks=stats["total_chunks"],
                        avg=f"{stats['total_chunks'] / max(stats['books_processed'], 1):.0f}",
                    )
                    bar.update()

                except Exception as e:
                    stats["books_errored"] += 1
                    error_info = {
                        "book_id": book_id,
                        "title": book_entry.get("title", "unknown")[:80],
                        "error": str(e)[:200],
                    }
                    stats["errors"].append(error_info)
                    logger.warning(f"Error processing book {book_id}: {e}")
                    checkpoint["errors"] = stats["errors"]
                    bar.update()

    # Final checkpoint
    save_checkpoint(checkpoint)

    elapsed = time.time() - start_time
    stats["elapsed_seconds"] = elapsed
    stats["elapsed_human"] = format_duration(elapsed)
    stats["books_per_second"] = stats["books_processed"] / elapsed if elapsed > 0 else 0
    stats["avg_chunks_per_book"] = stats["total_chunks"] / max(stats["books_processed"], 1)

    # Save stats
    with open(STATS_FILE, "w", encoding="utf-8") as f:
        json.dump(stats, f, ensure_ascii=False, indent=2)

    return stats


# ── Report ───────────────────────────────────────────────────────────────


def print_report(stats: dict[str, Any]) -> None:
    """Print a formatted statistics report."""
    print("\n" + "=" * 70)
    print("  HIERARCHICAL CHUNKING REPORT")
    print("=" * 70)

    print(f"\n  Books processed:    {stats['books_processed']}")
    print(f"  Books errored:      {stats['books_errored']}")
    print(f"  Total chunks:       {stats['total_chunks']}")
    print(f"  Avg chunks/book:    {stats.get('avg_chunks_per_book', 0):.1f}")
    print(f"  Data processed:     {format_size(stats['total_bytes_processed'])}")
    print(f"  Time elapsed:       {stats.get('elapsed_human', 'N/A')}")
    print(f"  Speed:              {stats.get('books_per_second', 0):.1f} books/sec")

    print(f"\n  Chunk type distribution:")
    for ct, count in sorted(stats.get("chunk_type_stats", {}).items(), key=lambda x: -x[1])[:10]:
        print(f"    {ct:20s}: {count:>8,}")

    print(f"\n  Chunk size distribution:")
    for size_label, count in stats.get("size_distribution", {}).items():
        print(f"    {size_label:10s}: {count:>8,}")

    print(f"\n  Top categories by chunks:")
    cat_stats = stats.get("category_stats", {})
    top_cats = sorted(cat_stats.items(), key=lambda x: -x[1]["chunks"])[:10]
    for cat, cstats in top_cats:
        print(f"    {cat:35s}: {cstats['chunks']:>8,} chunks ({cstats['books']} books)")

    errors = stats.get("errors", [])
    if errors:
        print(f"\n  Errors ({len(errors)}):")
        for err in errors[:5]:
            print(f"    Book {err['book_id']}: {err['error'][:80]}")
        if len(errors) > 5:
            print(f"    ... and {len(errors) - 5} more errors")

    print("\n" + "=" * 70)
    print(f"  Output: {OUTPUT_FILE}")
    print(f"  Stats:  {STATS_FILE}")
    print("=" * 70)


# ── CLI ──────────────────────────────────────────────────────────────────


def main() -> None:
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Batch chunk all Shamela books using hierarchical chunking",
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
        help="Start fresh, ignore checkpoint",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=0,
        help="Maximum number of books to process (0 = all)",
    )
    parser.add_argument(
        "--book-id",
        type=int,
        nargs="*",
        default=None,
        help="Process specific book IDs only",
    )
    args = parser.parse_args()

    resume = args.resume and not args.no_resume
    stats = run_chunking(
        resume=resume,
        limit=args.limit,
        book_ids=args.book_id,
    )
    print_report(stats)


if __name__ == "__main__":
    main()
