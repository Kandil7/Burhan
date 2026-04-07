import sqlite3
import os

# Sample a system book .db file
db_path = r"K:\business\projects_v2\Athar\datasets\system_book_datasets\book\000\0.db"
print(f"=== Sample DB: {db_path} ===")
print(f"File size: {os.path.getsize(db_path)} bytes")

conn = sqlite3.connect(db_path)
cur = conn.cursor()
cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cur.fetchall()
print(f"Tables: {[t[0] for t in tables]}")

for t in tables:
    tname = t[0]
    cur.execute(f"PRAGMA table_info({tname})")
    cols = cur.fetchall()
    print(f"\nTable: {tname}")
    print(f"  Columns: {[c[1] for c in cols]}")
    cur.execute(f"SELECT COUNT(*) FROM {tname}")
    print(f"  Count: {cur.fetchone()[0]}")
    cur.execute(f"SELECT * FROM {tname} LIMIT 2")
    rows = cur.fetchall()
    for i, row in enumerate(rows):
        print(f"  Row {i}: {dict(zip([c[1] for c in cols], row))}")
conn.close()

# Check service DBs
print("\n=== Service DBs ===")
for db_name in ['hadeeth.db', 'tafseer.db', 'trajim.db', 'S1.db', 'S2.db']:
    db_path = rf"K:\business\projects_v2\Athar\datasets\system_book_datasets\service\{db_name}"
    if os.path.exists(db_path):
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cur.fetchall()
        print(f"\n{db_name}: Tables={[t[0] for t in tables]}")
        for t in tables:
            cur.execute(f"SELECT COUNT(*) FROM {t[0]}")
            print(f"  {t[0]}: {cur.fetchone()[0]} rows")
        conn.close()

# Check user DB
user_db = r"K:\business\projects_v2\Athar\datasets\system_book_datasets\user\data.db"
if os.path.exists(user_db):
    conn = sqlite3.connect(user_db)
    cur = conn.cursor()
    cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cur.fetchall()
    print(f"\ndata.db: Tables={[t[0] for t in tables]}")
    for t in tables:
        cur.execute(f"SELECT COUNT(*) FROM {t[0]}")
        print(f"  {t[0]}: {cur.fetchone()[0]} rows")
    conn.close()
