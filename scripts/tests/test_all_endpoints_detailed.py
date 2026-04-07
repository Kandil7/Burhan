#!/usr/bin/env python3
"""
Comprehensive Endpoint Test Suite for Athar Islamic QA System.
Tests ALL endpoints with detailed response validation.
Usage: python scripts/test_all_endpoints_detailed.py
"""
import requests
import json
import sys
from typing import Any

BASE = "http://localhost:8002"
PASS = 0
FAIL = 0

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    BOLD = '\033[1m'
    END = '\033[0m'

def test(name, url, method="get", data=None, checks=None):
    global PASS, FAIL
    print(f"\n{Colors.CYAN}{'='*70}{Colors.END}")
    print(f"{Colors.BOLD}{name}{Colors.END}")
    print(f"{'='*70}")
    
    try:
        if method == "get":
            r = requests.get(url, timeout=15)
        elif method == "post":
            r = requests.post(url, json=data, timeout=15)
        
        status_ok = r.status_code in (200, 201)
        data = r.json() if status_ok else None
        
        if not status_ok:
            print(f"  {Colors.RED}✗ FAIL{Colors.END} - Status: {r.status_code}")
            print(f"  Response: {r.text[:200]}")
            FAIL += 1
            return None
        
        # Run checks
        all_passed = True
        if checks:
            for check_name, check_fn in checks.items():
                result = check_fn(data)
                if result:
                    print(f"  {Colors.GREEN}✓ {check_name}{Colors.END}: {result}")
                else:
                    print(f"  {Colors.RED}✗ {check_name}{Colors.END}")
                    all_passed = False
        
        if all_passed:
            print(f"  {Colors.GREEN}✓ PASSED{Colors.END}")
            PASS += 1
        else:
            FAIL += 1
        
        return data
        
    except Exception as e:
        print(f"  {Colors.RED}✗ ERROR{Colors.END}: {str(e)}")
        FAIL += 1
        return None

def main():
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*70}")
    print(f"  ATHAR ISLAMIC QA - COMPREHENSIVE ENDPOINT TEST")
    print(f"{'='*70}{Colors.END}")
    
    # 1. Health
    test("1. GET /health", f"{BASE}/health",
        checks={
            "status_ok": lambda d: d.get("status") == "ok",
            "version": lambda d: d.get("version", "N/A"),
            "api_healthy": lambda d: d.get("services", {}).get("api") == "healthy"
        })
    
    # 2. Root
    test("2. GET /", f"{BASE}/",
        checks={
            "name": lambda d: d.get("name") == "Athar",
            "version": lambda d: d.get("version", "N/A"),
            "has_query_endpoint": lambda d: "/api/v1/query" in d.get("query_endpoint", ""),
        })
    
    # 3. Quran Surahs
    test("3. GET /api/v1/quran/surahs", f"{BASE}/api/v1/quran/surahs",
        checks={
            "count_114": lambda d: f"{len(d)} surahs" if len(d) == 114 else f"Expected 114, got {len(d)}",
            "first_surah": lambda d: d[0]["name_en"] if d else None,
            "last_surah": lambda d: d[-1]["name_en"] if d else None,
        })
    
    # 4. Surah 1
    test("4. GET /api/v1/quran/surahs/1", f"{BASE}/api/v1/quran/surahs/1",
        checks={
            "number": lambda d: f"Surah {d.get('number')}" if d.get("number") == 1 else "Wrong number",
            "name": lambda d: d.get("name_en"),
            "ayah_count": lambda d: f"{d.get('verse_count')} ayahs",
            "has_ayahs": lambda d: f"{len(d.get('ayahs', []))} loaded" if d.get("ayahs") else "No ayahs"
        })
    
    # 5. Ayah 2:255
    test("5. GET /api/v1/quran/ayah/2:255", f"{BASE}/api/v1/quran/ayah/2:255",
        checks={
            "surah": lambda d: f"{d.get('surah_name_en')} 2:255" if d.get("surah_number") == 2 else "Wrong surah",
            "has_text": lambda d: f"{len(d.get('text_uthmani', ''))} chars" if d.get("text_uthmani") else "No text",
            "has_translation": lambda d: f"{len(d.get('translations', []))} translations" if d.get("translations") else "No translations"
        })
    
    # 6. Quran Search
    test("6. POST /api/v1/quran/search", f"{BASE}/api/v1/quran/search",
        method="post", data={"query": "رحمة", "limit": 3},
        checks={
            "found_verses": lambda d: f"{d.get('count', 0)} verses",
            "has_results": lambda d: f"First: {d['verses'][0]['surah_name_en']}:{d['verses'][0]['ayah_number']}" if d.get("verses") else "No results"
        })
    
    # 7. Quran Validate
    test("7. POST /api/v1/quran/validate", f"{BASE}/api/v1/quran/validate",
        method="post", data={"text": "بسم الله الرحمن الرحيم"},
        checks={
            "is_quran": lambda d: "YES" if d.get("is_quran") else "NO (expected due to diacritics)",
            "confidence": lambda d: d.get("confidence", 0)
        })
    
    # 8. Quran Analytics
    test("8. POST /api/v1/quran/analytics", f"{BASE}/api/v1/quran/analytics",
        method="post", data={"query": "How many verses are in Al-Baqarah?"},
        checks={
            "has_sql": lambda d: d.get("sql", "No SQL")[:50],
            "has_result": lambda d: str(d.get("result", "N/A"))[:50],
            "has_answer": lambda d: d.get("formatted_answer", "No answer")[:80]
        })
    
    # 9. Tafsir
    test("9. GET /api/v1/quran/tafsir/1:1", f"{BASE}/api/v1/quran/tafsir/1:1",
        checks={
            "has_ayah": lambda d: f"Surah {d['ayah']['surah_name_en']} 1:1" if d.get("ayah") else "No ayah",
            "tafsirs_count": lambda d: f"{len(d.get('tafsirs', []))} tafsirs (expected: 0 - not seeded)"
        })
    
    # 10. Zakat
    test("10. POST /api/v1/tools/zakat", f"{BASE}/api/v1/tools/zakat",
        method="post", data={"assets": {"cash": 50000, "gold_grams": 100}, "debts": 5000},
        checks={
            "is_zakatable": lambda d: f"YES" if d.get("is_zakatable") else "NO",
            "zakat_amount": lambda d: f"{d.get('zakat_amount', 0):.2f}",
            "nisab_gold": lambda d: f"Gold: {d.get('nisab', {}).get('gold', 0):.2f}",
            "nisab_silver": lambda d: f"Silver: {d.get('nisab', {}).get('silver', 0):.2f}"
        })
    
    # 11. Inheritance
    test("11. POST /api/v1/tools/inheritance", f"{BASE}/api/v1/tools/inheritance",
        method="post", data={"estate_value": 100000, "heirs": {"husband": True, "father": True, "mother": True, "sons": 1, "daughters": 1}},
        checks={
            "distribution_count": lambda d: f"{len(d.get('distribution', []))} heirs",
            "total_distributed": lambda d: f"{d.get('total_distributed', 0):.2f}",
            "has_amounts": lambda d: "YES - amounts calculated" if any(h.get("amount", 0) > 0 for h in d.get("distribution", [])) else "NO - amounts are zero"
        })
    
    # 12. Prayer Times
    test("12. POST /api/v1/tools/prayer-times", f"{BASE}/api/v1/tools/prayer-times",
        method="post", data={"lat": 25.2854, "lng": 51.5310, "method": "egyptian"},
        checks={
            "has_times": lambda d: f"Fajr: {d['times'].get('fajr', 'N/A')}, Dhuhr: {d['times'].get('dhuhr', 'N/A')}" if d.get("times") else "No times",
            "qibla": lambda d: f"{d.get('qibla_direction', 0):.1f}°" if d.get("qibla_direction") else "No qibla"
        })
    
    # 13. Hijri
    test("13. POST /api/v1/tools/hijri", f"{BASE}/api/v1/tools/hijri",
        method="post", data={"gregorian_date": "2026-04-05"},
        checks={
            "hijri_date": lambda d: f"{d['hijri_date'].get('day')}/{d['hijri_date'].get('month')}/{d['hijri_date'].get('year')}" if d.get("hijri_date") else "No date",
            "is_ramadan": lambda d: "YES" if d.get("is_ramadan") else "NO"
        })
    
    # 14. Duas
    test("14. POST /api/v1/tools/duas", f"{BASE}/api/v1/tools/duas",
        method="post", data={"occasion": "morning", "limit": 3},
        checks={
            "count": lambda d: f"{d.get('count', 0)} duas",
            "first_category": lambda d: d['duas'][0].get('category', 'N/A') if d.get("duas") else "No duas",
            "has_arabic": lambda d: "YES" if d.get("duas", [{}])[0].get("arabic_text") else "NO"
        })
    
    # 15. Query Greeting
    test("15. POST /api/v1/query (Greeting)", f"{BASE}/api/v1/query",
        method="post", data={"query": "السلام عليكم", "language": "ar"},
        checks={
            "intent": lambda d: d.get("intent"),
            "agent": lambda d: d.get("metadata", {}).get("agent", "N/A"),
            "has_answer": lambda d: f"{d.get('answer', '')[:80]}..." if d.get("answer") else "No answer"
        })
    
    # 16. Query Fiqh
    test("16. POST /api/v1/query (Fiqh)", f"{BASE}/api/v1/query",
        method="post", data={"query": "ما حكم صلاة الجمعة؟", "language": "ar"},
        checks={
            "intent": lambda d: d.get("intent"),
            "agent": lambda d: d.get("metadata", {}).get("agent", "N/A"),
            "has_retrieval": lambda d: f"{d.get('metadata', {}).get('retrieved_count', 0)} passages" if d.get("metadata", {}).get("retrieved_count") else "No retrieval",
            "confidence": lambda d: f"{d.get('metadata', {}).get('confidence', d.get('metadata', {}).get('scores', [0])[0] if d.get('metadata', {}).get('scores') else 0):.2f}",
            "has_answer": lambda d: f"{d.get('answer', '')[:100]}..." if d.get("answer") else "No answer"
        })
    
    # 17. RAG Fiqh
    test("17. POST /api/v1/rag/fiqh", f"{BASE}/api/v1/rag/fiqh",
        method="post", data={"query": "صلاة الجمعة", "language": "ar"},
        checks={
            "retrieved": lambda d: f"{d.get('metadata', {}).get('retrieved_count', 0)} passages",
            "used": lambda d: f"{d.get('metadata', {}).get('used_count', 0)} used",
            "scores": lambda d: f"{d.get('metadata', {}).get('scores', [0])[:3]}" if d.get('metadata', {}).get('scores') else "No scores",
            "confidence": lambda d: f"{d.get('confidence', 0):.2f}",
            "has_answer": lambda d: f"{d.get('answer', '')[:100]}..." if d.get("answer") else "No answer"
        })
    
    # 18. RAG Stats
    test("18. GET /api/v1/rag/stats", f"{BASE}/api/v1/rag/stats",
        checks={
            "total_docs": lambda d: f"{d.get('total_documents', 0)} documents",
            "fiqh_count": lambda d: f"fiqh: {d.get('collections', {}).get('fiqh_passages', {}).get('vectors_count', 0)}",
            "hadith_count": lambda d: f"hadith: {d.get('collections', {}).get('hadith_passages', {}).get('vectors_count', 0)}",
            "model": lambda d: d.get('embedding_model', 'N/A')
        })
    
    # Summary
    total = PASS + FAIL
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*70}")
    print(f"  RESULTS: {Colors.GREEN}{PASS}/{total} PASSED{Colors.END} | {Colors.RED if FAIL > 0 else Colors.END}{FAIL} FAILED")
    print(f"{'='*70}{Colors.END}\n")

if __name__ == "__main__":
    main()
