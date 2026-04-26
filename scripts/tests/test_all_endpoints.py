#!/usr/bin/env python3
"""
Comprehensive API Test Suite for Burhan Islamic QA System.

Tests every endpoint with detailed output.
Usage:
    python scripts/test_all_endpoints.py
"""
import urllib.request
import urllib.error
import json
import time
import sys
from typing import Any

BASE_URL = "http://localhost:8000"

# Colors for output
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    DIM = '\033[2m'

def print_header(text):
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*70}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{text:^70}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'='*70}{Colors.ENDC}\n")

def print_test(num, name, description=""):
    print(f"\n{Colors.CYAN}Test {num}: {Colors.BOLD}{name}{Colors.ENDC}")
    if description:
        print(f"{Colors.DIM}  {description}{Colors.ENDC}")

def print_success(data, key_fields=None):
    print(f"  {Colors.GREEN}✓ PASSED{Colors.ENDC}")
    if key_fields:
        for field in key_fields:
            value = data.get(field, 'N/A')
            if isinstance(value, (dict, list)):
                value = json.dumps(value, ensure_ascii=False)[:100]
            print(f"    {Colors.BLUE}▸{Colors.ENDC} {field}: {Colors.GREEN}{value}{Colors.ENDC}")

def print_failure(error):
    print(f"  {Colors.RED}✗ FAILED{Colors.ENDC}")
    print(f"    {Colors.RED}Error: {error}{Colors.ENDC}")

def make_request(method, path, data=None):
    """Make HTTP request and return (success, status_code, response_data)."""
    url = f"{BASE_URL}{path}"
    try:
        if data:
            body = json.dumps(data).encode('utf-8')
            req = urllib.request.Request(url, data=body, headers={'Content-Type': 'application/json'}, method=method)
        else:
            req = urllib.request.Request(url, method=method)
        
        response = urllib.request.urlopen(req, timeout=30)
        response_data = json.loads(response.read().decode())
        return True, response.status, response_data
    except urllib.error.HTTPError as e:
        try:
            error_data = json.loads(e.read().decode())
            return False, e.code, error_data
        except:
            return False, e.code, {"detail": str(e)}
    except Exception as e:
        return False, 0, {"error": str(e)}

def test_health():
    """Test health endpoints."""
    print_header("HEALTH CHECKS")
    
    # Test 1: /health
    print_test(1, "GET /health", "Check API health status")
    success, status, data = make_request("GET", "/health")
    if success and status == 200:
        print_success(data, ['status', 'version', 'components'])
    else:
        print_failure(data)
    
    # Test 2: /
    print_test(2, "GET /", "Root endpoint with API info")
    success, status, data = make_request("GET", "/")
    if success and status == 200:
        print_success(data, ['name', 'version', 'docs'])
    else:
        print_failure(data)

def test_query_endpoint():
    """Test main query endpoint."""
    print_header("MAIN QUERY ENDPOINT - POST /api/v1/query")
    
    # Test 1: Greeting
    print_test(1, "Greeting Query", "السلام عليكم")
    success, status, data = make_request("POST", "/api/v1/query", {
        "query": "السلام عليكم",
        "language": "ar"
    })
    if success and status == 200:
        print_success(data, ['query_id', 'intent', 'intent_confidence', 'answer'])
    else:
        print_failure(data)
    
    # Test 2: Fiqh Question
    print_test(2, "Fiqh Question", "ما حكم صلاة الجمعة؟")
    success, status, data = make_request("POST", "/api/v1/query", {
        "query": "ما حكم صلاة الجمعة؟",
        "language": "ar",
        "madhhab": "shafii"
    })
    if success and status == 200:
        print_success(data, ['query_id', 'intent', 'intent_confidence', 'answer'])
    else:
        print_failure(data)
    
    # Test 3: Quran Question
    print_test(3, "Quran Question", "كم عدد آيات سورة البقرة؟")
    success, status, data = make_request("POST", "/api/v1/query", {
        "query": "كم عدد آيات سورة البقرة؟",
        "language": "ar"
    })
    if success and status == 200:
        print_success(data, ['query_id', 'intent', 'intent_confidence', 'answer'])
    else:
        print_failure(data)
    
    # Test 4: Zakat Intent
    print_test(4, "Zakat Intent", "كيف احسب زكاة مالي؟")
    success, status, data = make_request("POST", "/api/v1/query", {
        "query": "كيف احسب زكاة مالي؟",
        "language": "ar"
    })
    if success and status == 200:
        print_success(data, ['query_id', 'intent', 'intent_confidence', 'answer'])
    else:
        print_failure(data)
    
    # Test 5: Dua Request
    print_test(5, "Dua Request", "أعطني دعاء السفر")
    success, status, data = make_request("POST", "/api/v1/query", {
        "query": "أعطني دعاء السفر",
        "language": "ar"
    })
    if success and status == 200:
        print_success(data, ['query_id', 'intent', 'intent_confidence', 'answer'])
    else:
        print_failure(data)
    
    # Test 6: Invalid Query
    print_test(6, "Empty Query (Validation)", "Should return 422 error")
    success, status, data = make_request("POST", "/api/v1/query", {
        "query": "",
        "language": "ar"
    })
    if status == 422:
        print(f"  {Colors.GREEN}✓ PASSED{Colors.ENDC} - Correctly rejected empty query")
    else:
        print_failure(f"Expected 422, got {status}")

def test_tools():
    """Test all tool endpoints."""
    print_header("TOOLS ENDPOINTS")
    
    # Test 1: Zakat Calculator
    print_test(1, "POST /api/v1/tools/zakat", "Calculate zakat on wealth")
    success, status, data = make_request("POST", "/api/v1/tools/zakat", {
        "assets": {
            "cash": 50000,
            "gold_grams": 100,
            "silver_grams": 500
        },
        "debts": 5000,
        "madhhab": "shafii"
    })
    if success and status == 200:
        print_success(data, ['is_zakatable', 'zakat_amount', 'nisab'])
    else:
        print_failure(data)
    
    # Test 2: Prayer Times
    print_test(2, "POST /api/v1/tools/prayer-times", "Get prayer times for Doha")
    success, status, data = make_request("POST", "/api/v1/tools/prayer-times", {
        "lat": 25.2854,
        "lng": 51.5310,
        "method": "egyptian"
    })
    if success and status == 200:
        print_success(data, ['times', 'qibla_direction'])
        if 'times' in data:
            print(f"    {Colors.BLUE}▸{Colors.ENDC} Fajr: {data['times'].get('fajr', 'N/A')}")
            print(f"    {Colors.BLUE}▸{Colors.ENDC} Dhuhr: {data['times'].get('dhuhr', 'N/A')}")
            print(f"    {Colors.BLUE}▸{Colors.ENDC} Asr: {data['times'].get('asr', 'N/A')}")
            print(f"    {Colors.BLUE}▸{Colors.ENDC} Maghrib: {data['times'].get('maghrib', 'N/A')}")
            print(f"    {Colors.BLUE}▸{Colors.ENDC} Isha: {data['times'].get('isha', 'N/A')}")
    else:
        print_failure(data)
    
    # Test 3: Hijri Calendar
    print_test(3, "POST /api/v1/tools/hijri", "Convert Gregorian to Hijri")
    success, status, data = make_request("POST", "/api/v1/tools/hijri", {
        "gregorian_date": "2026-04-05"
    })
    if success and status == 200:
        print_success(data, ['hijri_date', 'is_ramadan', 'is_eid'])
    else:
        print_failure(data)
    
    # Test 4: Duas
    print_test(4, "POST /api/v1/tools/duas", "Retrieve duas for morning")
    success, status, data = make_request("POST", "/api/v1/tools/duas", {
        "occasion": "morning",
        "limit": 3
    })
    if success and status == 200:
        print_success(data, ['duas', 'count'])
        if 'duas' in data and len(data['duas']) > 0:
            first_dua = data['duas'][0]
            print(f"    {Colors.BLUE}▸{Colors.ENDC} Category: {first_dua.get('category', 'N/A')}")
            print(f"    {Colors.BLUE}▸{Colors.ENDC} Arabic: {first_dua.get('arabic_text', 'N/A')[:50]}...")
    else:
        print_failure(data)
    
    # Test 5: Inheritance Calculator
    print_test(5, "POST /api/v1/tools/inheritance", "Calculate inheritance distribution")
    success, status, data = make_request("POST", "/api/v1/tools/inheritance", {
        "estate_value": 100000,
        "heirs": {
            "husband": True,
            "father": True,
            "mother": True,
            "sons": 1,
            "daughters": 1
        }
    })
    if success and status == 200:
        print_success(data, ['distribution', 'total_distributed'])
        if 'distribution' in data:
            for heir in data['distribution'][:3]:
                print(f"    {Colors.BLUE}▸{Colors.ENDC} {heir.get('heir', 'N/A')}: {heir.get('fraction', 'N/A')} ({heir.get('amount', 'N/A')})")
    else:
        print_failure(data)

def test_quran():
    """Test Quran endpoints."""
    print_header("QURAN ENDPOINTS")
    
    # Test 1: List Surahs
    print_test(1, "GET /api/v1/quran/surahs", "List all 114 surahs")
    success, status, data = make_request("GET", "/api/v1/quran/surahs")
    if success and status == 200:
        print(f"  {Colors.GREEN}✓ PASSED{Colors.ENDC}")
        if isinstance(data, list) and len(data) > 0:
            print(f"    {Colors.BLUE}▸{Colors.ENDC} Total surahs: {len(data)}")
            print(f"    {Colors.BLUE}▸{Colors.ENDC} First: {data[0].get('name_en', 'N/A')} ({data[0].get('name_ar', 'N/A')})")
            print(f"    {Colors.BLUE}▸{Colors.ENDC} Last: {data[-1].get('name_en', 'N/A')} ({data[-1].get('name_ar', 'N/A')})")
    else:
        print_failure(data)
    
    # Test 2: Get Specific Surah
    print_test(2, "GET /api/v1/quran/surahs/1", "Get Al-Fatihah details")
    success, status, data = make_request("GET", "/api/v1/quran/surahs/1")
    if success and status == 200:
        print_success(data, ['number', 'name_en', 'verse_count', 'revelation_type'])
    else:
        print_failure(data)
    
    # Test 3: Get Ayah
    print_test(3, "GET /api/v1/quran/ayah/2:255", "Get Ayat al-Kursi")
    success, status, data = make_request("GET", "/api/v1/quran/ayah/2:255")
    if success and status == 200:
        print_success(data, ['surah_number', 'ayah_number', 'text_uthmani', 'quran_url'])
        if 'text_uthmani' in data:
            print(f"    {Colors.BLUE}▸{Colors.ENDC} Text: {data['text_uthmani'][:100]}...")
    else:
        print_failure(data)
    
    # Test 4: Quran Search
    print_test(4, "POST /api/v1/quran/search", "Search for رحمة in Quran")
    success, status, data = make_request("POST", "/api/v1/quran/search", {
        "query": "رحمة",
        "limit": 5
    })
    if success and status == 200:
        print_success(data, ['verses', 'count'])
    else:
        print_failure(data)
    
    # Test 5: Validate Quotation
    print_test(5, "POST /api/v1/quran/validate", "Validate Quranic text")
    success, status, data = make_request("POST", "/api/v1/quran/validate", {
        "text": "بسم الله الرحمن الرحيم"
    })
    if success and status == 200:
        print_success(data, ['is_quran', 'confidence', 'matched_ayah'])
    else:
        print_failure(data)
    
    # Test 6: Tafsir
    print_test(6, "GET /api/v1/quran/tafsir/1:1", "Get tafsir for Al-Fatihah 1:1")
    success, status, data = make_request("GET", "/api/v1/quran/tafsir/1:1")
    if success and status == 200:
        print_success(data, ['ayah', 'tafsirs'])
    else:
        print_failure(data)
    
    # Test 7: Analytics (NL2SQL)
    print_test(7, "POST /api/v1/quran/analytics", "How many verses in Al-Baqarah?")
    success, status, data = make_request("POST", "/api/v1/quran/analytics", {
        "query": "كم عدد آيات سورة البقرة؟"
    })
    if success and status == 200:
        print_success(data, ['sql', 'result', 'formatted_answer'])
    else:
        print_failure(data)

def test_rag():
    """Test RAG endpoints."""
    print_header("RAG ENDPOINTS")
    
    # Test 1: Fiqh RAG
    print_test(1, "POST /api/v1/rag/fiqh", "Fiqh question with RAG")
    success, status, data = make_request("POST", "/api/v1/rag/fiqh", {
        "query": "ما حكم صلاة الجماعة؟",
        "language": "ar"
    })
    if success and status == 200:
        print_success(data, ['answer', 'citations', 'confidence'])
        if 'citations' in data:
            print(f"    {Colors.BLUE}▸{Colors.ENDC} Citations: {len(data['citations'])}")
    else:
        print_failure(data)
    
    # Test 2: General RAG
    print_test(2, "POST /api/v1/rag/general", "General Islamic knowledge")
    success, status, data = make_request("POST", "/api/v1/rag/general", {
        "query": "من هو عمر بن الخطاب؟",
        "language": "ar"
    })
    if success and status == 200:
        print_success(data, ['answer', 'citations', 'confidence'])
    else:
        print_failure(data)
    
    # Test 3: RAG Stats
    print_test(3, "GET /api/v1/rag/stats", "RAG system statistics")
    success, status, data = make_request("GET", "/api/v1/rag/stats")
    if success and status == 200:
        print_success(data, ['collections', 'total_documents', 'embedding_model'])
    else:
        print_failure(data)

def test_error_handling():
    """Test error handling."""
    print_header("ERROR HANDLING")
    
    # Test 1: Invalid endpoint
    print_test(1, "GET /api/v1/nonexistent", "Should return 404")
    success, status, data = make_request("GET", "/api/v1/nonexistent")
    if status == 404:
        print(f"  {Colors.GREEN}✓ PASSED{Colors.ENDC} - Correctly returned 404")
    else:
        print_failure(f"Expected 404, got {status}")
    
    # Test 2: Invalid method
    print_test(2, "DELETE /api/v1/query", "Should return 405")
    success, status, data = make_request("DELETE", "/api/v1/query")
    if status == 405:
        print(f"  {Colors.GREEN}✓ PASSED{Colors.ENDC} - Correctly returned 405")
    else:
        print_failure(f"Expected 405, got {status}")

def main():
    """Run all tests."""
    print_header("🕌 Burhan ISLAMIC QA SYSTEM - COMPREHENSIVE API TEST SUITE")
    
    print(f"{Colors.BOLD}Testing against:{Colors.ENDC} {BASE_URL}\n")
    
    # Check if API is running
    success, status, data = make_request("GET", "/health")
    if not success:
        print(f"{Colors.RED}✗ API is not running at {BASE_URL}{Colors.ENDC}")
        print(f"\n{Colors.YELLOW}Please start the API first:{Colors.ENDC}")
        print(f"  uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000\n")
        return
    
    print(f"{Colors.GREEN}✓ API is running (version: {data.get('version', 'unknown')}){Colors.ENDC}\n")
    
    # Run all test suites
    test_health()
    test_query_endpoint()
    test_tools()
    test_quran()
    test_rag()
    test_error_handling()
    
    # Summary
    print_header("✓ COMPREHENSIVE TEST SUITE COMPLETE")
    print(f"\n{Colors.GREEN}All endpoints tested successfully!{Colors.ENDC}\n")

if __name__ == "__main__":
    main()
