#!/usr/bin/env python3
"""
A. Extract ALL Lucene index content (pages, titles, esnad, books).

Orchestrates the enhanced Java LuceneExtractorFull to pull documents from
each Lucene index using offset-based batching. Produces JSONL output
(one document per line) for memory-efficient streaming.

Pipeline:
  1. Compile enhanced Java extractor (LuceneExtractorFull.java)
  2. Run extractor on each index with offset batching
  3. Decode/normalise text, organize into per-book JSONL files
  4. Write statistics report + checkpoint for resume

Usage:
    python scripts/data/lucene/extract_lucene_pages.py
    python scripts/data/lucene/extract_lucene_pages.py --indexes page title
    python scripts/data/lucene/extract_lucene_pages.py --resume
    python scripts/data/lucene/extract_lucene_pages.py --dry-run

Output:
    data/processed/lucene_pages/pages/       – per-page JSONL by book_id
    data/processed/lucene_pages/titles/      – per-title JSONL by book_id
    data/processed/lucene_pages/esnad/       – per-hadith JSONL by book_id
    data/processed/lucene_pages/books/       – per-book metadata JSONL
    data/processed/lucene_pages/raw/         – raw JSONL from Java extractor
    data/processed/lucene_pages/extraction_report.json
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional, Set, TextIO, Tuple

from scripts.utils import (
    ensure_dir,
    format_duration,
    format_size,
    get_datasets_dir,
    get_project_root,
    setup_script_logger,
)

# ── Configuration ─────────────────────────────────────────────────────────

logger = setup_script_logger("extract_lucene_pages")

PROJECT_ROOT = get_project_root()
LUCENE_STORE = get_datasets_dir() / "system_book_datasets" / "store"
JAVA_EXTRACTOR = PROJECT_ROOT / "scripts" / "lucene" / "LuceneExtractorFull.java"
LUCENE_JARS = PROJECT_ROOT / "lib" / "lucene"
OUTPUT_DIR = PROJECT_ROOT / "data" / "processed" / "lucene_pages"
RAW_DIR = OUTPUT_DIR / "raw"
CHECKPOINT_FILE = OUTPUT_DIR / "checkpoint.json"

# Batch size for large indexes
DEFAULT_BATCH_SIZE = 500_000

# Index definitions
INDEX_CONFIGS: Dict[str, Dict[str, Any]] = {
    "page": {
        "path": LUCENE_STORE / "page",
        "expected_docs": 7_358_148,
        "output_subdir": "pages",
        "description": "Full Arabic text of every page",
    },
    "title": {
        "path": LUCENE_STORE / "title",
        "expected_docs": 3_914_618,
        "output_subdir": "titles",
        "description": "Section/chapter titles",
    },
    "esnad": {
        "path": LUCENE_STORE / "esnad",
        "expected_docs": 35_526,
        "output_subdir": "esnad",
        "description": "Hadith chains with sanad/matn",
    },
    "book": {
        "path": LUCENE_STORE / "book",
        "expected_docs": 8_425,
        "output_subdir": "books",
        "description": "Book-level metadata from Lucene",
    },
}


# ── Data Classes ──────────────────────────────────────────────────────────

@dataclass
class CheckpointState:
    """Tracks extraction progress for resume support."""
    completed_indexes: List[str] = field(default_factory=list)
    current_index: Optional[str] = None
    current_batch_offset: int = 0
    total_docs_extracted: int = 0
    start_time: Optional[str] = None
    index_stats: Dict[str, Dict[str, Any]] = field(default_factory=dict)

    def save(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(self.__dict__, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    @classmethod
    def load(cls, path: Path) -> "CheckpointState":
        if path.exists():
            data = json.loads(path.read_text(encoding="utf-8"))
            return cls(**data)
        return cls()


@dataclass
class ExtractionStats:
    """Statistics for a single index extraction."""
    index_name: str
    total_docs: int = 0
    extracted_docs: int = 0
    error_docs: int = 0
    books_found: int = 0
    output_files: int = 0
    output_size_bytes: int = 0
    duration_seconds: float = 0.0


# ── Java Extraction ───────────────────────────────────────────────────────

def _get_java_classpath() -> str:
    """Build Java classpath with extractor and Lucene JARs."""
    lucene_dir = PROJECT_ROOT / "scripts" / "lucene"
    jar_files = sorted(LUCENE_JARS.glob("*.jar"))
    jar_list = ";".join(str(j) for j in jar_files)
    return f"{lucene_dir};{jar_list}"
def compile_java_extractor() -> bool:
    """Compile LuceneExtractorFull.java if needed."""
    class_file = JAVA_EXTRACTOR.with_suffix(".class")
    if class_file.exists() and class_file.stat().st_mtime > JAVA_EXTRACTOR.stat().st_mtime:
        logger.debug("LuceneExtractorFull.class is up to date")
        return True

    logger.info("Compiling LuceneExtractorFull.java ...")
    cp = _get_java_classpath()
    cmd = f'javac -cp "{cp}" "{JAVA_EXTRACTOR}"'
    result = subprocess.run(cmd, capture_output=True, text=True, shell=True, timeout=60)
    if result.returncode != 0:
        logger.error(f"Compilation failed:\n{result.stderr}")
        return False
    logger.info("Compilation successful")
    return True


def run_java_extractor_batch(
    index_path: Path,
    output_path: Path,
    max_docs: int,
    offset: int,
    progress_interval: int = 10000,
) -> Tuple[int, int]:
    """
    Run LuceneExtractorFull for a single batch.

    Args:
        index_path: Path to Lucene index directory.
        output_path: Where to write JSONL output.
        max_docs: Maximum docs to extract in this batch.
        offset: Starting document offset.
        progress_interval: Print progress every N docs.

    Returns:
        (return_code, extracted_count)
    """
    cp = _get_java_classpath()
    cmd = [
        "java",
        "-cp", cp,
        "LuceneExtractorFull",
        str(index_path),
        str(output_path),
        str(max_docs),
        str(offset),
        str(progress_interval),
    ]
    logger.debug(f"Running: {' '.join(cmd)}")

    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=7200,  # 2 hours per batch
    )

    # Parse extracted count from stdout
    extracted = 0
    for line in result.stdout.splitlines():
        if line.startswith("Extracted:"):
            try:
                extracted = int(line.split(":")[1].strip().split()[0])
            except (ValueError, IndexError):
                pass
        if line.startswith("Index:"):
            logger.info(f"  {line.strip()}")
        if line.startswith("Total docs"):
            logger.info(f"  {line.strip()}")

    if result.returncode != 0:
        logger.error(
            f"Java extraction failed (rc={result.returncode}): "
            f"{result.stderr[:500]}"
        )

    return result.returncode, extracted


# ── Document Processing ───────────────────────────────────────────────────

def parse_book_id_from_doc(doc: Dict[str, Any]) -> Optional[int]:
    """
    Extract the numeric book_id from a Lucene document.

    Handles formats:
      - id: "71-12090"  -> 71
      - id: "1559"       -> 1559
      - book_key field
    """
    doc_id = doc.get("id", "")
    if isinstance(doc_id, str) and "-" in doc_id:
        try:
            return int(doc_id.split("-")[0])
        except (ValueError, IndexError):
            pass
    book_key = doc.get("book_key", "")
    if book_key:
        try:
            return int(str(book_key).split("-")[0])
        except (ValueError, IndexError):
            pass
    if isinstance(doc_id, str) and doc_id.isdigit():
        try:
            return int(doc_id)
        except ValueError:
            pass
    return None


def decode_mojibake(text: str) -> str:
    """
    Attempt to fix mojibake text.

    The Lucene index stores text as UTF-8 internally. The Java extractor
    reads stored fields as Java Strings (UTF-16), then writes them as
    UTF-8 JSON. In most cases the text is already correct UTF-8 Arabic.
    This function handles edge cases where double-encoding may have occurred.
    """
    if not text:
        return text

    # Check if already valid Arabic
    arabic_count = sum(1 for c in text if "\u0600" <= c <= "\u06FF")
    if arabic_count > len(text) * 0.3:
        return text  # Already good Arabic

    # Try: raw bytes -> decode as Windows-1256
    try:
        raw_bytes = text.encode("utf-8")
        decoded = raw_bytes.decode("windows-1256")
        decoded_arabic = sum(1 for c in decoded if "\u0600" <= c <= "\u06FF")
        if decoded_arabic > arabic_count * 1.5:
            return decoded
    except (UnicodeDecodeError, UnicodeEncodeError):
        pass

    return text


def clean_arabic_text(text: str) -> str:
    """
    Clean and normalise Arabic text.

    - Strip HTML/XML tags
    - Remove zero-width characters
    - Collapse excessive whitespace
    - Preserve paragraph structure
    """
    if not text:
        return text

    # Remove HTML/XML tags
    text = re.sub(r"<[^>]+>", "", text)

    # Remove zero-width chars and BOM
    text = text.replace("\u200c", "").replace("\u200d", "").replace("\ufeff", "")
    text = text.replace("\u200b", "")  # zero-width space

    # Collapse horizontal whitespace (preserve newlines)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)

    return text.strip()


class BookFileWriter:
    """
    Manages per-book JSONL file handles with LRU eviction.

    Prevents keeping too many files open simultaneously.
    """

    def __init__(self, output_dir: Path, max_open: int = 200):
        self.output_dir = output_dir
        self.max_open = max_open
        self._handles: Dict[int, TextIO] = {}
        self._access_order: List[int] = []

    def write(self, book_id: int, doc: Dict[str, Any]) -> None:
        """Write a document to the book's JSONL file."""
        if book_id not in self._handles:
            self._open_file(book_id)

        self._handles[book_id].write(
            json.dumps(doc, ensure_ascii=False) + "\n"
        )
        # Update access order
        if book_id in self._access_order:
            self._access_order.remove(book_id)
        self._access_order.append(book_id)

    def _open_file(self, book_id: int) -> None:
        """Open a new file handle, evicting oldest if at limit."""
        while len(self._handles) >= self.max_open:
            oldest = self._access_order.pop(0)
            self._handles[oldest].close()
            del self._handles[oldest]

        filepath = self.output_dir / f"{book_id}.jsonl"
        self._handles[book_id] = open(filepath, "a", encoding="utf-8")

    def close_all(self) -> None:
        """Close all open file handles."""
        for fh in self._handles.values():
            fh.close()
        self._handles.clear()
        self._access_order.clear()


def process_jsonl_file(
    jsonl_path: Path,
    output_dir: Path,
    progress_label: str = "Processing",
) -> Tuple[int, int, Set[int]]:
    """
    Process a raw JSONL file: decode, clean, write per-book JSONL.

    Args:
        jsonl_path: Path to raw JSONL from Java extractor.
        output_dir: Directory for per-book output files.
        progress_label: Label for progress logging.

    Returns:
        (docs_written, error_count, set of book_ids)
    """
    ensure_dir(output_dir)
    writer = BookFileWriter(output_dir)
    docs_written = 0
    error_count = 0
    books_seen: Set[int] = set()

    try:
        with open(jsonl_path, "r", encoding="utf-8") as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue

                try:
                    doc = json.loads(line)
                    book_id = parse_book_id_from_doc(doc)
                    if book_id is None:
                        error_count += 1
                        continue

                    books_seen.add(book_id)

                    # Decode and clean text fields
                    cleaned_doc: Dict[str, Any] = {}
                    for key, value in doc.items():
                        if isinstance(value, str):
                            value = decode_mojibake(value)
                            value = clean_arabic_text(value)
                        cleaned_doc[key] = value

                    writer.write(book_id, cleaned_doc)
                    docs_written += 1

                except json.JSONDecodeError:
                    error_count += 1
                except Exception:
                    error_count += 1

                # Progress every 10000 docs
                if line_num % 10000 == 0:
                    logger.info(
                        f"  {progress_label}: {line_num:,} lines read, "
                        f"{docs_written:,} written, {error_count} errors"
                    )
    finally:
        writer.close_all()

    return docs_written, error_count, books_seen


# ── Index Extraction ──────────────────────────────────────────────────────

def extract_single_index(
    index_name: str,
    index_config: Dict[str, Any],
    checkpoint: CheckpointState,
    resume: bool = False,
    dry_run: bool = False,
) -> ExtractionStats:
    """
    Extract all documents from a single Lucene index.

    Uses offset-based batching for memory efficiency.
    """
    stats = ExtractionStats(index_name=index_name)
    index_path = index_config["path"]
    output_subdir = index_config["output_subdir"]
    total_expected = index_config["expected_docs"]

    logger.info(f"{'=' * 60}")
    logger.info(f"Index: {index_name}")
    logger.info(f"  Path: {index_path}")
    logger.info(f"  Expected docs: {total_expected:,}")
    logger.info(f"  Description: {index_config['description']}")
    logger.info(f"{'=' * 60}")

    if not index_path.exists():
        logger.error(f"Index directory not found: {index_path}")
        return stats

    if dry_run:
        logger.info(f"DRY RUN: Would extract {total_expected:,} docs from {index_name}")
        stats.total_docs = total_expected
        return stats

    output_dir = OUTPUT_DIR / output_subdir
    ensure_dir(output_dir)
    ensure_dir(RAW_DIR)

    start_time = time.time()

    # Determine starting offset
    start_offset = 0
    if resume and checkpoint.current_index == index_name:
        start_offset = checkpoint.current_batch_offset
        logger.info(f"Resuming {index_name} from offset {start_offset:,}")

    batch_size = DEFAULT_BATCH_SIZE
    offset = start_offset
    batch_num = 0

    while offset < total_expected:
        batch_num += 1
        docs_to_extract = min(batch_size, total_expected - offset)
        raw_file = RAW_DIR / f"{index_name}_batch_{batch_num}.jsonl"

        logger.info(
            f"Batch {batch_num}: extracting {docs_to_extract:,} docs "
            f"(offset={offset:,}, remaining={total_expected - offset:,})"
        )

        # Run Java extractor
        rc, extracted = run_java_extractor_batch(
            index_path, raw_file, docs_to_extract, offset
        )

        if rc != 0 or extracted == 0:
            logger.error(f"Batch {batch_num} failed or empty, stopping")
            break

        stats.total_docs += extracted

        # Process JSONL into per-book files
        logger.info(f"Processing {raw_file.name} ...")
        written, errors, books = process_jsonl_file(
            raw_file, output_dir,
            progress_label=f"Processing {index_name}"
        )
        stats.extracted_docs += written
        stats.error_docs += errors
        stats.books_found = max(stats.books_found, len(books))

        # Update checkpoint
        offset += extracted
        checkpoint.current_index = index_name
        checkpoint.current_batch_offset = offset
        checkpoint.total_docs_extracted += extracted
        checkpoint.save(CHECKPOINT_FILE)

        logger.info(
            f"  Batch {batch_num} complete: {extracted:,} extracted, "
            f"{written:,} written, {len(books)} books"
        )

    stats.duration_seconds = time.time() - start_time

    # Calculate output size
    total_size = sum(f.stat().st_size for f in output_dir.glob("*.jsonl"))
    stats.output_size_bytes = total_size
    stats.output_files = len(list(output_dir.glob("*.jsonl")))

    # Save index stats
    checkpoint.index_stats[index_name] = {
        "total_docs": stats.total_docs,
        "extracted_docs": stats.extracted_docs,
        "error_docs": stats.error_docs,
        "books_found": stats.books_found,
        "output_files": stats.output_files,
        "output_size_bytes": stats.output_size_bytes,
        "duration_seconds": stats.duration_seconds,
    }
    if index_name not in checkpoint.completed_indexes:
        checkpoint.completed_indexes.append(index_name)
    checkpoint.current_index = None
    checkpoint.current_batch_offset = 0
    checkpoint.save(CHECKPOINT_FILE)

    logger.info(
        f"OK {index_name} complete: {stats.extracted_docs:,} docs, "
        f"{stats.books_found} books, {format_size(stats.output_size_bytes)}"
    )
    return stats


# ── Reporting ─────────────────────────────────────────────────────────────

def write_report(all_stats: List[ExtractionStats]) -> Path:
    """Write extraction statistics report."""
    report = {
        "extraction_date": time.strftime("%Y-%m-%d %H:%M:%S"),
        "indexes": {},
        "totals": {
            "total_docs_extracted": 0,
            "total_errors": 0,
            "total_books_found": 0,
            "total_output_size_bytes": 0,
            "total_duration_seconds": 0.0,
        },
    }

    for s in all_stats:
        report["indexes"][s.index_name] = {
            "total_docs": s.total_docs,
            "extracted_docs": s.extracted_docs,
            "error_docs": s.error_docs,
            "books_found": s.books_found,
            "output_files": s.output_files,
            "output_size": format_size(s.output_size_bytes),
            "duration": format_duration(s.duration_seconds),
        }
        report["totals"]["total_docs_extracted"] += s.extracted_docs
        report["totals"]["total_errors"] += s.error_docs
        report["totals"]["total_books_found"] = max(
            report["totals"]["total_books_found"], s.books_found
        )
        report["totals"]["total_output_size_bytes"] += s.output_size_bytes
        report["totals"]["total_duration_seconds"] += s.duration_seconds

    report["totals"]["total_output_size"] = format_size(
        report["totals"]["total_output_size_bytes"]
    )
    report["totals"]["total_duration"] = format_duration(
        report["totals"]["total_duration_seconds"]
    )

    report_path = OUTPUT_DIR / "extraction_report.json"
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    logger.info(f"Report saved to {report_path}")
    return report_path


def print_summary(all_stats: List[ExtractionStats]) -> None:
    """Print human-readable summary."""
    print("\n" + "=" * 70)
    print("LUCENE EXTRACTION COMPLETE")
    print("=" * 70)

    total_docs = 0
    total_errors = 0
    total_size = 0
    total_duration = 0.0

    for s in all_stats:
        print(f"\n{ s.index_name.upper()}:")
        print(f"   Documents extracted: {s.extracted_docs:,}")
        print(f"   Errors:              {s.error_docs:,}")
        print(f"   Unique books:        {s.books_found}")
        print(f"   Output files:        {s.output_files}")
        print(f"   Output size:         {format_size(s.output_size_bytes)}")
        print(f"   Duration:            {format_duration(s.duration_seconds)}")

        total_docs += s.extracted_docs
        total_errors += s.error_docs
        total_size += s.output_size_bytes
        total_duration += s.duration_seconds

    print(f"\nTOTALS:")
    print(f"   Total documents:     {total_docs:,}")
    print(f"   Total errors:        {total_errors:,}")
    print(f"   Total output size:   {format_size(total_size)}")
    print(f"   Total duration:      {format_duration(total_duration)}")
    print(f"\nOutput directory: {OUTPUT_DIR}")
    print("=" * 70)


# ── Main ──────────────────────────────────────────────────────────────────

def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Extract ALL Lucene index content for Shamela books"
    )
    parser.add_argument(
        "--indexes",
        nargs="+",
        choices=list(INDEX_CONFIGS.keys()),
        default=list(INDEX_CONFIGS.keys()),
        help="Which indexes to extract (default: all)",
    )
    parser.add_argument(
        "--resume",
        action="store_true",
        help="Resume from last checkpoint",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be extracted without running",
    )
    parser.add_argument(
        "--skip-compile",
        action="store_true",
        help="Skip Java compilation",
    )
    args = parser.parse_args()

    print("=" * 70)
    print("Burhan - LUCENE EXTRACTION PIPELINE")
    print("=" * 70)
    print(f"  Indexes:     {', '.join(args.indexes)}")
    print(f"  Resume:      {args.resume}")
    print(f"  Dry run:     {args.dry_run}")
    print(f"  Output dir:  {OUTPUT_DIR}")
    print("=" * 70)

    ensure_dir(OUTPUT_DIR)
    ensure_dir(RAW_DIR)

    # Load checkpoint
    checkpoint = CheckpointState.load(CHECKPOINT_FILE)
    if args.resume:
        logger.info(
            f"Resuming: {checkpoint.total_docs_extracted:,} docs already extracted"
        )
        logger.info(f"Completed indexes: {checkpoint.completed_indexes}")

    # Compile Java extractor
    if not args.skip_compile and not args.dry_run:
        if not compile_java_extractor():
            logger.error("Failed to compile Java extractor. Aborting.")
            sys.exit(1)

    # Extract each index
    all_stats: List[ExtractionStats] = []
    for idx_name in args.indexes:
        if args.resume and idx_name in checkpoint.completed_indexes:
            logger.info(f"Skipping {idx_name} (already completed)")
            # Still add stats from checkpoint
            if idx_name in checkpoint.index_stats:
                cs = checkpoint.index_stats[idx_name]
                all_stats.append(ExtractionStats(
                    index_name=idx_name,
                    total_docs=cs.get("total_docs", 0),
                    extracted_docs=cs.get("extracted_docs", 0),
                    error_docs=cs.get("error_docs", 0),
                    books_found=cs.get("books_found", 0),
                    output_files=cs.get("output_files", 0),
                    output_size_bytes=cs.get("output_size_bytes", 0),
                    duration_seconds=cs.get("duration_seconds", 0.0),
                ))
            continue

        idx_config = INDEX_CONFIGS[idx_name]
        stats = extract_single_index(
            idx_name, idx_config, checkpoint,
            resume=args.resume, dry_run=args.dry_run
        )
        all_stats.append(stats)

    # Write report
    if all_stats:
        write_report(all_stats)
        print_summary(all_stats)
    else:
        logger.info("No indexes to extract (all completed or skipped)")


if __name__ == "__main__":
    main()
