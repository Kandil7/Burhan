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
    return str(data) if data else "(NULL)"

# S2 Analysis continuation
print("=== S2 ROOTS ANALYSIS (continued) ===")
conn = sqlite3.connect(str(BASE_DIR / "service" / "S2.db"))
c = conn.cursor()

print("\nMost common roots:")
rows = c.execute("SELECT root, COUNT(*) as cnt FROM roots GROUP BY root ORDER BY cnt DESC LIMIT 15").fetchall()
for root, cnt in rows:
    decoded = hex_to_arabic(root)
    print(f"  {decoded:30s} : {cnt:,} tokens")

print("\nToken length distribution:")
rows = c.execute("SELECT LENGTH(token), COUNT(*) FROM roots GROUP BY LENGTH(token) ORDER BY LENGTH(token)").fetchall()
for length, count in rows:
    print(f"  Length {length}: {count:,} tokens")

conn.close()

# S1 Analysis
print("\n=== S1 DATABASE ANALYSIS ===")
conn = sqlite3.connect(str(BASE_DIR / "service" / "S1.db"))
c = conn.cursor()

cols = c.execute("PRAGMA table_info('b')").fetchall()
print("\nTable 'b' columns:")
for col in cols:
    print(f"  {col}")

total = c.execute("SELECT COUNT(*) FROM b").fetchone()[0]
print(f"\nTotal rows: {total:,}")

# Count types per column
col_names = [col[1] for col in cols]
for col in col_names:
    types = c.execute(f'SELECT typeof("{col}"), COUNT(*) FROM b GROUP BY typeof("{col}")').fetchall()
    type_dict = dict(types)
    print(f"  Column '{col}' types: {type_dict}")

# D column stats
d_stats = c.execute("SELECT MIN(d), MAX(d), AVG(d), COUNT(d), COUNT(*) - COUNT(d) as nulls FROM b").fetchone()
print(f"\nColumn 'd' stats: min={d_stats[0]}, max={d_stats[1]}, avg={d_stats[2]}, non-null={d_stats[3]}, nulls={d_stats[4]}")

# Sample rows with d values
print("\nSample rows with d values:")
samples = c.execute("SELECT i, d, typeof(s), typeof(l), typeof(a), typeof(b) FROM b WHERE d IS NOT NULL LIMIT 5").fetchall()
for row in samples:
    print(f"  i={row[0]}, d={row[1]}, s_type={row[2]}, l_type={row[3]}, a_type={row[4]}, b_type={row[5]}")

# Try to decode blobs as Arabic
print("\nTrying to decode blob content as Arabic...")
samples = c.execute("SELECT i, s, l FROM b WHERE d IS NOT NULL LIMIT 3").fetchall()
for i, s, l in samples:
    d_val = c.execute("SELECT d FROM b WHERE i=?", (i,)).fetchone()[0]
    print(f"\n  Row i={i}, d={d_val}:")
    s_decoded = hex_to_arabic(s)
    l_decoded = hex_to_arabic(l)
    print(f"    s (decoded): {s_decoded[:200]}")
    print(f"    l (decoded): {l_decoded[:200]}")

conn.close()

# Hadeeth relationships
print("\n=== HADEETH DATABASE RELATIONSHIPS ===")
conn = sqlite3.connect(str(BASE_DIR / "service" / "hadeeth.db"))
c = conn.cursor()

unique_books = c.execute("SELECT COUNT(DISTINCT book_id) FROM service").fetchone()[0]
unique_keys = c.execute("SELECT COUNT(DISTINCT key_id) FROM service").fetchone()[0]
unique_pages = c.execute("SELECT COUNT(DISTINCT page_id) FROM service").fetchone()[0]
total_rows = c.execute("SELECT COUNT(*) FROM service").fetchone()[0]

print(f"  Total rows: {total_rows:,}")
print(f"  Unique book_ids: {unique_books:,}")
print(f"  Unique key_ids: {unique_keys:,}")
print(f"  Unique page_ids: {unique_pages:,}")

print("\nKey ID distribution (top 15):")
rows = c.execute("SELECT key_id, COUNT(*) as cnt FROM service GROUP BY key_id ORDER BY cnt DESC LIMIT 15").fetchall()
for key_id, cnt in rows:
    print(f"  key_id={key_id}: {cnt} occurrences")

print("\nSample relationships:")
samples = c.execute("SELECT * FROM service LIMIT 10").fetchall()
for row in samples:
    print(f"  key_id={row[0]}, book_id={row[1]}, page_id={row[2]}")

conn.close()

# Tafseer relationships
print("\n=== TAFSEER DATABASE RELATIONSHIPS ===")
conn = sqlite3.connect(str(BASE_DIR / "service" / "tafseer.db"))
c = conn.cursor()

unique_books = c.execute("SELECT COUNT(DISTINCT book_id) FROM service").fetchone()[0]
unique_keys = c.execute("SELECT COUNT(DISTINCT key_id) FROM service").fetchone()[0]
unique_pages = c.execute("SELECT COUNT(DISTINCT page_id) FROM service").fetchone()[0]
total_rows = c.execute("SELECT COUNT(*) FROM service").fetchone()[0]

print(f"  Total rows: {total_rows:,}")
print(f"  Unique book_ids: {unique_books:,}")
print(f"  Unique key_ids: {unique_keys:,}")
print(f"  Unique page_ids: {unique_pages:,}")

key_range = c.execute("SELECT MIN(key_id), MAX(key_id) FROM service").fetchone()
print(f"  Key ID range: {key_range[0]} to {key_range[1]}")

print("\nSample relationships (first 20):")
samples = c.execute("SELECT * FROM service LIMIT 20").fetchall()
for row in samples:
    print(f"  key_id={row[0]}, book_id={row[1]}, page_id={row[2]}")

conn.close()
