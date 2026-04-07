import sqlite3

conn = sqlite3.connect(r'K:\business\projects_v2\Athar\datasets\data\metadata\books.db')
cur = conn.cursor()

# Books per category using cat_name
cur.execute("""
    SELECT cat_name, COUNT(*) as cnt 
    FROM books 
    GROUP BY cat_name 
    ORDER BY cnt DESC
""")
print('=== Books per Category ===')
total_books = 0
for row in cur.fetchall():
    print(f'  {row[0]}: {row[1]}')
    total_books += row[1]
print(f'Total: {total_books}')

# Extracted vs not
cur.execute("SELECT extracted, COUNT(*) FROM books GROUP BY extracted")
print('\n=== Extraction Status ===')
for row in cur.fetchall():
    status = 'Extracted' if row[0] == 1 else 'Not Extracted'
    print(f'  {status}: {row[1]}')

# Size distribution
cur.execute("SELECT MIN(size_mb), MAX(size_mb), AVG(size_mb), SUM(size_mb) FROM books")
row = cur.fetchone()
print(f'\n=== Size Stats (MB) ===')
print(f'  Min: {row[0]}, Max: {row[1]}, Avg: {row[2]:.2f}, Total: {row[3]:.2f}')

# Type distribution
cur.execute("SELECT type, COUNT(*) FROM books GROUP BY type ORDER BY type")
print('\n=== Book Types ===')
for row in cur.fetchall():
    print(f'  Type {row[0]}: {row[1]}')

conn.close()
