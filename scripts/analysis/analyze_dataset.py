#!/usr/bin/env python3
"""
Complete Dataset Analysis for Athar Islamic QA System.

Analyzes the datasets/data directory structure:
- Extracted books statistics (count, size, distribution)
- Metadata analysis (categories, authors, books.db)
- Category distribution with super-category grouping
- Chunking strategy recommendations
- Embedding priority ranking

Usage:
    python scripts/analysis/analyze_dataset.py
    python scripts/analysis/analyze_dataset.py --report     # Detailed report
    python scripts/analysis/analyze_dataset.py --json       # JSON output

Author: Athar Engineering Team
"""

import argparse
import glob
import json
import os
import sqlite3
import sys
from pathlib import Path
from typing import Any

from scripts.utils import (
    get_project_root,
    get_datasets_dir,
    setup_script_logger,
    format_size,
)

logger = setup_script_logger("analyze-dataset")

# ── Configuration ────────────────────────────────────────────────────────

DATA_DIR = get_datasets_dir("data")
BOOKS_DIR = DATA_DIR / "extracted_books"
METADATA_DIR = DATA_DIR / "metadata"


# ── Analysis Functions ───────────────────────────────────────────────────


def analyze_extracted_books() -> dict[str, Any]:
    """
    Analyze extracted books directory.

    Returns:
        Dict with book statistics.
    """
    if not BOOKS_DIR.exists():
        return {"error": f"Books directory not found: {BOOKS_DIR}"}

    txt_files = glob.glob(os.path.join(BOOKS_DIR, "*.txt"))
    sizes = [os.path.getsize(f) for f in txt_files]
    total_size = sum(sizes)

    # Size distribution
    large = [s for s in sizes if s > 10e6]  # > 10MB
    medium = [s for s in sizes if 1e6 < s <= 10e6]  # 1-10MB
    small = [s for s in sizes if s <= 1e6]  # < 1MB

    return {
        "total_files": len(txt_files),
        "total_size_bytes": total_size,
        "total_size_human": format_size(total_size),
        "avg_size_bytes": sum(sizes) / len(sizes) if sizes else 0,
        "avg_size_human": format_size(int(sum(sizes) / len(sizes))) if sizes else "0 B",
        "largest_bytes": max(sizes) if sizes else 0,
        "largest_human": format_size(max(sizes)) if sizes else "0 B",
        "smallest_bytes": min(sizes) if sizes else 0,
        "smallest_human": format_size(min(sizes)) if sizes else "0 B",
        "size_distribution": {
            "> 10MB": len(large),
            "1-10MB": len(medium),
            "< 1MB": len(small),
        },
    }


def analyze_metadata() -> dict[str, Any]:
    """
    Analyze metadata files.

    Returns:
        Dict with metadata statistics.
    """
    result: dict[str, Any] = {}

    # Categories
    categories_file = METADATA_DIR / "categories.json"
    if categories_file.exists():
        with open(categories_file, encoding="utf-8") as f:
            cats_data = json.load(f)
            result["categories_count"] = len(cats_data.get("categories", []))
    else:
        result["categories_count"] = 0
        result["categories_error"] = "File not found"

    # Authors
    authors_file = METADATA_DIR / "authors.json"
    if authors_file.exists():
        with open(authors_file, encoding="utf-8") as f:
            authors = json.load(f)
            result["authors_count"] = len(authors)
    else:
        result["authors_count"] = 0
        result["authors_error"] = "File not found"

    # Books database
    books_db = METADATA_DIR / "books.db"
    if books_db.exists():
        result["books_db"] = analyze_books_db(books_db)
    else:
        result["books_db"] = {"error": "File not found"}

    return result


def analyze_books_db(db_path: Path) -> dict[str, Any]:
    """
    Analyze books.db SQLite database.

    Args:
        db_path: Path to books.db.

    Returns:
        Dict with database statistics.
    """
    result: dict[str, Any] = {}

    conn = sqlite3.connect(str(db_path))
    cur = conn.cursor()

    # Books per category
    cur.execute(
        """
        SELECT cat_name, COUNT(*) as cnt, SUM(size_mb) as total_mb,
               AVG(size_mb) as avg_mb, MIN(size_mb) as min_mb, MAX(size_mb) as max_mb
        FROM books
        GROUP BY cat_name
        ORDER BY cnt DESC
    """
    )

    categories = []
    cat_groups: dict[str, dict[str, float]] = {}

    for row in cur.fetchall():
        cat_name, cnt, total_mb, avg_mb, min_mb, max_mb = row
        total_gb = total_mb / 1024 if total_mb else 0

        # Group into super-categories
        group = categorize_super_category(cat_name)
        cat_groups.setdefault(group, {"books": 0, "size_gb": 0})
        cat_groups[group]["books"] += cnt
        cat_groups[group]["size_gb"] += total_gb

        categories.append({
            "name": cat_name,
            "count": cnt,
            "total_gb": round(total_gb, 2),
            "avg_mb": round(avg_mb, 0) if avg_mb else 0,
            "min_mb": round(min_mb, 0) if min_mb else 0,
            "max_mb": round(max_mb, 0) if max_mb else 0,
        })

    result["categories"] = categories
    result["super_categories"] = cat_groups
    result["total_categories"] = len(categories)

    # Extraction status
    cur.execute("SELECT extracted, COUNT(*) FROM books GROUP BY extracted")
    extraction_status = {}
    for row in cur.fetchall():
        status = "Extracted" if row[0] == 1 else "Not Extracted"
        extraction_status[status] = row[1]
    result["extraction_status"] = extraction_status

    # Size stats
    cur.execute("SELECT MIN(size_mb), MAX(size_mb), AVG(size_mb), SUM(size_mb) FROM books")
    row = cur.fetchone()
    result["size_stats_mb"] = {
        "min": round(row[0], 0) if row[0] else 0,
        "max": round(row[1], 0) if row[1] else 0,
        "avg": round(row[2], 0) if row[2] else 0,
        "total": round(row[3], 0) if row[3] else 0,
    }

    conn.close()
    return result


def categorize_super_category(cat_name: str) -> str:
    """
    Map a category name to a super-category.

    Args:
        cat_name: Original category name.

    Returns:
        Super-category name.
    """
    if any(k in cat_name for k in ["الفقه", "فقه", "فرائض", "فتاوى", "سياسة", "قضاء"]):
        return "Fiqh (Jurisprudence)"
    elif any(k in cat_name for k in ["حديث", "السنة", "شروح", "تخريج", "أطراف", "علل", "جوامع"]):
        return "Hadith (Traditions)"
    elif any(k in cat_name for k in ["عقيدة", "فرق", "ردود"]):
        return "Aqeedah (Creed)"
    elif any(k in cat_name for k in ["تفسير", "قرآن", "تجويد", "قراءات"]):
        return "Quran & Tafsir"
    elif any(k in cat_name for k in ["سيرة", "تاريخ", "تراجم", "طبقات", "أنساب", "بلدان", "رحلات"]):
        return "History & Biography"
    elif any(k in cat_name for k in ["لغة", "غريب", "معاجم", "نحو", "صرف", "أدب", "بلاغة", "عروض", "دواوين", "شعرية"]):
        return "Arabic Language & Literature"
    elif any(k in cat_name for k in ["رقائق", "آداب", "أذكار"]):
        return "Spirituality & Ethics"
    elif any(k in cat_name for k in ["عامة", "علوم أخرى", "منطق", "#", "فهارس"]):
        return "General & Reference"
    else:
        return "Other"


def print_report(books_stats: dict, metadata_stats: dict, detailed: bool = False) -> None:
    """
    Print formatted analysis report.

    Args:
        books_stats: Extracted books statistics.
        metadata_stats: Metadata statistics.
        detailed: Show detailed output.
    """
    print("=" * 70)
    print("COMPLETE DATASET ANALYSIS - datasets/data")
    print("=" * 70)

    # 1. Extracted Books
    print(f"\n{'📚' if not detailed else '1.'} EXTRACTED BOOKS")
    print("-" * 70)
    if "error" in books_stats:
        print(f"  ✗ {books_stats['error']}")
    else:
        print(f"  Total files:  {books_stats['total_files']:,}")
        print(f"  Total size:   {books_stats['total_size_human']}")
        print(f"  Avg size:     {books_stats['avg_size_human']}")
        print(f"  Largest:      {books_stats['largest_human']}")
        print(f"  Smallest:     {books_stats['smallest_human']}")

        dist = books_stats.get("size_distribution", {})
        print(f"  > 10MB:       {dist.get('> 10MB', 0)} books")
        print(f"  1-10MB:       {dist.get('1-10MB', 0)} books")
        print(f"  < 1MB:        {dist.get('< 1MB', 0)} books")

    # 2. Metadata
    print(f"\n{'📋' if not detailed else '2.'} METADATA")
    print("-" * 70)
    print(f"  Categories: {metadata_stats.get('categories_count', 'N/A')}")
    print(f"  Authors:    {metadata_stats.get('authors_count', 'N/A'):,}")

    # 3. Category Distribution
    books_db = metadata_stats.get("books_db", {})
    if "error" not in books_db:
        categories = books_db.get("categories", [])
        if categories:
            print(f"\n{'📊' if not detailed else '3.'} CATEGORY DISTRIBUTION ({books_db.get('total_categories', 0)} categories)")
            print("-" * 70)
            print(f"{'Category':<30} {'Books':>6} {'Total GB':>8} {'Avg MB':>7} {'Min MB':>7} {'Max MB':>7}")
            print("-" * 70)

            for cat in categories:
                print(
                    f"{cat['name']:<30} {cat['count']:>6,} {cat['total_gb']:>8.1f} "
                    f"{cat['avg_mb']:>7.0f} {cat['min_mb']:>7.0f} {cat['max_mb']:>7.0f}"
                )

        # 4. Super-category summary
        super_cats = books_db.get("super_categories", {})
        if super_cats:
            print(f"\n{'🎯' if not detailed else '4.'} SUPER-CATEGORY SUMMARY")
            print("-" * 50)
            print(f"{'Super-Category':<35} {'Books':>6} {'Size GB':>8}")
            print("-" * 50)
            for group, stats in sorted(super_cats.items(), key=lambda x: -x[1]["books"]):
                print(f"{group:<35} {stats['books']:>6,} {stats['size_gb']:>8.1f}")

        # Extraction status
        extraction = books_db.get("extraction_status", {})
        if extraction:
            print(f"\n  Extraction Status:")
            for status, count in extraction.items():
                print(f"    {status}: {count:,}")

    # 5. Chunking Strategy Recommendations
    if detailed and super_cats:
        print(f"\n{'📝' if not detailed else '5.'} RECOMMENDED CHUNKING STRATEGY")
        print("-" * 60)
        print(f"{'Super-Category':<35} {'Chunk Size':>12} {'Est. Chunks':>12}")
        print("-" * 60)

        chunk_estimates = {
            "Hadith (Traditions)": ("1 hadith each", "~650K"),
            "Fiqh (Jurisprudence)": ("300-500 chars", "~800K"),
            "Quran & Tafsir": ("1 ayah + tafsir", "~50K"),
            "Aqeedah (Creed)": ("300-500 chars", "~100K"),
            "History & Biography": ("400-600 chars", "~500K"),
            "Arabic Language & Literature": ("300-500 chars", "~300K"),
            "Spirituality & Ethics": ("300-500 chars", "~200K"),
            "General & Reference": ("300-500 chars", "~100K"),
            "Other": ("300-500 chars", "~50K"),
        }

        for group in sorted(super_cats.keys()):
            if group in chunk_estimates:
                chunk_size, est = chunk_estimates[group]
                print(f"{group:<35} {chunk_size:>12} {est:>12}")

    # 6. Priority Ranking
    if detailed:
        print(f"\n{'🚀' if not detailed else '6.'} EMBEDDING PRIORITY (by ROI)")
        print("-" * 70)
        priorities = [
            ("P0 - Critical", "Sanadset Hadith", "650K hadith", "Already chunked"),
            ("P0 - Critical", "Quran Ayahs", "6,236 ayahs", "Check quran.db"),
            ("P1 - High", "Hadith Books (كتب السنة)", "1,226 books, 1.7 GB", "Need re-chunking"),
            ("P1 - High", "Tafsir Books", "270 books, 1.7 GB", "High-value content"),
            ("P2 - Medium", "Fiqh Books (all madhhabs)", "1,000+ books, 2.5 GB", "Core Islamic law"),
            ("P2 - Medium", "Aqeedah Books", "794 books, 0.6 GB", "Core theology"),
            ("P3 - Low", "History & Biography", "1,000+ books, 2.4 GB", "Historical context"),
            ("P3 - Low", "Arabic Language", "500+ books, 0.8 GB", "Grammar, lexicon"),
        ]

        for priority, name, volume, status in priorities:
            print(f"  {priority}: {name}")
            print(f"    Volume: {volume}")
            print(f"    Status: {status}")
            print()

    print("=" * 70)


# ── Main ─────────────────────────────────────────────────────────────────


def main():
    """Run dataset analysis."""
    parser = argparse.ArgumentParser(
        description="Analyze Athar datasets",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/analysis/analyze_dataset.py
  python scripts/analysis/analyze_dataset.py --report
  python scripts/analysis/analyze_dataset.py --json
        """,
    )
    parser.add_argument("--report", action="store_true", help="Show detailed report")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    args = parser.parse_args()

    print("\n🔍 Analyzing datasets...\n")

    # Run analysis
    books_stats = analyze_extracted_books()
    metadata_stats = analyze_metadata()

    if args.json:
        # JSON output
        output = {
            "extracted_books": books_stats,
            "metadata": metadata_stats,
        }
        print(json.dumps(output, indent=2, ensure_ascii=False, default=str))
    else:
        # Formatted report
        print_report(books_stats, metadata_stats, detailed=args.report)


if __name__ == "__main__":
    main()
