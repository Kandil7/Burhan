#!/usr/bin/env python3
"""Comprehensive test of ALL 18 Athar API endpoints."""
import json
import urllib.request
import urllib.error
import time

BASE = "http://localhost:8002"
results = []

def request(method, path, data=None):
    url = f"{BASE}{path}"
    try:
        if data:
            req = urllib.request.Request(url, method=method, data=json.dumps(data).encode('utf-8'), headers={'Content-Type': 'application/json'})
        else:
            req = urllib.request.Request(url, method=method)
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.status, json.loads(r.read().decode('utf-8'))
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read().decode('utf-8')) if e.read else None
    except Exception as e:
        return 0, str(e)

def test(name, path, method="GET", data=None, checks=None):
    start = time.time()
    status, body = request(method, path, data)
    elapsed = int((time.time() - start) * 1000)
    
    passed = True
    issues = []
    if checks:
        for check_name, check_fn in checks.items():
            if not check_fn(status, body):
                passed = False
                issues.append(f"  ❌ {check_name}")
    
    status_icon = "✅" if passed else "⚠️"
    results.append({"name": name, "path": path, "status": status, "time": elapsed, "passed": passed, "issues": issues, "body": body})
    print(f"{status_icon} {name}")
    print(f"   {method} {path}")
    print(f"   Status: {status} | Time: {elapsed}ms")
    if issues:
        for i in issues:
            print(i)
    if body and not passed:
        print(f"   Response: {str(body)[:200]}")
    print()

print("="*70)
print("ATHAR ISLAMIC QA SYSTEM - COMPREHENSIVE API ENDPOINT TEST")
print("="*70)
print()

# HEALTH ENDPOINTS
test("Health Check", "/health", checks={"status_ok": lambda s,b: s==200 and b.get("status")=="ok"})
test("Readiness Check", "/ready", checks={"all_healthy": lambda s,b: s==200 and all(v=="healthy" or "healthy" in str(v) for v in b.get("services",{}).values())})

# QUERY ENDPOINT
test("Query - Fiqh", "/api/v1/query", "POST", {"query": "ما حكم الزكاة"}, checks={"intent_fiqh": lambda s,b: s==200 and b.get("intent")=="fiqh"})
test("Query - Greeting", "/api/v1/query", "POST", {"query": "مرحبا"}, checks={"intent_greeting": lambda s,b: s==200 and b.get("intent")=="greeting"})

# TOOLS ENDPOINTS
test("Zakat Calculator", "/api/v1/tools/zakat", "POST", {"assets": {"cash": 10000}}, checks={"zakat_250": lambda s,b: s==200 and b.get("zakat_amount")==250.0})
test("Inheritance Calculator", "/api/v1/tools/inheritance", "POST", {"total_estate": 100000, "deceased_gender": "male", "relatives": [{"relation": "son", "count": 2}, {"relation": "wife", "count": 1}]})
test("Prayer Times", "/api/v1/tools/prayer-times", "POST", {"city": "Makkah", "country": "SA"})
test("Hijri Date", "/api/v1/tools/hijri", "POST", {"date": "2026-04-12"}, checks={"hijri_1447": lambda s,b: s==200 and (b.get("hijri_date",{}).get("year")==1447 or 1447 in str(b))})
test("Dua Retrieval", "/api/v1/tools/duas", "POST", {"category": "morning"})

# QURAN ENDPOINTS
test("List Surahs", "/api/v1/quran/surahs", checks={"surahs_list": lambda s,b: s==200 and isinstance(b, list) and len(b)>0})
test("Surah Details", "/api/v1/quran/surahs/1", checks={"surah_1": lambda s,b: s==200 and b.get("number")==1})
test("Ayah 1:1", "/api/v1/quran/ayah/1:1", checks={"ayah_text": lambda s,b: s==200 and b.get("text_uthmani")})
test("Ayah Search", "/api/v1/quran/search", "POST", {"query": "رحمة"})
test("Quotation Validation", "/api/v1/quran/validate", "POST", {"text": "بسم الله الرحمن الرحيم"})
test("NL2SQL Analytics", "/api/v1/quran/analytics", "POST", {"question": "كم عدد السور في القرآن؟"})
test("Tafsir Retrieval", "/api/v1/quran/tafsir/1:1")

# RAG ENDPOINTS
test("RAG Fiqh", "/api/v1/rag/fiqh", "POST", {"question": "ما هو حكم الصلاة؟"})
test("RAG General", "/api/v1/rag/general", "POST", {"question": "ما هي أركان الإسلام؟"})
test("RAG Statistics", "/api/v1/rag/stats")

# SUMMARY
print("="*70)
passed_count = sum(1 for r in results if r["passed"])
failed_count = len(results) - passed_count
avg_time = sum(r["time"] for r in results) / len(results) if results else 0
print(f"RESULTS: {passed_count}/{len(results)} passed, {failed_count} failed")
print(f"Average response time: {avg_time:.0f}ms")
print("="*70)

# Detail failed/slow tests
failed = [r for r in results if not r["passed"]]
if failed:
    print("\n⚠️  FAILED/ISSUES:")
    for r in failed:
        print(f"  - {r['name']}: {', '.join(r['issues'])}")

exit(0 if failed_count == 0 else 1)
