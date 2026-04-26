#!/usr/bin/env python3
"""
Quick Smoke Test for Burhan Islamic QA System API.

Tests all critical endpoints with minimal overhead:
- Health check
- Main query endpoint (greeting, fiqh)
- Tool endpoints (zakat, prayer times, hijri, duas)
- Quran endpoints (surahs, ayah, search)
- RAG endpoints (fiqh, stats)

Usage:
    python scripts/quick_test.py
    python scripts/quick_test.py --port 8002
    python scripts/quick_test.py --url http://localhost:8000
    python scripts/quick_test.py --verbose

Author: Burhan Engineering Team
"""

import argparse
import json
import sys
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from typing import Any, Optional

from scripts.utils import (
    setup_script_logger,
    ProgressBar,
    format_duration,
)

logger = setup_script_logger("quick-test")


# ── Test Result Tracking ─────────────────────────────────────────────────


@dataclass
class TestResult:
    """Result of a single test."""
    name: str
    passed: bool
    status_code: int = 0
    response_time_ms: float = 0
    error: str = ""
    detail: str = ""


@dataclass
class TestSuite:
    """Collection of test results."""
    results: list[TestResult] = field(default_factory=list)
    start_time: float = 0

    def add(self, result: TestResult) -> None:
        self.results.append(result)

    @property
    def passed_count(self) -> int:
        return sum(1 for r in self.results if r.passed)

    @property
    def failed_count(self) -> int:
        return sum(1 for r in self.results if not r.passed)

    @property
    def total_count(self) -> int:
        return len(self.results)

    @property
    def total_time_ms(self) -> float:
        return sum(r.response_time_ms for r in self.results)


# ── HTTP Request Helper ──────────────────────────────────────────────────


def make_request(
    method: str,
    url: str,
    data: Optional[dict] = None,
    timeout: int = 30,
) -> tuple[bool, int, dict, float]:
    """
    Make HTTP request and return (success, status_code, response_data, response_time_ms).

    Args:
        method: HTTP method (GET, POST, etc.)
        url: Full URL to request.
        data: JSON body for POST requests.
        timeout: Request timeout in seconds.

    Returns:
        Tuple of (success, status_code, response_data, response_time_ms).
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


# ── Test Definitions ─────────────────────────────────────────────────────


def test_health(base_url: str) -> TestResult:
    """Test health endpoint."""
    success, status, data, elapsed = make_request("GET", f"{base_url}/health")
    detail = ""
    passed = success and status == 200
    if passed:
        detail = f"status={data.get('status', 'N/A')}, version={data.get('version', 'N/A')}"
    return TestResult("Health Check", passed, status, elapsed, detail=detail)


def test_root(base_url: str) -> TestResult:
    """Test root endpoint."""
    success, status, data, elapsed = make_request("GET", f"{base_url}/")
    detail = ""
    passed = success and status == 200
    if passed:
        detail = f"name={data.get('name', 'N/A')}"
    return TestResult("Root Endpoint", passed, status, elapsed, detail=detail)


def test_query_greeting(base_url: str) -> TestResult:
    """Test query endpoint with greeting."""
    success, status, data, elapsed = make_request(
        "POST", f"{base_url}/api/v1/query",
        {"query": "السلام عليكم", "language": "ar"}
    )
    detail = ""
    passed = success and status == 200
    if passed:
        detail = f"intent={data.get('intent', 'N/A')}"
    return TestResult("Query: Greeting", passed, status, elapsed, detail=detail)


def test_query_fiqh(base_url: str) -> TestResult:
    """Test query endpoint with fiqh question."""
    success, status, data, elapsed = make_request(
        "POST", f"{base_url}/api/v1/query",
        {"query": "ما حكم صلاة الجمعة؟", "language": "ar"},
        timeout=30,
    )
    detail = ""
    passed = success and status == 200
    if passed:
        detail = f"intent={data.get('intent', 'N/A')}"
    return TestResult("Query: Fiqh", passed, status, elapsed, detail=detail)


def test_zakat(base_url: str) -> TestResult:
    """Test zakat calculator."""
    success, status, data, elapsed = make_request(
        "POST", f"{base_url}/api/v1/tools/zakat",
        {"assets": {"cash": 50000, "gold_grams": 100}, "debts": 5000}
    )
    detail = ""
    passed = success and status == 200
    if passed:
        detail = f"zakatable={data.get('is_zakatable', False)}, amount={data.get('zakat_amount', 0):.2f}"
    return TestResult("Tool: Zakat", passed, status, elapsed, detail=detail)


def test_prayer_times(base_url: str) -> TestResult:
    """Test prayer times tool."""
    success, status, data, elapsed = make_request(
        "POST", f"{base_url}/api/v1/tools/prayer-times",
        {"lat": 25.2854, "lng": 51.5310, "method": "egyptian"},
        timeout=15,
    )
    detail = ""
    passed = success and status == 200
    if passed:
        times = data.get("times", {})
        detail = f"fajr={times.get('fajr', 'N/A')}, qibla={data.get('qibla_direction', 0):.1f}°"
    return TestResult("Tool: Prayer Times", passed, status, elapsed, detail=detail)


def test_hijri(base_url: str) -> TestResult:
    """Test Hijri calendar tool."""
    success, status, data, elapsed = make_request(
        "POST", f"{base_url}/api/v1/tools/hijri",
        {"gregorian_date": "2026-04-05"}
    )
    detail = ""
    passed = success and status == 200
    if passed:
        hijri = data.get("hijri_date", {})
        detail = f"{hijri.get('day', '?')}/{hijri.get('month', '?')}/{hijri.get('year', '?')}"
    return TestResult("Tool: Hijri Calendar", passed, status, elapsed, detail=detail)


def test_duas(base_url: str) -> TestResult:
    """Test duas retrieval tool."""
    success, status, data, elapsed = make_request(
        "POST", f"{base_url}/api/v1/tools/duas",
        {"occasion": "morning", "limit": 2}
    )
    detail = ""
    passed = success and status == 200
    if passed:
        detail = f"count={data.get('count', 0)}"
    return TestResult("Tool: Duas", passed, status, elapsed, detail=detail)


def test_inheritance(base_url: str) -> TestResult:
    """Test inheritance calculator."""
    success, status, data, elapsed = make_request(
        "POST", f"{base_url}/api/v1/tools/inheritance",
        {"estate_value": 100000, "heirs": {"husband": True, "father": True, "mother": True, "sons": 1, "daughters": 1}}
    )
    detail = ""
    passed = success and status == 200
    if passed:
        detail = f"distribution={len(data.get('distribution', []))} heirs"
    return TestResult("Tool: Inheritance", passed, status, elapsed, detail=detail)


def test_quran_surahs(base_url: str) -> TestResult:
    """Test Quran surahs listing."""
    success, status, data, elapsed = make_request("GET", f"{base_url}/api/v1/quran/surahs")
    detail = ""
    passed = success and status == 200
    if passed and isinstance(data, list):
        detail = f"{len(data)} surahs"
    return TestResult("Quran: Surahs List", passed, status, elapsed, detail=detail)


def test_quran_ayah(base_url: str) -> TestResult:
    """Test Quran ayah lookup."""
    success, status, data, elapsed = make_request("GET", f"{base_url}/api/v1/quran/ayah/2:255")
    detail = ""
    passed = success and status == 200
    if passed:
        detail = f"surah={data.get('surah_name_en', 'N/A')}"
    return TestResult("Quran: Ayah 2:255", passed, status, elapsed, detail=detail)


def test_quran_search(base_url: str) -> TestResult:
    """Test Quran search."""
    success, status, data, elapsed = make_request(
        "POST", f"{base_url}/api/v1/quran/search",
        {"query": "رحمة", "limit": 3}
    )
    detail = ""
    passed = success and status == 200
    if passed:
        detail = f"found={data.get('count', 0)} verses"
    return TestResult("Quran: Search", passed, status, elapsed, detail=detail)


def test_rag_fiqh(base_url: str) -> TestResult:
    """Test RAG fiqh endpoint."""
    success, status, data, elapsed = make_request(
        "POST", f"{base_url}/api/v1/rag/fiqh",
        {"query": "صلاة الجمعة", "language": "ar"},
        timeout=30,
    )
    detail = ""
    passed = success and status == 200
    if passed:
        detail = f"confidence={data.get('confidence', 0):.2f}"
    return TestResult("RAG: Fiqh", passed, status, elapsed, detail=detail)


def test_rag_stats(base_url: str) -> TestResult:
    """Test RAG stats endpoint."""
    success, status, data, elapsed = make_request("GET", f"{base_url}/api/v1/rag/stats")
    detail = ""
    passed = success and status == 200
    if passed:
        detail = f"documents={data.get('total_documents', 0)}"
    return TestResult("RAG: Stats", passed, status, elapsed, detail=detail)


# ── Test Suite Runner ────────────────────────────────────────────────────


# Define all tests in order
ALL_TESTS = [
    ("Health & Root", [test_health, test_root]),
    ("Query Endpoint", [test_query_greeting, test_query_fiqh]),
    ("Tools", [test_zakat, test_prayer_times, test_hijri, test_duas, test_inheritance]),
    ("Quran", [test_quran_surahs, test_quran_ayah, test_quran_search]),
    ("RAG", [test_rag_fiqh, test_rag_stats]),
]


def run_tests(
    base_url: str,
    verbose: bool = False,
    test_filter: Optional[str] = None,
) -> TestSuite:
    """
    Run all smoke tests.

    Args:
        base_url: API base URL.
        verbose: Show detailed output per test.
        test_filter: Only run tests matching this category name.

    Returns:
        TestSuite with all results.
    """
    suite = TestSuite()
    suite.start_time = time.time()

    # Count total tests
    total_tests = 0
    for category, tests in ALL_TESTS:
        if test_filter and test_filter.lower() not in category.lower():
            continue
        total_tests += len(tests)

    # Run tests with progress bar
    with ProgressBar(total=total_tests, desc="Running Tests", unit="tests") as bar:
        for category, tests in ALL_TESTS:
            if test_filter and test_filter.lower() not in category.lower():
                continue

            if verbose:
                print(f"\n{'─' * 60}")
                print(f"  {category}")
                print(f"{'─' * 60}")

            for test_func in tests:
                result = test_func(base_url)
                suite.add(result)
                bar.update()

                if verbose:
                    status = "✓" if result.passed else "✗"
                    print(f"  {status} {result.name} ({result.response_time_ms:.0f}ms)")
                    if result.detail:
                        print(f"    {result.detail}")
                    if result.error:
                        print(f"    ERROR: {result.error}")

    return suite


def print_summary(suite: TestSuite) -> None:
    """Print test summary."""
    print("\n" + "=" * 70)
    print("QUICK TEST RESULTS")
    print("=" * 70)

    # Per-result summary
    for result in suite.results:
        icon = "✓" if result.passed else "✗"
        color_start = "" if result.passed else ""
        color_end = "" if result.passed else ""
        print(f"  {icon} {result.name}")
        if result.detail and result.passed:
            print(f"    {result.detail}")
        if result.error:
            print(f"    ERROR: {result.error}")
        if not result.passed and result.status_code:
            print(f"    Status: {result.status_code}")

    # Overall summary
    elapsed = time.time() - suite.start_time
    print(f"\n{'─' * 70}")
    print(f"  Total:  {suite.total_count}")
    print(f"  Passed: {suite.passed_count}")
    print(f"  Failed: {suite.failed_count}")
    print(f"  Time:   {format_duration(elapsed)}")

    if suite.failed_count == 0:
        print(f"\n  STATUS: ALL TESTS PASSED ✓")
    else:
        print(f"\n  STATUS: {suite.failed_count} TEST(S) FAILED ✗")

    print("=" * 70)


# ── Main ─────────────────────────────────────────────────────────────────


def main():
    """Run quick smoke tests against Burhan API."""
    parser = argparse.ArgumentParser(
        description="Quick smoke test for Burhan API",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/quick_test.py
  python scripts/quick_test.py --port 8002
  python scripts/quick_test.py --url http://localhost:8000
  python scripts/quick_test.py --verbose
  python scripts/quick_test.py --filter tools
        """,
    )
    parser.add_argument("--port", type=int, default=8000, help="API port (default: 8000)")
    parser.add_argument("--url", type=str, default="", help="Full API URL (overrides --port)")
    parser.add_argument("--verbose", "-v", action="store_true", help="Show detailed output")
    parser.add_argument("--filter", type=str, default="", help="Filter tests by category name")

    args = parser.parse_args()

    # Determine base URL
    if args.url:
        base_url = args.url.rstrip("/")
    else:
        base_url = f"http://localhost:{args.port}"

    print(f"\n{'=' * 70}")
    print("🕌 Burhan ISLAMIC QA - QUICK SMOKE TEST")
    print(f"{'=' * 70}")
    print(f"  Target: {base_url}")
    if args.filter:
        print(f"  Filter: {args.filter}")
    print(f"{'=' * 70}\n")

    # Check if API is running first
    success, status, data, elapsed = make_request("GET", f"{base_url}/health")
    if not success:
        print(f"✗ API is not running at {base_url}")
        print(f"\nPlease start the API first:")
        print(f"  uvicorn src.api.main:app --reload --host 0.0.0.0 --port {args.port}")
        sys.exit(1)

    print(f"✓ API is running (version: {data.get('version', 'unknown')})\n")

    # Run tests
    suite = run_tests(base_url, verbose=args.verbose, test_filter=args.filter or None)

    # Print summary
    print_summary(suite)

    # Exit code
    sys.exit(1 if suite.failed_count > 0 else 0)


if __name__ == "__main__":
    main()
