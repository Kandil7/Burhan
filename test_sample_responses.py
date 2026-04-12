#!/usr/bin/env python3
"""Capture detailed sample responses from key endpoints."""
import json
import urllib.request

BASE = "http://localhost:8002"

def get(method, path, data=None):
    url = f"{BASE}{path}"
    if data:
        req = urllib.request.Request(url, method=method, data=json.dumps(data).encode('utf-8'), headers={'Content-Type': 'application/json'})
    else:
        req = urllib.request.Request(url, method=method)
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.loads(r.read().decode('utf-8'))
    except urllib.error.HTTPError as e:
        body = e.read()
        return {"_error": e.code, "_detail": json.loads(body.decode()) if body else str(e)}

print("="*70)
print("SAMPLE RESPONSES FROM KEY ENDPOINTS")
print("="*70)

samples = {
    "1. HEALTH": get("GET", "/health"),
    "2. QUERY - Fiqh": get("POST", "/api/v1/query", {"query": "ما حكم الزكاة"}),
    "3. QUERY - Greeting": get("POST", "/api/v1/query", {"query": "مرحبا"}),
    "4. ZAKAT - Cash": get("POST", "/api/v1/tools/zakat", {"assets": {"cash": 10000}}),
    "5. ZAKAT - Gold (100g)": get("POST", "/api/v1/tools/zakat", {"assets": {"gold_grams": 100}}),
    "6. INHERITANCE": get("POST", "/api/v1/tools/inheritance", {"estate_value": 100000, "heirs": {"sons": 2, "wife_count": 1}}),
    "7. PRAYER TIMES": get("POST", "/api/v1/tools/prayer-times", {"lat": 21.4225, "lng": 39.8262, "method": "MWL"}),
    "8. HIJRI DATE": get("POST", "/api/v1/tools/hijri", {"gregorian_date": "2026-04-12"}),
    "9. DUA": get("POST", "/api/v1/tools/duas", {"category": "morning"}),
    "10. SURAHS (first 2)": get("GET", "/api/v1/quran/surahs")[:2],
    "11. SURAHA 1": get("GET", "/api/v1/quran/surahs/1"),
    "12. AYAH 1:1": get("GET", "/api/v1/quran/ayah/1:1"),
    "13. SEARCH رحمة (first 2)": get("POST", "/api/v1/quran/search", {"query": "رحمة"}).get("verses", [])[:2],
    "14. VALIDATE": get("POST", "/api/v1/quran/validate", {"text": "بسم الله الرحمن الرحيم"}),
    "15. NL2SQL": get("POST", "/api/v1/quran/analytics", {"query": "How many surahs are there?"}),
    "16. TAFSIR 1:1": get("GET", "/api/v1/quran/tafsir/1:1"),
    "17. RAG Fiqh": get("POST", "/api/v1/rag/fiqh", {"query": "ما هو حكم الصلاة؟"}),
    "18. RAG General": get("POST", "/api/v1/rag/general", {"query": "ما هي أركان الإسلام؟"}),
    "19. RAG Stats": get("GET", "/api/v1/rag/stats"),
}

for name, body in samples.items():
    print(f"\n{'='*70}")
    print(f"{name}")
    print(f"{'='*70}")
    print(json.dumps(body, indent=2, ensure_ascii=False)[:800])
