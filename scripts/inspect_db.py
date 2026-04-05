#!/usr/bin/env python3
"""
Database Inspector Script for quran.db.

Inspects the structure of an existing SQLite Quran database.
Helps understand schema before integration.

Usage:
    python scripts/inspect_db.py --db data/quran.db
"""
import argparse
import sqlite3
import sys
from pathlib import Path

def inspect_database(db_path: str):
    """Inspect SQLite database structure."""
    if not Path(db_path).exists():
        print(f"Error: Database not found at {db_path}")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("=" * 60)
    print(f"Quran Database Inspector: {db_path}")
    print("=" * 60)
    
    # List all tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    
    print(f"\n📊 Tables Found: {len(tables)}")
    print("-" * 60)
    for table in tables:
        table_name = table[0]
        
        # Get row count
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        count = cursor.fetchone()[0]
        
        print(f"  • {table_name}: {count} rows")
    
    # Show schema for each table
    print(f"\n📋 Table Schemas:")
    print("-" * 60)
    for table in tables:
        table_name = table[0]
        print(f"\nTable: {table_name}")
        
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = cursor.fetchall()
        
        for col in columns:
            col_id, name, col_type, notnull, default, pk = col
            pk_marker = " [PK]" if pk else ""
            nullable = "" if notnull else " (nullable)"
            print(f"  - {name}: {col_type}{pk_marker}{nullable}")
    
    # Sample data from first table
    if tables:
        first_table = tables[0][0]
        print(f"\n📝 Sample Data from '{first_table}':")
        print("-" * 60)
        
        cursor.execute(f"SELECT * FROM {first_table} LIMIT 3")
        rows = cursor.fetchall()
        
        cursor.execute(f"PRAGMA table_info({first_table})")
        columns = [col[1] for col in cursor.fetchall()]
        
        print(f"Columns: {', '.join(columns)}")
        for i, row in enumerate(rows, 1):
            print(f"\nRow {i}:")
            for col_name, value in zip(columns, row):
                # Truncate long text
                if isinstance(value, str) and len(value) > 80:
                    value = value[:80] + "..."
                print(f"  {col_name}: {value}")
    
    conn.close()
    print("\n" + "=" * 60)
    print("✅ Inspection complete")
    print("=" * 60)


def main():
    parser = argparse.ArgumentParser(description="Inspect Quran Database")
    parser.add_argument(
        "--db",
        default="data/quran.db",
        help="Path to SQLite database file"
    )
    
    args = parser.parse_args()
    inspect_database(args.db)


if __name__ == "__main__":
    main()
