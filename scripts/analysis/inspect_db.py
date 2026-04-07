#!/usr/bin/env python3
"""
Database Inspector Script for Athar Islamic QA System.

Inspects SQLite database structure and contents:
- Lists all tables with row counts
- Shows schema for each table
- Displays sample data
- Reports database file size

Usage:
    python scripts/analysis/inspect_db.py
    python scripts/analysis/inspect_db.py --db data/quran.db
    python scripts/analysis/inspect_db.py --db datasets/data/metadata/books.db
    python scripts/analysis/inspect_db.py --db data/quran.db --sample 10

Author: Athar Engineering Team
"""

import argparse
import sqlite3
import sys
from pathlib import Path

from scripts.utils import (
    get_project_root,
    format_size,
    setup_script_logger,
)

logger = setup_script_logger("inspect-db")


def inspect_database(db_path: str, sample_rows: int = 3) -> None:
    """
    Inspect SQLite database structure and contents.

    Args:
        db_path: Path to SQLite database file.
        sample_rows: Number of sample rows to display per table.
    """
    db_file = Path(db_path)

    if not db_file.exists():
        print(f"✗ Database not found: {db_file}")
        print(f"\nAvailable databases:")
        _list_available_dbs()
        return

    # Show file info
    file_size = db_file.stat().st_size
    print("=" * 60)
    print(f"Database Inspector: {db_file}")
    print(f"File size: {format_size(file_size)}")
    print("=" * 60)

    try:
        conn = sqlite3.connect(str(db_file))
        cursor = conn.cursor()

        # List all tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
        tables = cursor.fetchall()

        print(f"\n📊 Tables Found: {len(tables)}")
        print("-" * 60)

        total_rows = 0
        table_info = []

        for table in tables:
            table_name = table[0]
            try:
                cursor.execute(f"SELECT COUNT(*) FROM [{table_name}]")
                count = cursor.fetchone()[0]
                total_rows += count
                table_info.append((table_name, count))
                print(f"  • {table_name}: {count:,} rows")
            except Exception as e:
                print(f"  • {table_name}: ERROR - {e}")

        print(f"\n  Total rows across all tables: {total_rows:,}")

        # Show schema for each table
        print(f"\n📋 Table Schemas:")
        print("-" * 60)

        for table_name, _ in table_info:
            print(f"\nTable: {table_name}")
            cursor.execute(f"PRAGMA table_info([{table_name}])")
            columns = cursor.fetchall()

            for col in columns:
                col_id, name, col_type, notnull, default, pk = col
                pk_marker = " [PK]" if pk else ""
                nullable = "" if notnull else " (nullable)"
                default_str = f" DEFAULT {default}" if default else ""
                print(f"  - {name}: {col_type}{pk_marker}{nullable}{default_str}")

        # Sample data from each table
        print(f"\n📝 Sample Data (first {sample_rows} rows per table):")
        print("-" * 60)

        for table_name, _ in table_info:
            print(f"\n{'─' * 60}")
            print(f"Table: {table_name}")
            print(f"{'─' * 60}")

            cursor.execute(f"PRAGMA table_info([{table_name}])")
            columns = [col[1] for col in cursor.fetchall()]
            print(f"Columns: {', '.join(columns)}")

            cursor.execute(f"SELECT * FROM [{table_name}] LIMIT {sample_rows}")
            rows = cursor.fetchall()

            for i, row in enumerate(rows, 1):
                print(f"\n  Row {i}:")
                for col_name, value in zip(columns, row):
                    # Truncate long text
                    if isinstance(value, str) and len(value) > 100:
                        value = value[:100] + "..."
                    print(f"    {col_name}: {value}")

        conn.close()

    except sqlite3.Error as e:
        print(f"\n✗ Database error: {e}")
        logger.error("db_error", path=db_path, error=str(e))
        return

    print("\n" + "=" * 60)
    print("✅ Inspection complete")
    print("=" * 60)


def _list_available_dbs() -> None:
    """List available SQLite databases in the project."""
    root = get_project_root()

    common_paths = [
        root / "data" / "quran.db",
        root / "datasets" / "data" / "metadata" / "books.db",
        root / "data" / "embeddings" / "metadata.db",
    ]

    for path in common_paths:
        if path.exists():
            size = format_size(path.stat().st_size)
            print(f"  ✓ {path} ({size})")
        else:
            print(f"  ✗ {path} (not found)")


def main():
    """Run database inspector."""
    parser = argparse.ArgumentParser(
        description="Inspect SQLite database structure",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/analysis/inspect_db.py
  python scripts/analysis/inspect_db.py --db data/quran.db
  python scripts/analysis/inspect_db.py --db datasets/data/metadata/books.db --sample 10
        """,
    )
    parser.add_argument(
        "--db",
        default=str(get_project_root() / "data" / "quran.db"),
        help="Path to SQLite database file",
    )
    parser.add_argument(
        "--sample",
        type=int,
        default=3,
        help="Number of sample rows to display (default: 3)",
    )
    args = parser.parse_args()

    inspect_database(args.db, sample_rows=args.sample)


if __name__ == "__main__":
    main()
