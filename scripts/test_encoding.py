#!/usr/bin/env python3
"""Quick test to understand Lucene encoding."""
import json
import sys

sample_file = r"K:\business\projects_v2\Athar\data\processed\lucene_sample_pages.json"

with open(sample_file, "rb") as f:
    raw = f.read()

# Find the first "body" value
idx = raw.find(b'"body": "')
if idx == -1:
    print("No body found")
    sys.exit(1)

# Get some bytes after the key
start = idx + len(b'"body": "')
chunk = raw[start:start+200]
print(f"Raw bytes hex: {chunk[:60].hex()}")

# Try decoding as Windows-1256 directly
try:
    decoded = chunk.decode("windows-1256")
    print(f"Windows-1256 decode: {decoded[:100]}")
except Exception as e:
    print(f"Windows-1256 failed: {e}")

# The file was written by Java as UTF-8, so let's read it properly
with open(sample_file, "r", encoding="utf-8") as f:
    data = json.load(f)

doc = data[0]
body = doc["body"]
print(f"\nBody as UTF-8 string (first 100 chars):")
print(body[:100])
print(f"\nBody repr (first 100 chars):")
print(repr(body[:100]))

# The body is already valid UTF-8 but contains what looks like
# double-encoded text. Let's check if it's UTF-8 bytes interpreted as Latin-1
# then stored as UTF-8
try:
    # Re-encode as latin-1 to get original bytes, then decode as windows-1256
    decoded = body.encode("latin-1").decode("windows-1256")
    print(f"\nDecoded (latin-1 -> windows-1256): {decoded[:100]}")
except Exception as e:
    print(f"\nlatin-1 -> windows-1256 failed: {e}")

# Check if any chars are outside ASCII
non_ascii = [(i, c, ord(c), hex(ord(c))) for i, c in enumerate(body[:200]) if ord(c) > 127]
print(f"\nFirst 10 non-ASCII chars in body: {non_ascii[:10]}")

# Check id field for book_key pattern
print(f"\nID field: {doc.get('id', 'N/A')}")
print(f"All keys: {list(doc.keys())}")
