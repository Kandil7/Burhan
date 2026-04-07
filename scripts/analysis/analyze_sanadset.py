import csv
import sys

# Fix field size limit for Windows
try:
    csv.field_size_limit(sys.maxsize)
except OverflowError:
    csv.field_size_limit(2**31 - 1)

f = open(r'K:\business\projects_v2\Athar\datasets\Sanadset 368K Data on Hadith Narrators\Sanadset 368K Data on Hadith Narrators\sanadset.csv', encoding='utf-8')
reader = csv.DictReader(f)

# Get header
first_row = next(reader)
print(f'Columns ({len(first_row.keys())}): {list(first_row.keys())}')
print(f'\nFirst record:')
for k, v in first_row.items():
    val = str(v)[:150] + '...' if len(str(v)) > 150 else str(v)
    print(f'  {k}: {val}')

# Count books
f.seek(0)
reader = csv.DictReader(f)
books = {}
total = 0
for row in reader:
    total += 1
    book = row.get('book', 'UNKNOWN')
    books[book] = books.get(book, 0) + 1
    if total % 100000 == 0:
        print(f'  Processed {total} rows...')

print(f'\nTotal hadith records: {total}')
print(f'Unique books: {len(books)}')
print(f'\nTop 20 books by hadith count:')
for book, cnt in sorted(books.items(), key=lambda x: -x[1])[:20]:
    print(f'  {book}: {cnt:,}')

f.close()
