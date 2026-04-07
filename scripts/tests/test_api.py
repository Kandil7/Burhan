#!/usr/bin/env python3
"""
Quick API Test for Athar Islamic QA System.

Minimal smoke test to verify the API is running and responding:
- Health check
- Query endpoint with greeting

Usage:
    python scripts/tests/test_api.py
    python scripts/tests/test_api.py --port 8002

Author: Athar Engineering Team
"""

import argparse
import json
import sys
import urllib.error
import urllib.request
from typing import Optional

from scripts.utils import setup_script_logger

logger = setup_script_logger("test-api")


def make_request(
    method: str, url: str, data: Optional[dict] = None, timeout: int = 30
) -> tuple[bool, int, dict]:
    """Make HTTP request and return (success, status_code, response_data)."""
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


def test_health(base_url: str) -> bool:
    """Test health endpoint."""
    print("Testing /health endpoint...")
    success, status, data = make_request("GET", f"{base_url}/health")

    if success and status == 200:
        print(f"  ✓ Health: {data.get('status', 'unknown')}")
        print(f"  ✓ Version: {data.get('version', 'unknown')}")
        return True
    else:
        print(f"  ✗ Error: Status {status}")
        return False


def test_query(base_url: str) -> bool:
    """Test query endpoint with greeting."""
    print("\nTesting /api/v1/query endpoint...")
    success, status, data = make_request(
        "POST", f"{base_url}/api/v1/query", {"query": "السلام عليكم", "language": "ar"}, timeout=30
    )

    if success and status == 200:
        print(f"  ✓ Query successful")
        print(f"  ✓ Intent: {data.get('intent', 'unknown')}")
        answer = data.get("answer", "")
        print(f"  ✓ Answer: {answer[:100]}...")
        return True
    else:
        print(f"  ✗ HTTP Error: {status}")
        if data:
            print(f"  ✗ Response: {str(data)[:200]}")
        return False


def main():
    """Run quick API tests."""
    parser = argparse.ArgumentParser(description="Quick API test for Athar")
    parser.add_argument("--port", type=int, default=8000, help="API port (default: 8000)")
    parser.add_argument("--url", type=str, default="", help="Full API URL")
    args = parser.parse_args()

    base_url = args.url.rstrip("/") if args.url else f"http://localhost:{args.port}"

    print("=" * 60)
    print("ATHAR API TEST")
    print(f"Target: {base_url}")
    print("=" * 60 + "\n")

    health_ok = test_health(base_url)

    if health_ok:
        query_ok = test_query(base_url)
    else:
        print(f"\n✗ API is not running at {base_url}")
        print(f"\nPlease start the API first:")
        print(f"  uvicorn src.api.main:app --reload --host 0.0.0.0 --port {args.port}")
        sys.exit(1)

    print("\n" + "=" * 60)
    print("NEXT STEPS:")
    print("=" * 60)
    print("\n1. Open http://localhost:8000/docs for interactive API docs")
    print("2. Open http://localhost:3000 for chat interface (if frontend running)")
    print("3. Try these queries:")
    print("   - السلام عليكم")
    print("   - ما حكم صلاة الجمعة؟")
    print("   - كم عدد آيات سورة البقرة؟")
    print("\nTo stop services:")
    print("  docker compose -f docker/docker-compose.dev.yml down\n")


if __name__ == "__main__":
    main()
