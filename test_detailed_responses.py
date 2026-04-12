#!/usr/bin/env python3
"""Detailed investigation of 422 responses and failures."""
import json
import urllib.request
import urllib.error
import time

BASE = "http://localhost:8002"

def request(method, path, data=None):
    url = f"{BASE}{path}"
    try:
        if data:
            req = urllib.request.Request(url, method=method, data=json.dumps(data).encode('utf-8'), headers={'Content-Type': 'application/json'})
        else:
            req = urllib.request.Request(url, method=method)
        with urllib.request.urlopen(req, timeout=60) as r:
            return r.status, json.loads(r.read().decode('utf-8'))
    except urllib.error.HTTPError as e:
        body_bytes = e.read()
        return e.code, json.loads(body_bytes.decode('utf-8')) if body_bytes else None
    except Exception as e:
        return 0, str(e)

def detail(name, path, method="GET", data=None):
    print(f"\n{'='*70}")
    print(f"{name}")
    print(f"{method} {path}")
    if data:
        print(f"Request: {json.dumps(data)}")
    print("-"*70)
    start = time.time()
    status, body = request(method, path, data)
    elapsed = int((time.time() - start) * 1000)
    print(f"Status: {status} | Time: {elapsed}ms")
    if body:
        print(f"Response:\n{json.dumps(body, indent=2, ensure_ascii=False)[:1000]}")
    return status, body

print("="*70)
print("DETAILED RESPONSE INVESTIGATION")
print("="*70)

# Investigate 422 responses
s1, b1 = detail("Inheritance Calculator (422)", "/api/v1/tools/inheritance", "POST",
    {"total_estate": 100000, "deceased_gender": "male", "relatives": [{"relation": "son", "count": 2}, {"relation": "wife", "count": 1}]})

s2, b2 = detail("Prayer Times (422)", "/api/v1/tools/prayer-times", "POST",
    {"city": "Makkah", "country": "SA"})

s3, b3 = detail("NL2SQL Analytics (422)", "/api/v1/quran/analytics", "POST",
    {"question": "كم عدد السور في القرآن؟"})

s4, b4 = detail("RAG Fiqh (422)", "/api/v1/rag/fiqh", "POST",
    {"question": "ما هو حكم الصلاة؟"})

s5, b5 = detail("RAG General (422)", "/api/v1/rag/general", "POST",
    {"question": "ما هي أركان الإسلام؟"})

# Test greeting with shorter timeout
print(f"\n{'='*70}")
print("Greeting Query (investigation)")
print("POST /api/v1/query")
print("-"*70)
start = time.time()
try:
    req = urllib.request.Request(f"{BASE}/api/v1/query", method="POST",
        data=json.dumps({"query": "مرحبا"}).encode('utf-8'),
        headers={'Content-Type': 'application/json'})
    with urllib.request.urlopen(req, timeout=45) as r:
        elapsed = int((time.time() - start) * 1000)
        body = json.loads(r.read().decode('utf-8'))
        print(f"Status: {r.status} | Time: {elapsed}ms")
        print(f"Response:\n{json.dumps(body, indent=2, ensure_ascii=False)[:800]}")
except urllib.error.HTTPError as e:
    elapsed = int((time.time() - start) * 1000)
    body = json.loads(e.read().decode('utf-8')) if e.read else None
    print(f"Status: {e.code} | Time: {elapsed}ms")
    print(f"Response: {body}")
except Exception as e:
    elapsed = int((time.time() - start) * 1000)
    print(f"Error after {elapsed}ms: {e}")
