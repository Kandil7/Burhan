import sqlite3
import os

# Check a few non-empty .db files from different ranges
import glob

all_dbs = glob.glob(r"K:\business\projects_v2\Athar\datasets\system_book_datasets\book\*\*.db")
non_empty = [(p, os.path.getsize(p)) for p in all_dbs if os.path.getsize(p) > 0]
print(f"Total .db files: {len(all_dbs)}")
print(f"Non-empty .db files: {len(non_empty)}")
total_size = sum(s for _, s in non_empty)
print(f"Total size of non-empty DBs: {total_size / (1024*1024*1024):.2f} GB")

# Sample 3 non-empty DBs
for db_path, size in non_empty[:3]:
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cur.fetchall()
    print(f"\n=== {os.path.basename(db_path)} ({size/1024:.1f} KB) ===")
    for t in tables:
        cur.execute(f"SELECT COUNT(*) FROM {t[0]}")
        cnt = cur.fetchone()[0]
        if cnt > 0:
            cur.execute(f"SELECT * FROM {t[0]} LIMIT 1")
            row = cur.fetchone()
            cur.execute(f"PRAGMA table_info({t[0]})")
            cols = [c[1] for c in cur.fetchall()]
            sample = dict(zip(cols, row))
            # Truncate long values
            sample = {k: (str(v)[:100]+'...' if len(str(v))>100 else str(v)) for k,v in sample.items()}
            print(f"  {t[0]}: {cnt} rows, sample: {sample}")
    conn.close()
