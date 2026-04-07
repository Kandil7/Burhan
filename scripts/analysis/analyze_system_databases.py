"""
Deep analysis of Shamela system_book_datasets SQLite databases.
Analyzes schemas, content, data quality, and extraction potential.
"""
import sqlite3
import os
import json
from collections import defaultdict
from pathlib import Path

BASE_DIR = Path(r"K:\business\projects_v2\Athar\datasets\system_book_datasets")

def analyze_table_structure(cursor, table_name):
    """Get column info, indexes, and foreign keys for a table."""
    columns = cursor.execute(f"PRAGMA table_info('{table_name}')").fetchall()
    indexes = cursor.execute(f"PRAGMA index_list('{table_name}')").fetchall()
    foreign_keys = cursor.execute(f"PRAGMA foreign_key_list('{table_name}')").fetchall()
    
    index_details = []
    for idx in indexes:
        idx_name = idx[1]
        idx_cols = cursor.execute(f"PRAGMA index_info('{idx_name}')").fetchall()
        index_details.append({
            'name': idx_name,
            'unique': idx[2],
            'columns': [c[2] for c in idx_cols]
        })
    
    return {
        'columns': [{'cid': c[0], 'name': c[1], 'type': c[2], 'notnull': c[3], 'default': c[4], 'pk': c[5]} for c in columns],
        'indexes': index_details,
        'foreign_keys': [{'id': fk[0], 'from': fk[3], 'table': fk[2], 'to': fk[4]} for fk in foreign_keys]
    }

def sample_table_data(cursor, table_name, limit=3):
    """Get sample rows from a table."""
    try:
        rows = cursor.execute(f"SELECT * FROM '{table_name}' LIMIT {limit}").fetchall()
        cols = [desc[0] for desc in cursor.description]
        return [{'columns': cols, 'rows': [dict(zip(cols, row)) for row in rows]}]
    except Exception as e:
        return [{'error': str(e)}]

def get_row_count(cursor, table_name):
    """Get row count for a table."""
    try:
        count = cursor.execute(f"SELECT COUNT(*) FROM '{table_name}'").fetchone()[0]
        return count
    except:
        return 0

def get_null_stats(cursor, table_name, columns):
    """Get NULL statistics for columns."""
    stats = {}
    total = get_row_count(cursor, table_name)
    if total == 0:
        return stats
    for col in columns:
        try:
            nulls = cursor.execute(f"SELECT COUNT(*) FROM '{table_name}' WHERE \"{col}\" IS NULL").fetchone()[0]
            stats[col] = {'total': total, 'nulls': nulls, 'null_pct': round(nulls/total*100, 1)}
        except:
            pass
    return stats

def analyze_service_database(db_path, db_name):
    """Analyze service databases (hadeeth, tafseer, S1, S2, trajim)."""
    print(f"\n{'='*80}")
    print(f"SERVICE DATABASE: {db_name}")
    print(f"{'='*80}")
    
    size = os.path.getsize(db_path)
    print(f"  Size: {size:,} bytes ({size/1024/1024:.1f} MB)")
    
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    # Get all tables
    tables = cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name").fetchall()
    tables = [t[0] for t in tables]
    print(f"  Tables: {len(tables)}")
    
    for table in tables:
        print(f"\n  --- Table: {table} ---")
        structure = analyze_table_structure(cursor, table)
        row_count = get_row_count(cursor, table)
        print(f"    Rows: {row_count:,}")
        
        # Print columns
        for col in structure['columns']:
            print(f"    Column: {col['name']:30s} Type: {col['type']:15s} PK: {bool(col['pk'])} NOT NULL: {bool(col['notnull'])}")
        
        # Print indexes
        if structure['indexes']:
            print(f"    Indexes:")
            for idx in structure['indexes']:
                unique_str = "UNIQUE" if idx['unique'] else "NON-UNIQUE"
                print(f"      {idx['name']} ({unique_str}): {', '.join(idx['columns'])}")
        
        # Print foreign keys
        if structure['foreign_keys']:
            print(f"    Foreign Keys:")
            for fk in structure['foreign_keys']:
                print(f"      {fk['from']} -> {fk['table']}({fk['to']})")
        
        # Sample data
        samples = sample_table_data(cursor, table)
        if samples and 'rows' in samples[0]:
            print(f"    Sample data:")
            for row in samples[0]['rows']:
                # Truncate long text values
                truncated = {}
                for k, v in row.items():
                    if isinstance(v, str) and len(v) > 100:
                        truncated[k] = v[:100] + "..."
                    else:
                        truncated[k] = v
                print(f"      {truncated}")
        
        # NULL stats for small tables
        if row_count < 1000 and structure['columns']:
            col_names = [c['name'] for c in structure['columns']]
            null_stats = get_null_stats(cursor, table, col_names)
            if null_stats:
                print(f"    NULL stats:")
                for col, stats in null_stats.items():
                    if stats['nulls'] > 0:
                        print(f"      {col}: {stats['nulls']}/{stats['total']} ({stats['null_pct']}%)")
    
    conn.close()

def analyze_book_databases():
    """Analyze a sample of individual book databases."""
    print(f"\n{'='*80}")
    print(f"BOOK DATABASES ANALYSIS")
    print(f"{'='*80}")
    
    book_dir = BASE_DIR / "book"
    
    # Sample databases from different categories
    sample_dbs = []
    categories_seen = set()
    
    for cat_dir in sorted(book_dir.iterdir()):
        if not cat_dir.is_dir():
            continue
        category = cat_dir.name
        for db_file in sorted(cat_dir.glob("*.db")):
            if category not in categories_seen or len(sample_dbs) < 25:
                sample_dbs.append(db_file)
                categories_seen.add(category)
                if len(sample_dbs) >= 25:
                    break
        if len(sample_dbs) >= 25:
            break
    
    print(f"\nTotal book databases: 8,427")
    print(f"Analyzing sample of {len(sample_dbs)} databases across {len(categories_seen)} categories")
    
    schema_patterns = defaultdict(list)
    
    for i, db_path in enumerate(sample_dbs):
        print(f"\n  [{i+1}/{len(sample_dbs)}] {db_path.name} (category: {db_path.parent.name}, size: {os.path.getsize(db_path):,} bytes)")
        
        try:
            conn = sqlite3.connect(str(db_path))
            cursor = conn.cursor()
            
            tables = cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name").fetchall()
            tables = [t[0] for t in tables]
            
            # Create schema signature
            schema_sig = tuple(sorted(tables))
            schema_patterns[schema_sig].append(db_path.name)
            
            print(f"    Tables: {tables}")
            
            for table in tables:
                structure = analyze_table_structure(cursor, table)
                row_count = get_row_count(cursor, table)
                print(f"    {table}: {row_count:,} rows")
                
                if row_count <= 5:  # Show sample for small tables
                    samples = sample_table_data(cursor, table)
                    if samples and 'rows' in samples[0]:
                        for row in samples[0]['rows']:
                            truncated = {}
                            for k, v in row.items():
                                if isinstance(v, str) and len(v) > 150:
                                    truncated[k] = v[:150] + "..."
                                else:
                                    truncated[k] = v
                            print(f"      Sample: {truncated}")
            
            conn.close()
        except Exception as e:
            print(f"    ERROR: {e}")
    
    print(f"\n  {'='*60}")
    print(f"  SCHEMA PATTERNS FOUND:")
    print(f"  {'='*60}")
    for sig, dbs in schema_patterns.items():
        print(f"\n  Schema {sig}: {len(dbs)} databases")
        print(f"    Examples: {dbs[:5]}")

def analyze_user_database():
    """Analyze user data database."""
    print(f"\n{'='*80}")
    print(f"USER DATABASE: data.db")
    print(f"{'='*80}")
    
    db_path = BASE_DIR / "user" / "data.db"
    size = os.path.getsize(db_path)
    print(f"  Size: {size:,} bytes ({size/1024:.1f} KB)")
    
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    tables = cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name").fetchall()
    tables = [t[0] for t in tables]
    print(f"  Tables: {len(tables)} - {tables}")
    
    for table in tables:
        print(f"\n  --- Table: {table} ---")
        structure = analyze_table_structure(cursor, table)
        row_count = get_row_count(cursor, table)
        print(f"    Rows: {row_count:,}")
        
        for col in structure['columns']:
            print(f"    Column: {col['name']:30s} Type: {col['type']:15s} PK: {bool(col['pk'])}")
        
        samples = sample_table_data(cursor, table, 5)
        if samples and 'rows' in samples[0]:
            print(f"    Sample data:")
            for row in samples[0]['rows']:
                truncated = {}
                for k, v in row.items():
                    if isinstance(v, str) and len(v) > 150:
                        truncated[k] = v[:150] + "..."
                    else:
                        truncated[k] = v
                print(f"      {truncated}")
    
    conn.close()

def analyze_store_indexes():
    """Analyze Lucene store indexes."""
    print(f"\n{'='*80}")
    print(f"STORE (LUCENE INDEXES) ANALYSIS")
    print(f"{'='*80}")
    
    store_dir = BASE_DIR / "store"
    if not store_dir.exists():
        print("  Store directory not found")
        return
    
    for idx_dir in sorted(store_dir.iterdir()):
        if idx_dir.is_dir():
            files = list(idx_dir.glob("*"))
            print(f"\n  Index: {idx_dir.name}")
            print(f"    Files: {len(files)}")
            # Show file types
            extensions = defaultdict(int)
            for f in files:
                ext = f.suffix if f.suffix else '(no extension)'
                extensions[ext] += 1
            print(f"    File types: {dict(extensions)}")

def main():
    print("╔" + "═"*78 + "╗")
    print("║" + " SHAMELA SYSTEM_BOOK_DATASETS - COMPREHENSIVE DATABASE ANALYSIS".center(78) + "║")
    print("╚" + "═"*78 + "╝")
    
    # 1. Analyze service databases
    service_dir = BASE_DIR / "service"
    service_dbs = list(service_dir.glob("*.db"))
    
    print(f"\n{'='*80}")
    print(f"OVERVIEW")
    print(f"{'='*80}")
    print(f"Base directory: {BASE_DIR}")
    print(f"Service databases: {len(service_dbs)}")
    
    # Calculate total size of book databases
    book_dir = BASE_DIR / "book"
    total_book_size = 0
    total_book_count = 0
    for cat_dir in book_dir.iterdir():
        if cat_dir.is_dir():
            for db_file in cat_dir.glob("*.db"):
                total_book_size += os.path.getsize(db_file)
                total_book_count += 1
    
    print(f"Book databases: {total_book_count}")
    print(f"Total book size: {total_book_size:,} bytes ({total_book_size/1024/1024:.1f} MB)")
    
    for db_path in sorted(service_dbs):
        analyze_service_database(db_path, db_path.name)
    
    # 2. Analyze sample book databases
    analyze_book_databases()
    
    # 3. Analyze user database
    analyze_user_database()
    
    # 4. Analyze store indexes
    analyze_store_indexes()

if __name__ == "__main__":
    main()
