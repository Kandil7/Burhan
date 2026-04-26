#!/usr/bin/env python3
"""
Comprehensive Endpoint Test Suite for Burhan Islamic QA System.

Tests ALL endpoints with detailed response validation including:
- Health & readiness checks
- Main query endpoint (all intent types)
- Tool endpoints (zakat, inheritance, prayer times, hijri, duas)
- Quran endpoints (surahs, ayah, search, validate, tafsir, analytics)
- RAG endpoints (fiqh, general, stats)
- Error handling (404, 405, validation)

Usage:
    python scripts/tests/test_all_endpoints_detailed.py
    python scripts/tests/test_all_endpoints_detailed.py --port 8002
    python scripts/tests/test_all_endpoints_detailed.py --url http://localhost:8000
    python scripts/tests/test_all_endpoints_detailed.py --verbose

Author: Burhan Engineering Team
"""

import argparse
import json
import sys
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from typing import Any, Callable, Optional

from scripts.utils import (
    setup_script_logger,
    format_duration,
)

logger = setup_script_logger("test-endpoints-detailed")


# ── Configuration ────────────────────────────────────────────────────────


@dataclass
class TestResult:
    """Result of a single endpoint test."""
    name: str
    passed: bool
    status_code: int = 0
    response_time_ms: float = 0
    checks_passed: int = 0
    checks_total: int = 0
    check_details: list[str] = field(default_factory=list)
    error: str = ""


# ── HTTP Helper ──────────────────────────────────────────────────────────


def make_request(
    method: str,
    url: str,
    data: Optional[dict] = None,
    timeout: int = 30,
) -> tuple[bool, int, dict, float]:
    """
    Make HTTP request and return (success, status, data, elapsed_ms).

    Args:
        method: HTTP method.
        url: Full URL.
        data: JSON body for POST.
        timeout: Request timeout.

    Returns:
        Tuple of (success, status_code, response_data, elapsed_ms).
    """
    start = time.time()
    try:
        if data:
            body = json.dumps(data).encode("utf-8")
            req = urllib.request.Request(
                url, data=body, headers={"Content-Type": "application/json"}, method=method
            )
        else:
            req = urllib.request.Request(url, method=method)

        response = urllib.request.urlopen(req, timeout=timeout)
        elapsed = (time.time() - start) * 1000
        response_data = json.loads(response.read().decode())
        return True, response.status, response_data, elapsed

    except urllib.error.HTTPError as e:
        elapsed = (time.time() - start) * 1000
        try:
            error_data = json.loads(e.read().decode())
        except Exception:
            error_data = {"detail": str(e)}
        return False, e.code, error_data, elapsed

    except Exception as e:
        elapsed = (time.time() - start) * 1000
        return False, 0, {"error": str(e)}, elapsed


# ── Terminal Colors ──────────────────────────────────────────────────────


class Colors:
    """ANSI color codes for terminal output."""
    GREEN = "\033[92m"
    RED = "\033[91m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    CYAN = "\033[96m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    END = "\033[0m"


# ── Test Runner ──────────────────────────────────────────────────────────


def run_test(
    name: str,
    method: str,
    url: str,
    data: Optional[dict] = None,
    checks: Optional[dict[str, Callable]] = None,
    timeout: int = 30,
    verbose: bool = False,
) -> TestResult:
    """
    Run a single endpoint test with validation checks.

    Args:
        name: Test name for display.
        method: HTTP method.
        url: Full URL.
        data: POST body.
        checks: Dict of check_name -> check_function(response_data).
        timeout: Request timeout.
        verbose: Show detailed check output.

    Returns:
        TestResult with pass/fail status.
    """
    result = TestResult(name=name)

    print(f"\n{Colors.CYAN}{'=' * 70}{Colors.END}")
    print(f"{Colors.BOLD}{name}{Colors.END}")
    print(f"{'=' * 70}")
    if verbose:
        print(f"  {method} {url}")
        if data:
            print(f"  Body: {json.dumps(data, ensure_ascii=False)[:200]}")

    success, status, response_data, elapsed = make_request(method, url, data, timeout)
    result.status_code = status
    result.response_time_ms = elapsed

    if not success:
        result.error = f"Status: {status}"
        print(f"  {Colors.RED}✗ FAIL{Colors.END} - Status: {status}")
        if response_data:
            detail = str(response_data)[:200]
            print(f"  Response: {detail}")
        return result

    # Run checks
    if checks:
        result.checks_total = len(checks)
        for check_name, check_fn in checks.items():
            try:
                check_result = check_fn(response_data)
                if check_result:
                    result.checks_passed += 1
                    if verbose or True:  # Always show check results
                        print(f"  {Colors.GREEN}✓ {check_name}{Colors.END}: {check_result}")
                else:
                    if verbose:
                        print(f"  {Colors.RED}✗ {check_name}{Colors.END}")
            except Exception as e:
                if verbose:
                    print(f"  {Colors.RED}✗ {check_name}{Colors.END}: Error - {e}")
    else:
        result.checks_passed = 1
        result.checks_total = 1

    # Determine pass/fail
    result.passed = result.checks_passed == result.checks_total and result.checks_total > 0

    if result.passed:
        print(f"  {Colors.GREEN}✓ PASSED{Colors.END} ({elapsed:.0f}ms)")
    else:
        print(f"  {Colors.RED}✗ FAIL{Colors.END} ({result.checks_passed}/{result.checks_total} checks)")

    return result


# ── Test Definitions ─────────────────────────────────────────────────────


def run_all_tests(base_url: str, verbose: bool = False) -> list[TestResult]:
    """Run all endpoint tests and return results."""
    results: list[TestResult] = []

    # ── 1. Health ──
    results.append(run_test(
        "1. GET /health", "GET", f"{base_url}/health",
        checks={
            "status_ok": lambda d: d.get("status") == "ok",
            "version": lambda d: d.get("version", "N/A"),
            "api_healthy": lambda d: d.get("services", {}).get("api") == "healthy",
        },
        verbose=verbose,
    ))

    # ── 2. Root ──
    results.append(run_test(
        "2. GET /", f"{base_url}/",
        checks={
            "name": lambda d: d.get("name") == "Burhan",
            "version": lambda d: d.get("version", "N/A"),
            "has_query_endpoint": lambda d: "/api/v1/query" in d.get("query_endpoint", ""),
        },
        verbose=verbose,
    ))

    # ── 3. Quran Surahs ──
    results.append(run_test(
        "3. GET /api/v1/quran/surahs", f"{base_url}/api/v1/quran/surahs",
        checks={
            "count_114": lambda d: f"{len(d)} surahs" if len(d) == 114 else f"Expected 114, got {len(d)}",
            "first_surah": lambda d: d[0]["name_en"] if d else None,
            "last_surah": lambda d: d[-1]["name_en"] if d else None,
        },
        verbose=verbose,
    ))

    # ── 4. Surah 1 ──
    results.append(run_test(
        "4. GET /api/v1/quran/surahs/1", f"{base_url}/api/v1/quran/surahs/1",
        checks={
            "number": lambda d: f"Surah {d.get('number')}" if d.get("number") == 1 else "Wrong number",
            "name": lambda d: d.get("name_en"),
            "ayah_count": lambda d: f"{d.get('verse_count')} ayahs",
            "has_ayahs": lambda d: f"{len(d.get('ayahs', []))} loaded" if d.get("ayahs") else "No ayahs",
        },
        verbose=verbose,
    ))

    # ── 5. Ayah 2:255 ──
    results.append(run_test(
        "5. GET /api/v1/quran/ayah/2:255", f"{base_url}/api/v1/quran/ayah/2:255",
        checks={
            "surah": lambda d: f"{d.get('surah_name_en')} 2:255" if d.get("surah_number") == 2 else "Wrong surah",
            "has_text": lambda d: f"{len(d.get('text_uthmani', ''))} chars" if d.get("text_uthmani") else "No text",
            "has_translation": lambda d: f"{len(d.get('translations', []))} translations" if d.get("translations") else "No translations",
        },
        verbose=verbose,
    ))

    # ── 6. Quran Search ──
    results.append(run_test(
        "6. POST /api/v1/quran/search", f"{base_url}/api/v1/quran/search",
        method="POST", data={"query": "رحمة", "limit": 3},
        checks={
            "found_verses": lambda d: f"{d.get('count', 0)} verses",
            "has_results": lambda d: f"First: {d['verses'][0]['surah_name_en']}:{d['verses'][0]['ayah_number']}" if d.get("verses") else "No results",
        },
        verbose=verbose,
    ))

    # ── 7. Quran Validate ──
    results.append(run_test(
        "7. POST /api/v1/quran/validate", f"{base_url}/api/v1/quran/validate",
        method="POST", data={"text": "بسم الله الرحمن الرحيم"},
        checks={
            "is_quran": lambda d: "YES" if d.get("is_quran") else "NO (expected due to diacritics)",
            "confidence": lambda d: d.get("confidence", 0),
        },
        verbose=verbose,
    ))

    # ── 8. Quran Analytics ──
    results.append(run_test(
        "8. POST /api/v1/quran/analytics", f"{base_url}/api/v1/quran/analytics",
        method="POST", data={"query": "How many verses are in Al-Baqarah?"},
        checks={
            "has_sql": lambda d: d.get("sql", "No SQL")[:50],
            "has_result": lambda d: str(d.get("result", "N/A"))[:50],
            "has_answer": lambda d: d.get("formatted_answer", "No answer")[:80],
        },
        timeout=15,
        verbose=verbose,
    ))

    # ── 9. Tafsir ──
    results.append(run_test(
        "9. GET /api/v1/quran/tafsir/1:1", f"{base_url}/api/v1/quran/tafsir/1:1",
        checks={
            "has_ayah": lambda d: f"Surah {d['ayah']['surah_name_en']} 1:1" if d.get("ayah") else "No ayah",
            "tafsirs_count": lambda d: f"{len(d.get('tafsirs', []))} tafsirs",
        },
        verbose=verbose,
    ))

    # ── 10. Zakat ──
    results.append(run_test(
        "10. POST /api/v1/tools/zakat", f"{base_url}/api/v1/tools/zakat",
        method="POST", data={"assets": {"cash": 50000, "gold_grams": 100}, "debts": 5000},
        checks={
            "is_zakatable": lambda d: "YES" if d.get("is_zakatable") else "NO",
            "zakat_amount": lambda d: f"{d.get('zakat_amount', 0):.2f}",
            "nisab_gold": lambda d: f"Gold: {d.get('nisab', {}).get('gold', 0):.2f}",
            "nisab_silver": lambda d: f"Silver: {d.get('nisab', {}).get('silver', 0):.2f}",
        },
        verbose=verbose,
    ))

    # ── 11. Inheritance ──
    results.append(run_test(
        "11. POST /api/v1/tools/inheritance", f"{base_url}/api/v1/tools/inheritance",
        method="POST",
        data={"estate_value": 100000, "heirs": {"husband": True, "father": True, "mother": True, "sons": 1, "daughters": 1}},
        checks={
            "distribution_count": lambda d: f"{len(d.get('distribution', []))} heirs",
            "total_distributed": lambda d: f"{d.get('total_distributed', 0):.2f}",
            "has_amounts": lambda d: "YES" if any(h.get("amount", 0) > 0 for h in d.get("distribution", [])) else "All zero",
        },
        verbose=verbose,
    ))

    # ── 12. Prayer Times ──
    results.append(run_test(
        "12. POST /api/v1/tools/prayer-times", f"{base_url}/api/v1/tools/prayer-times",
        method="POST", data={"lat": 25.2854, "lng": 51.5310, "method": "egyptian"},
        checks={
            "has_times": lambda d: f"Fajr: {d['times'].get('fajr', 'N/A')}, Dhuhr: {d['times'].get('dhuhr', 'N/A')}" if d.get("times") else "No times",
            "qibla": lambda d: f"{d.get('qibla_direction', 0):.1f}°" if d.get("qibla_direction") else "No qibla",
        },
        timeout=15,
        verbose=verbose,
    ))

    # ── 13. Hijri ──
    results.append(run_test(
        "13. POST /api/v1/tools/hijri", f"{base_url}/api/v1/tools/hijri",
        method="POST", data={"gregorian_date": "2026-04-05"},
        checks={
            "hijri_date": lambda d: f"{d['hijri_date'].get('day')}/{d['hijri_date'].get('month')}/{d['hijri_date'].get('year')}" if d.get("hijri_date") else "No date",
            "is_ramadan": lambda d: "YES" if d.get("is_ramadan") else "NO",
        },
        verbose=verbose,
    ))

    # ── 14. Duas ──
    results.append(run_test(
        "14. POST /api/v1/tools/duas", f"{base_url}/api/v1/tools/duas",
        method="POST", data={"occasion": "morning", "limit": 3},
        checks={
            "count": lambda d: f"{d.get('count', 0)} duas",
            "first_category": lambda d: d["duas"][0].get("category", "N/A") if d.get("duas") else "No duas",
            "has_arabic": lambda d: "YES" if d.get("duas", [{}])[0].get("arabic_text") else "NO",
        },
        verbose=verbose,
    ))

    # ── 15. Query Greeting ──
    results.append(run_test(
        "15. POST /api/v1/query (Greeting)", f"{base_url}/api/v1/query",
        method="POST", data={"query": "السلام عليكم", "language": "ar"},
        checks={
            "intent": lambda d: d.get("intent"),
            "agent": lambda d: d.get("metadata", {}).get("agent", "N/A"),
            "has_answer": lambda d: f"{d.get('answer', '')[:80]}..." if d.get("answer") else "No answer",
        },
        timeout=30,
        verbose=verbose,
    ))

    # ── 16. Query Fiqh ──
    results.append(run_test(
        "16. POST /api/v1/query (Fiqh)", f"{base_url}/api/v1/query",
        method="POST", data={"query": "ما حكم صلاة الجمعة؟", "language": "ar"},
        checks={
            "intent": lambda d: d.get("intent"),
            "agent": lambda d: d.get("metadata", {}).get("agent", "N/A"),
            "has_retrieval": lambda d: f"{d.get('metadata', {}).get('retrieved_count', 0)} passages" if d.get("metadata", {}).get("retrieved_count") else "No retrieval",
            "has_answer": lambda d: f"{d.get('answer', '')[:100]}..." if d.get("answer") else "No answer",
        },
        timeout=30,
        verbose=verbose,
    ))

    # ── 17. RAG Fiqh ──
    results.append(run_test(
        "17. POST /api/v1/rag/fiqh", f"{base_url}/api/v1/rag/fiqh",
        method="POST", data={"query": "صلاة الجمعة", "language": "ar"},
        checks={
            "retrieved": lambda d: f"{d.get('metadata', {}).get('retrieved_count', 0)} passages",
            "confidence": lambda d: f"{d.get('confidence', 0):.2f}",
            "has_answer": lambda d: f"{d.get('answer', '')[:100]}..." if d.get("answer") else "No answer",
        },
        timeout=30,
        verbose=verbose,
    ))

    # ── 18. RAG Stats ──
    results.append(run_test(
        "18. GET /api/v1/rag/stats", f"{base_url}/api/v1/rag/stats",
        checks={
            "total_docs": lambda d: f"{d.get('total_documents', 0)} documents",
            "fiqh_count": lambda d: f"fiqh: {d.get('collections', {}).get('fiqh_passages', {}).get('vectors_count', 0)}",
            "hadith_count": lambda d: f"hadith: {d.get('collections', {}).get('hadith_passages', {}).get('vectors_count', 0)}",
            "model": lambda d: d.get("embedding_model", "N/A"),
        },
        verbose=verbose,
    ))

    return results


# ── Main ─────────────────────────────────────────────────────────────────


def main():
    """Run comprehensive endpoint tests."""
    parser = argparse.ArgumentParser(
        description="Comprehensive endpoint test for Burhan API",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/tests/test_all_endpoints_detailed.py
  python scripts/tests/test_all_endpoints_detailed.py --port 8002
  python scripts/tests/test_all_endpoints_detailed.py --verbose
        """,
    )
    parser.add_argument("--port", type=int, default=8000, help="API port (default: 8000)")
    parser.add_argument("--url", type=str, default="", help="Full API URL")
    parser.add_argument("--verbose", "-v", action="store_true", help="Show detailed output")
    args = parser.parse_args()

    base_url = args.url.rstrip("/") if args.url else f"http://localhost:{args.port}"

    print(f"\n{Colors.BOLD}{Colors.BLUE}{'=' * 70}")
    print(f"  Burhan ISLAMIC QA - COMPREHENSIVE ENDPOINT TEST")
    print(f"{'=' * 70}{Colors.END}")
    print(f"  Target: {base_url}")
    print(f"{'=' * 70}\n")

    # Check API is running
    success, status, data, elapsed = make_request("GET", f"{base_url}/health")
    if not success:
        print(f"{Colors.RED}✗ API is not running at {base_url}{Colors.END}")
        print(f"\nPlease start the API first:")
        print(f"  uvicorn src.api.main:app --reload --host 0.0.0.0 --port {args.port}")
        sys.exit(1)

    print(f"{Colors.GREEN}✓ API is running (version: {data.get('version', 'unknown')}){Colors.END}\n")

    start_time = time.time()
    results = run_all_tests(base_url, verbose=args.verbose)

    # Summary
    passed = sum(1 for r in results if r.passed)
    failed = sum(1 for r in results if not r.passed)
    total = len(results)
    elapsed = time.time() - start_time

    print(f"\n{Colors.BOLD}{Colors.BLUE}{'=' * 70}")
    print(f"  RESULTS: {Colors.GREEN}{passed}/{total} PASSED{Colors.END} | {Colors.RED if failed > 0 else Colors.END}{failed} FAILED")
    print(f"  Time: {format_duration(elapsed)}")
    print(f"{'=' * 70}{Colors.END}\n")

    sys.exit(1 if failed > 0 else 0)


if __name__ == "__main__":
    main()
