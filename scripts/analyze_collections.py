#!/usr/bin/env python3
"""
Collection Quality Dashboard for Athar Islamic QA System.

Analyzes all 10 collections and generates comprehensive statistics:
- Document counts and sizes
- Author distribution
- Time period coverage
- Collection quality metrics
- Search readiness assessment

Usage:
    python scripts/analyze_collections.py
    python scripts/analyze_collections.py --output dashboard.json
    python scripts/analyze_collections.py --report
"""

import json
import time
from pathlib import Path
from collections import Counter, defaultdict
from datetime import datetime

COLLECTIONS_DIR = Path("data/processed/lucene_pages/collections")
METADATA_DIR = Path("data/processed")

COLLECTIONS = [
    "fiqh_passages",
    "hadith_passages",
    "quran_tafsir",
    "aqeedah_passages",
    "seerah_passages",
    "islamic_history_passages",
    "arabic_language_passages",
    "spirituality_passages",
    "general_islamic",
    "usul_fiqh",
]


def analyze_collection(filepath: Path) -> dict:
    """Analyze a single collection file."""
    stats = {
        "file": filepath.name,
        "file_size_mb": filepath.stat().st_size / (1024 * 1024),
        "doc_count": 0,
        "avg_content_length": 0,
        "min_content_length": float("inf"),
        "max_content_length": 0,
        "authors": Counter(),
        "books": Counter(),
        "categories": Counter(),
        "eras": Counter(),
        "pages_with_chapters": 0,
        "pages_with_sections": 0,
        "avg_page": 0,
        "total_content_chars": 0,
    }

    page_numbers = []

    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            try:
                doc = json.loads(line)
                stats["doc_count"] += 1

                # Content analysis
                content = doc.get("content", "")
                content_len = len(content)
                stats["total_content_chars"] += content_len
                stats["min_content_length"] = min(stats["min_content_length"], content_len)
                stats["max_content_length"] = max(stats["max_content_length"], content_len)

                # Author analysis
                author = doc.get("author", "")
                if author:
                    stats["authors"][author] += 1

                # Book analysis
                book_title = doc.get("title", "")
                if book_title:
                    stats["books"][book_title] += 1

                # Category
                category = doc.get("category", "")
                if category:
                    stats["categories"][category] += 1

                # Era classification
                author_death = doc.get("author_death")
                if author_death:
                    era = classify_era(author_death)
                    stats["eras"][era] += 1

                # Structure analysis
                if doc.get("chapter"):
                    stats["pages_with_chapters"] += 1
                if doc.get("section"):
                    stats["pages_with_sections"] += 1

                # Page analysis
                page = doc.get("page")
                if page:
                    page_numbers.append(page)

            except (json.JSONDecodeError, Exception):
                continue

    # Calculate averages
    if stats["doc_count"] > 0:
        stats["avg_content_length"] = stats["total_content_chars"] // stats["doc_count"]
    if page_numbers:
        stats["avg_page"] = sum(page_numbers) / len(page_numbers)
    if stats["min_content_length"] == float("inf"):
        stats["min_content_length"] = 0

    # Convert Counters to dicts for JSON serialization
    stats["authors"] = dict(stats["authors"].most_common(20))
    stats["books"] = dict(stats["books"].most_common(20))
    stats["categories"] = dict(stats["categories"].most_common())
    stats["eras"] = dict(stats["eras"])

    return stats


def classify_era(death_year_hijri: int) -> str:
    """Classify scholar's era based on death year (Hijri)."""
    if death_year_hijri <= 100:
        return "prophetic"
    elif death_year_hijri <= 200:
        return "tabiun"
    elif death_year_hijri <= 500:
        return "classical"
    elif death_year_hijri <= 900:
        return "medieval"
    elif death_year_hijri <= 1300:
        return "ottoman"
    else:
        return "modern"


def load_metadata() -> dict:
    """Load metadata files for enriched analysis."""
    metadata = {}

    # Load master catalog
    master_file = METADATA_DIR / "master_catalog.json"
    if master_file.exists():
        with open(master_file) as f:
            metadata["master_catalog"] = json.load(f)
            metadata["book_count"] = len(metadata["master_catalog"])

    # Load author catalog
    author_file = METADATA_DIR / "author_catalog.json"
    if author_file.exists():
        with open(author_file) as f:
            metadata["authors"] = json.load(f)
            metadata["author_count"] = len(metadata["authors"])

    # Load category mapping
    category_file = METADATA_DIR / "category_mapping.json"
    if category_file.exists():
        with open(category_file) as f:
            metadata["categories"] = json.load(f)

    return metadata


def generate_report(all_stats: list[dict], metadata: dict) -> dict:
    """Generate comprehensive dashboard report."""
    total_docs = sum(s["doc_count"] for s in all_stats)
    total_size_mb = sum(s["file_size_mb"] for s in all_stats)
    total_chars = sum(s["total_content_chars"] for s in all_stats)

    # Aggregate author stats
    all_authors = Counter()
    all_eras = Counter()
    for stats in all_stats:
        for author, count in stats["authors"].items():
            all_authors[author] += count
        for era, count in stats["eras"].items():
            all_eras[era] += count

    # Quality scores
    structure_score = 0
    metadata_score = 0
    for stats in all_stats:
        if stats["doc_count"] > 0:
            # Structure: chapters and sections present
            chapter_pct = stats["pages_with_chapters"] / stats["doc_count"]
            section_pct = stats["pages_with_sections"] / stats["doc_count"]
            structure_score += (chapter_pct + section_pct) / 2

            # Metadata: authors and books present
            meta_ratio = len(stats["authors"]) / max(stats["doc_count"] / 100, 1)
            metadata_score += min(meta_ratio, 1.0)

    structure_score = (structure_score / len(all_stats)) * 100
    metadata_score = (metadata_score / len(all_stats)) * 100

    report = {
        "generated_at": datetime.now().isoformat(),
        "summary": {
            "total_collections": len(all_stats),
            "total_documents": total_docs,
            "total_size_mb": round(total_size_mb, 1),
            "total_size_gb": round(total_size_mb / 1024, 2),
            "total_content_chars": total_chars,
            "avg_doc_size_chars": total_chars // max(total_docs, 1),
        },
        "collections": all_stats,
        "top_authors": dict(all_authors.most_common(30)),
        "era_distribution": dict(all_eras),
        "metadata": {
            "books_in_catalog": metadata.get("book_count", 0),
            "authors_in_catalog": metadata.get("author_count", 0),
            "categories_mapped": len(metadata.get("categories", {})),
        },
        "quality_scores": {
            "structure_score": round(structure_score, 1),
            "metadata_score": round(metadata_score, 1),
            "overall_score": round((structure_score + metadata_score) / 2, 1),
        },
        "search_readiness": {
            "has_content": total_docs > 0,
            "has_metadata": metadata.get("book_count", 0) > 0,
            "has_authors": len(all_authors) > 0,
            "has_structure": structure_score > 50,
            "ready": total_docs > 0 and metadata.get("book_count", 0) > 0,
        },
    }

    return report


def print_summary(report: dict):
    """Print human-readable summary."""
    summary = report["summary"]
    print("=" * 70)
    print("🕌 ATHAR - COLLECTION QUALITY DASHBOARD")
    print("=" * 70)
    print(f"\n📊 SUMMARY:")
    print(f"  Collections:       {summary['total_collections']}")
    print(f"  Total Documents:   {summary['total_documents']:,}")
    print(f"  Total Size:        {summary['total_size_gb']} GB")
    print(f"  Avg Doc Size:      {summary['avg_doc_size_chars']:,} chars")

    print(f"\n📚 COLLECTIONS:")
    for coll in report["collections"]:
        print(f"  • {coll['file']:40s} {coll['doc_count']:>10,} docs  {coll['file_size_mb']:>8.1f} MB")

    print(f"\n👥 TOP AUTHORS:")
    for author, count in list(report["top_authors"].items())[:10]:
        print(f"  • {author:40s} {count:>10,}")

    print(f"\n⏳ ERA DISTRIBUTION:")
    for era, count in sorted(report["era_distribution"].items()):
        print(f"  • {era:20s} {count:>10,} ({count/summary['total_documents']*100:.1f}%)")

    print(f"\n📈 QUALITY SCORES:")
    scores = report["quality_scores"]
    print(f"  Structure:         {scores['structure_score']:.1f}%")
    print(f"  Metadata:          {scores['metadata_score']:.1f}%")
    print(f"  Overall:           {scores['overall_score']:.1f}%")

    print(f"\n✅ SEARCH READINESS:")
    readiness = report["search_readiness"]
    for key, value in readiness.items():
        status = "✅" if value else "❌"
        print(f"  {status} {key:20s} {value}")

    print("=" * 70)


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Analyze collection quality")
    parser.add_argument("--output", type=str, help="Output JSON file")
    parser.add_argument("--report", action="store_true", help="Print summary report")
    args = parser.parse_args()

    print("🔍 Analyzing collections...")
    start_time = time.time()

    all_stats = []
    for collection in COLLECTIONS:
        filepath = COLLECTIONS_DIR / f"{collection}.jsonl"
        if filepath.exists():
            print(f"  Analyzing {collection}...")
            stats = analyze_collection(filepath)
            all_stats.append(stats)
        else:
            print(f"  ⚠️  {collection}: File not found")

    elapsed = time.time() - start_time
    print(f"\n✅ Analysis complete in {elapsed:.1f}s")

    # Load metadata
    metadata = load_metadata()

    # Generate report
    report = generate_report(all_stats, metadata)

    # Save to file
    if args.output:
        output_path = Path(args.output)
    else:
        output_path = Path("data/processed/collection_dashboard.json")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    print(f"💾 Dashboard saved to: {output_path}")

    # Print report
    if args.report or not args.output:
        print_summary(report)


if __name__ == "__main__":
    main()
