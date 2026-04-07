#!/usr/bin/env python
"""Analyze books.json metadata."""
import json
from collections import Counter

path = r'K:\business\projects_v2\Athar\datasets\data\metadata\books.json'
data = json.load(open(path, encoding='utf-8'))
books = data['books']
print(f'Total books: {len(books)}')
print(f'Extracted: {data.get("extracted","?")}')

# Category distribution
cats = Counter(b.get('cat_name', 'unknown') for b in books)
print('\n=== CATEGORY DISTRIBUTION ===')
for cat, cnt in cats.most_common():
    print(f'  {cat}: {cnt}')

# Type distribution
types = Counter(b.get('type', 0) for b in books)
print('\n=== BOOK TYPE DISTRIBUTION ===')
for t, cnt in types.most_common():
    print(f'  Type {t}: {cnt}')

# Date distribution
dates = [b.get('date', 0) for b in books]
print(f'\n=== DATE RANGE ===')
valid_dates = [d for d in dates if 0 < d < 99999]
if valid_dates:
    print(f'  Min: {min(valid_dates)}')
    print(f'  Max: {max(valid_dates)}')
print(f'  Unknown (99999): {sum(1 for d in dates if d == 99999)}')

# Author distribution
author_counts = [len(b.get('authors', [])) for b in books]
print(f'\n=== AUTHOR COUNT PER BOOK ===')
print(f'  No authors: {sum(1 for a in author_counts if a == 0)}')
print(f'  1 author: {sum(1 for a in author_counts if a == 1)}')
print(f'  2+ authors: {sum(1 for a in author_counts if a >= 2)}')

# Sample a few books
print('\n=== SAMPLE BOOKS ===')
for b in books[:3]:
    print(json.dumps(b, ensure_ascii=False, indent=2)[:500])
    print('---')
