#!/usr/bin/env python3
"""Debug: Check all citation fields"""

import sys
import io

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

import requests

url = "http://localhost:8002/api/v1/ask"
headers = {"Content-Type": "application/json"}

q = "ما حدث التاريخي الذي تدور حوله الفقرة الأولى؟"
resp = requests.post(url, json={"query": q}, headers=headers, timeout=60)
data = resp.json()

print("Citation fields available:")
for c in data.get("citations", [])[:1]:
    print("\nAll keys in citation:")
    for k in sorted(c.keys()):
        print(f"  {k}: {type(c.get(k)).__name__} = {c.get(k)}")
