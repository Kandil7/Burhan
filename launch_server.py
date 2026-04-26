"""
Simple launcher script to start the API server with verbose logging.
"""

import subprocess
import os

os.chdir(r"K:\business\projects_v2\Burhan")

# Set debug logging
env = os.environ.copy()
env["LOG_LEVEL"] = "DEBUG"
env["LOG_FORMAT"] = "json"

# Start uvicorn using poetry
proc = subprocess.Popen(
    [
        "poetry",
        "run",
        "python",
        "-m",
        "uvicorn",
        "src.api.main:app",
        "--host",
        "0.0.0.0",
        "--port",
        "8003",
        "--log-level",
        "debug",
    ],
    env=env,
    creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if os.name == "nt" else 0,
)
print(f"Started server with PID: {proc.pid}")
print("Waiting for startup...")
import time

time.sleep(6)
print("Server should be running on http://localhost:8003")
print(f"STDOUT PID: {proc.pid}")
