#!/usr/bin/env python3
"""
Simple test script to check if API is running.
"""

import urllib.request
import urllib.error
import json
import sys


def test_endpoint(url, name):
    """Test a single endpoint."""
    try:
        req = urllib.request.Request(url, method="GET")
        response = urllib.request.urlopen(req, timeout=10)
        data = json.loads(response.read().decode())
        print(f"✓ {name}: {data}")
        return True
    except urllib.error.URLError as e:
        print(f"✗ {name}: {e}")
        return False
    except Exception as e:
        print(f"✗ {name}: {type(e).__name__}: {e}")
        return False


if __name__ == "__main__":
    base_url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000"

    print(f"Testing {base_url}...")
    test_endpoint(f"{base_url}/health", "Health")
    test_endpoint(f"{base_url}/", "Root")
    test_endpoint(f"{base_url}/ready", "Ready")
    test_endpoint(f"{base_url}/classify", "Classify")
