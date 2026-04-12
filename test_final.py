#!/usr/bin/env python3
"""Final comprehensive test of all fixed issues."""
import json
import urllib.request
import urllib.error

BASE = "http://localhost:8002"

def post_json(url, data):
    req = urllib.request.Request(
        url,
        data=json.dumps(data).encode('utf-8'),
        headers={'Content-Type': 'application/json'}
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode('utf-8'))

def get_json(url):
    with urllib.request.urlopen(url, timeout=10) as r:
        return json.loads(r.read().decode('utf-8'))

def test_all():
    passed = 0
    failed = 0
    
    print("="*70)
    print("ATHAR ISLAMIC QA SYSTEM - FINAL TEST SUITE")
    print("="*70)
    
    # Test 1: Health Check
    try:
        h = get_json(f"{BASE}/health")
        if h.get("status") == "ok":
            print("✅ PASS 1: Health check - system healthy")
            passed += 1
        else:
            print("❌ FAIL 1: Health check returned non-ok")
            failed += 1
    except Exception as e:
        print(f"❌ FAIL 1: Health check error: {e}")
        failed += 1
    
    # Test 2: Quran Ayah (FIXED)
    try:
        a = get_json(f"{BASE}/api/v1/quran/ayah/1:1")
        if a.get("text_uthmani") and a.get("translations"):
            print(f"✅ PASS 2: Quran ayah 1:1 - {a.get('surah_name_en', '')} (FIXED!)")
            passed += 1
        else:
            print("❌ FAIL 2: Quran ayah returned empty data")
            failed += 1
    except Exception as e:
        print(f"❌ FAIL 2: Quran ayah error: {e}")
        failed += 1
    
    # Test 3: Fiqh Query with RAG
    try:
        d = post_json(f"{BASE}/api/v1/query", {"query": "حكم الصيام في رمضان"})
        if d.get("intent") == "fiqh" and d.get("metadata", {}).get("retrieved_count", 0) > 0:
            count = d["metadata"]["retrieved_count"]
            print(f"✅ PASS 3: Fiqh RAG - {count} passages retrieved")
            passed += 1
        else:
            print("❌ FAIL 3: Fiqh RAG returned no passages")
            failed += 1
    except Exception as e:
        print(f"❌ FAIL 3: Fiqh query error: {e}")
        failed += 1
    
    # Test 4: Greeting Intent
    try:
        d = post_json(f"{BASE}/api/v1/query", {"query": "مرحبا كيف حالك"})
        if d.get("intent") == "greeting":
            print(f"✅ PASS 4: Greeting intent - {d.get('answer', '')[:30]}")
            passed += 1
        else:
            print(f"❌ FAIL 4: Expected greeting, got {d.get('intent')}")
            failed += 1
    except Exception as e:
        print(f"❌ FAIL 4: Greeting error: {e}")
        failed += 1
    
    # Test 5: Zakat Calculator
    try:
        d = post_json(f"{BASE}/api/v1/tools/zakat", {"assets": {"cash": 10000}})
        if d.get("zakat_amount") == 250.0:
            print(f"✅ PASS 5: Zakat calc - $10,000 → ${d.get('zakat_amount')}")
            passed += 1
        else:
            print(f"❌ FAIL 5: Zakat wrong: {d.get('zakat_amount')}")
            failed += 1
    except Exception as e:
        print(f"❌ FAIL 5: Zakat error: {e}")
        failed += 1
    
    # Test 6: Hijri Date
    try:
        d = post_json(f"{BASE}/api/v1/tools/hijri", {"date": "2026-04-12"})
        hijri = d.get("hijri_date", {})
        if hijri.get("year") == 1447:
            print(f"✅ PASS 6: Hijri date - {hijri.get('formatted_en', 'N/A')}")
            passed += 1
        else:
            print(f"❌ FAIL 6: Hijri wrong: {hijri}")
            failed += 1
    except Exception as e:
        print(f"❌ FAIL 6: Hijri error: {e}")
        failed += 1
    
    # Test 7: Surah List
    try:
        s = get_json(f"{BASE}/api/v1/quran/surahs")
        if isinstance(s, list) and len(s) > 0:
            print(f"✅ PASS 7: Surah list - {len(s)} surahs available")
            passed += 1
        else:
            print(f"❌ FAIL 7: Surah list empty or invalid")
            failed += 1
    except Exception as e:
        print(f"❌ FAIL 7: Surah list error: {e}")
        failed += 1
    
    # Test 8: Dua Retrieval (FIXED)
    try:
        d = post_json(f"{BASE}/api/v1/tools/duas", {"category": "morning"})
        duas = d.get("duas", [])
        if len(duas) > 0:
            print(f"✅ PASS 8: Dua retrieval - {len(duas)} morning duas found (FIXED!)")
            passed += 1
        else:
            print(f"❌ FAIL 8: No morning duas returned")
            failed += 1
    except Exception as e:
        print(f"❌ FAIL 8: Dua retrieval error: {e}")
        failed += 1
    
    print()
    print("="*70)
    print(f"RESULTS: {passed} passed, {failed} failed out of {passed+failed} tests")
    if failed == 0:
        print("🎉 ALL TESTS PASSED!")
    else:
        print(f"⚠️  {failed} test(s) need attention")
    print("="*70)
    
    return failed == 0

if __name__ == "__main__":
    success = test_all()
    exit(0 if success else 1)
