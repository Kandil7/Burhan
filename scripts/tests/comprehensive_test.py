#!/usr/bin/env python3
"""
Comprehensive Endpoint Testing & Validation Suite for Athar Islamic QA System.

Tests every endpoint with thorough response validation:
1. Health checks (/health, /ready, /)
2. Tool endpoints (zakat, prayer-times, hijri, duas, inheritance)
3. Quran endpoints (surahs, ayah, search, validate, tafsir, analytics)
4. RAG endpoints (fiqh, general, stats)
5. Main query endpoint (greeting, fiqh, quran, zakat, dua)

Usage:
    python scripts/tests/comprehensive_test.py
    python scripts/tests/comprehensive_test.py --port 8002
    python scripts/tests/comprehensive_test.py --verbose

Author: Athar Engineering Team
"""

import argparse
import json
import sys
import time
import urllib.error
import urllib.request
from typing import Any, Optional

from scripts.utils import setup_script_logger, format_duration

logger = setup_script_logger("comprehensive-test")


# ── Configuration ────────────────────────────────────────────────────────


# Terminal colors
class Colors:
    HEADER = "\033[95m"
    BLUE = "\033[94m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    CYAN = "\033[96m"
    WHITE = "\033[97m"
    ENDC = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"


# ── HTTP Helper ──────────────────────────────────────────────────────────


def make_request(
    method: str, path: str, data: Optional[dict] = None, timeout: int = 30
) -> tuple[bool, int, dict]:
    """Make HTTP request and return (success, status_code, response_data)."""
    base_url = make_request.base_url  # type: ignore[attr-defined]
    url = f"{base_url}{path}"
    try:
        if data:
            body = json.dumps(data).encode("utf-8")
            req = urllib.request.Request(
                url, data=body, headers={"Content-Type": "application/json"}, method=method
            )
        else:
            req = urllib.request.Request(url, method=method)

        response = urllib.request.urlopen(req, timeout=timeout)
        response_data = json.loads(response.read().decode())
        return True, response.status, response_data

    except urllib.error.HTTPError as e:
        try:
            error_data = json.loads(e.read().decode())
        except Exception:
            error_data = {"detail": str(e)}
        return False, e.code, error_data

    except Exception as e:
        return False, 0, {"error": str(e)}


# ── Test Helpers ─────────────────────────────────────────────────────────


def print_header(text: str) -> None:
    """Print a section header."""
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'=' * 80}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{text:^80}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'=' * 80}{Colors.ENDC}\n")


def print_test(num: int, name: str, description: str = "") -> None:
    """Print test header."""
    print(f"\n{Colors.CYAN}Test {num}: {Colors.BOLD}{name}{Colors.ENDC}")
    if description:
        print(f"{Colors.DIM}  {description}{Colors.ENDC}")


def print_success(data: dict, key_fields: Optional[list[str]] = None) -> None:
    """Print successful test result."""
    print(f"  {Colors.GREEN}✓ PASSED{Colors.ENDC}")
    if key_fields:
        for field in key_fields:
            value = data.get(field, "N/A")
            if isinstance(value, (dict, list)):
                value = json.dumps(value, ensure_ascii=False, default=str)[:100]
            print(f"    {Colors.BLUE}▸{Colors.ENDC} {field}: {Colors.GREEN}{value}{Colors.ENDC}")


def print_warning(message: str) -> None:
    """Print warning message."""
    print(f"  {Colors.YELLOW}⚠ WARNING: {message}{Colors.ENDC}")


def print_failure(error: str) -> None:
    """Print failure message."""
    print(f"  {Colors.RED}✗ FAILED{Colors.ENDC}")
    print(f"    {Colors.RED}Error: {error}{Colors.ENDC}")


def validate_field(
    data: dict, field_name: str, expected_type: Any = None, required: bool = True
) -> bool:
    """Validate a field exists and has the correct type."""
    if required and field_name not in data:
        print_warning(f"Missing required field: {field_name}")
        return False

    value = data.get(field_name)
    if expected_type and value is not None:
        if not isinstance(value, expected_type):
            print_warning(
                f"Field {field_name} has wrong type: {type(value).__name__} "
                f"(expected {expected_type.__name__})"
            )
            return False
    return True


# ── Test Suites ──────────────────────────────────────────────────────────


def test_health_endpoints() -> bool:
    """Test health endpoints."""
    print_header("1. HEALTH CHECKS")

    tests_passed = 0
    tests_total = 3

    # Test 1: /health
    print_test(1, "GET /health", "Check API health status")
    success, status, data = make_request("GET", "/health")
    if success and status == 200:
        if validate_field(data, "status", str) and validate_field(data, "version", str):
            print_success(data, ["status", "version"])
            tests_passed += 1
        else:
            print_warning("Missing required fields in health response")
    else:
        print_failure(f"Status: {status}, Error: {data}")

    # Test 2: /ready
    print_test(2, "GET /ready", "Check readiness probe")
    success, status, data = make_request("GET", "/ready")
    if success and status == 200:
        print_success(data, ["status"])
        tests_passed += 1
    else:
        print_failure(f"Status: {status}, Error: {data}")

    # Test 3: /
    print_test(3, "GET /", "Root endpoint with API info")
    success, status, data = make_request("GET", "/")
    if success and status == 200:
        if validate_field(data, "name", str) and validate_field(data, "version", str):
            print_success(data, ["name", "version"])
            tests_passed += 1
        else:
            print_warning("Missing required fields in root response")
    else:
        print_failure(f"Status: {status}, Error: {data}")

    print(f"\n{Colors.BLUE}Health Tests: {tests_passed}/{tests_total} passed{Colors.ENDC}")
    return tests_passed == tests_total


def test_tool_endpoints() -> bool:
    """Test all tool endpoints."""
    print_header("2. TOOL ENDPOINTS")

    tests_passed = 0
    tests_total = 5

    # Test 1: Zakat Calculator
    print_test(1, "POST /api/v1/tools/zakat", "Calculate zakat on wealth")
    success, status, data = make_request(
        "POST", "/api/v1/tools/zakat",
        {"assets": {"cash": 50000, "gold_grams": 100, "silver_grams": 500}, "debts": 5000, "madhhab": "shafii"},
    )
    if success and status == 200:
        if validate_field(data, "is_zakatable", bool) and validate_field(data, "zakat_amount", (int, float)):
            print_success(data, ["is_zakatable", "zakat_amount", "nisab"])
            tests_passed += 1
        else:
            print_warning("Missing zakat calculation fields")
    else:
        print_failure(f"Status: {status}, Error: {data}")

    # Test 2: Prayer Times
    print_test(2, "POST /api/v1/tools/prayer-times", "Get prayer times for Doha")
    success, status, data = make_request(
        "POST", "/api/v1/tools/prayer-times",
        {"lat": 25.2854, "lng": 51.5310, "method": "egyptian"}, timeout=10,
    )
    if success and status == 200:
        if validate_field(data, "times", dict):
            print_success(data, ["times"])
            if "times" in data:
                times = data["times"]
                print(f"    {Colors.BLUE}▸{Colors.ENDC} Fajr: {times.get('fajr', 'N/A')}")
                print(f"    {Colors.BLUE}▸{Colors.ENDC} Dhuhr: {times.get('dhuhr', 'N/A')}")
            tests_passed += 1
        else:
            print_warning("Missing prayer times")
    else:
        print_failure(f"Status: {status}, Error: {data}")

    # Test 3: Hijri Calendar
    print_test(3, "POST /api/v1/tools/hijri", "Convert Gregorian to Hijri")
    success, status, data = make_request(
        "POST", "/api/v1/tools/hijri", {"gregorian_date": "2026-04-05"}
    )
    if success and status == 200:
        if validate_field(data, "hijri_date", dict):
            print_success(data, ["hijri_date", "is_ramadan", "is_eid"])
            tests_passed += 1
        else:
            print_warning("Missing Hijri date fields")
    else:
        print_failure(f"Status: {status}, Error: {data}")

    # Test 4: Duas
    print_test(4, "POST /api/v1/tools/duas", "Retrieve duas for morning")
    success, status, data = make_request(
        "POST", "/api/v1/tools/duas", {"occasion": "morning", "limit": 3}
    )
    if success and status == 200:
        if validate_field(data, "duas", list) and validate_field(data, "count", int):
            print_success(data, ["duas", "count"])
            tests_passed += 1
        else:
            print_warning("Missing duas fields")
    else:
        print_failure(f"Status: {status}, Error: {data}")

    # Test 5: Inheritance Calculator
    print_test(5, "POST /api/v1/tools/inheritance", "Calculate inheritance distribution")
    success, status, data = make_request(
        "POST", "/api/v1/tools/inheritance",
        {"estate_value": 100000, "heirs": {"husband": True, "father": True, "mother": True, "sons": 1, "daughters": 1}},
    )
    if success and status == 200:
        if validate_field(data, "distribution", list):
            print_success(data, ["distribution", "total_distributed"])
            tests_passed += 1
        else:
            print_warning("Missing distribution data")
    else:
        print_failure(f"Status: {status}, Error: {data}")

    print(f"\n{Colors.BLUE}Tool Tests: {tests_passed}/{tests_total} passed{Colors.ENDC}")
    return tests_passed == tests_total


def test_quran_endpoints() -> bool:
    """Test all Quran endpoints."""
    print_header("3. QURAN ENDPOINTS")

    tests_passed = 0
    tests_total = 7

    # Test 1: List Surahs
    print_test(1, "GET /api/v1/quran/surahs", "List all 114 surahs")
    success, status, data = make_request("GET", "/api/v1/quran/surahs")
    if success and status == 200:
        if isinstance(data, list) and len(data) == 114:
            print(f"  {Colors.GREEN}✓ PASSED{Colors.ENDC}")
            print(f"    {Colors.BLUE}▸{Colors.ENDC} Total surahs: {len(data)}")
            tests_passed += 1
        else:
            print_warning(f"Expected 114 surahs, got {len(data) if isinstance(data, list) else 'not a list'}")
    else:
        print_failure(f"Status: {status}, Error: {data}")

    # Test 2: Get Specific Surah
    print_test(2, "GET /api/v1/quran/surahs/1", "Get Al-Fatihah details")
    success, status, data = make_request("GET", "/api/v1/quran/surahs/1")
    if success and status == 200:
        if validate_field(data, "number", int) and validate_field(data, "ayahs", list):
            print_success(data, ["number", "name_en", "verse_count"])
            tests_passed += 1
        else:
            print_warning("Missing surah details")
    else:
        print_failure(f"Status: {status}, Error: {data}")

    # Test 3: Get Ayah
    print_test(3, "GET /api/v1/quran/ayah/2:255", "Get Ayat al-Kursi")
    success, status, data = make_request("GET", "/api/v1/quran/ayah/2:255")
    if success and status == 200:
        if validate_field(data, "surah_number", int) and validate_field(data, "text_uthmani", str):
            print_success(data, ["surah_number", "ayah_number", "text_uthmani"])
            tests_passed += 1
        else:
            print_warning("Missing ayah details")
    else:
        print_failure(f"Status: {status}, Error: {data}")

    # Test 4: Quran Search
    print_test(4, "POST /api/v1/quran/search", "Search for رحمة in Quran")
    success, status, data = make_request(
        "POST", "/api/v1/quran/search", {"query": "رحمة", "limit": 5}
    )
    if success and status == 200:
        if validate_field(data, "verses", list) and validate_field(data, "count", int):
            print_success(data, ["verses", "count"])
            tests_passed += 1
        else:
            print_warning("Missing search results")
    else:
        print_failure(f"Status: {status}, Error: {data}")

    # Test 5: Validate Quotation
    print_test(5, "POST /api/v1/quran/validate", "Validate Quranic text")
    success, status, data = make_request(
        "POST", "/api/v1/quran/validate", {"text": "بسم الله الرحمن الرحيم"}
    )
    if success and status == 200:
        if validate_field(data, "is_quran", bool):
            print_success(data, ["is_quran", "confidence"])
            tests_passed += 1
        else:
            print_warning("Missing validation result")
    else:
        print_failure(f"Status: {status}, Error: {data}")

    # Test 6: Tafsir
    print_test(6, "GET /api/v1/quran/tafsir/1:1", "Get tafsir for Al-Fatihah 1:1")
    success, status, data = make_request("GET", "/api/v1/quran/tafsir/1:1")
    if success and status == 200:
        if validate_field(data, "ayah", dict):
            print_success(data, ["ayah", "tafsirs"])
            tests_passed += 1
        else:
            print_warning("Missing tafsir data")
    else:
        print_failure(f"Status: {status}, Error: {data}")

    # Test 7: Analytics (NL2SQL)
    print_test(7, "POST /api/v1/quran/analytics", "How many verses in Al-Baqarah?")
    success, status, data = make_request(
        "POST", "/api/v1/quran/analytics",
        {"query": "How many verses are in Surah Al-Baqarah?"}, timeout=10,
    )
    if success and status == 200:
        if validate_field(data, "sql", str):
            print_success(data, ["sql", "result", "formatted_answer"])
            tests_passed += 1
        else:
            print_warning("Missing analytics result")
    else:
        print_failure(f"Status: {status}, Error: {data}")

    print(f"\n{Colors.BLUE}Quran Tests: {tests_passed}/{tests_total} passed{Colors.ENDC}")
    return tests_passed == tests_total


def test_rag_endpoints() -> bool:
    """Test RAG endpoints."""
    print_header("4. RAG ENDPOINTS")

    tests_passed = 0
    tests_total = 3

    # Test 1: Fiqh RAG
    print_test(1, "POST /api/v1/rag/fiqh", "Fiqh question with RAG")
    success, status, data = make_request(
        "POST", "/api/v1/rag/fiqh",
        {"query": "ما حكم صلاة الجماعة؟", "language": "ar"}, timeout=30,
    )
    if success and status == 200:
        if validate_field(data, "answer", str) and validate_field(data, "citations", list):
            print_success(data, ["answer", "citations", "confidence"])
            tests_passed += 1
        else:
            print_warning("Missing RAG response fields")
    else:
        print_failure(f"Status: {status}, Error: {data}")

    # Test 2: General RAG
    print_test(2, "POST /api/v1/rag/general", "General Islamic knowledge")
    success, status, data = make_request(
        "POST", "/api/v1/rag/general",
        {"query": "من هو عمر بن الخطاب؟", "language": "ar"}, timeout=15,
    )
    if success and status == 200:
        if validate_field(data, "answer", str):
            print_success(data, ["answer", "confidence"])
            tests_passed += 1
        else:
            print_warning("Missing general knowledge response")
    else:
        print_failure(f"Status: {status}, Error: {data}")

    # Test 3: RAG Stats
    print_test(3, "GET /api/v1/rag/stats", "RAG system statistics")
    success, status, data = make_request("GET", "/api/v1/rag/stats")
    if success and status == 200:
        if validate_field(data, "collections", dict) and validate_field(data, "total_documents", int):
            print_success(data, ["collections", "total_documents", "embedding_model"])
            tests_passed += 1
        else:
            print_warning("Missing RAG stats fields")
    else:
        print_failure(f"Status: {status}, Error: {data}")

    print(f"\n{Colors.BLUE}RAG Tests: {tests_passed}/{tests_total} passed{Colors.ENDC}")
    return tests_passed == tests_total


def test_query_endpoint() -> bool:
    """Test main query endpoint with different intents."""
    print_header("5. MAIN QUERY ENDPOINT")

    tests_passed = 0
    tests_total = 5

    # Test 1: Greeting
    print_test(1, "Greeting Query", "السلام عليكم")
    success, status, data = make_request(
        "POST", "/api/v1/query", {"query": "السلام عليكم", "language": "ar"}
    )
    if success and status == 200:
        if validate_field(data, "intent", str) and validate_field(data, "answer", str):
            print_success(data, ["query_id", "intent", "intent_confidence", "answer"])
            tests_passed += 1
        else:
            print_warning("Missing query response fields")
    else:
        print_failure(f"Status: {status}, Error: {data}")

    # Test 2: Fiqh Question
    print_test(2, "Fiqh Question", "ما حكم صلاة الجمعة؟")
    success, status, data = make_request(
        "POST", "/api/v1/query",
        {"query": "ما حكم صلاة الجمعة؟", "language": "ar", "madhhab": "shafii"}, timeout=15,
    )
    if success and status == 200:
        if validate_field(data, "intent", str) and validate_field(data, "answer", str):
            print_success(data, ["query_id", "intent", "intent_confidence"])
            tests_passed += 1
        else:
            print_warning("Missing fiqh query response")
    else:
        print_failure(f"Status: {status}, Error: {data}")

    # Test 3: Quran Question
    print_test(3, "Quran Question", "كم عدد آيات سورة البقرة؟")
    success, status, data = make_request(
        "POST", "/api/v1/query",
        {"query": "كم عدد آيات سورة البقرة؟", "language": "ar"}, timeout=15,
    )
    if success and status == 200:
        if validate_field(data, "intent", str):
            print_success(data, ["query_id", "intent", "intent_confidence"])
            tests_passed += 1
        else:
            print_warning("Missing quran query response")
    else:
        print_failure(f"Status: {status}, Error: {data}")

    # Test 4: Zakat Intent
    print_test(4, "Zakat Intent", "كيف احسب زكاة مالي؟")
    success, status, data = make_request(
        "POST", "/api/v1/query",
        {"query": "كيف احسب زكاة مالي؟", "language": "ar"}, timeout=15,
    )
    if success and status == 200:
        if validate_field(data, "intent", str):
            print_success(data, ["query_id", "intent", "intent_confidence"])
            tests_passed += 1
        else:
            print_warning("Missing zakat query response")
    else:
        print_failure(f"Status: {status}, Error: {data}")

    # Test 5: Dua Request
    print_test(5, "Dua Request", "أعطني دعاء السفر")
    success, status, data = make_request(
        "POST", "/api/v1/query",
        {"query": "أعطني دعاء السفر", "language": "ar"}, timeout=15,
    )
    if success and status == 200:
        if validate_field(data, "intent", str):
            print_success(data, ["query_id", "intent", "intent_confidence"])
            tests_passed += 1
        else:
            print_warning("Missing dua query response")
    else:
        print_failure(f"Status: {status}, Error: {data}")

    print(f"\n{Colors.BLUE}Query Tests: {tests_passed}/{tests_total} passed{Colors.ENDC}")
    return tests_passed == tests_total


# ── Main ─────────────────────────────────────────────────────────────────


def main():
    """Run all tests."""
    parser = argparse.ArgumentParser(
        description="Comprehensive validation suite for Athar API",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/tests/comprehensive_test.py
  python scripts/tests/comprehensive_test.py --port 8002
        """,
    )
    parser.add_argument("--port", type=int, default=8000, help="API port (default: 8000)")
    parser.add_argument("--url", type=str, default="", help="Full API URL")
    args = parser.parse_args()

    base_url = args.url.rstrip("/") if args.url else f"http://localhost:{args.port}"
    make_request.base_url = base_url  # type: ignore[attr-defined]

    print_header("🕌 ATHAR ISLAMIC QA SYSTEM - COMPREHENSIVE VALIDATION SUITE")
    print(f"{Colors.BOLD}Testing against:{Colors.ENDC} {base_url}\n")

    # Check if API is running
    success, status, data = make_request("GET", "/health")
    if not success:
        print(f"{Colors.RED}✗ API is not running at {base_url}{Colors.ENDC}")
        print(f"\n{Colors.YELLOW}Please start the API first:{Colors.ENDC}")
        print(f"  uvicorn src.api.main:app --reload --host 0.0.0.0 --port {args.port}\n")
        sys.exit(1)

    print(f"{Colors.GREEN}✓ API is running (version: {data.get('version', 'unknown')}){Colors.ENDC}\n")

    start_time = time.time()

    # Run all test suites
    all_results = {
        "Health": test_health_endpoints(),
        "Tools": test_tool_endpoints(),
        "Quran": test_quran_endpoints(),
        "RAG": test_rag_endpoints(),
        "Query": test_query_endpoint(),
    }

    elapsed = time.time() - start_time

    # Summary
    print_header("✓ COMPREHENSIVE VALIDATION COMPLETE")

    passed = sum(1 for v in all_results.values() if v)
    total = len(all_results)

    print(f"\n{Colors.BOLD}Results Summary:{Colors.ENDC}\n")
    for category, result in all_results.items():
        status_icon = f"{Colors.GREEN}✓ PASS{Colors.ENDC}" if result else f"{Colors.RED}✗ FAIL{Colors.ENDC}"
        print(f"  {status_icon} {category}")

    print(f"\n{Colors.BOLD}Overall: {passed}/{total} test suites passed{Colors.ENDC}")
    print(f"{Colors.BOLD}Time:    {format_duration(elapsed)}{Colors.ENDC}\n")

    if passed == total:
        print(f"{Colors.GREEN}{'=' * 80}{Colors.ENDC}")
        print(f"{Colors.GREEN}  ALL TESTS PASSED - SYSTEM IS FULLY OPERATIONAL{Colors.ENDC}")
        print(f"{Colors.GREEN}{'=' * 80}{Colors.ENDC}\n")
    else:
        print(f"{Colors.YELLOW}{'=' * 80}{Colors.ENDC}")
        print(f"{Colors.YELLOW}  SOME TESTS FAILED - REVIEW NEEDED{Colors.ENDC}")
        print(f"{Colors.YELLOW}{'=' * 80}{Colors.ENDC}\n")

    sys.exit(0 if passed == total else 1)


if __name__ == "__main__":
    main()
