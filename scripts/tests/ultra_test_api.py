
import sys
import os
from fastapi.testclient import TestClient
import json

# Add project root to path
sys.path.append(os.getcwd())

from src.api.main import app

client = TestClient(app)

def print_result(name, response, expected_status=200):
    status = response.status_code
    icon = "✅" if status == expected_status or (expected_status == "any" and status < 500) else "❌"
    print(f"{icon} {name:.<50} {status} (Expected: {expected_status})")
    if icon == "❌":
        try:
            print(f"   Response: {response.json()}")
        except:
            print(f"   Response: {response.text[:200]}")

def test_root_and_health():
    print("\n--- Testing Root & Health ---")
    print_result("GET /", client.get("/"))
    print_result("GET /health", client.get("/health"))
    print_result("GET /ready", client.get("/ready"))

def test_query():
    print("\n--- Testing Query Endpoint ---")
    # Valid query
    payload = {"query": "ما حكم صلاة الكسوف؟", "language": "ar", "madhhab": "shafii"}
    # Note: might 500 if LLM/DB not ready, but we check if it's reachable
    print_result("POST /api/v1/query (Valid)", client.post("/api/v1/query", json=payload), expected_status="any")
    
    # Invalid query (empty)
    print_result("POST /api/v1/query (Empty)", client.post("/api/v1/query", json={"query": ""}), expected_status=422)

def test_tools():
    print("\n--- Testing Tools ---")
    
    # Zakat
    zakat_payload = {
        "assets": {"cash": 10000, "gold_grams": 100},
        "debts": 1000,
        "madhhab": "hanafi"
    }
    print_result("POST /api/v1/tools/zakat", client.post("/api/v1/tools/zakat", json=zakat_payload))
    
    # Inheritance
    inheritance_payload = {
        "estate_value": 100000,
        "heirs": {"husband": False, "wife_count": 1, "sons": 2, "daughters": 1},
        "madhhab": "general",
        "debts": 0
    }
    print_result("POST /api/v1/tools/inheritance", client.post("/api/v1/tools/inheritance", json=inheritance_payload))
    
    # Prayer Times
    prayer_payload = {"lat": 30.0444, "lng": 31.2357, "method": "egyptian"}
    print_result("POST /api/v1/tools/prayer-times", client.post("/api/v1/tools/prayer-times", json=prayer_payload))
    
    # Hijri
    hijri_payload = {"gregorian_date": "2026-04-14"}
    print_result("POST /api/v1/tools/hijri", client.post("/api/v1/tools/hijri", json=hijri_payload))
    
    # Duas
    duas_payload = {"query": "سفر", "limit": 3}
    print_result("POST /api/v1/tools/duas", client.post("/api/v1/tools/duas", json=duas_payload))

def test_quran():
    print("\n--- Testing Quran Endpoints ---")
    
    print_result("GET /api/v1/quran/surahs", client.get("/api/v1/quran/surahs"))
    print_result("GET /api/v1/quran/surahs/1", client.get("/api/v1/quran/surahs/1"))
    print_result("GET /api/v1/quran/ayah/2:255", client.get("/api/v1/quran/ayah/2:255"))
    
    # Search
    print_result("POST /api/v1/quran/search", client.post("/api/v1/quran/search", json={"query": "الله لا إله إلا هو", "limit": 1}))
    
    # Validate
    print_result("POST /api/v1/quran/validate", client.post("/api/v1/quran/validate", json={"text": "الحمد لله رب العالمين"}))
    
    # Analytics
    print_result("POST /api/v1/quran/analytics", client.post("/api/v1/quran/analytics", json={"query": "كم عدد آيات سورة الكهف؟"}), expected_status="any")
    
    # Tafsir
    print_result("GET /api/v1/quran/tafsir/1:1", client.get("/api/v1/quran/tafsir/1:1"))
    print_result("GET /api/v1/quran/tafsir-sources", client.get("/api/v1/quran/tafsir-sources"))

def test_rag():
    print("\n--- Testing RAG Endpoints ---")
    
    rag_payload = {"query": "ما هي أركان الإسلام؟", "top_k": 5}
    
    # These might return 503 if torch/transformers not installed or 500 if Qdrant not running
    # But we test the endpoint existence and handling
    print_result("POST /api/v1/rag/fiqh", client.post("/api/v1/rag/fiqh", json=rag_payload), expected_status="any")
    print_result("POST /api/v1/rag/general", client.post("/api/v1/rag/general", json=rag_payload), expected_status="any")
    print_result("GET /api/v1/rag/stats", client.get("/api/v1/rag/stats"), expected_status="any")
    
    simple_rag_payload = {"query": "ما هو فضل قيام الليل؟", "collection": "general_islamic"}
    print_result("POST /api/v1/rag/simple", client.post("/api/v1/rag/simple", json=simple_rag_payload), expected_status="any")

if __name__ == "__main__":
    test_root_and_health()
    test_query()
    test_tools()
    test_quran()
    test_rag()
    print("\n--- Ultra Test Complete ---")
