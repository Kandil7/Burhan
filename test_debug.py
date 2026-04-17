"""Start server, test query endpoint, dump all debug info."""

import subprocess
import os
import sys
import time

os.chdir(r"K:\business\projects_v2\Athar")

# Start server
print("Starting server...")
proc = subprocess.Popen(
    ["poetry", "run", "python", "-m", "uvicorn", "src.api.main:app", "--host", "127.0.0.1", "--port", "9000"],
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=True,
)

# Wait for startup
time.sleep(10)

# Make request
print("Making request...")
result = subprocess.run(
    [
        "curl",
        "-s",
        "-X",
        "POST",
        "http://127.0.0.1:9000/api/v1/query",
        "-H",
        "Content-Type: application/json",
        "-d",
        '{"query": "test"}',
    ],
    capture_output=True,
    text=True,
)
print(f"Status: {result.returncode}")
print(f"Response: {result.stdout}")
print(f"Stderr: {result.stderr}")

# Get server output
proc.terminate()
stdout, stderr = proc.communicate(timeout=5)
print("\n=== SERVER STDOUT ===")
print(stdout[-2000:] if len(stdout) > 2000 else stdout)
print("\n=== SERVER STDERR ===")
print(stderr[-2000:] if len(stderr) > 2000 else stderr)
