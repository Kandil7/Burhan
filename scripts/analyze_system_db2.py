import sqlite3

# Check a few system_book .db files with content
db_files = [
    r"K:\business\projects_v2\Athar\datasets\system_book_datasets\book\000\1000.db",
    r"K:\business\projects_v2\Athar\datasets\system_book_datasets\book\000\10000.db",
    r"K:\business\projects_v2\Athar\datasets\system_book_datasets\book\001\1.db",
]

for db_path in db_files:
    import os
    size = os.path.getsize(db_path) if os.path.exists(db_path) else 0
    print(f"\n=== {db_path} ({size} bytes) ===")
    if size == 0:
        print("  EMPTY FILE")
        continue
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cur.fetchall()
    print(f"  Tables: {[t[0] for t in tables]}")
    for t in tables:
        tname = t[0]
        cur.execute(f"PRAGMA table_info({tname})")
        cols = cur.fetchall()
        print(f"  {tname} columns: {[c[1] for c in cols]}")
        cur.execute(f"SELECT COUNT(*) FROM {tname}")
        cnt = cur.fetchone()[0]
        print(f"  {tname} rows: {cnt}")
        if cnt > 0:
            cur.execute(f"SELECT * FROM {tname} LIMIT 1")
            row = cur.fetchone()
            print(f"  Sample: {dict(zip([c[1] for c in cols], row))}")
    conn.close()

# Check S1.db structure (seems important - 18989 rows)
print("\n\n=== S1.db (service) ===")
conn = sqlite3.connect(r"K:\business\projects_v2\Athar\datasets\system_book_datasets\service\S1.db")
cur = conn.cursor()
cur.execute("PRAGMA table_info(b)")
cols = cur.fetchall()
print(f"  b columns: {[c[1] for c in cols]}")
cur.execute("SELECT COUNT(*) FROM b")
print(f"  b rows: {cur.fetchone()[0]}")
cur.execute("SELECT * FROM b LIMIT 2")
rows = cur.fetchall()
for i, row in enumerate(rows):
    print(f"  Row {i}: {dict(zip([c[1] for c in cols], row))}")
conn.close()

# Check S2.db structure (roots - 3.2M rows)
print("\n\n=== S2.db (roots) ===")
conn = sqlite3.connect(r"K:\business\projects_v2\Athar\datasets\system_book_datasets\service\S2.db")
cur = conn.cursor()
cur.execute("PRAGMA table_info(roots)")
cols = cur.fetchall()
print(f"  roots columns: {[c[1] for c in cols]}")
cur.execute("SELECT COUNT(*) FROM roots")
print(f"  roots rows: {cur.fetchone()[0]}")
cur.execute("SELECT * FROM roots LIMIT 2")
rows = cur.fetchall()
for i, row in enumerate(rows):
    val = {k: (str(v)[:80]+'...' if len(str(v))>80 else str(v)) for k,v in zip([c[1] for c in cols], row)}
    print(f"  Row {i}: {val}")
conn.close()

# Check hadeeth.db service
print("\n\n=== hadeeth.db (service) ===")
conn = sqlite3.connect(r"K:\business\projects_v2\Athar\datasets\system_book_datasets\service\hadeeth.db")
cur = conn.cursor()
cur.execute("PRAGMA table_info(service)")
cols = cur.fetchall()
print(f"  service columns: {[c[1] for c in cols]}")
cur.execute("SELECT * FROM service LIMIT 2")
rows = cur.fetchall()
for i, row in enumerate(rows):
    val = {k: (str(v)[:80]+'...' if len(str(v))>80 else str(v)) for k,v in zip([c[1] for c in cols], row)}
    print(f"  Row {i}: {val}")
cur.execute("PRAGMA table_info(inservice)")
cols2 = cur.fetchall()
print(f"  inservice columns: {[c[1] for c in cols2]}")
cur.execute("SELECT * FROM inservice LIMIT 2")
rows2 = cur.fetchall()
for i, row in enumerate(rows2):
    print(f"  Row {i}: {dict(zip([c[1] for c in cols2], row))}")
conn.close()
