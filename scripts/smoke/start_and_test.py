#!/usr/bin/env python3
"""
Start Burhan API server and run tests.
"""

import multiprocessing
import time
import sys
import urllib.request
import json


def start_server():
    """Run the uvicorn server."""
    import uvicorn

    uvicorn.run("src.api.main:app", host="127.0.0.1", port=8000, log_level="error")


def test_endpoints():
    """Test the API endpoints."""
    base_url = "http://127.0.0.1:8000"

    time.sleep(15)  # Wait for server to start

    tests = [
        ("/health", "Health"),
        ("/", "Root"),
        ("/ready", "Ready"),
    ]

    for path, name in tests:
        try:
            response = urllib.request.urlopen(f"{base_url}{path}", timeout=10)
            data = json.loads(response.read().decode())
            print(f"✓ {name}: {data.get('status') or data.get('name')}")
        except Exception as e:
            print(f"✗ {name}: {e}")


if __name__ == "__main__":
    # Start server in a separate process
    server_process = multiprocessing.Process(target=start_server, daemon=True)
    server_process.start()

    # Run tests
    try:
        test_endpoints()
    finally:
        server_process.terminate()
        server_process.join()
