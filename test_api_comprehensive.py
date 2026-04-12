#!/usr/bin/env python3
"""
Comprehensive test of ALL 18+ Athar API endpoints.
Tests health, query, tools, quran, and RAG endpoints with correct payloads.
"""
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
        with urllib.request.urlopen(req, timeout=60) as r:
            return r.status, json.loads(r.read().decode('utf-8'))
    except urllib.error.HTTPError as e:
        body_bytes = e.read()
        return e.code, json.loads(body_bytes.decode('utf-8')) if body_bytes else None
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
            try:
                if not check_fn(status, body):
                    passed = False
                    issues.append(check_name)
            except Exception as e:
                passed = False
                issues.append(f"{check_name}: {e}")
    
    icon = "PASS" if passed else "FAIL"
    results.append({
        "name": name, "path": path, "method": method,
        "status": status, "time": elapsed, "passed": passed,
        "issues": issues, "body": body
    })
    print(f"[{icon}] {name}")
    print(f"   {method} {path} -> {status} ({elapsed}ms)")
    if issues:
        for i in issues:
            print(f"      - {i}")
    print()
    return status, body

print("="*70)
print("ATHAR ISLAMIC QA SYSTEM - COMPREHENSIVE API TEST")
print(f"Base: {BASE} | Date: 2026-04-12 | Endpoints: 18+")
print("="*70)
print()

# =====================================================================
# 1. HEALTH ENDPOINTS (2)
# =====================================================================
print("--- HEALTH ENDPOINTS ---")
test("Health Check", "/health",
    checks={"200_ok": lambda s,b: s==200 and b.get("status")=="ok"})

test("Readiness Check", "/ready",
    checks={"200_ready": lambda s,b: s==200})

# =====================================================================
# 2. MAIN QUERY ENDPOINT (3 variations)
# =====================================================================
print("--- QUERY ENDPOINT ---")
test("Query - Fiqh (Arabic)", "/api/v1/query", "POST", {"query": "ما حكم الزكاة"},
    checks={"200": lambda s,b: s==200, "has_intent": lambda s,b: isinstance(b,dict) and "intent" in b, "has_answer": lambda s,b: isinstance(b,dict) and "answer" in b})

test("Query - Greeting", "/api/v1/query", "POST", {"query": "مرحبا"},
    checks={"200": lambda s,b: s==200, "intent_greeting": lambda s,b: isinstance(b,dict) and b.get("intent")=="greeting"})

test("Query - English", "/api/v1/query", "POST", {"query": "What is Islam?"},
    checks={"200": lambda s,b: s==200, "has_answer": lambda s,b: isinstance(b,dict) and "answer" in b})

# =====================================================================
# 3. TOOLS ENDPOINTS (5 tools + variants)
# =====================================================================
print("--- TOOLS ENDPOINTS ---")
test("Zakat - Cash", "/api/v1/tools/zakat", "POST", {"assets": {"cash": 10000}},
    checks={"200": lambda s,b: s==200, "zakat_250": lambda s,b: isinstance(b,dict) and b.get("zakat_amount")==250.0})

# ZakatAssets uses gold_grams and silver_grams
test("Zakat - Gold", "/api/v1/tools/zakat", "POST", {"assets": {"gold_grams": 100}},
    checks={"200": lambda s,b: s==200, "has_result": lambda s,b: isinstance(b,dict) and "zakat_amount" in b})

# Heirs uses wife_count (not wife), sons (correct)
test("Inheritance", "/api/v1/tools/inheritance", "POST",
    {"estate_value": 100000, "heirs": {"sons": 2, "wife_count": 1}},
    checks={"200": lambda s,b: s==200, "has_result": lambda s,b: isinstance(b,dict) and ("distribution" in b or "shares" in b or "heirs" in b or "result" in b)})

# method must be a string, not int
test("Prayer Times", "/api/v1/tools/prayer-times", "POST",
    {"lat": 21.4225, "lng": 39.8262, "method": "MWL"},
    checks={"200": lambda s,b: s==200, "has_times": lambda s,b: isinstance(b,dict) and ("timings" in b or "fajr" in str(b).lower() or "prayers" in str(b).lower())})

test("Hijri Date", "/api/v1/tools/hijri", "POST", {"gregorian_date": "2026-04-12"},
    checks={"200": lambda s,b: s==200, "has_hijri": lambda s,b: isinstance(b,dict) and ("hijri_date" in b or "hijri" in str(b).lower())})

test("Dua Retrieval", "/api/v1/tools/duas", "POST", {"category": "morning"},
    checks={"200": lambda s,b: s==200, "has_duas": lambda s,b: isinstance(b,dict) and ("duas" in b or "items" in b or len(b) > 0)})

# =====================================================================
# 4. QURAN ENDPOINTS (7)
# =====================================================================
print("--- QURAN ENDPOINTS ---")
test("List Surahs", "/api/v1/quran/surahs",
    checks={"200": lambda s,b: s==200, "has_list": lambda s,b: isinstance(b, list) and len(b)>0})

test("Surah 1 Details", "/api/v1/quran/surahs/1",
    checks={"200": lambda s,b: s==200, "surah_1": lambda s,b: isinstance(b,dict) and b.get("number")==1})

test("Ayah 1:1", "/api/v1/quran/ayah/1:1",
    checks={"200": lambda s,b: s==200, "has_text": lambda s,b: isinstance(b,dict) and (b.get("text_uthmani") or b.get("text"))})

test("Ayah Search", "/api/v1/quran/search", "POST", {"query": "رحمة"},
    checks={"200": lambda s,b: s==200, "has_verses": lambda s,b: isinstance(b,dict) and "verses" in b})

test("Quotation Validation", "/api/v1/quran/validate", "POST", {"text": "بسم الله الرحمن الرحيم"},
    checks={"200": lambda s,b: s==200, "has_result": lambda s,b: isinstance(b,dict) and ("is_quran" in b or "confidence" in b or "matched_ayah" in b)})

test("NL2SQL Analytics", "/api/v1/quran/analytics", "POST",
    {"query": "How many surahs are there?"},
    checks={"200_or_400": lambda s,b: s in [200, 400], "has_response": lambda s,b: isinstance(b,dict)})

test("Tafsir 1:1", "/api/v1/quran/tafsir/1:1",
    checks={"200": lambda s,b: s==200, "has_content": lambda s,b: isinstance(b,dict) and len(b) > 0})

# =====================================================================
# 5. RAG ENDPOINTS (3)
# =====================================================================
print("--- RAG ENDPOINTS ---")
test("RAG Fiqh", "/api/v1/rag/fiqh", "POST", {"query": "ما هو حكم الصلاة؟"},
    checks={"200": lambda s,b: s==200, "has_answer": lambda s,b: isinstance(b,dict) and ("answer" in b or "response" in b or "results" in b or "text" in b)})

test("RAG General", "/api/v1/rag/general", "POST", {"query": "ما هي أركان الإسلام؟"},
    checks={"200": lambda s,b: s==200, "has_answer": lambda s,b: isinstance(b,dict) and ("answer" in b or "response" in b or "results" in b or "text" in b)})

test("RAG Statistics", "/api/v1/rag/stats",
    checks={"200": lambda s,b: s==200, "has_stats": lambda s,b: isinstance(b, dict) and len(b) > 0})

# =====================================================================
# SUMMARY
# =====================================================================
print("="*70)
print("FINAL RESULTS")
print("="*70)

total = len(results)
passed = sum(1 for r in results if r["passed"])
failed = total - passed
avg_ms = sum(r["time"] for r in results) / total if total else 0
min_ms = min((r["time"] for r in results), default=0)
max_ms = max((r["time"] for r in results), default=0)

print(f"\nEndpoints Tested:  {total}")
print(f"Passed:            {passed}")
print(f"Failed:            {failed}")
print(f"Pass Rate:         {passed/total*100:.1f}%")
print(f"\nResponse Times:")
print(f"  Average:         {avg_ms:.0f}ms")
print(f"  Fastest:         {min_ms}ms")
print(f"  Slowest:         {max_ms}ms")

# Category breakdown
categories = {
    "Health": lambda r: "/health" in r["path"] or "/ready" in r["path"],
    "Query":  lambda r: r["path"] == "/api/v1/query",
    "Tools":  lambda r: "/api/v1/tools/" in r["path"],
    "Quran":  lambda r: "/api/v1/quran/" in r["path"],
    "RAG":    lambda r: "/api/v1/rag/" in r["path"],
}

for cat, filt in categories.items():
    items = [r for r in results if filt(r)]
    if not items: continue
    cat_pass = sum(1 for r in items if r["passed"])
    cat_total = len(items)
    cat_avg = sum(r["time"] for r in items) / cat_total
    tag = "ALL PASS" if cat_pass == cat_total else f"{cat_pass}/{cat_total}"
    print(f"\n  {cat:12s} [{tag:10s}]  {cat_total} endpoints, avg {cat_avg:.0f}ms")
    for r in items:
        sign = "+" if r["passed"] else "-"
        print(f"    [{sign}] {r['name']:30s} {r['status']:>4}  {r['time']:>5}ms")

# Failed details
failed_list = [r for r in results if not r["passed"]]
if failed_list:
    print(f"\n{'='*70}")
    print("FAILED ENDPOINTS - DETAILS")
    print(f"{'='*70}")
    for r in failed_list:
        print(f"\n  {r['name']}")
        print(f"  {r['method']} {r['path']}")
        print(f"  Status: {r['status']} | Time: {r['time']}ms")
        if r["issues"]:
            print(f"  Issues: {', '.join(r['issues'])}")
        if r["body"] and isinstance(r["body"], dict):
            body_str = json.dumps(r["body"], ensure_ascii=False, indent=2)[:400]
            print(f"  Body: {body_str}")

print(f"\n{'='*70}")
print(f"OVERALL: {'ALL TESTS PASSED' if failed == 0 else f'{failed} TEST(S) NEED ATTENTION'}")
print(f"{'='*70}")

exit(0 if failed == 0 else 1)
