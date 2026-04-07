"""
Deep content analysis of book database page and title tables.
Also analyzes the Lucene index structures and S1/S2 database content.
"""
import sqlite3
import os
import json
import re
from collections import defaultdict
from pathlib import Path

BASE_DIR = Path(r"K:\business\projects_v2\Athar\datasets\system_book_datasets")

def hex_to_arabic(data):
    """Try to decode binary data as Arabic text (Windows-1256 encoding)."""
    if isinstance(data, bytes):
        try:
            return data.decode('windows-1256')
        except:
            try:
                return data.decode('utf-8')
            except:
                return repr(data)[:100]
    return data

def analyze_book_content(db_path, db_name, category):
    """Deep analysis of a single book database's content."""
    print(f"\n  {'─'*60}")
    print(f"  Book: {db_name} | Category: {category} | Size: {os.path.getsize(db_path):,} bytes")
    
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    # Analyze page table
    page_count = cursor.execute("SELECT COUNT(*) FROM page").fetchone()[0]
    print(f"  page table: {page_count:,} rows")
    
    # Get page table schema
    page_cols = cursor.execute("PRAGMA table_info('page')").fetchall()
    print(f"  page columns: {[(c[1], c[2]) for c in page_cols]}")
    
    # Sample page data
    sample_pages = cursor.execute("SELECT * FROM page LIMIT 5").fetchall()
    if sample_pages:
        print(f"  Sample page rows:")
        for row in sample_pages:
            print(f"    {row}")
    
    # Analyze title table
    title_count = cursor.execute("SELECT COUNT(*) FROM title").fetchone()[0]
    print(f"  title table: {title_count:,} rows")
    
    # Get title table schema
    title_cols = cursor.execute("PRAGMA table_info('title')").fetchall()
    print(f"  title columns: {[(c[1], c[2]) for c in title_cols]}")
    
    # Sample title data
    sample_titles = cursor.execute("SELECT * FROM title LIMIT 10").fetchall()
    if sample_titles:
        print(f"  Sample title rows:")
        for row in sample_titles:
            print(f"    {row}")
    
    # Check for page data types
    if page_count > 0:
        # Get all column names
        page_col_names = [c[1] for c in page_cols]
        
        # Sample a middle page
        mid_page = page_count // 2
        mid_row = cursor.execute(f"SELECT * FROM page LIMIT 1 OFFSET {mid_page}").fetchone()
        if mid_row:
            print(f"  Middle page (row {mid_page}):")
            for col, val in zip(page_col_names, mid_row):
                if isinstance(val, bytes):
                    decoded = hex_to_arabic(val)
                    print(f"    {col}: {decoded[:200]}")
                else:
                    print(f"    {col}: {val}")
        
        # Check data types distribution
        for col_name in page_col_names:
            if col_name == 'id':
                continue
            try:
                # Count different data types
                text_count = cursor.execute(f"SELECT COUNT(*) FROM page WHERE typeof(\"{col_name}\") = 'text'").fetchone()[0]
                blob_count = cursor.execute(f"SELECT COUNT(*) FROM page WHERE typeof(\"{col_name}\") = 'blob'").fetchone()[0]
                int_count = cursor.execute(f"SELECT COUNT(*) FROM page WHERE typeof(\"{col_name}\") = 'integer'").fetchone()[0]
                null_count = cursor.execute(f"SELECT COUNT(*) FROM page WHERE \"{col_name}\" IS NULL").fetchone()[0]
                
                print(f"  Column '{col_name}' types: text={text_count}, blob={blob_count}, int={int_count}, null={null_count}")
                
                # If text, sample some content
                if text_count > 0:
                    text_sample = cursor.execute(f"SELECT \"{col_name}\" FROM page WHERE typeof(\"{col_name}\") = 'text' AND \"{col_name}\" IS NOT NULL LIMIT 3").fetchall()
                    for idx, (val,) in enumerate(text_sample):
                        if val:
                            decoded = hex_to_arabic(val) if isinstance(val, bytes) else val
                            print(f"    Text sample {idx+1}: {decoded[:300]}")
                
                # If blob, sample and try to decode
                if blob_count > 0:
                    blob_sample = cursor.execute(f"SELECT \"{col_name}\" FROM page WHERE typeof(\"{col_name}\") = 'blob' AND \"{col_name}\" IS NOT NULL LIMIT 3").fetchall()
                    for idx, (val,) in enumerate(blob_sample):
                        if val:
                            decoded = hex_to_arabic(val)
                            print(f"    Blob sample {idx+1}: {decoded[:300]}")
            except Exception as e:
                print(f"  Error analyzing column {col_name}: {e}")
    
    conn.close()

def analyze_s1_database():
    """Analyze S1.db in detail - it has interesting BLOB data."""
    print(f"\n{'='*80}")
    print(f"S1 DATABASE DEEP ANALYSIS")
    print(f"{'='*80}")
    
    db_path = BASE_DIR / "service" / "S1.db"
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    # Get column info
    cols = cursor.execute("PRAGMA table_info('b')").fetchall()
    print(f"\n  Table 'b' columns:")
    for c in cols:
        print(f"    {c}")
    
    # Count different types in each column
    col_names = [c[1] for c in cols]
    total = cursor.execute("SELECT COUNT(*) FROM b").fetchone()[0]
    print(f"\n  Total rows: {total:,}")
    
    for col in col_names:
        types = cursor.execute(f"SELECT typeof(\"{col}\"), COUNT(*) FROM b GROUP BY typeof(\"{col}\")").fetchall()
        print(f"  Column '{col}' types: {dict(types)}")
    
    # Analyze the 'd' column (seems to be integer)
    d_stats = cursor.execute("SELECT MIN(d), MAX(d), AVG(d), COUNT(d), COUNT(*) - COUNT(d) as nulls FROM b").fetchone()
    print(f"\n  Column 'd' stats: min={d_stats[0]}, max={d_stats[1]}, avg={d_stats[2]}, non-null={d_stats[3]}, nulls={d_stats[4]}")
    
    # Sample rows with different d values
    print(f"\n  Sample rows with d values:")
    samples = cursor.execute("SELECT i, d, typeof(s), typeof(l), typeof(a), typeof(b) FROM b WHERE d IS NOT NULL LIMIT 5").fetchall()
    for row in samples:
        print(f"    i={row[0]}, d={row[1]}, s_type={row[2]}, l_type={row[3]}, a_type={row[4]}, b_type={row[5]}")
    
    # Try to decode some blob content
    print(f"\n  Trying to decode blob content...")
    blob_samples = cursor.execute("SELECT i, s, l, a, b FROM b WHERE d IS NOT NULL LIMIT 3").fetchall()
    for row in blob_samples:
        i, s, l, a, b = row
        print(f"\n    Row i={i}, d={cursor.execute('SELECT d FROM b WHERE i=?', (i,)).fetchone()[0]}:")
        print(f"      s (first 100 bytes): {s[:100] if s else None}")
        print(f"      l (first 100 bytes): {l[:100] if l else None}")
        print(f"      a: {a[:100] if a else None}")
        print(f"      b (first 100 bytes): {b[:100] if b else None}")
    
    conn.close()

def analyze_s2_database():
    """Analyze S2.db - the roots database."""
    print(f"\n{'='*80}")
    print(f"S2 DATABASE DEEP ANALYSIS (ARABIC ROOTS)")
    print(f"{'='*80}")
    
    db_path = BASE_DIR / "service" / "S2.db"
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    total = cursor.execute("SELECT COUNT(*) FROM roots").fetchone()[0]
    print(f"\n  Total rows: {total:,}")
    
    # Sample data - try to decode
    print(f"\n  Sample rows (trying windows-1256 decoding):")
    samples = cursor.execute("SELECT token, root FROM roots LIMIT 20").fetchall()
    for token, root in samples:
        token_decoded = hex_to_arabic(token)
        root_decoded = hex_to_arabic(root)
        print(f"    token: {token_decoded:30s} -> root: {root_decoded}")
    
    # Count unique roots
    unique_roots = cursor.execute("SELECT COUNT(DISTINCT root) FROM roots").fetchone()[0]
    print(f"\n  Unique roots: {unique_roots:,}")
    
    # Most common roots
    print(f"\n  Most common roots:")
    top_roots = cursor.execute("SELECT root, COUNT(*) as cnt FROM roots GROUP BY root ORDER BY cnt DESC LIMIT 15").fetchall()
    for root, cnt in top_roots:
        root_decoded = hex_to_arabic(root)
        print(f"    {root_decoded:20s} : {cnt:,} tokens")
    
    # Token length distribution
    print(f"\n  Token length distribution:")
    lengths = cursor.execute("SELECT LENGTH(token), COUNT(*) FROM roots GROUP BY LENGTH(token) ORDER BY LENGTH(token)").fetchall()
    for length, count in lengths:
        print(f"    Length {length}: {count:,} tokens")
    
    conn.close()

def analyze_hadeeth_relationships():
    """Analyze hadeeth.db relationships."""
    print(f"\n{'='*80}")
    print(f"HADEETH DATABASE RELATIONSHIP ANALYSIS")
    print(f"{'='*80}")
    
    db_path = BASE_DIR / "service" / "hadeeth.db"
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    # Analyze service table
    print(f"\n  Service table relationships:")
    
    # Count unique book_ids
    unique_books = cursor.execute("SELECT COUNT(DISTINCT book_id) FROM service").fetchone()[0]
    print(f"  Unique book_ids: {unique_books:,}")
    
    # Count unique key_ids
    unique_keys = cursor.execute("SELECT COUNT(DISTINCT key_id) FROM service").fetchone()[0]
    print(f"  Unique key_ids: {unique_keys:,}")
    
    # Count unique page_ids
    unique_pages = cursor.execute("SELECT COUNT(DISTINCT page_id) FROM service").fetchone()[0]
    print(f"  Unique page_ids: {unique_pages:,}")
    
    # Sample of relationships
    print(f"\n  Sample relationships:")
    samples = cursor.execute("SELECT * FROM service LIMIT 10").fetchall()
    for row in samples:
        print(f"    key_id={row[0]}, book_id={row[1]}, page_id={row[2]}")
    
    # Check key_id distribution
    print(f"\n  Key ID distribution (top 20):")
    key_dist = cursor.execute("SELECT key_id, COUNT(*) as cnt FROM service GROUP BY key_id ORDER BY cnt DESC LIMIT 20").fetchall()
    for key_id, cnt in key_dist:
        print(f"    key_id={key_id}: {cnt} occurrences")
    
    conn.close()

def analyze_tafseer_relationships():
    """Analyze tafseer.db relationships."""
    print(f"\n{'='*80}")
    print(f"TAFSEER DATABASE RELATIONSHIP ANALYSIS")
    print(f"{'='*80}")
    
    db_path = BASE_DIR / "service" / "tafseer.db"
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    print(f"\n  Service table relationships:")
    
    unique_books = cursor.execute("SELECT COUNT(DISTINCT book_id) FROM service").fetchone()[0]
    print(f"  Unique book_ids: {unique_books:,}")
    
    unique_keys = cursor.execute("SELECT COUNT(DISTINCT key_id) FROM service").fetchone()[0]
    print(f"  Unique key_ids: {unique_keys:,}")
    
    unique_pages = cursor.execute("SELECT COUNT(DISTINCT page_id) FROM service").fetchone()[0]
    print(f"  Unique page_ids: {unique_pages:,}")
    
    # Key ID distribution - this likely maps to Quran verses
    print(f"\n  Key ID range:")
    key_range = cursor.execute("SELECT MIN(key_id), MAX(key_id) FROM service").fetchone()
    print(f"  Min key_id: {key_range[0]}, Max key_id: {key_range[1]}")
    
    # Sample relationships
    print(f"\n  Sample relationships (first 15):")
    samples = cursor.execute("SELECT * FROM service LIMIT 15").fetchall()
    for row in samples:
        print(f"    key_id={row[0]}, book_id={row[1]}, page_id={row[2]}")
    
    conn.close()

def analyze_diverse_books():
    """Analyze books from different categories to find schema variations."""
    print(f"\n{'='*80}")
    print(f"DIVERSE BOOK DATABASE ANALYSIS (30 samples across categories)")
    print(f"{'='*80}")
    
    book_dir = BASE_DIR / "book"
    
    # Get all categories
    categories = sorted([d.name for d in book_dir.iterdir() if d.is_dir()])
    print(f"\n  Total categories: {len(categories)}")
    print(f"  Category range: {categories[0]} to {categories[-1]}")
    
    # Sample books from different categories
    sampled = 0
    for cat in categories:
        if sampled >= 30:
            break
        cat_dir = book_dir / cat
        db_files = sorted(list(cat_dir.glob("*.db")))
        if not db_files:
            continue
        
        # Pick first non-empty db
        for db_file in db_files:
            if db_file.stat().st_size > 0 and sampled < 30:
                analyze_book_content(db_file, db_file.name, cat)
                sampled += 1
                break

def main():
    print("╔" + "═"*78 + "╗")
    print("║" + " SHAMELA SYSTEM_BOOK_DATASETS - DEEP CONTENT ANALYSIS".center(78) + "║")
    print("╚" + "═"*78 + "╝")
    
    # 1. Analyze S2 roots database
    analyze_s2_database()
    
    # 2. Analyze S1 database
    analyze_s1_database()
    
    # 3. Analyze hadeeth relationships
    analyze_hadeeth_relationships()
    
    # 4. Analyze tafseer relationships
    analyze_tafseer_relationships()
    
    # 5. Analyze diverse book databases
    analyze_diverse_books()

if __name__ == "__main__":
    main()
