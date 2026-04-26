#!/usr/bin/env python3
"""
Create Mini-Dataset for Burhan Islamic QA System MVP.

Extracts representative samples from full datasets to create a
GitHub-friendly mini-dataset (<50 MB) that demonstrates all features.

The mini-dataset includes:
- Fiqh passages from Shamela books
- Hadith from Sanadset 368K dataset
- Aqeedah, Seerah, History, Arabic Language, Spirituality passages
- General Islamic knowledge passages

Usage:
    python scripts/data/create_mini_dataset.py
    python scripts/data/create_mini_dataset.py --output data/my_mini_dataset

Output:
    data/mini_dataset/
    ├── fiqh_passages.jsonl                 (sampled fiqh docs)
    ├── hadith_passages.jsonl               (sampled hadith docs)
    ├── aqeedah_passages.jsonl              (sampled aqeedah docs)
    ├── seerah_passages.jsonl               (sampled seerah docs)
    ├── islamic_history_passages.jsonl      (sampled history docs)
    ├── arabic_language_passages.jsonl      (sampled language docs)
    ├── spirituality_passages.jsonl         (sampled spirituality docs)
    ├── general_islamic.jsonl               (sampled general docs)
    ├── collection_stats.json               (statistics)
    ├── book_selections.json                (metadata)
    └── README.md                           (documentation)

Author: Burhan Engineering Team
"""

import csv
import json
import random
import re
import sys
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
    format_size,
    ensure_dir,
)

# ── Configuration ────────────────────────────────────────────────────────

# Reproducible sampling
random.seed(42)

# Paths
PROJECT_ROOT = get_project_root()
DATA_DIR = get_datasets_dir("data")
BOOKS_DIR = DATA_DIR / "extracted_books"
METADATA_DIR = DATA_DIR / "metadata"
SANADSET_CSV = (
    get_datasets_dir()
    / "Sanadset 368K Data on Hadith Narrators"
    / "Sanadset 368K Data on Hadith Narrators"
    / "sanadset.csv"
)
OUTPUT_DIR = get_data_dir("mini_dataset")

# Chunking parameters
MIN_CHUNK_SIZE = 250
MAX_CHUNK_SIZE = 500

# Book selections by collection
BOOK_SELECTIONS: dict[str, list[dict]] = {
    "fiqh_passages": [
        {"book_pattern": "بداية المجتهد", "chunks": 80, "category": "الفقه العام"},
        {"book_pattern": "المغني", "chunks": 60, "category": "الفقه الحنبلي"},
        {"book_pattern": "الأم للشافعي", "chunks": 60, "category": "الفقه الشافعي"},
        {"book_pattern": "المدونة", "chunks": 60, "category": "الفقه المالكي"},
        {"book_pattern": "الهداية", "chunks": 60, "category": "الفقه الحنفي"},
        {"book_pattern": "فتاوى", "chunks": 50, "category": "الفتاوى"},
        {"book_pattern": "المحلى", "chunks": 40, "category": "مسائل فقهية"},
        {"book_pattern": "أصول", "chunks": 40, "category": "أصول الفقه"},
    ],
    "aqeedah_passages": [
        {"book_pattern": "العقيدة الطحاوية", "chunks": 60, "category": "العقيدة"},
        {"book_pattern": "كتاب التوحيد", "chunks": 50, "category": "العقيدة"},
        {"book_pattern": "لمعة الاعتقاد", "chunks": 40, "category": "العقيدة"},
        {"book_pattern": "العقيدة الواسطية", "chunks": 30, "category": "العقيدة"},
        {"book_pattern": "شرح أصول", "chunks": 20, "category": "العقيدة"},
    ],
    "seerah_passages": [
        {"book_pattern": "زاد المعاد", "chunks": 60, "category": "السيرة النبوية"},
        {"book_pattern": "السيرة النبوية", "chunks": 50, "category": "السيرة النبوية"},
        {"book_pattern": "الرحيق المختوم", "chunks": 50, "category": "السيرة النبوية"},
        {"book_pattern": "فقه السيرة", "chunks": 40, "category": "السيرة النبوية"},
    ],
    "islamic_history_passages": [
        {"book_pattern": "تاريخ الطبري", "chunks": 80, "category": "التاريخ"},
        {"book_pattern": "البداية والنهاية", "chunks": 60, "category": "التاريخ"},
        {"book_pattern": "وفيات الأعيان", "chunks": 60, "category": "التراجم"},
        {"book_pattern": "طبقات", "chunks": 50, "category": "التراجم"},
        {"book_pattern": "معجم البلدان", "chunks": 30, "category": "البلدان"},
        {"book_pattern": "رحلة", "chunks": 20, "category": "الرحلات"},
    ],
    "arabic_language_passages": [
        {"book_pattern": "ألفية ابن مالك", "chunks": 80, "category": "النحو"},
        {"book_pattern": "لسان العرب", "chunks": 60, "category": "المعاجم"},
        {"book_pattern": "النحو الوافي", "chunks": 50, "category": "النحو"},
        {"book_pattern": "البلاغة", "chunks": 40, "category": "البلاغة"},
        {"book_pattern": "ديوان", "chunks": 40, "category": "الشعر"},
        {"book_pattern": "الصرف", "chunks": 30, "category": "الصرف"},
    ],
    "spirituality_passages": [
        {"book_pattern": "إحياء علوم الدين", "chunks": 60, "category": "الرقائق"},
        {"book_pattern": "رياض الصالحين", "chunks": 50, "category": "الرقائق"},
        {"book_pattern": "الآداب الشرعية", "chunks": 40, "category": "الرقائق"},
        {"book_pattern": "مدارج السالكين", "chunks": 30, "category": "الرقائق"},
        {"book_pattern": "التذكرة", "chunks": 20, "category": "الرقائق"},
    ],
    "general_islamic": [
        {"book_pattern": "المنطق", "chunks": 50, "category": "المنطق"},
        {"book_pattern": "الجوامع", "chunks": 60, "category": "الجوامع"},
        {"book_pattern": "الطب", "chunks": 40, "category": "الطب"},
        {"book_pattern": "فهارس", "chunks": 50, "category": "الفهارس"},
        {"book_pattern": "عامة", "chunks": 100, "category": "كتب عامة"},
    ],
}

logger = setup_script_logger("create-mini-dataset")


# ── Book Matching ────────────────────────────────────────────────────────


def find_book_files(pattern: str, limit: int = 5) -> list[Path]:
    """
    Find book files matching a pattern with flexible matching.

    Tries exact match first, then falls back to partial matching
    using the first 5 characters of the pattern.

    Args:
        pattern: Arabic book name pattern to match.
        limit: Maximum number of matches to return.

    Returns:
        List of matching book file paths.
    """
    if not BOOKS_DIR.exists():
        logger.warning("books_dir_not_found", path=str(BOOKS_DIR))
        return []

    matches: list[Path] = []

    # Try exact pattern first
    for f in BOOKS_DIR.glob("*.txt"):
        if pattern in f.name:
            matches.append(f)
            if len(matches) >= limit:
                return matches

    # If no matches, try partial matching (first 5 chars of pattern)
    if len(pattern) > 5 and not matches:
        short_pattern = pattern[:5]
        for f in BOOKS_DIR.glob("*.txt"):
            if short_pattern in f.name:
                matches.append(f)
                if len(matches) >= limit:
                    break

    return matches


# ── Chunk Extraction ─────────────────────────────────────────────────────


def extract_chunks_from_book(book_file: Path, num_chunks: int) -> list[str]:
    """
    Extract random chunks from a book file.

    Chunks are extracted respecting paragraph boundaries and
    constrained to MIN_CHUNK_SIZE - MAX_CHUNK_SIZE characters.

    Args:
        book_file: Path to the book text file.
        num_chunks: Number of chunks to extract.

    Returns:
        List of chunk strings.
    """
    if not book_file.exists():
        return []

    try:
        with open(book_file, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()

        # Clean content
        content = re.sub(r"\[Page \d+\]", "", content)
        content = re.sub(r"\n{3,}", "\n\n", content)  # Normalize newlines

        # Split into paragraphs
        paragraphs = [p.strip() for p in content.split("\n\n") if len(p.strip()) > MIN_CHUNK_SIZE]

        if not paragraphs:
            # Try splitting by single newlines
            paragraphs = [l.strip() for l in content.split("\n") if len(l.strip()) > MIN_CHUNK_SIZE]

        if not paragraphs:
            return []

        # Sample paragraphs
        selected = random.sample(paragraphs, min(num_chunks * 2, len(paragraphs)))

        chunks: list[str] = []
        for para in selected:
            if len(chunks) >= num_chunks:
                break

            # If paragraph is too long, split it
            if len(para) > MAX_CHUNK_SIZE:
                sentences = re.split(r"[.!?؟]\s+", para)
                current_chunk = ""
                for sentence in sentences:
                    if len(current_chunk) + len(sentence) <= MAX_CHUNK_SIZE:
                        current_chunk += sentence + ". "
                    else:
                        if len(current_chunk) > MIN_CHUNK_SIZE:
                            chunks.append(current_chunk.strip())
                        current_chunk = sentence + ". "
                if len(current_chunk) > MIN_CHUNK_SIZE:
                    chunks.append(current_chunk.strip())
            else:
                chunks.append(para[:MAX_CHUNK_SIZE])

        return chunks[:num_chunks]

    except Exception as e:
        logger.warning("extract_error", book=book_file.name, error=str(e))
        return []


# ── Hadith Sampling ──────────────────────────────────────────────────────


def sample_sanadset_hadith(num_samples: int = 300) -> list[dict]:
    """
    Sample hadith from Sanadset CSV with balanced collection representation.

    Samples evenly from major hadith collections (Sahih Bukhari, Muslim, etc.)
    to ensure diverse coverage.

    Args:
        num_samples: Total number of hadith to sample.

    Returns:
        List of hadith document dicts ready for JSONL output.
    """
    if not SANADSET_CSV.exists():
        logger.warning("sanadset_not_found", path=str(SANADSET_CSV))
        return []

    logger.info("sampling_hadith", target=num_samples)

    # Increase CSV field size limit for large hadith
    try:
        csv.field_size_limit(sys.maxsize)
    except OverflowError:
        csv.field_size_limit(2**31 - 1)

    hadith_by_book: dict[str, list[dict]] = {}

    # First pass: group hadith by book
    with open(SANADSET_CSV, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            book = row.get("Book", "").strip()
            if book:
                hadith_by_book.setdefault(book, []).append(row)

    # Select major hadith collections
    major_collections = [
        "صحيح البخاري",
        "صحيح مسلم",
        "سنن أبي داود",
        "سنن الترمذي",
        "سنن النسائي",
        "سنن ابن ماجه",
        "مسند أحمد",
    ]

    sampled: list[dict] = []
    samples_per_book = num_samples // len(major_collections)

    with ProgressBar(total=num_samples, desc="Sampling Hadith", unit="hadith") as bar:
        for collection_name in major_collections:
            matching_books = [b for b in hadith_by_book.keys() if collection_name in b]

            for book in matching_books[:2]:  # Max 2 books per collection
                available = hadith_by_book[book]
                num_to_sample = min(samples_per_book // 2, len(available))

                if num_to_sample <= 0:
                    continue

                sample = random.sample(available, num_to_sample)

                for row in sample:
                    sanad_raw = row.get("Sanad", "")
                    sanad_clean = re.sub(r"<[^>]+>", "", sanad_raw).strip()
                    matn = row.get("Matn", "").strip()
                    book_name = row.get("Book", "").strip()

                    # Build content
                    content_parts = []
                    if matn:
                        content_parts.append(matn)
                    if sanad_clean and sanad_clean != "No SANAD":
                        content_parts.append(sanad_clean)
                    if book_name:
                        content_parts.append(book_name)

                    content = " | ".join(content_parts)[:3000]

                    sampled.append({
                        "chunk_index": len(sampled),
                        "content": content,
                        "metadata": {
                            "type": "hadith",
                            "book": book_name,
                            "num_hadith": row.get("Num_hadith", ""),
                            "matn": matn[:2000],
                            "sanad": sanad_clean[:1000],
                            "sanad_length": row.get("Sanad_Length", ""),
                            "dataset": "sanadset_mini",
                            "language": "ar",
                        },
                    })

                    bar.update(1)

                    if len(sampled) >= num_samples:
                        break

            if len(sampled) >= num_samples:
                break

    logger.info("hadith_sampled", count=len(sampled))
    return sampled


# ── Collection Extraction ────────────────────────────────────────────────


def extract_books_for_collection(
    collection_name: str,
    selections: list[dict],
) -> list[dict]:
    """
    Extract chunks from selected books for a collection.

    Args:
        collection_name: Name of the collection (e.g., 'fiqh_passages').
        selections: List of book selection configs.

    Returns:
        List of document dicts.
    """
    logger.info("extracting_collection", collection=collection_name)

    all_chunks: list[dict] = []

    # Count total target chunks for progress bar
    total_target = sum(s["chunks"] for s in selections)

    with ProgressBar(total=total_target, desc=f"Extracting {collection_name}", unit="chunks") as bar:
        for selection in selections:
            pattern = selection["book_pattern"]
            num_chunks = selection["chunks"]
            category = selection["category"]

            book_files = find_book_files(pattern, limit=3)

            if not book_files:
                logger.warning("no_books_found", pattern=pattern)
                bar.update(num_chunks)  # Skip progress
                continue

            book_file = book_files[0]
            chunks = extract_chunks_from_book(book_file, num_chunks)

            for chunk in chunks:
                all_chunks.append({
                    "chunk_index": len(all_chunks),
                    "content": chunk[:MAX_CHUNK_SIZE],
                    "metadata": {
                        "type": collection_name.split("_")[0],
                        "book": book_file.name,
                        "category": category,
                        "language": "ar",
                        "collection": collection_name,
                    },
                })
                bar.update(1)

    logger.info("collection_extracted", collection=collection_name, chunks=len(all_chunks))
    return all_chunks


# ── Output Helpers ───────────────────────────────────────────────────────


def save_jsonl(documents: list[dict], filepath: Path) -> None:
    """
    Save documents as JSONL file.

    Args:
        documents: List of document dicts.
        filepath: Output file path.
    """
    ensure_dir(filepath.parent)

    with open(filepath, "w", encoding="utf-8") as f:
        for doc in documents:
            f.write(json.dumps(doc, ensure_ascii=False) + "\n")

    size_mb = filepath.stat().st_size / 1e6
    logger.info("saved_jsonl", file=filepath.name, docs=len(documents), size_mb=f"{size_mb:.1f}")


def create_readme(stats: dict[str, dict], total_docs: int, total_size_mb: float) -> str:
    """
    Generate README.md for the mini-dataset.

    Args:
        stats: Collection statistics dict.
        total_docs: Total document count.
        total_size_mb: Total estimated size in MB.

    Returns:
        README markdown content.
    """
    rows = []
    for coll_name, coll_stats in stats.items():
        docs = coll_stats.get("documents", 0)
        size = coll_stats.get("size_mb", 0)
        rows.append(f"| {coll_name} | {docs} | {size:.1f} MB |")

    return f"""# Burhan Mini-Dataset for MVP

This mini-dataset contains representative samples from the full Burhan datasets,
optimized for GitHub (<50 MB) while demonstrating all system features.

## Dataset Overview

- **Total Documents:** {total_docs:,}
- **Estimated Size:** {total_size_mb:.1f} MB
- **Collections:** {len(stats)}
- **Language:** Arabic

## Collections

| Collection | Documents | Size (est.) |
|------------|-----------|-------------|
{chr(10).join(rows)}

## File Format

Each `.jsonl` file contains one JSON object per line:

```json
{{
  "chunk_index": 0,
  "content": "Arabic text here...",
  "metadata": {{
    "type": "fiqh",
    "book": "book_name.txt",
    "category": "الفقه العام",
    "language": "ar",
    "collection": "fiqh_passages"
  }}
}}
```

## Usage

### Load in Python
```python
import json

documents = []
with open('data/mini_dataset/fiqh_passages.jsonl', 'r', encoding='utf-8') as f:
    for line in f:
        documents.append(json.loads(line))

print(f"Loaded {{len(documents)}} documents")
```

## Full Datasets

This is a **sample** for MVP/demo purposes. Full datasets are available separately:
- **Shamela Library:** 8,425 books (17.16 GB)
- **Sanadset Hadith:** 650,986 hadith (1.43 GB)

Full datasets are excluded from Git per `.gitignore`.

---

**Created:** Auto-generated
**Purpose:** MVP demonstration and GitHub hosting
"""


# ── Main Pipeline ────────────────────────────────────────────────────────


def main(output_dir: Optional[str] = None) -> None:
    """
    Create complete mini-dataset.

    Args:
        output_dir: Custom output directory (default: data/mini_dataset).
    """
    target_dir = Path(output_dir) if output_dir else OUTPUT_DIR
    ensure_dir(target_dir)

    print(f"\n{'=' * 70}")
    print("  Burhan MINI-DATASET CREATOR")
    print(f"{'=' * 70}")
    print(f"  Output: {target_dir}")
    print(f"  Books:  {BOOKS_DIR}")
    print(f"  Hadith: {SANADSET_CSV}")
    print(f"{'=' * 70}\n")

    # Define collection extraction order
    collections = [
        ("fiqh_passages", BOOK_SELECTIONS["fiqh_passages"]),
        ("aqeedah_passages", BOOK_SELECTIONS["aqeedah_passages"]),
        ("seerah_passages", BOOK_SELECTIONS["seerah_passages"]),
        ("islamic_history_passages", BOOK_SELECTIONS["islamic_history_passages"]),
        ("arabic_language_passages", BOOK_SELECTIONS["arabic_language_passages"]),
        ("spirituality_passages", BOOK_SELECTIONS["spirituality_passages"]),
        ("general_islamic", BOOK_SELECTIONS["general_islamic"]),
    ]

    collection_stats: dict[str, dict] = {}
    total_docs = 0

    # Extract book-based collections
    for coll_name, selections in collections:
        docs = extract_books_for_collection(coll_name, selections)
        save_jsonl(docs, target_dir / f"{coll_name}.jsonl")

        size_mb = len(docs) * 0.017  # ~17KB per doc estimate
        collection_stats[coll_name] = {"documents": len(docs), "size_mb": size_mb}
        total_docs += len(docs)

    # Sample hadith from Sanadset
    hadith_docs = sample_sanadset_hadith(300)
    save_jsonl(hadith_docs, target_dir / "hadith_passages.jsonl")
    hadith_size = len(hadith_docs) * 0.02
    collection_stats["hadith_passages"] = {"documents": len(hadith_docs), "size_mb": hadith_size}
    total_docs += len(hadith_docs)

    # Calculate total size
    total_size_mb = sum(s["size_mb"] for s in collection_stats.values())

    # Save metadata
    save_jsonl([], target_dir / ".placeholder")  # Ensure directory is tracked

    with open(target_dir / "collection_stats.json", "w", encoding="utf-8") as f:
        json.dump(collection_stats, f, indent=2, ensure_ascii=False)

    with open(target_dir / "book_selections.json", "w", encoding="utf-8") as f:
        json.dump(BOOK_SELECTIONS, f, indent=2, ensure_ascii=False)

    # Create README
    with open(target_dir / "README.md", "w", encoding="utf-8") as f:
        f.write(create_readme(collection_stats, total_docs, total_size_mb))

    # Print summary
    print(f"\n{'=' * 70}")
    print("  MINI-DATASET CREATION COMPLETE")
    print(f"{'=' * 70}")
    print(f"  Total documents: {total_docs:,}")
    print(f"  Estimated size:  {total_size_mb:.1f} MB")
    print(f"  Collections:     {len(collection_stats)}")
    print(f"\n  Files:")
    for f in sorted(target_dir.glob("*")):
        if f.name.startswith("."):
            continue
        size = format_size(f.stat().st_size)
        print(f"    {f.name:<40s} {size:>10s}")
    print(f"\n{'=' * 70}\n")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Create mini-dataset for Burhan MVP",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Example: python scripts/data/create_mini_dataset.py --output data/my_mini",
    )
    parser.add_argument("--output", type=str, default=None, help="Custom output directory")
    args = parser.parse_args()

    try:
        main(output_dir=args.output)
    except KeyboardInterrupt:
        print("\n\n  Interrupted by user.")
        sys.exit(1)
    except Exception as e:
        logger.error("fatal_error", error=str(e), exc_info=True)
        print(f"\nFatal error: {e}")
        sys.exit(1)
