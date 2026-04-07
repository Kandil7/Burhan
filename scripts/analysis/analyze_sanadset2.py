import csv
import sys

try:
    csv.field_size_limit(sys.maxsize)
except OverflowError:
    csv.field_size_limit(2**31 - 1)

# Analyze Sanadset more carefully
f = open(r'K:\business\projects_v2\Athar\datasets\Sanadset 368K Data on Hadith Narrators\Sanadset 368K Data on Hadith Narrators\sanadset.csv', encoding='utf-8')
reader = csv.reader(f)
header = next(reader)
print(f'Columns: {header}')

# Sample rows at different positions
positions = [0, 1, 2, 100, 10000, 50000, 100000, 200000, 300000, 400000, 500000, 600000, 650000]
for i, row in enumerate(reader):
    if i in positions:
        print(f'\n--- Row {i} ---')
        print(f'  Book col (idx 1): {row[1][:80] if len(row)>1 else "N/A"}')
        print(f'  Num_hadith col (idx 2): {row[2] if len(row)>2 else "N/A"}')
        print(f'  Matn (first 100): {row[3][:100] if len(row)>3 else "N/A"}')
        print(f'  Sanad_Length (idx 5): {row[5] if len(row)>5 else "N/A"}')
    if i > 650986:
        break

f.close()

# Also check the books.csv more carefully
print('\n\n=== Books CSV ===')
f = open(r'K:\business\projects_v2\Athar\datasets\Sanadset 368K Data on Hadith Narrators\Sanadset 368K Data on Hadith Narrators\books.csv', encoding='utf-8')
lines = f.readlines()
print(f'Total lines (incl header): {len(lines)}')
print(f'First 10 books:')
for line in lines[:11]:
    print(f'  {line.strip()}')
f.close()
