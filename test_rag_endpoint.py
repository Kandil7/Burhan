"""Test the simple RAG endpoint directly."""
import asyncio
import httpx
import json

async def test():
    url = "http://localhost:8002/api/v1/rag/simple"
    payload = {
        "query": "what is islam",
        "collection": "general_islamic",
        "language": "en",
        "top_k": 5
    }
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            response = await client.post(url, json=payload)
            print(f"Status: {response.status_code}")
            print(f"Response: {json.dumps(response.json(), indent=2)}")
        except Exception as e:
            print(f"Exception: {e}")

if __name__ == "__main__":
    asyncio.run(test())
