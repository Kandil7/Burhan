"""
Find where the actual book text content is stored.
Check Lucene indexes and other data sources.
"""
import sqlite3
import os
from pathlib import Path

BASE_DIR = Path(r"K:\business\projects_v2\Athar\datasets\system_book_datasets")

def hex_to_arabic(data):
    if isinstance(data, bytes):
        try:
            return data.decode("windows-1256")
        except:
            try:
                return data.decode("utf-8")
            except:
                return repr(data)[:100]
    return str(data) if data is not None else "(NULL)"

def check_book_db_for_content(db_path, db_name):
    """Check if a book database has any text content."""
    conn = sqlite3.connect(str(db_path))
    c = conn.cursor()
    
    # Check all tables for text content
    tables = c.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
    
    has_text_content = False
    
    for (table_name,) in tables:
        cols = c.execute(f"PRAGMA table_info('{table_name}')").fetchall()
        col_names = [col[1] for col in cols]
        
        for col_name in col_names:
            # Check for text content
            text_rows = c.execute(f'SELECT COUNT(*) FROM "{table_name}" WHERE typeof("{col_name}") = "text" AND "{col_name}" IS NOT NULL AND LENGTH("{col_name}") > 10').fetchone()[0]
            if text_rows > 0:
                sample = c.execute(f'SELECT "{col_name}" FROM "{table_name}" WHERE typeof("{col_name}") = "text" AND "{col_name}" IS NOT NULL AND LENGTH("{col_name}") > 10 LIMIT 2').fetchall()
                for (val,) in sample:
                    decoded = hex_to_arabic(val) if isinstance(val, bytes) else val
                    if any(ord(ch) > 127 for ch in decoded):  # Contains non-ASCII (Arabic)
                        has_text_content = True
                        print(f"  FOUND TEXT CONTENT in {db_name}.{table_name}.{col_name}:")
                        print(f"    {decoded[:200]}")
    
    conn.close()
    return has_text_content


def analyze_lucene_index_files():
    """Check if Lucene index files contain actual text content."""
    print("\n=== LUCENE INDEX ANALYSIS ===")
    
    store_dir = BASE_DIR / "store" / "page"
    if not store_dir.exists():
        print("Page store directory not found")
        return
    
    # Look for .fdt files (stored fields data)
    fdt_files = list(store_dir.glob("*.fdt"))
    print(f"\nFound {len(fdt_files)} .fdt files in page store")
    
    # Check file sizes
    total_size = sum(f.stat().st_size for f in fdt_files)
    print(f"Total .fdt size: {total_size:,} bytes ({total_size/1024/1024:.1f} MB)")
    
    # Try to read some content from .fdt files
    if fdt_files:
        print(f"\nSample .fdt file content (first 500 bytes as hex):")
        with open(fdt_files[0], "rb") as f:
            data = f.read(500)
            print(f"  File: {fdt_files[0].name}")
            print(f"  Size: {fdt_files[0].stat().st_size:,} bytes")
            print(f"  Hex: {data[:200].hex()}")
            # Try to decode as Arabic
            try:
                decoded = data.decode("windows-1256")
                print(f"  Decoded (windows-1256): {decoded[:200]}")
            except:
                print("  Could not decode as windows-1256")


def check_extracted_books_structure():
    """Check what extracted_books looks like for comparison."""
    print("\n=== EXTRACTED BOOKS STRUCTURE ===")
    
    extracted_dir = Path(r"K:\business\projects_v2\Athar\datasets\extracted_books")
    if not extracted_dir.exists():
        print("Extracted books directory not found")
        return
    
    # Count files
    txt_files = list(extracted_dir.rglob("*.txt"))
    print(f"Total .txt files: {len(txt_files)}")
    
    # Sample a few files
    for txt_file in txt_files[:5]:
        size = txt_file.stat().st_size
        print(f"\nFile: {txt_file.name} ({size:,} bytes)")
        try:
            with open(txt_file, "r", encoding="utf-8") as f:
                content = f.read(500)
                print(f"  Content preview: {content[:300]}")
        except Exception as e:
            print(f"  Error reading: {e}")


def check_dataset_directories():
    """Check all dataset directories."""
    print("\n=== ALL DATASET DIRECTORIES ===")
    
    datasets_dir = Path(r"K:\business\projects_v2\Athar\datasets")
    for item in sorted(datasets_dir.iterdir()):
        if item.is_dir():
            print(f"\nDirectory: {item.name}")
            # Count files
            files = list(item.rglob("*"))
            print(f"  Total items: {len(files)}")
            # Get total size
            total_size = sum(f.stat().st_size for f in files if f.is_file())
            print(f"  Total size: {total_size:,} bytes ({total_size/1024/1024:.1f} MB)")


def check_service_db_content_mapping():
    """Check how service databases map to book content."""
    print("\n=== SERVICE DATABASE CONTENT MAPPING ===")
    
    # Check hadeeth.db inservice table
    conn = sqlite3.connect(str(BASE_DIR / "service" / "hadeeth.db"))
    c = conn.cursor()
    
    print("\nHadeeth inservice table:")
    rows = c.execute("SELECT * FROM inservice").fetchall()
    for row in rows:
        book_id, user_excluded = row
        # Check how many service entries for this book
        count = c.execute("SELECT COUNT(*) FROM service WHERE book_id = ?", (book_id,)).fetchone()[0]
        print(f"  book_id={book_id}, excluded={user_excluded}, service_entries={count}")
    
    conn.close()
    
    # Check tafseer.db inservice table
    conn = sqlite3.connect(str(BASE_DIR / "service" / "tafseer.db"))
    c = conn.cursor()
    
    print("\nTafseer inservice table:")
    rows = c.execute("SELECT * FROM inservice").fetchall()
    for row in rows:
        book_id, user_excluded = row
        count = c.execute("SELECT COUNT(*) FROM service WHERE book_id = ?", (book_id,)).fetchone()[0]
        print(f"  book_id={book_id}, excluded={user_excluded}, service_entries={count}")
    
    conn.close()


def check_for_text_in_page_content():
    """Look deeper into page table for any hidden text content."""
    print("\n=== DEEP PAGE CONTENT SEARCH ===")
    
    # Check a few book databases for any text in any column
    book_dir = BASE_DIR / "book"
    checked = 0
    
    for cat_dir in sorted(book_dir.iterdir()):
        if not cat_dir.is_dir() or checked >= 5:
            continue
        
        for db_file in sorted(cat_dir.glob("*.db")):
            if db_file.stat().st_size == 0 or checked >= 5:
                continue
            
            conn = sqlite3.connect(str(db_file))
            c = conn.cursor()
            
            # Check all columns in page table for any non-null, non-numeric content
            cols = c.execute("PRAGMA table_info('page')").fetchall()
            for col in cols:
                col_name = col[1]
                if col_name in ('id', 'page'):
                    continue
                
                # Check for any content that's not purely numeric
                samples = c.execute(f'SELECT DISTINCT "{col_name}" FROM page WHERE "{col_name}" IS NOT NULL LIMIT 5').fetchall()
                for (val,) in samples:
                    decoded = hex_to_arabic(val) if isinstance(val, bytes) else str(val)
                    if decoded and not decoded.isdigit():
                        print(f"  {db_file.name}.page.{col_name} = {decoded[:100]!r}")
            
            conn.close()
            checked += 1
            break


def main():
    print("="*80)
    print("FINDING ACTUAL BOOK TEXT CONTENT")
    print("="*80)
    
    # 1. Check if book databases have any text content
    print("\n=== CHECKING BOOK DATABASES FOR TEXT CONTENT ===")
    book_dir = BASE_DIR / "book"
    
    checked = 0
    for cat_dir in sorted(book_dir.iterdir()):
        if not cat_dir.is_dir():
            continue
        for db_file in sorted(cat_dir.glob("*.db")):
            if db_file.stat().st_size > 50000 and checked < 5:
                check_book_db_for_content(db_file, db_file.name)
                checked += 1
    
    # 2. Check Lucene index files
    analyze_lucene_index_files()
    
    # 3. Check extracted books
    check_extracted_books_structure()
    
    # 4. Check all dataset directories
    check_dataset_directories()
    
    # 5. Check service database mapping
    check_service_db_content_mapping()
    
    # 6. Deep page content search
    check_for_text_in_page_content()


if __name__ == "__main__":
    main()
