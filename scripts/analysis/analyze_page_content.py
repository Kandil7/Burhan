"""
Analyze actual page content and title hierarchy in book databases.
"""
import sqlite3
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

def analyze_book_db_deep(db_path, db_name, category):
    """Deep analysis of a book database with full content examination."""
    print(f"\n{'='*80}")
    print(f"BOOK: {db_name} | Category: {category} | Size: {Path(db_path).stat().st_size:,} bytes")
    print(f"{'='*80}")
    
    conn = sqlite3.connect(str(db_path))
    c = conn.cursor()
    
    # Page table analysis
    page_cols = c.execute("PRAGMA table_info('page')").fetchall()
    page_col_names = [col[1] for col in page_cols]
    print(f"\nPage columns: {page_col_names}")
    
    page_count = c.execute("SELECT COUNT(*) FROM page").fetchone()[0]
    print(f"Page count: {page_count:,}")
    
    # Sample pages
    print(f"\nSample pages (first 5):")
    pages = c.execute("SELECT * FROM page LIMIT 5").fetchall()
    for row in pages:
        print(f"  Row: ", end="")
        for col, val in zip(page_col_names, row):
            if isinstance(val, bytes):
                decoded = hex_to_arabic(val)
                print(f"{col}={decoded[:150]!r}", end=" | ")
            else:
                print(f"{col}={val}", end=" | ")
        print()
    
    # Check data types for all columns
    for col_name in page_col_names:
        if col_name == "id":
            continue
        types = c.execute(f'SELECT typeof("{col_name}"), COUNT(*) FROM page GROUP BY typeof("{col_name}")').fetchall()
        type_dict = dict(types)
        print(f"\nColumn '{col_name}' type distribution: {type_dict}")
        
        # If text type exists, show samples
        if "text" in type_dict:
            samples = c.execute(f'SELECT "{col_name}" FROM page WHERE typeof("{col_name}") = "text" AND "{col_name}" IS NOT NULL LIMIT 3').fetchall()
            for idx, (val,) in enumerate(samples):
                if val:
                    decoded = hex_to_arabic(val) if isinstance(val, bytes) else val
                    print(f"  Text sample {idx+1}: {decoded[:300]}")
        
        # If blob type exists, try decoding
        if "blob" in type_dict:
            samples = c.execute(f'SELECT "{col_name}" FROM page WHERE typeof("{col_name}") = "blob" AND "{col_name}" IS NOT NULL LIMIT 3').fetchall()
            for idx, (val,) in enumerate(samples):
                if val:
                    decoded = hex_to_arabic(val)
                    print(f"  Blob sample {idx+1}: {decoded[:300]}")
    
    # Title table analysis
    title_cols = c.execute("PRAGMA table_info('title')").fetchall()
    title_col_names = [col[1] for col in title_cols]
    print(f"\nTitle columns: {title_col_names}")
    
    title_count = c.execute("SELECT COUNT(*) FROM title").fetchone()[0]
    print(f"Title count: {title_count:,}")
    
    if title_count > 0:
        # Show title hierarchy
        print(f"\nTitle hierarchy (first 20):")
        titles = c.execute("SELECT * FROM title ORDER BY id LIMIT 20").fetchall()
        for row in titles:
            for col, val in zip(title_col_names, row):
                if isinstance(val, bytes):
                    decoded = hex_to_arabic(val)
                    print(f"  {col}: {decoded[:150]!r}")
                else:
                    print(f"  {col}: {val}")
            print("  ---")
        
        # Check for parent-child relationships
        if "parent" in title_col_names:
            root_titles = c.execute("SELECT COUNT(*) FROM title WHERE parent = 0 OR parent IS NULL").fetchone()[0]
            child_titles = c.execute("SELECT COUNT(*) FROM title WHERE parent > 0").fetchone()[0]
            print(f"\nTitle hierarchy: {root_titles} root titles, {child_titles} child titles")
            
            # Show depth distribution
            depths = c.execute("""
                SELECT 
                    CASE 
                        WHEN parent = 0 OR parent IS NULL THEN 'root'
                        WHEN EXISTS (SELECT 1 FROM title t2 WHERE t2.id = title.parent AND t2.parent = 0) THEN 'level_1'
                        ELSE 'level_2+'
                    END as depth,
                    COUNT(*)
                FROM title
                GROUP BY depth
            """).fetchall()
            for depth, count in depths:
                print(f"  {depth}: {count}")
    
    conn.close()


def main():
    print("="*80)
    print("DEEP PAGE CONTENT AND TITLE HIERARCHY ANALYSIS")
    print("="*80)
    
    book_dir = BASE_DIR / "book"
    
    # Select diverse books from different categories
    selected_books = []
    categories = sorted([d.name for d in book_dir.iterdir() if d.is_dir()])
    
    for cat in categories:
        cat_dir = book_dir / cat
        db_files = sorted(list(cat_dir.glob("*.db")))
        for db_file in db_files:
            if db_file.stat().st_size > 100000 and len(selected_books) < 15:
                selected_books.append((db_file, db_file.name, cat))
                break
    
    # Also add some smaller books
    for cat in categories:
        cat_dir = book_dir / cat
        db_files = sorted(list(cat_dir.glob("*.db")))
        for db_file in db_files:
            if db_file.stat().st_size > 0 and db_file.stat().st_size <= 100000 and len(selected_books) < 20:
                selected_books.append((db_file, db_file.name, cat))
                break
    
    print(f"\nSelected {len(selected_books)} books for deep analysis")
    
    for db_path, db_name, category in selected_books:
        analyze_book_db_deep(db_path, db_name, category)


if __name__ == "__main__":
    main()
