import logging
import io
import sys
from pathlib import Path

# Force override the root logger
logging.basicConfig(
    level=logging.DEBUG,
    handlers=[
        logging.FileHandler("api_test.log", encoding="utf-8"),
        logging.StreamHandler(io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")),
    ],
)

import asyncio
from fastapi.testclient import TestClient
from src.api.main import create_app


async def main():
    print("Creating app...")
    app = create_app()

    # Use test client - this triggers lifespan
    with TestClient(app) as client:
        print("Testing /classify endpoint...")
        response = client.post("/classify", json={"query": "صلاة"})
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")


if __name__ == "__main__":
    asyncio.run(main())
