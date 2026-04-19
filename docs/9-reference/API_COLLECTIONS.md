# Athar API - Collection Endpoints

## Overview

This document describes the API endpoints for the Multi-Agent Collection-Aware RAG system.

---

## Endpoints Summary

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/fiqh/answer` | POST | Fiqh-specific query answering with verification |
| `/ask` | POST | General query answering with routing |
| `/classify` | POST | Intent classification only |
| `/search` | POST | Search operations |
| `/quran/validate` | POST | Quran quotation validation |

---

## 1. Fiqh Answer Endpoint

### POST `/fiqh/answer`

Answer Islamic jurisprudence questions with full verification pipeline.

#### Request

```bash
curl -X POST "http://localhost:8000/fiqh/answer" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your_api_key" \
  -d '{
    "query": "ما حكم ترك صلاة الجمعة عمداً؟",
    "language": "ar",
    "madhhab": "hanafi"
  }'
```

#### Request Body

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `query` | string | Yes | The question in Arabic or English |
| `language` | string | No | Output language (default: "ar") |
| `madhhab` | string | No | Preferred madhhab: "hanafi", "maliki", "shafi", "hanbali" |

#### Query Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `author` | string | Filter by author name |
| `era` | string | Filter by era: "prophetic", "tabiun", "classical", "medieval", "ottoman", "modern" |
| `book_id` | int | Filter by book ID |

#### Response

```json
{
  "answer": "حرام على المكلف الذي mampu...",
  "citations": [
    {
      "id": "C1",
      "type": "fiqh_book",
      "source": "الهداية",
      "reference": "المرغيناني - ت 593 هـ - ص 120",
      "url": null,
      "text_excerpt": "فمن ترك الجمعة..."
    }
  ],
  "confidence": 0.95,
  "ikhtilaf_detected": true,
  "metadata": {
    "intent": "fiqh_hukm",
    "collection": "fiqh",
    "retrieved": 80,
    "verified": 5,
    "is_verified": true,
    "verification_confidence": 0.9,
    "verification_issues": []
  },
  "trace_id": "550e8400-e29b-41d4-a716-446655440000",
  "processing_time_ms": 150
}
```

#### Response Fields

| Field | Type | Description |
|-------|------|-------------|
| `answer` | string | Generated answer |
| `citations` | array | List of citation objects |
| `confidence` | float | Overall confidence (0-1) |
| `ikhtilaf_detected` | boolean | Whether Islamic school differences detected |
| `metadata` | object | Agent metadata |
| `trace_id` | string | Unique trace ID |
| `processing_time_ms` | int | Processing time in milliseconds |

#### Error Responses

**422 Validation Error**
```json
{
  "error": "ValidationError",
  "message": "Query is required",
  "trace_id": "..."
}
```

**500 Internal Error**
```json
{
  "error": "InternalError",
  "message": "Internal server error while processing the query",
  "trace_id": "..."
}
```

---

## 2. General Ask Endpoint

### POST `/api/v1/ask`

General query answering with automatic intent classification and routing.

```bash
curl -X POST "http://localhost:8000/api/v1/ask" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your_api_key" \
  -d '{
    "query": "ما حكم الزكاة؟",
    "language": "ar"
  }'
```

#### Request Body

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `query` | string | Yes | The question |
| `language` | string | No | Output language (default: "ar") |
| `madhhab` | string | No | Preferred madhhab |

#### Query Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `author` | string | Filter by author |
| `era` | string | Filter by era |
| `book_id` | int | Filter by book ID |
| `category` | string | Filter by category |
| `hierarchical` | boolean | Enable hierarchical retrieval |

---

## 3. Classification Endpoint

### POST `/classify`

Classify query intent without answering.

```bash
curl -X POST "http://localhost:8000/classify" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "ما صحة حديث إنما الأعمال بالنية"
  }'
```

#### Response

```json
{
  "intent": "hadith",
  "confidence": 0.92,
  "method": "keyword_fast_path",
  "language": "ar",
  "requires_retrieval": true
}
```

---

## 4. Search Endpoint

### POST `/api/v1/search`

Search across all collections.

```bash
curl -X POST "http://localhost:8000/api/v1/search" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "صلاة الجماعة",
    "collection": "fiqh",
    "top_k": 10
  }'
```

---

## 5. Quran Validation

### POST `/quran/validate`

Validate if a text is a real Quran verse.

```bash
curl -X POST "http://localhost:8000/quran/validate" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "بسم الله الرحمن الرحيم"
  }'
```

#### Response

```json
{
  "is_valid": true,
  "surah": "الفاتحة",
  "ayah_start": 1,
  "ayah_end": 1,
  "confidence": 0.98
}
```

---

## Tools Endpoints

### Zakat Calculator

**POST** `/api/v1/tools/zakat`

```json
{
  "gold_grams": 100,
  "silver_grams": 0,
  "cash_amount": 10000,
  "business_assets": 50000,
  "agricultural_products": 0
}
```

### Inheritance Calculator

**POST** `/api/v1/tools/inheritance`

```json
{
  "deceased_male": true,
  "heirs": [
    {"type": "wife", "count": 1},
    {"type": "son", "count": 2},
    {"type": "daughter", "count": 1}
  ]
}
```

### Prayer Times

**POST** `/api/v1/tools/prayer-times`

```json
{
  "latitude": 24.7136,
  "longitude": 46.6753,
  "date": "2024-01-15"
}
```

### Hijri Calendar

**POST** `/api/v1/tools/hijri`

```json
{
  "gregorian_date": "2024-01-15"
}
```

### Duas Retrieval

**POST** `/api/v1/tools/duas`

```json
{
  "occasion": "morning",
  "language": "ar"
}
```

---

## Authentication

All endpoints require `X-API-Key` header:

```bash
-H "X-API-Key: your_api_key"
```

---

## Rate Limiting

- Default: 60 requests per minute
- Configurable via `RATE_LIMIT_RPM` environment variable

---

## Response Codes

| Code | Description |
|------|-------------|
| 200 | Success |
| 400 | Bad Request |
| 401 | Unauthorized |
| 422 | Validation Error |
| 500 | Internal Server Error |
| 504 | Timeout |

---

## SDK Examples

### Python

```python
import requests

url = "http://localhost:8000/fiqh/answer"
headers = {"X-API-Key": "your_key", "Content-Type": "application/json"}
data = {"query": "ما حكم الزكاة؟", "language": "ar"}

response = requests.post(url, json=data, headers=headers)
result = response.json()

print(result["answer"])
print(result["citations"])
```

### JavaScript

```javascript
const response = await fetch("http://localhost:8000/fiqh/answer", {
  method: "POST",
  headers: {
    "Content-Type": "application/json",
    "X-API-Key": "your_key"
  },
  body: JSON.stringify({
    query: "ما حكم الزكاة؟",
    language: "ar"
  })
});

const result = await response.json();
console.log(result.answer);
```

---

## Error Handling

Always check for errors in responses:

```python
if response.status_code == 200:
    result = response.json()
else:
    error = response.json()
    print(f"Error: {error['message']}")
```

---

## See Also

- [Phase 10 Index](./PHASE10_INDEX.md) - Navigation guide
- [Multi-Agent Architecture](./MULTI_AGENT_COLLECTION_ARCHITECTURE.md) - Main architecture
- [Retrieval Strategies](./RETRIEVAL_STRATEGIES.md) - Retrieval configuration
- [Verification Framework](./VERIFICATION_FRAMEWORK.md) - Verification system
- [Orchestration Patterns](./ORCHESTRATION_PATTERNS.md) - Multi-agent patterns