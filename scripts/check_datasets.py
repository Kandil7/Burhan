#!/usr/bin/env python3
"""
Dataset Integrity Checker for Athar Islamic QA System.

Verifies the integrity of all datasets used by the system:
- Checks file existence and accessibility
- Validates JSON/JSONL file structure
- Checks CSV file readability
- Reports statistics on all datasets
- Identifies corrupted or incomplete files

Usage:
    python scripts/check_datasets.py
    python scripts/check_datasets.py --fix        # Attempt to fix issues
    python scripts/check_datasets.py --report     # Generate detailed report
    python scripts/check_datasets.py --datasets   # Check only datasets/
    python scripts/check_datasets.py --data       # Check only data/

Author: Athar Engineering Team
"""

import argparse
import csv
import json
import sys
from pathlib import Path
from typing import Any

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.utils import (
    get_project_root,
    get_data_dir,
    get_datasets_dir,
    setup_script_logger,
    ProgressBar,
    format_size,
)

logger = setup_script_logger("check-datasets")

# ── Results Tracker ──────────────────────────────────────────────────────


class CheckResults:
    """Track check results across all datasets."""

    def __init__(self):
        self.passed: list[dict] = []
        self.warnings: list[dict] = []
        self.errors: list[dict] = []

    def add_pass(self, check: str, detail: str = "") -> None:
        self.passed.append({"check": check, "detail": detail})

    def add_warning(self, check: str, detail: str = "") -> None:
        self.warnings.append({"check": check, "detail": detail})

    def add_error(self, check: str, detail: str = "") -> None:
        self.errors.append({"check": check, "detail": detail})

    @property
    def total(self) -> int:
        return len(self.passed) + len(self.warnings) + len(self.errors)

    def summary(self) -> str:
        lines = [
            f"Total checks: {self.total}",
            f"  Passed:  {len(self.passed)}",
            f"  Warnings: {len(self.warnings)}",
            f"  Errors:  {len(self.errors)}",
        ]
        return "\n".join(lines)


# ── Check Functions ──────────────────────────────────────────────────────


def check_file_exists(results: CheckResults, path: Path, description: str) -> bool:
    """Check if a file or directory exists."""
    if path.exists():
        results.add_pass(f"Exists: {description}", str(path))
        return True
    else:
        results.add_error(f"Missing: {description}", str(path))
        return False


def check_json_file(results: CheckResults, path: Path, description: str) -> bool:
    """Check if a JSON file is valid."""
    if not check_file_exists(results, path, description):
        return False

    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        size = path.stat().st_size
        results.add_pass(f"Valid JSON: {description}", f"{format_size(size)}")
        return True
    except json.JSONDecodeError as e:
        results.add_error(f"Invalid JSON: {description}", str(e))
        return False
    except Exception as e:
        results.add_error(f"Error reading: {description}", str(e))
        return False


def check_jsonl_file(results: CheckResults, path: Path, description: str) -> tuple[bool, int]:
    """Check if a JSONL file is valid and count lines."""
    if not check_file_exists(results, path, description):
        return False, 0

    line_count = 0
    error_count = 0

    try:
        with open(path, "r", encoding="utf-8") as f:
            for i, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue
                try:
                    json.loads(line)
                    line_count += 1
                except json.JSONDecodeError as e:
                    error_count += 1
                    if error_count <= 3:
                        results.add_warning(
                            f"Invalid JSONL line: {description}",
                            f"Line {i}: {str(e)[:100]}"
                        )

        size = path.stat().st_size
        status = "valid" if error_count == 0 else f"has {error_count} errors"
        results.add_pass(
            f"JSONL: {description}",
            f"{line_count} docs, {format_size(size)} ({status})"
        )
        return error_count == 0, line_count
    except Exception as e:
        results.add_error(f"Error reading JSONL: {description}", str(e))
        return False, 0


def check_csv_file(results: CheckResults, path: Path, description: str) -> tuple[bool, int]:
    """Check if a CSV file is readable and count rows."""
    if not check_file_exists(results, path, description):
        return False, 0

    # Increase field size limit for large hadith files
    try:
        csv.field_size_limit(sys.maxsize)
    except OverflowError:
        csv.field_size_limit(2**31 - 1)

    row_count = 0
    try:
        with open(path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            headers = reader.fieldnames
            for _ in reader:
                row_count += 1

        size = path.stat().st_size
        results.add_pass(
            f"CSV: {description}",
            f"{row_count} rows, {len(headers) if headers else 0} cols, {format_size(size)}"
        )
        return True, row_count
    except Exception as e:
        results.add_error(f"Error reading CSV: {description}", str(e))
        return False, 0


def check_sqlite_db(results: CheckResults, path: Path, description: str) -> bool:
    """Check if a SQLite database is accessible."""
    import sqlite3

    if not check_file_exists(results, path, description):
        return False

    try:
        conn = sqlite3.connect(str(path))
        cur = conn.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [r[0] for r in cur.fetchall()]

        table_info = []
        for table in tables:
            cur.execute(f"SELECT COUNT(*) FROM {table}")
            count = cur.fetchone()[0]
            table_info.append(f"{table}({count})")

        conn.close()
        results.add_pass(f"SQLite DB: {description}", f"Tables: {', '.join(table_info)}")
        return True
    except Exception as e:
        results.add_error(f"Error reading SQLite DB: {description}", str(e))
        return False


def check_directory_contents(
    results: CheckResults,
    path: Path,
    description: str,
    expected_min: int = 0,
) -> int:
    """Check directory exists and count files."""
    if not check_file_exists(results, path, description):
        return 0

    files = list(path.iterdir())
    count = len(files)

    if expected_min > 0 and count < expected_min:
        results.add_warning(
            f"Few files: {description}",
            f"Found {count}, expected at least {expected_min}"
        )
    else:
        results.add_pass(f"Directory: {description}", f"{count} items")

    return count


# ── Dataset Checks ───────────────────────────────────────────────────────


def check_processed_data(results: CheckResults) -> None:
    """Check processed data files."""
    logger.info("Checking processed data...")
    processed_dir = get_data_dir("processed")

    if not processed_dir.exists():
        results.add_warning("Processed data directory", "Not created yet (run ingestion first)")
        return

    # Check for key processed files
    key_files = {
        "all_chunks.json": "All chunks",
        "hadith_chunks.json": "Hadith chunks",
        "fiqh_chunks.json": "Fiqh chunks",
        "duas_chunks.json": "Dua chunks",
    }

    for filename, description in key_files.items():
        check_json_file(results, processed_dir / filename, description)


def check_seed_data(results: CheckResults) -> None:
    """Check seed data files."""
    logger.info("Checking seed data...")
    seed_dir = get_data_dir("seed")

    if not seed_dir.exists():
        results.add_warning("Seed data directory", "Not created yet")
        return

    seed_files = {
        "duas.json": "Duas seed data",
        "quran_sample.json": "Quran sample data",
    }

    for filename, description in seed_files.items():
        check_json_file(results, seed_dir / filename, description)


def check_mini_dataset(results: CheckResults) -> None:
    """Check mini-dataset files."""
    logger.info("Checking mini-dataset...")
    mini_dir = get_data_dir("mini_dataset")

    if not mini_dir.exists():
        results.add_warning("Mini-dataset", "Not created yet (run create_mini_dataset.py)")
        return

    # Check JSONL files
    jsonl_files = list(mini_dir.glob("*.jsonl"))
    total_docs = 0

    for jsonl_file in jsonl_files:
        valid, count = check_jsonl_file(results, jsonl_file, jsonl_file.name)
        total_docs += count

    # Check metadata files
    check_json_file(results, mini_dir / "collection_stats.json", "Collection stats")
    check_json_file(results, mini_dir / "book_selections.json", "Book selections")
    check_file_exists(results, mini_dir / "README.md", "Mini-dataset README")

    if total_docs > 0:
        results.add_pass("Mini-dataset total", f"{total_docs} documents")


def check_embeddings(results: CheckResults) -> None:
    """Check embedding-related files."""
    logger.info("Checking embeddings...")
    embeddings_dir = get_data_dir("embeddings")

    if not embeddings_dir.exists():
        results.add_warning("Embeddings directory", "Not created yet (run embedding pipeline)")
        return

    # Check for checkpoints
    checkpoint_dir = embeddings_dir / "checkpoints"
    if checkpoint_dir.exists():
        checkpoints = list(checkpoint_dir.glob("*.json"))
        results.add_pass("Embedding checkpoints", f"{len(checkpoints)} checkpoints")
    else:
        results.add_warning("Embedding checkpoints", "No checkpoints directory")

    # Check error log
    error_log = embeddings_dir / "errors.log"
    if error_log.exists():
        size = error_log.stat().st_size
        results.add_warning("Embedding error log", f"Exists ({format_size(size)})")
    else:
        results.add_pass("Embedding error log", "No errors logged")


def check_datasets_directory(results: CheckResults) -> None:
    """Check the datasets/ directory structure."""
    logger.info("Checking datasets directory...")
    datasets_dir = get_datasets_dir()

    if not datasets_dir.exists():
        results.add_error("Datasets directory", "Missing entirely")
        return

    # Check extracted books
    books_dir = datasets_dir / "data" / "extracted_books"
    if books_dir.exists():
        txt_files = list(books_dir.glob("*.txt"))
        total_size = sum(f.stat().st_size for f in txt_files)
        results.add_pass(
            "Extracted books",
            f"{len(txt_files)} files, {format_size(total_size)}"
        )
    else:
        results.add_warning("Extracted books", "Directory not found")

    # Check metadata
    metadata_dir = datasets_dir / "data" / "metadata"
    if metadata_dir.exists():
        check_json_file(results, metadata_dir / "categories.json", "Categories metadata")
        check_json_file(results, metadata_dir / "authors.json", "Authors metadata")
        check_sqlite_db(results, metadata_dir / "books.db", "Books database")
    else:
        results.add_warning("Metadata directory", "Not found")

    # Check Sanadset CSV
    sanadset_dir = datasets_dir / "Sanadset 368K Data on Hadith Narrators" / "Sanadset 368K Data on Hadith Narrators"
    sanadset_csv = sanadset_dir / "sanadset.csv"
    check_csv_file(results, sanadset_csv, "Sanadset hadith data")


def check_quran_database(results: CheckResults) -> None:
    """Check Quran database."""
    logger.info("Checking Quran database...")
    quran_db = get_data_dir("quran.db")
    check_sqlite_db(results, quran_db, "Quran SQLite database")


def check_config_files(results: CheckResults) -> None:
    """Check configuration files."""
    logger.info("Checking configuration files...")
    root = get_project_root()

    check_file_exists(results, root / ".env.example", "Environment template")

    env_file = root / ".env"
    if env_file.exists():
        results.add_pass("Environment file", "Exists (check that secrets are set)")
    else:
        results.add_warning("Environment file", "Not found (copy from .env.example)")


# ── Report Generation ────────────────────────────────────────────────────


def generate_report(results: CheckResults, detailed: bool = False) -> str:
    """Generate a human-readable report."""
    lines = [
        "=" * 70,
        "ATHAR DATASET INTEGRITY REPORT",
        "=" * 70,
        "",
    ]

    # Errors first (most important)
    if results.errors:
        lines.append("ERRORS:")
        lines.append("-" * 70)
        for err in results.errors:
            lines.append(f"  ✗ {err['check']}")
            if detailed and err["detail"]:
                lines.append(f"    {err['detail']}")
        lines.append("")

    # Warnings
    if results.warnings:
        lines.append("WARNINGS:")
        lines.append("-" * 70)
        for warn in results.warnings:
            lines.append(f"  ⚠ {warn['check']}")
            if detailed and warn["detail"]:
                lines.append(f"    {warn['detail']}")
        lines.append("")

    # Passed checks
    if detailed and results.passed:
        lines.append("PASSED:")
        lines.append("-" * 70)
        for p in results.passed:
            lines.append(f"  ✓ {p['check']}")
            if p["detail"]:
                lines.append(f"    {p['detail']}")
        lines.append("")

    # Summary
    lines.append("SUMMARY:")
    lines.append("-" * 70)
    lines.append(f"  {results.summary()}")
    lines.append("")

    if results.errors:
        lines.append("STATUS: FAIL - Errors found")
    elif results.warnings:
        lines.append("STATUS: WARN - Warnings found (non-critical)")
    else:
        lines.append("STATUS: PASS - All checks passed")

    lines.append("=" * 70)
    return "\n".join(lines)


# ── Main ─────────────────────────────────────────────────────────────────


def main():
    """Run all dataset integrity checks."""
    parser = argparse.ArgumentParser(
        description="Check Athar dataset integrity",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/check_datasets.py
  python scripts/check_datasets.py --report
  python scripts/check_datasets.py --datasets
  python scripts/check_datasets.py --data
        """,
    )
    parser.add_argument("--report", action="store_true", help="Generate detailed report")
    parser.add_argument("--datasets", action="store_true", help="Check only datasets/ directory")
    parser.add_argument("--data", action="store_true", help="Check only data/ directory")

    args = parser.parse_args()

    print("\n" + "=" * 70)
    print("🔍 ATHAR DATASET INTEGRITY CHECKER")
    print("=" * 70 + "\n")

    results = CheckResults()

    if args.data or (not args.datasets and not args.data):
        # Check data/ directory contents
        check_processed_data(results)
        check_seed_data(results)
        check_mini_dataset(results)
        check_embeddings(results)
        check_quran_database(results)

    if args.datasets or (not args.datasets and not args.data):
        # Check datasets/ directory contents
        check_datasets_directory(results)

    # Always check config
    check_config_files(results)

    # Generate report
    report = generate_report(results, detailed=args.report)
    print(report)

    # Return exit code
    if results.errors:
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()
