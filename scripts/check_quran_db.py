import sqlite3
conn = sqlite3.connect(r"K:\business\projects_v2\Athar\data\quran.db")
cur = conn.cursor()
cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cur.fetchall()
print(f"quran.db Tables: {[t[0] for t in tables]}")
for t in tables:
    cur.execute(f"PRAGMA table_info({t[0]})")
    cols = cur.fetchall()
    cur.execute(f"SELECT COUNT(*) FROM {t[0]}")
    cnt = cur.fetchone()[0]
    print(f"  {t[0]}: {cnt} rows, cols={[c[1] for c in cols]}")
conn.close()
