#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Comprehensive test for all 20 Athar API endpoints.
"""

import urllib.request
import urllib.error
import json
import sys
import time

# Set UTF-8 output
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BASE_URL = "http://127.0.0.1:8000"

TESTS = [
    # Health & Status (3)
    ("GET", "/health", None, "Health Check"),
    ("GET", "/ready", None, "Ready Check"),
    ("GET", "/", None, "Root Endpoint"),
    # Classification (1)
    ("POST", "/classify", {"query": "ما حكم الزكاة؟"}, "Intent Classification"),
    # Query (1)
    ("POST", "/api/v1/query", {"query": "السلام عليكم", "language": "ar"}, "Main Query"),
    # Tools (5)
    ("POST", "/api/v1/tools/zakat", {"assets": {"cash": 50000, "gold_grams": 100}, "debts": 5000}, "Zakat Calculator"),
    (
        "POST",
        "/api/v1/tools/inheritance",
        {"estate_value": 100000, "heirs": {"father": True, "mother": True}},
        "Inheritance",
    ),
    ("POST", "/api/v1/tools/prayer-times", {"lat": 25.2854, "lng": 51.5310, "method": "egyptian"}, "Prayer Times"),
    ("POST", "/api/v1/tools/hijri", {"gregorian_date": "2026-04-15"}, "Hijri Calendar"),
    ("POST", "/api/v1/tools/duas", {"occasion": "morning", "limit": 2}, "Duas Retrieval"),
    # Quran (6)
    ("GET", "/api/v1/quran/surahs", None, "Quran: Surahs List"),
    ("GET", "/api/v1/quran/surahs/2", None, "Quran: Surah Details"),
    ("GET", "/api/v1/quran/ayah/2:255", None, "Quran: Ayah Lookup"),
    ("POST", "/api/v1/quran/search", {"query": "رحمة", "limit": 3}, "Quran: Search"),
    ("POST", "/api/v1/quran/validate", {"text": "بسم الله الرحمن الرحيم"}, "Quran: Validate"),
    ("POST", "/api/v1/quran/analytics", {"query": "كم عدد آيات سورة البقرة"}, "Quran: Analytics"),
    # RAG (4)
    ("POST", "/api/v1/rag/fiqh", {"query": "صلاة الجمعة", "language": "ar"}, "RAG: Fiqh"),
    ("POST", "/api/v1/rag/general", {"query": "الله", "language": "ar"}, "RAG: General"),
    ("GET", "/api/v1/rag/stats", None, "RAG: Stats"),
    ("POST", "/api/v1/rag/simple", {"query": "test", "limit": 1}, "RAG: Simple"),
]


def make_request(method, path, data=None, timeout=30):
    """Make HTTP request."""
    url = f"{BASE_URL}{path}"
    try:
        if data:
            body = json.dumps(data, ensure_ascii=False).encode("utf-8")
            req = urllib.request.Request(
                url, data=body, headers={"Content-Type": "application/json; charset=utf-8"}, method=method
            )
        else:
            req = urllib.request.Request(url, method=method)

        response = urllib.request.urlopen(req, timeout=timeout)
        result = json.loads(response.read().decode("utf-8"))
        return True, response.status, result
    except urllib.error.HTTPError as e:
        try:
            error_data = json.loads(e.read().decode())
        except:
            error_data = {"detail": str(e)}
        return False, e.code, error_data
    except Exception as e:
        return False, 0, {"error": str(e)}


def main():
    print("=" * 70)
    print("TESTING ALL 20 ATHAR API ENDPOINTS")
    print("=" * 70)
    print(f"Base URL: {BASE_URL}")
    print("=" * 70)

    passed = 0
    failed = 0

    for method, path, data, name in TESTS:
        status_msg = f"Testing: {method} {path} ... "
        try:
            print(status_msg, end="")
            sys.stdout.flush()
        except:
            print(f"{method} {path}")
            continue

        success, status, result = make_request(method, path, data)

        if success and status == 200:
            print("OK")
            passed += 1
        else:
            print(f"FAILED")
            print(f"  Error: {result}")
            failed += 1

    print()
    print("=" * 70)
    print(f"RESULTS: {passed} passed, {failed} failed")
    print("=" * 70)

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
