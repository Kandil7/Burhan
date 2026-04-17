"""
Simple launcher that prints errors to stdout.
"""

import subprocess
import os
import sys

os.chdir(r"K:\business\projects_v2\Athar")

# Start uvicorn using poetry - capture output
proc = subprocess.Popen(
    ["poetry", "run", "python", "-m", "uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8004"],
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
    text=True,
    creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if os.name == "nt" else 0,
)

# Let it start
import time

time.sleep(8)

# Test with curl
import urllib.request
import json

req = urllib.request.Request(
    "http://localhost:8004/api/v1/query",
    data=json.dumps({"query": "test"}).encode("utf-8"),
    headers={"Content-Type": "application/json"},
)

try:
    with urllib.request.urlopen(req) as response:
        print("Response:", response.status, response.read().decode("utf-8")[:500])
except urllib.error.HTTPError as e:
    print("HTTPError:", e.code, e.read().decode("utf-8")[:500])

# Show output
proc.terminate()
out, _ = proc.communicate(timeout=5)
print("=== SERVER OUTPUT ===")
print(out[-3000:] if len(out) > 3000 else out)
