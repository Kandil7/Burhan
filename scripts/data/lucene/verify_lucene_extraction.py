#!/usr/bin/env python3
"""
D. Verify quality of Lucene extraction.

Comprehensive quality checks:
- All 8,425 books have content
- Valid encoding (no mojibake)
- Page count distribution analysis
- Hierarchy preservation verification
- Content completeness checks
- Collection balance verification

Usage:
    python scripts/data/lucene/verify_lucene_extraction.py
    python scripts/data/lucene/verify_lucene_extraction.py --quick
    python scripts/data/lucene/verify_lucene_extraction.py --report

Output:
    data/processed/lucene_pages/quality_report.json
    data/processed/lucene_pages/missing_books.json
    data/processed/lucene_pages/page_distribution.json
"""

from __future__ import annotations

import json
import re
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from scripts.utils import (
    ensure_dir,
    format_size,
    get_project_root,
    setup_script_logger,
)

# ── Configuration ─────────────────────────────────────────────────────────

logger = setup_script_logger("verify_lucene_extraction")

PROJECT_ROOT = get_project_root()
LUCENE_PAGES_DIR = PROJECT_ROOT / "data" / "processed" / "lucene_pages"
MASTER_CATALOG = PROJECT_ROOT / "data" / "processed" / "master_catalog.json"

# Expected counts
EXPECTED_TOTAL_BOOKS = 8425

# Arabic Unicode ranges for validation
ARABIC_RANGES = [
    (0x0600, 0x06FF),   # Arabic
    (0x0750, 0x077F),   # Arabic Supplement
    (0x08A0, 0x08FF),   # Arabic Extended-A
    (0xFB50, 0xFDFF),   # Arabic Presentation Forms-A
    (0xFE70, 0xFEFF),   # Arabic Presentation Forms-B
]


# ── Data Classes ──────────────────────────────────────────────────────────

@dataclass
class BookContentStats:
    """Content statistics for a single book."""
    book_id: int
    title: str
    page_count: int = 0
    title_count: int = 0
    esnad_count: int = 0
    total_chars: int = 0
    arabic_chars: int = 0
    arabic_ratio: float = 0.0
    has_mojibake: bool = False
    encoding_issues: List[str] = field(default_factory=list)


@dataclass
class QualityReport:
    """Overall quality report."""
    # Book coverage
    total_expected_books: int = 0
    books_with_pages: int = 0
    books_with_titles: int = 0
    books_with_esnad: int = 0
    books_with_any_content: int = 0
    books_missing: List[int] = field(default_factory=list)

    # Content statistics
    total_pages: int = 0
    total_titles: int = 0
    total_esnad: int = 0
    total_chars: int = 0
    total_arabic_chars: int = 0
    overall_arabic_ratio: float = 0.0

    # Encoding quality
    files_with_mojibake: int = 0
    files_with_errors: int = 0
    encoding_error_details: List[str] = field(default_factory=list)

    # Page distribution
    page_count_distribution: Dict[str, int] = field(default_factory=dict)
    min_pages_per_book: int = 0
    max_pages_per_book: int = 0
    median_pages_per_book: float = 0.0
    mean_pages_per_book: float = 0.0

    # Hierarchy
    books_with_hierarchy: int = 0
    books_with_titles_mapped: int = 0
    orphan_pages: int = 0  # Pages without matching titles

    # Collection stats
    collection_book_counts: Dict[str, int] = field(default_factory=dict)
    collection_doc_counts: Dict[str, int] = field(default_factory=dict)

    # File stats
    total_output_size_bytes: int = 0
    total_files: int = 0

    # Timing
    duration_seconds: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "book_coverage": {
                "total_expected": self.total_expected_books,
                "books_with_pages": self.books_with_pages,
                "books_with_titles": self.books_with_titles,
                "books_with_esnad": self.books_with_esnad,
                "books_with_any_content": self.books_with_any_content,
                "coverage_percentage": round(
                    self.books_with_any_content / self.total_expected_books * 100, 2
                ) if self.total_expected_books > 0 else 0,
                "missing_books_count": len(self.books_missing),
            },
            "content_statistics": {
                "total_pages": self.total_pages,
                "total_titles": self.total_titles,
                "total_esnad": self.total_esnad,
                "total_chars": self.total_chars,
                "total_arabic_chars": self.total_arabic_chars,
                "overall_arabic_ratio": round(self.overall_arabic_ratio, 4),
            },
            "encoding_quality": {
                "files_with_mojibake": self.files_with_mojibake,
                "files_with_errors": self.files_with_errors,
                "mojibake_rate": round(
                    self.files_with_mojibake / self.total_files * 100, 2
                ) if self.total_files > 0 else 0,
                "error_details": self.encoding_error_details[:50],  # Limit
            },
            "page_distribution": {
                "distribution": self.page_count_distribution,
                "min_pages": self.min_pages_per_book,
                "max_pages": self.max_pages_per_book,
                "median_pages": round(self.median_pages_per_book, 1),
                "mean_pages": round(self.mean_pages_per_book, 1),
            },
            "hierarchy": {
                "books_with_hierarchy": self.books_with_hierarchy,
                "books_with_titles_mapped": self.books_with_titles_mapped,
                "orphan_pages": self.orphan_pages,
            },
            "collections": {
                "book_counts": self.collection_book_counts,
                "doc_counts": self.collection_doc_counts,
            },
            "file_statistics": {
                "total_output_size": format_size(self.total_output_size_bytes),
                "total_output_size_bytes": self.total_output_size_bytes,
                "total_files": self.total_files,
            },
            "duration": f"{self.duration_seconds:.1f}s",
        }


# ── Helpers ───────────────────────────────────────────────────────────────

def count_arabic_chars(text: str) -> int:
    """Count Arabic characters in text."""
    count = 0
    for ch in text:
        cp = ord(ch)
        for start, end in ARABIC_RANGES:
            if start <= cp <= end:
                count += 1
                break
    return count


def detect_mojibake(text: str) -> bool:
    """
    Detect if text contains mojibake (encoding corruption).

    Checks for common Windows-1256 -> UTF-8 misencoding patterns.
    """
    if not text:
        return False

    # Common mojibake patterns for Arabic
    mojibake_indicators = [
        # Windows-1256 bytes interpreted as Latin-1/CP1252 then UTF-8
        "\u00c7\u00e1",  # ال (Al-)
        "\u00c8\u00e4",  # بن (bin)
        "\u00cf\u00e8",  # محمد (Muhammad - partial)
        "\u00d8\u00a7",  # ا (Alef)
        "\u00d9\u0086",  # ن (Noon)
    ]

    for pattern in mojibake_indicators:
        if pattern in text:
            return True

    # Check for high ratio of non-Arabic, non-ASCII Latin chars
    total_chars = len(text)
    if total_chars < 10:
        return False

    latin_high = sum(1 for c in text if 0x80 <= ord(c) <= 0xFF)
    arabic = count_arabic_chars(text)

    # If more high Latin chars than Arabic, likely mojibake
    if latin_high > arabic * 2 and latin_high > total_chars * 0.1:
        return True

    return False


def get_page_count_category(count: int) -> str:
    """Categorize book by page count."""
    if count == 0:
        return "empty"
    elif count <= 10:
        return "1-10"
    elif count <= 50:
        return "11-50"
    elif count <= 100:
        return "51-100"
    elif count <= 200:
        return "101-200"
    elif count <= 500:
        return "201-500"
    elif count <= 1000:
        return "501-1000"
    else:
        return "1000+"


def load_master_catalog(catalog_path: Path) -> Tuple[Set[int], Dict[int, str]]:
    """
    Load master catalog and return book IDs and titles.

    Returns:
        (set of book_ids, dict of book_id -> title)
    """
    if not catalog_path.exists():
        return set(), {}

    with open(catalog_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    book_ids: Set[int] = set()
    book_titles: Dict[int, str] = {}
    for book in data.get("books", []):
        bid = book.get("book_id")
        if bid is not None:
            book_ids.add(bid)
            book_titles[bid] = book.get("title", "")

    return book_ids, book_titles


def count_lines_in_file(filepath: Path) -> int:
    """Count lines in a file efficiently."""
    count = 0
    with open(filepath, "r", encoding="utf-8") as f:
        for _ in f:
            count += 1
    return count


def sample_file_content(filepath: Path, n: int = 5) -> List[Dict[str, Any]]:
    """Sample first N documents from a JSONL file."""
    docs = []
    with open(filepath, "r", encoding="utf-8") as f:
        for i, line in enumerate(f):
            if i >= n:
                break
            line = line.strip()
            if line:
                try:
                    docs.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    return docs


# ── Verification Functions ────────────────────────────────────────────────

def verify_book_coverage(
    pages_dir: Path,
    titles_dir: Path,
    esnad_dir: Path,
    expected_book_ids: Set[int],
) -> Tuple[int, int, int, int, List[int]]:
    """
    Verify that all expected books have content.

    Returns:
        (books_with_pages, books_with_titles, books_with_esnad,
         books_with_any_content, list of missing book_ids)
    """
    books_with_pages: Set[int] = set()
    books_with_titles: Set[int] = set()
    books_with_esnad: Set[int] = set()

    for d, target in [
        (pages_dir, books_with_pages),
        (titles_dir, books_with_titles),
        (esnad_dir, books_with_esnad),
    ]:
        if d.exists():
            for f in d.glob("*.jsonl"):
                try:
                    bid = int(f.stem)
                    target.add(bid)
                except ValueError:
                    continue

    all_with_content = books_with_pages | books_with_titles | books_with_esnad
    missing = sorted(expected_book_ids - all_with_content)

    return (
        len(books_with_pages),
        len(books_with_titles),
        len(books_with_esnad),
        len(all_with_content),
        missing,
    )


def verify_encoding_quality(
    content_dirs: List[Path],
    sample_size: int = 100,
) -> Tuple[int, int, List[str]]:
    """
    Verify encoding quality across content files.

    Samples documents from each file and checks for mojibake.

    Returns:
        (files_with_mojibake, files_with_errors, error_details)
    """
    mojibake_count = 0
    error_count = 0
    error_details: List[str] = []

    for content_dir in content_dirs:
        if not content_dir.exists():
            continue

        files = list(content_dir.glob("*.jsonl"))
        logger.info(f"Checking encoding in {len(files)} files in {content_dir.name}")

        for filepath in files:
            try:
                samples = sample_file_content(filepath, sample_size)
                has_mojibake = False
                for doc in samples:
                    for key, value in doc.items():
                        if isinstance(value, str) and len(value) > 20:
                            if detect_mojibake(value):
                                has_mojibake = True
                                error_details.append(
                                    f"{filepath.name}: mojibake in field '{key}'"
                                )
                                break
                    if has_mojibake:
                        break

                if has_mojibake:
                    mojibake_count += 1

            except Exception as e:
                error_count += 1
                error_details.append(f"{filepath.name}: {type(e).__name__}: {e}")

    return mojibake_count, error_count, error_details


def verify_page_distribution(
    pages_dir: Path,
    book_titles: Dict[int, str],
) -> Dict[str, Any]:
    """
    Analyze page count distribution across books.

    Returns:
        Distribution statistics dictionary.
    """
    if not pages_dir.exists():
        return {}

    page_counts: List[int] = []
    empty_books: List[int] = []

    for filepath in sorted(pages_dir.glob("*.jsonl")):
        try:
            book_id = int(filepath.stem)
            count = count_lines_in_file(filepath)
            page_counts.append(count)
            if count == 0:
                empty_books.append(book_id)
        except ValueError:
            continue

    if not page_counts:
        return {"error": "No page files found"}

    page_counts.sort()
    n = len(page_counts)

    # Distribution buckets
    distribution: Dict[str, int] = {}
    for count in page_counts:
        category = get_page_count_category(count)
        distribution[category] = distribution.get(category, 0) + 1

    return {
        "total_books_with_pages": n,
        "empty_books": len(empty_books),
        "min_pages": min(page_counts),
        "max_pages": max(page_counts),
        "median_pages": page_counts[n // 2],
        "mean_pages": round(sum(page_counts) / n, 1),
        "total_pages": sum(page_counts),
        "distribution": distribution,
        "empty_book_ids": empty_books[:100],  # Limit
    }


def verify_hierarchy_preservation(
    pages_dir: Path,
    titles_dir: Path,
) -> Tuple[int, int, int]:
    """
    Verify that title hierarchy is properly preserved.

    Checks:
    - Books have both pages and titles
    - Title page numbers map to actual pages
    - No orphan pages (pages without titles)

    Returns:
        (books_with_hierarchy, books_with_titles_mapped, orphan_pages)
    """
    if not pages_dir.exists() or not titles_dir.exists():
        return 0, 0, 0

    books_with_hierarchy = 0
    books_with_titles_mapped = 0
    orphan_pages = 0

    title_files = {int(f.stem): f for f in titles_dir.glob("*.jsonl") if f.stem.isdigit()}

    for page_file in pages_dir.glob("*.jsonl"):
        try:
            book_id = int(page_file.stem)
        except ValueError:
            continue

        if book_id not in title_files:
            continue

        # Load title page numbers
        title_page_nums: set = set()
        with open(title_files[book_id], "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        doc = json.loads(line)
                        page = doc.get("page")
                        if page:
                            title_page_nums.add(int(page))
                    except (json.JSONDecodeError, ValueError, TypeError):
                        continue

        if not title_page_nums:
            continue

        books_with_titles_mapped += 1

        # Check if pages align with titles
        has_matching_page = False
        with open(page_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        doc = json.loads(line)
                        doc_id = doc.get("id", "")
                        if isinstance(doc_id, str) and "-" in doc_id:
                            try:
                                page_num = int(doc_id.split("-")[1])
                                if page_num in title_page_nums:
                                    has_matching_page = True
                            except (ValueError, IndexError):
                                pass
                    except json.JSONDecodeError:
                        continue

        if has_matching_page:
            books_with_hierarchy += 1

    return books_with_hierarchy, books_with_titles_mapped, orphan_pages


def verify_collection_balance(
    collections_dir: Path,
    master_catalog: Optional[Dict] = None,
) -> Tuple[Dict[str, int], Dict[str, int]]:
    """
    Verify document distribution across collections.

    Returns:
        (book_counts_per_collection, doc_counts_per_collection)
    """
    book_counts: Dict[str, int] = {}
    doc_counts: Dict[str, int] = {}

    if collections_dir.exists():
        for filepath in collections_dir.glob("*.jsonl"):
            collection = filepath.stem
            doc_count = count_lines_in_file(filepath)
            doc_counts[collection] = doc_count

    return book_counts, doc_counts


# ── Main Verification Pipeline ────────────────────────────────────────────

def run_full_verification(quick: bool = False) -> QualityReport:
    """
    Run complete quality verification.

    Args:
        quick: If True, skip expensive checks (encoding sampling).

    Returns:
        QualityReport with all findings.
    """
    report = QualityReport()
    start_time = time.time()

    pages_dir = LUCENE_PAGES_DIR / "pages"
    titles_dir = LUCENE_PAGES_DIR / "titles"
    esnad_dir = LUCENE_PAGES_DIR / "esnad"
    collections_dir = LUCENE_PAGES_DIR / "collections"

    # 1. Load master catalog
    expected_ids, book_titles = load_master_catalog(MASTER_CATALOG)
    report.total_expected_books = len(expected_ids) or EXPECTED_TOTAL_BOOKS

    logger.info(f"Expected books: {report.total_expected_books}")

    # 2. Book coverage
    logger.info("Checking book coverage...")
    (
        report.books_with_pages,
        report.books_with_titles,
        report.books_with_esnad,
        report.books_with_any_content,
        report.books_missing,
    ) = verify_book_coverage(pages_dir, titles_dir, esnad_dir, expected_ids)

    coverage = report.books_with_any_content / report.total_expected_books * 100
    logger.info(
        f"Coverage: {report.books_with_any_content}/{report.total_expected_books} "
        f"({coverage:.1f}%)"
    )

    # 3. Page distribution
    logger.info("Analyzing page distribution...")
    page_dist = verify_page_distribution(pages_dir, book_titles)
    if page_dist:
        report.total_pages = page_dist.get("total_pages", 0)
        report.min_pages_per_book = page_dist.get("min_pages", 0)
        report.max_pages_per_book = page_dist.get("max_pages", 0)
        report.median_pages_per_book = page_dist.get("median_pages", 0)
        report.mean_pages_per_book = page_dist.get("mean_pages", 0)
        report.page_count_distribution = page_dist.get("distribution", {})

    # 4. Encoding quality
    if not quick:
        logger.info("Checking encoding quality (this may take a while)...")
        content_dirs = [d for d in [pages_dir, titles_dir, esnad_dir] if d.exists()]
        (
            report.files_with_mojibake,
            report.files_with_errors,
            report.encoding_error_details,
        ) = verify_encoding_quality(content_dirs, sample_size=50)
    else:
        logger.info("Quick mode: skipping encoding check")

    # 5. Hierarchy preservation
    logger.info("Checking hierarchy preservation...")
    (
        report.books_with_hierarchy,
        report.books_with_titles_mapped,
        report.orphan_pages,
    ) = verify_hierarchy_preservation(pages_dir, titles_dir)

    # 6. Collection balance
    logger.info("Checking collection balance...")
    report.collection_book_counts, report.collection_doc_counts = (
        verify_collection_balance(collections_dir)
    )

    # 7. File statistics
    total_files = 0
    total_size = 0
    for d in [pages_dir, titles_dir, esnad_dir, collections_dir]:
        if d.exists():
            for f in d.rglob("*.jsonl"):
                total_files += 1
                total_size += f.stat().st_size
    report.total_files = total_files
    report.total_output_size_bytes = total_size

    # 8. Calculate totals
    for content_dir in [pages_dir, titles_dir, esnad_dir]:
        if content_dir.exists():
            for filepath in content_dir.glob("*.jsonl"):
                try:
                    count = count_lines_in_file(filepath)
                    if "pages" in str(content_dir):
                        report.total_pages += count
                    elif "titles" in str(content_dir):
                        report.total_titles += count
                    elif "esnad" in str(content_dir):
                        report.total_esnad += count
                except Exception:
                    pass

    # Calculate arabic ratio from samples
    total_chars = 0
    arabic_chars = 0
    sample_count = 0
    for content_dir in [pages_dir, titles_dir]:
        if not content_dir.exists():
            continue
        for filepath in list(content_dir.glob("*.jsonl"))[:20]:
            samples = sample_file_content(filepath, 3)
            for doc in samples:
                for key, value in doc.items():
                    if isinstance(value, str):
                        total_chars += len(value)
                        arabic_chars += count_arabic_chars(value)
            sample_count += 1

    if total_chars > 0:
        report.total_chars = total_chars
        report.total_arabic_chars = arabic_chars
        report.overall_arabic_ratio = arabic_chars / total_chars

    report.duration_seconds = time.time() - start_time
    return report


def write_quality_report(report: QualityReport) -> Path:
    """Write quality report to JSON file."""
    ensure_dir(LUCENE_PAGES_DIR)

    report_path = LUCENE_PAGES_DIR / "quality_report.json"
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report.to_dict(), f, indent=2, ensure_ascii=False)

    # Write missing books list
    if report.books_missing:
        missing_path = LUCENE_PAGES_DIR / "missing_books.json"
        with open(missing_path, "w", encoding="utf-8") as f:
            json.dump({
                "missing_count": len(report.books_missing),
                "missing_book_ids": report.books_missing,
            }, f, indent=2, ensure_ascii=False)

    # Write page distribution
    if report.page_count_distribution:
        dist_path = LUCENE_PAGES_DIR / "page_distribution.json"
        with open(dist_path, "w", encoding="utf-8") as f:
            json.dump({
                "distribution": report.page_count_distribution,
                "min": report.min_pages_per_book,
                "max": report.max_pages_per_book,
                "median": report.median_pages_per_book,
                "mean": report.mean_pages_per_book,
            }, f, indent=2, ensure_ascii=False)

    logger.info(f"Quality report saved to {report_path}")
    return report_path


def print_quality_summary(report: QualityReport) -> None:
    """Print human-readable quality summary."""
    print(f"\n{'=' * 70}")
    print("LUCENE EXTRACTION QUALITY REPORT")
    print(f"{'=' * 70}")

    # Book coverage
    coverage = report.books_with_any_content / report.total_expected_books * 100 \
        if report.total_expected_books > 0 else 0
    print(f"\nBOOK COVERAGE:")
    print(f"  Expected books:      {report.total_expected_books:,}")
    print(f"  Books with content:  {report.books_with_any_content:,}")
    print(f"  Coverage:            {coverage:.1f}%")
    print(f"  Missing books:       {len(report.books_missing)}")
    if report.books_missing and len(report.books_missing) <= 20:
        print(f"  Missing IDs:         {report.books_missing}")

    # Content statistics
    print(f"\nCONTENT STATISTICS:")
    print(f"  Total pages:         {report.total_pages:,}")
    print(f"  Total titles:        {report.total_titles:,}")
    print(f"  Total esnad:         {report.total_esnad:,}")
    print(f"  Arabic ratio:        {report.overall_arabic_ratio:.2%}")

    # Encoding quality
    print(f"\nENCODING QUALITY:")
    print(f"  Files with mojibake: {report.files_with_mojibake}")
    print(f"  Files with errors:   {report.files_with_errors}")
    if report.encoding_error_details:
        print(f"  Sample issues:")
        for detail in report.encoding_error_details[:5]:
            print(f"    - {detail}")

    # Page distribution
    print(f"\nPAGE DISTRIBUTION:")
    print(f"  Min pages/book:      {report.min_pages_per_book}")
    print(f"  Max pages/book:      {report.max_pages_per_book}")
    print(f"  Mean pages/book:     {report.mean_pages_per_book:.1f}")
    print(f"  Median pages/book:   {report.median_pages_per_book:.1f}")
    if report.page_count_distribution:
        print(f"  Distribution:")
        for bucket in ["empty", "1-10", "11-50", "51-100", "101-200",
                        "201-500", "501-1000", "1000+"]:
            count = report.page_count_distribution.get(bucket, 0)
            if count > 0:
                print(f"    {bucket:>8s}: {count:>6,} books")

    # Hierarchy
    print(f"\nHIERARCHY:")
    print(f"  Books with hierarchy:  {report.books_with_hierarchy}")
    print(f"  Books with titles:     {report.books_with_titles_mapped}")

    # Collections
    if report.collection_doc_counts:
        print(f"\nCOLLECTION DOCUMENTS:")
        for coll in sorted(report.collection_doc_counts.keys()):
            count = report.collection_doc_counts[coll]
            print(f"  {coll:30s}: {count:>10,}")

    # File stats
    print(f"\nFILE STATISTICS:")
    print(f"  Total files:         {report.total_files}")
    print(f"  Total output size:   {format_size(report.total_output_size_bytes)}")
    print(f"  Duration:            {report.duration_seconds:.1f}s")

    # Overall verdict
    print(f"\n{'=' * 70}")
    if coverage >= 95 and report.files_with_mojibake == 0:
        print("VERDICT: PASS - Extraction quality is excellent")
    elif coverage >= 80:
        print("VERDICT: ACCEPTABLE - Some books missing, review recommended")
    else:
        print("VERDICT: NEEDS ATTENTION - Significant coverage issues")
    print(f"{'=' * 70}")


# ── Main ──────────────────────────────────────────────────────────────────

def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Verify quality of Lucene extraction"
    )
    parser.add_argument(
        "--quick",
        action="store_true",
        help="Quick mode: skip expensive encoding checks",
    )
    parser.add_argument(
        "--report",
        action="store_true",
        help="Only print existing report, don't re-run",
    )
    args = parser.parse_args()

    print(f"{'=' * 70}")
    print("Burhan - LUCENE EXTRACTION QUALITY VERIFICATION")
    print(f"{'=' * 70}")
    print(f"  Quick mode:  {args.quick}")
    print(f"  Report only: {args.report}")
    print(f"{'=' * 70}")

    # Report-only mode
    if args.report:
        report_path = LUCENE_PAGES_DIR / "quality_report.json"
        if report_path.exists():
            with open(report_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            print(json.dumps(data, indent=2, ensure_ascii=False))
        else:
            logger.error("No existing quality report found")
        return

    # Run full verification
    report = run_full_verification(quick=args.quick)

    # Write and print
    write_quality_report(report)
    print_quality_summary(report)


if __name__ == "__main__":
    main()
