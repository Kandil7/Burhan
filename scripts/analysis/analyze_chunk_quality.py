#!/usr/bin/env python3
"""
Analyze hierarchical chunk quality.

Evaluates the output of chunk_all_books.py by analyzing:
- Chunk size distribution (target: 300-600 tokens / 600-1800 chars)
- Metadata completeness (all required fields present)
- Chapter/page boundary respect
- Content type distribution
- Overlap effectiveness
- Anomaly detection

Usage:
    python scripts/analyze_chunk_quality.py
    python scripts/analyze_chunk_quality.py --input data/processed/hierarchical_chunks.jsonl
    python scripts/analyze_chunk_quality.py --sample 10000
"""

from __future__ import annotations

import json
import math
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

# Add project root to path for src imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.utils import (
    ProgressBar,
    format_size,
    get_data_dir,
    get_script_logger,
    progress_iter,
)

# ── Configuration ────────────────────────────────────────────────────────

DEFAULT_INPUT = get_data_dir("processed/hierarchical_chunks.jsonl")
REPORT_FILE = get_data_dir("processed/chunk_quality_report.json")

logger = get_script_logger("chunk-quality")

# Quality thresholds
TARGET_MIN_CHARS = 600     # ~200 tokens
TARGET_MAX_CHARS = 1800    # ~600 tokens
IDEAL_MIN_CHARS = 800      # ~267 tokens
IDEAL_MAX_CHARS = 1400     # ~467 tokens
MAX_ALLOWED_CHARS = 3000   # Hard limit before flagging
MIN_METADATA_FIELDS = 7    # Required metadata fields per chunk

# Required metadata fields
REQUIRED_FIELDS = [
    "chunk_id", "book_id", "book_title", "author", "category",
    "content", "chunk_type",
]


# ── Analysis Functions ───────────────────────────────────────────────────

def load_chunks(
    input_path: Path,
    sample: int = 0,
) -> list[dict[str, Any]]:
    """
    Load chunks from JSONL file.

    Args:
        input_path: Path to JSONL file.
        sample: Maximum number of chunks to load (0 = all).

    Returns:
        List of chunk dicts.
    """
    chunks = []
    total_lines = sum(1 for _ in open(input_path, encoding="utf-8"))
    logger.info(f"Loading {total_lines:,} chunks from {input_path}")

    with open(input_path, encoding="utf-8") as f:
        for line in progress_iter(f, total=total_lines, desc="Loading chunks"):
            line = line.strip()
            if line:
                try:
                    chunks.append(json.loads(line))
                except json.JSONDecodeError:
                    logger.warning(f"Invalid JSON line: {line[:100]}")
                if sample > 0 and len(chunks) >= sample:
                    break

    logger.info(f"Loaded {len(chunks):,} chunks")
    return chunks


def analyze_size_distribution(
    chunks: list[dict[str, Any]],
) -> dict[str, Any]:
    """Analyze chunk size distribution."""
    sizes = [c.get("content_length", len(c.get("content", ""))) for c in chunks]

    if not sizes:
        return {"error": "No chunks to analyze"}

    sizes_sorted = sorted(sizes)
    n = len(sizes_sorted)

    # Percentiles
    def percentile(data: list[int], p: float) -> int:
        k = (len(data) - 1) * p / 100
        f = math.floor(k)
        c = math.ceil(k)
        if f == c:
            return data[int(k)]
        return int(data[f] * (c - k) + data[c] * (k - f))

    # Size categories
    tiny = sum(1 for s in sizes if s < TARGET_MIN_CHARS)
    ideal = sum(1 for s in sizes if IDEAL_MIN_CHARS <= s <= IDEAL_MAX_CHARS)
    in_range = sum(1 for s in sizes if TARGET_MIN_CHARS <= s <= TARGET_MAX_CHARS)
    large = sum(1 for s in sizes if s > TARGET_MAX_CHARS and s <= MAX_ALLOWED_CHARS)
    oversized = sum(1 for s in sizes if s > MAX_ALLOWED_CHARS)

    return {
        "total_chunks": n,
        "min_chars": sizes_sorted[0],
        "max_chars": sizes_sorted[-1],
        "mean_chars": round(sum(sizes) / n, 1),
        "median_chars": percentile(sizes_sorted, 50),
        "p25_chars": percentile(sizes_sorted, 25),
        "p75_chars": percentile(sizes_sorted, 75),
        "p95_chars": percentile(sizes_sorted, 95),
        "p99_chars": percentile(sizes_sorted, 99),
        "std_chars": round(
            math.sqrt(sum((s - sum(sizes) / n) ** 2 for s in sizes) / n), 1
        ),
        # Distribution buckets
        "distribution": {
            "tiny_lt_600": {"count": tiny, "pct": round(tiny / n * 100, 2)},
            "target_600_1800": {"count": in_range, "pct": round(in_range / n * 100, 2)},
            "ideal_800_1400": {"count": ideal, "pct": round(ideal / n * 100, 2)},
            "large_1800_3000": {"count": large, "pct": round(large / n * 100, 2)},
            "oversized_gt_3000": {"count": oversized, "pct": round(oversized / n * 100, 2)},
        },
        "quality_score": round(in_range / n * 100, 2) if n > 0 else 0,
    }


def analyze_metadata_completeness(
    chunks: list[dict[str, Any]],
) -> dict[str, Any]:
    """Analyze metadata completeness across chunks."""
    results: dict[str, Any] = {
        "total_chunks": len(chunks),
        "required_fields": REQUIRED_FIELDS,
        "field_presence": {},
        "field_empty": {},
        "complete_chunks": 0,
        "incomplete_chunks": 0,
        "missing_field_counts": Counter(),
        "book_id_coverage": 0,
        "category_coverage": 0,
        "page_number_coverage": 0,
        "chapter_title_coverage": 0,
    }

    # Check each field
    for field in REQUIRED_FIELDS:
        present = sum(1 for c in chunks if field in c)
        empty = sum(
            1 for c in chunks
            if field in c and (c[field] is None or c[field] == "" or c[field] == 0)
        )
        results["field_presence"][field] = {
            "present": present,
            "pct": round(present / len(chunks) * 100, 2) if chunks else 0,
        }
        results["field_empty"][field] = {
            "empty": empty,
            "pct": round(empty / len(chunks) * 100, 2) if chunks else 0,
        }

    # Check complete vs incomplete
    for chunk in chunks:
        missing = [f for f in REQUIRED_FIELDS if f not in chunk]
        if missing:
            results["incomplete_chunks"] += 1
            for f in missing:
                results["missing_field_counts"][f] += 1
        else:
            results["complete_chunks"] += 1

    # Coverage stats
    results["book_id_coverage"] = round(
        sum(1 for c in chunks if c.get("book_id")) / len(chunks) * 100, 2
    ) if chunks else 0
    results["category_coverage"] = round(
        sum(1 for c in chunks if c.get("category")) / len(chunks) * 100, 2
    ) if chunks else 0
    results["page_number_coverage"] = round(
        sum(1 for c in chunks if c.get("page_number")) / len(chunks) * 100, 2
    ) if chunks else 0
    results["chapter_title_coverage"] = round(
        sum(1 for c in chunks if c.get("chapter_title")) / len(chunks) * 100, 2
    ) if chunks else 0

    results["missing_field_counts"] = dict(results["missing_field_counts"])

    return results


def analyze_chunk_types(
    chunks: list[dict[str, Any]],
) -> dict[str, Any]:
    """Analyze chunk type distribution and quality per type."""
    type_counter: Counter = Counter()
    type_sizes: dict[str, list[int]] = defaultdict(list)

    for chunk in chunks:
        ct = chunk.get("chunk_type", "unknown")
        type_counter[ct] += 1
        cl = chunk.get("content_length", len(chunk.get("content", "")))
        type_sizes[ct].append(cl)

    results: dict[str, Any] = {
        "total_types": len(type_counter),
        "type_counts": dict(type_counter.most_common()),
        "type_quality": {},
    }

    for ct, sizes in type_sizes.items():
        n = len(sizes)
        in_range = sum(1 for s in sizes if TARGET_MIN_CHARS <= s <= TARGET_MAX_CHARS)
        results["type_quality"][ct] = {
            "count": n,
            "mean_size": round(sum(sizes) / n, 1) if n else 0,
            "in_range_pct": round(in_range / n * 100, 2) if n else 0,
            "min_size": min(sizes) if sizes else 0,
            "max_size": max(sizes) if sizes else 0,
        }

    return results


def analyze_boundary_respect(
    chunks: list[dict[str, Any]],
) -> dict[str, Any]:
    """
    Analyze whether chapter and page boundaries are respected.

    Checks:
    - Chunks with chapter_id should have chapter_title
    - Page numbers should be present and monotonically increasing within book
    """
    results: dict[str, Any] = {
        "total_chunks": len(chunks),
        "with_page_number": 0,
        "with_chapter_title": 0,
        "with_chapter_id": 0,
        "chapter_title_without_id": 0,
        "page_sequence_violations": 0,
    }

    for chunk in chunks:
        if chunk.get("page_number"):
            results["with_page_number"] += 1
        if chunk.get("chapter_title"):
            results["with_chapter_title"] += 1
        if chunk.get("chapter_id"):
            results["with_chapter_id"] += 1
        if chunk.get("chapter_title") and not chunk.get("chapter_id"):
            results["chapter_title_without_id"] += 1

    # Check page number monotonicity per book
    book_pages: dict[int, list[int]] = defaultdict(list)
    for chunk in chunks:
        bid = chunk.get("book_id")
        pn = chunk.get("page_number")
        if bid and pn:
            book_pages[bid].append(pn)

    violations = 0
    for bid, pages in book_pages.items():
        for i in range(1, len(pages)):
            if pages[i] < pages[i - 1]:
                violations += 1
                if violations <= 5:  # Log first 5
                    logger.debug(
                        f"Page violation in book {bid}: "
                        f"{pages[i-1]} → {pages[i]}"
                    )

    results["page_sequence_violations"] = violations
    results["books_with_page_data"] = len(book_pages)

    # Percentages
    if chunks:
        results["page_coverage_pct"] = round(
            results["with_page_number"] / len(chunks) * 100, 2
        )
        results["chapter_coverage_pct"] = round(
            results["with_chapter_title"] / len(chunks) * 100, 2
        )

    return results


def analyze_per_book_quality(
    chunks: list[dict[str, Any]],
    top_n: int = 20,
) -> dict[str, Any]:
    """Analyze quality metrics per book."""
    book_chunks: dict[int, list[dict]] = defaultdict(list)
    for chunk in chunks:
        bid = chunk.get("book_id", 0)
        book_chunks[bid].append(chunk)

    book_stats: list[dict] = []
    for bid, bchunks in book_chunks.items():
        sizes = [c.get("content_length", 0) for c in bchunks]
        in_range = sum(1 for s in sizes if TARGET_MIN_CHARS <= s <= TARGET_MAX_CHARS)
        types = Counter(c.get("chunk_type", "unknown") for c in bchunks)

        book_stats.append({
            "book_id": bid,
            "book_title": bchunks[0].get("book_title", ""),
            "category": bchunks[0].get("category", ""),
            "chunk_count": len(bchunks),
            "mean_size": round(sum(sizes) / len(sizes), 1) if sizes else 0,
            "in_range_pct": round(in_range / len(bchunks) * 100, 2) if bchunks else 0,
            "chunk_types": dict(types),
        })

    # Sort by chunk count
    book_stats.sort(key=lambda x: -x["chunk_count"])

    return {
        "total_books": len(book_stats),
        "top_books_by_chunks": book_stats[:top_n],
        "books_with_few_chunks": sum(1 for b in book_stats if b["chunk_count"] < 5),
        "books_with_many_chunks": sum(1 for b in book_stats if b["chunk_count"] > 1000),
    }


def detect_anomalies(
    chunks: list[dict[str, Any]],
) -> dict[str, Any]:
    """Detect anomalous chunks (empty content, oversized, duplicate IDs)."""
    anomalies: dict[str, Any] = {
        "empty_content": 0,
        "whitespace_only": 0,
        "oversized": 0,
        "duplicate_chunk_ids": 0,
        "missing_book_id": 0,
        "html_leakage": 0,
        "sample_issues": [],
    }

    seen_ids: set[str] = set()
    issue_count = 0

    for chunk in chunks:
        content = chunk.get("content", "")
        chunk_id = chunk.get("chunk_id", "")

        # Empty content
        if not content:
            anomalies["empty_content"] += 1
            if issue_count < 10:
                anomalies["sample_issues"].append({
                    "type": "empty_content",
                    "chunk_id": chunk_id,
                })
                issue_count += 1

        # Whitespace only
        elif not content.strip():
            anomalies["whitespace_only"] += 1
            if issue_count < 10:
                anomalies["sample_issues"].append({
                    "type": "whitespace_only",
                    "chunk_id": chunk_id,
                })
                issue_count += 1

        # Oversized
        cl = chunk.get("content_length", len(content))
        if cl > MAX_ALLOWED_CHARS:
            anomalies["oversized"] += 1
            if issue_count < 10:
                anomalies["sample_issues"].append({
                    "type": "oversized",
                    "chunk_id": chunk_id,
                    "size": cl,
                })
                issue_count += 1

        # Duplicate IDs
        if chunk_id in seen_ids:
            anomalies["duplicate_chunk_ids"] += 1
        seen_ids.add(chunk_id)

        # Missing book_id
        if not chunk.get("book_id"):
            anomalies["missing_book_id"] += 1

        # HTML leakage
        if "<span" in content or "</span>" in content:
            anomalies["html_leakage"] += 1
            if issue_count < 10:
                anomalies["sample_issues"].append({
                    "type": "html_leakage",
                    "chunk_id": chunk_id,
                    "preview": content[:100],
                })
                issue_count += 1

    return anomalies


def generate_report(
    chunks: list[dict[str, Any]],
) -> dict[str, Any]:
    """Generate comprehensive quality report."""
    logger.info("Analyzing size distribution...")
    size_dist = analyze_size_distribution(chunks)

    logger.info("Analyzing metadata completeness...")
    metadata = analyze_metadata_completeness(chunks)

    logger.info("Analyzing chunk types...")
    types = analyze_chunk_types(chunks)

    logger.info("Analyzing boundary respect...")
    boundaries = analyze_boundary_respect(chunks)

    logger.info("Analyzing per-book quality...")
    per_book = analyze_per_book_quality(chunks)

    logger.info("Detecting anomalies...")
    anomalies = detect_anomalies(chunks)

    # Overall quality score
    size_score = size_dist.get("quality_score", 0)
    metadata_score = (
        metadata["complete_chunks"] / len(chunks) * 100
        if chunks else 0
    )
    anomaly_penalty = (
        (anomalies["empty_content"] + anomalies["oversized"] + anomalies["html_leakage"])
        / len(chunks) * 100
        if chunks else 0
    )
    overall_score = max(0, min(100, size_score * 0.5 + metadata_score * 0.3 + (100 - anomaly_penalty) * 0.2))

    report = {
        "version": "1.0",
        "total_chunks_analyzed": len(chunks),
        "overall_quality_score": round(overall_score, 2),
        "size_distribution": size_dist,
        "metadata_completeness": metadata,
        "chunk_types": types,
        "boundary_respect": boundaries,
        "per_book_quality": per_book,
        "anomalies": anomalies,
        "recommendations": [],
    }

    # Generate recommendations
    recs = []
    if size_dist.get("distribution", {}).get("tiny_lt_600", {}).get("pct", 0) > 20:
        recs.append(
            "High percentage of tiny chunks (>20%). "
            "Consider merging small consecutive chunks."
        )
    if size_dist.get("distribution", {}).get("oversized_gt_3000", {}).get("pct", 0) > 5:
        recs.append(
            "Significant number of oversized chunks (>5%). "
            "Review chunking parameters for fatwa/hadith handling."
        )
    if metadata.get("incomplete_chunks", 0) > 0:
        recs.append(
            f"{metadata['incomplete_chunks']} chunks have incomplete metadata. "
            "Ensure all required fields are populated."
        )
    if anomalies["html_leakage"] > 0:
        recs.append(
            f"{anomalies['html_leakage']} chunks contain HTML leakage. "
            "Review HTML cleaning in chunker."
        )
    if anomalies["duplicate_chunk_ids"] > 0:
        recs.append(
            f"{anomalies['duplicate_chunk_ids']} duplicate chunk IDs found. "
            "Fix chunk ID generation to ensure uniqueness."
        )
    if boundaries.get("page_sequence_violations", 0) > 0:
        recs.append(
            f"{boundaries['page_sequence_violations']} page sequence violations. "
            "This may be expected for multi-edition books."
        )

    if not recs:
        recs.append("No critical issues found. Chunking quality is good.")

    report["recommendations"] = recs

    return report


def print_report_summary(report: dict[str, Any]) -> None:
    """Print formatted quality report summary."""
    print("\n" + "=" * 70)
    print("  CHUNK QUALITY ANALYSIS REPORT")
    print("=" * 70)

    print(f"\n  Chunks analyzed:      {report['total_chunks_analyzed']:,}")
    print(f"  Overall quality score: {report['overall_quality_score']:.1f}/100")

    # Size distribution
    sd = report.get("size_distribution", {})
    dist = sd.get("distribution", {})
    print(f"\n  ── Size Distribution ──")
    print(f"    Mean chunk size:    {sd.get('mean_chars', 0):,.0f} chars")
    print(f"    Median chunk size:  {sd.get('median_chars', 0):,} chars")
    print(f"    P25: {sd.get('p25_chars', 0):,}  P75: {sd.get('p75_chars', 0):,}  P95: {sd.get('p95_chars', 0):,}")
    print(f"    Tiny (<600):        {dist.get('tiny_lt_600', {}).get('count', 0):>8,} ({dist.get('tiny_lt_600', {}).get('pct', 0):.1f}%)")
    print(f"    Target (600-1800):  {dist.get('target_600_1800', {}).get('count', 0):>8,} ({dist.get('target_600_1800', {}).get('pct', 0):.1f}%)")
    print(f"    Ideal (800-1400):   {dist.get('ideal_800_1400', {}).get('count', 0):>8,} ({dist.get('ideal_800_1400', {}).get('pct', 0):.1f}%)")
    print(f"    Large (1800-3000):  {dist.get('large_1800_3000', {}).get('count', 0):>8,} ({dist.get('large_1800_3000', {}).get('pct', 0):.1f}%)")
    print(f"    Oversized (>3000):  {dist.get('oversized_gt_3000', {}).get('count', 0):>8,} ({dist.get('oversized_gt_3000', {}).get('pct', 0):.1f}%)")
    print(f"    Quality score:      {sd.get('quality_score', 0):.1f}%")

    # Metadata
    md = report.get("metadata_completeness", {})
    print(f"\n  ── Metadata Completeness ──")
    print(f"    Complete chunks:    {md.get('complete_chunks', 0):>8,} ({md.get('complete_chunks', 0) / max(report['total_chunks_analyzed'], 1) * 100:.1f}%)")
    print(f"    Incomplete chunks:  {md.get('incomplete_chunks', 0):>8,}")
    print(f"    Book ID coverage:   {md.get('book_id_coverage', 0):.1f}%")
    print(f"    Category coverage:  {md.get('category_coverage', 0):.1f}%")
    print(f"    Page # coverage:    {md.get('page_number_coverage', 0):.1f}%")
    print(f"    Chapter coverage:   {md.get('chapter_title_coverage', 0):.1f}%")

    # Chunk types
    ct = report.get("chunk_types", {})
    if ct.get("type_counts"):
        print(f"\n  ── Chunk Types ──")
        for ct_name, count in list(ct["type_counts"].items())[:10]:
            tq = ct.get("type_quality", {}).get(ct_name, {})
            print(f"    {ct_name:20s}: {count:>8,} chunks (mean: {tq.get('mean_size', 0):,.0f}, "
                  f"in-range: {tq.get('in_range_pct', 0):.1f}%)")

    # Boundaries
    br = report.get("boundary_respect", {})
    print(f"\n  ── Boundary Respect ──")
    print(f"    Page coverage:      {br.get('page_coverage_pct', 0):.1f}%")
    print(f"    Chapter coverage:   {br.get('chapter_coverage_pct', 0):.1f}%")
    print(f"    Page violations:    {br.get('page_sequence_violations', 0)}")

    # Anomalies
    an = report.get("anomalies", {})
    print(f"\n  ── Anomalies ──")
    print(f"    Empty content:      {an.get('empty_content', 0):>8,}")
    print(f"    Oversized:          {an.get('oversized', 0):>8,}")
    print(f"    HTML leakage:       {an.get('html_leakage', 0):>8,}")
    print(f"    Duplicate IDs:      {an.get('duplicate_chunk_ids', 0):>8,}")
    print(f"    Missing book_id:    {an.get('missing_book_id', 0):>8,}")

    # Recommendations
    recs = report.get("recommendations", [])
    if recs:
        print(f"\n  ── Recommendations ──")
        for i, rec in enumerate(recs, 1):
            print(f"    {i}. {rec}")

    # Per-book summary
    pb = report.get("per_book_quality", {})
    print(f"\n  ── Per-Book Summary ──")
    print(f"    Total books:        {pb.get('total_books', 0):,}")
    print(f"    Books with <5 ch.:  {pb.get('books_with_few_chunks', 0):,}")
    print(f"    Books with >1000 ch.: {pb.get('books_with_many_chunks', 0):,}")

    print("\n" + "=" * 70)
    print(f"  Report saved: {REPORT_FILE}")
    print("=" * 70)


# ── CLI ──────────────────────────────────────────────────────────────────

def main() -> None:
    """CLI entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Analyze hierarchical chunk quality",
    )
    parser.add_argument(
        "--input", type=str, default=str(DEFAULT_INPUT),
        help="Path to hierarchical_chunks.jsonl",
    )
    parser.add_argument(
        "--sample", type=int, default=0,
        help="Analyze only first N chunks (0 = all)",
    )
    args = parser.parse_args()

    input_path = Path(args.input)
    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}")
        print(f"Error: {input_path} not found. Run chunk_all_books.py first.")
        sys.exit(1)

    chunks = load_chunks(input_path, sample=args.sample)
    if not chunks:
        logger.error("No chunks loaded")
        print("Error: No chunks to analyze.")
        sys.exit(1)

    report = generate_report(chunks)

    # Save report
    with open(REPORT_FILE, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2, default=str)

    logger.info(f"Report saved to {REPORT_FILE}")
    print_report_summary(report)


if __name__ == "__main__":
    main()
