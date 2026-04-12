#!/usr/bin/env python3
"""Comprehensive test of ALL Athar API endpoints with corrected payloads."""
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
                    issues.append(f"  FAIL: {check_name}")
            except Exception as e:
                passed = False
                issues.append(f"  FAIL: {check_name} (error: {e})")
    
    status_icon = "PASS" if passed else "WARN"
    results.append({"name": name, "path": path, "status": status, "time": elapsed, "passed": passed, "issues": issues, "body": body})
    print(f"[{status_icon}] {name}")
    print(f"   {method} {path}")
    print(f"   Status: {status} | Time: {elapsed}ms")
    if issues:
        for i in issues:
            print(i)
    if body and not passed and status != 200:
        detail = json.dumps(body, ensure_ascii=False)[:300]
        print(f"   Response: {detail}")
    print()

print("="*70)
print("ATHAR ISLAMIC QA SYSTEM - COMPREHENSIVE API ENDPOINT TEST")
print("="*70)
print(f"Base URL: {BASE}")
print(f"Date: 2026-04-12")
print()

# ===================== HEALTH ENDPOINTS (2) =====================
test("Health Check", "/health",
    checks={"status_ok": lambda s,b: s==200 and b.get("status")=="ok"})

test("Readiness Check", "/ready",
    checks={"all_healthy": lambda s,b: s==200})

# ===================== QUERY ENDPOINT (1 main, expanded) =====================
test("Query - Fiqh", "/api/v1/query", "POST", {"query": "ما حكم الزكاة"},
    checks={"status_200": lambda s,b: s==200, "has_intent": lambda s,b: b.get("intent") in ["fiqh", "zakat"]})

test("Query - Greeting", "/api/v1/query", "POST", {"query": "مرحبا"},
    checks={"status_200": lambda s,b: s==200, "intent_greeting": lambda s,b: b.get("intent")=="greeting"})

test("Query - English", "/api/v1/query", "POST", {"query": "What is Islam?"},
    checks={"status_200": lambda s,b: s==200, "has_answer": lambda s,b: "answer" in b})

# ===================== TOOLS ENDPOINTS (5) =====================
test("Zakat Calculator", "/api/v1/tools/zakat", "POST", {"assets": {"cash": 10000}},
    checks={"status_200": lambda s,b: s==200, "zakat_250": lambda s,b: b.get("zakat_amount")==250.0})

test("Zakat - Gold", "/api/v1/tools/zakat", "POST", {"assets": {"gold_value": 50000}},
    checks={"status_200": lambda s,b: s==200, "has_result": lambda s,b: "zakat_amount" in b})

test("Inheritance Calculator", "/api/v1/tools/inheritance", "POST",
    {"estate_value": 100000, "heirs": [{"relation": "son", "count": 2}, {"relation": "wife", "count": 1}]},
    checks={"status_200": lambda s,b: s==200, "has_distribution": lambda s,b: "distribution" in b or "shares" in b or "heirs" in b})

test("Prayer Times", "/api/v1/tools/prayer-times", "POST",
    {"lat": 21.4225, "lng": 39.8262, "method": 4},
    checks={"status_200": lambda s,b: s==200, "has_times": lambda s,b: "timings" in b or "fajr" in str(b).lower() or "prayer" in str(b).lower()})

test("Hijri Date", "/api/v1/tools/hijri", "POST", {"date": "2026-04-12"},
    checks={"status_200": lambda s,b: s==200, "has_hijri": lambda s,b: "hijri_date" in b or "hijri" in str(b).lower()})

test("Dua Retrieval", "/api/v1/tools/duas", "POST", {"category": "morning"},
    checks={"status_200": lambda s,b: s==200, "has_duas": lambda s,b: "duas" in b or "items" in b or len(b) > 0})

# ===================== QURAN ENDPOINTS (7) =====================
test("List Surahs", "/api/v1/quran/surahs",
    checks={"status_200": lambda s,b: s==200, "surahs_list": lambda s,b: isinstance(b, list) and len(b)>0})

test("Surah Details", "/api/v1/quran/surahs/1",
    checks={"status_200": lambda s,b: s==200, "surah_1": lambda s,b: b.get("number")==1})

test("Ayah 1:1", "/api/v1/quran/ayah/1:1",
    checks={"status_200": lambda s,b: s==200, "ayah_text": lambda s,b: b.get("text_uthmani") or b.get("text")})

test("Ayah Search", "/api/v1/quran/search", "POST", {"query": "رحمة"},
    checks={"status_200": lambda s,b: s==200, "has_results": lambda s,b: "results" in b or "ayahs" in b or isinstance(b, list)})

test("Quotation Validation", "/api/v1/quran/validate", "POST", {"text": "بسم الله الرحمن الرحيم"},
    checks={"status_200": lambda s,b: s==200, "has_validation": lambda s,b: "valid" in b or "matches" in b or "result" in b})

test("NL2SQL Analytics", "/api/v1/quran/analytics", "POST",
    {"query": "كم عدد السور في القرآن؟"},
    checks={"status_200": lambda s,b: s==200, "has_answer": lambda s,b: "answer" in b or "result" in b or "sql" in b})

test("Tafsir Retrieval", "/api/v1/quran/tafsir/1:1",
    checks={"status_200": lambda s,b: s==200, "has_tafsir": lambda s,b: "tafsir" in b or "text" in b or len(b) > 0})

# ===================== RAG ENDPOINTS (3) =====================
test("RAG Fiqh", "/api/v1/rag/fiqh", "POST",
    {"query": "ما هو حكم الصلاة؟"},
    checks={"status_200": lambda s,b: s==200, "has_answer": lambda s,b: "answer" in b or "response" in b or "results" in b})

test("RAG General", "/api/v1/rag/general", "POST",
    {"query": "ما هي أركان الإسلام؟"},
    checks={"status_200": lambda s,b: s==200, "has_answer": lambda s,b: "answer" in b or "response" in b or "results" in b})

test("RAG Statistics", "/api/v1/rag/stats",
    checks={"status_200": lambda s,b: s==200, "has_stats": lambda s,b: isinstance(b, dict) and len(b) > 0})

# ===================== SUMMARY =====================
print("="*70)
print("TEST RESULTS SUMMARY")
print("="*70)

passed_count = sum(1 for r in results if r["passed"])
failed_count = len(results) - passed_count
total = len(results)
avg_time = sum(r["time"] for r in results) / total if total > 0 else 0
min_time = min((r["time"] for r in results), default=0)
max_time = max((r["time"] for r in results), default=0)

print(f"\nTotal Endpoints Tested: {total}")
print(f"Passed: {passed_count}")
print(f"Failed: {failed_count}")
print(f"Pass Rate: {passed_count/total*100:.1f}%" if total > 0 else "N/A")
print(f"\nResponse Times:")
print(f"  Average: {avg_time:.0f}ms")
print(f"  Min:     {min_time}ms")
print(f"  Max:     {max_time}ms")

print(f"\n{'='*70}")
print(f"DETAILED RESULTS BY CATEGORY")
print(f"{'='*70}")

categories = {
    "Health": [r for r in results if "/health" in r["path"] or "/ready" in r["path"]],
    "Query": [r for r in results if r["path"] == "/api/v1/query"],
    "Tools": [r for r in results if "/api/v1/tools/" in r["path"]],
    "Quran": [r for r in results if "/api/v1/quran/" in r["path"]],
    "RAG": [r for r in results if "/api/v1/rag/" in r["path"]],
}

for cat, items in categories.items():
    cat_passed = sum(1 for r in items if r["passed"])
    cat_total = len(items)
    cat_avg = sum(r["time"] for r in items) / cat_total if cat_total > 0 else 0
    status = "ALL PASS" if cat_passed == cat_total else f"{cat_passed}/{cat_total}"
    print(f"\n{cat} ({status}, avg {cat_avg:.0f}ms):")
    for r in items:
        icon = "+" if r["passed"] else "-"
        print(f"  [{icon}] {r['name']} - {r['status']} ({r['time']}ms)")
        if r["issues"]:
            for issue in r["issues"]:
                print(f"      {issue}")

# Failed details
failed = [r for r in results if not r["passed"]]
if failed:
    print(f"\n{'='*70}")
    print(f"FAILED ENDPOINTS DETAIL")
    print(f"{'='*70}")
    for r in failed:
        print(f"\n{r['name']} ({r['path']})")
        print(f"  Status: {r['status']}")
        print(f"  Issues: {', '.join(r['issues'])}")
        if r["body"]:
            body_str = json.dumps(r["body"], ensure_ascii=False, indent=2)[:500]
            print(f"  Response: {body_str}")

print(f"\n{'='*70}")
exit(0 if failed_count == 0 else 1)
