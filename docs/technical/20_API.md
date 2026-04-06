# 📚 Athar API Documentation

Complete API reference for the Athar Islamic QA system.

---

## 📋 Table of Contents

- [Authentication](#authentication)
- [Base URL](#base-url)
- [Error Handling](#error-handling)
- [Main Query Endpoint](#main-query-endpoint)
- [Tool Endpoints](#tool-endpoints)
- [Quran Endpoints](#quran-endpoints)
- [RAG Endpoints](#rag-endpoints)
- [Health Endpoints](#health-endpoints)
- [Rate Limiting](#rate-limiting)
- [Examples](#examples)

---

## 🔐 Authentication

**Phase 1-5:** No authentication required (development mode)

**Phase 6+ (Planned):**
```http
Authorization: Bearer <api-key>
```

---

## 🌐 Base URL

```
Development: http://localhost:8000
Production: https://api.athar.app (example)
```

All endpoints are prefixed with `/api/v1`

---

## ❌ Error Handling

### Error Response Format

```json
{
  "error": "Validation Error",
  "detail": "Query cannot be empty",
  "request_id": "uuid-string"
}
```

### HTTP Status Codes

| Code | Meaning | Example |
|------|---------|---------|
| 200 | Success | Query answered |
| 400 | Bad Request | Invalid parameters |
| 401 | Unauthorized | Invalid API key (Phase 6+) |
| 422 | Validation Error | Missing required field |
| 429 | Rate Limited | Too many requests (Phase 6+) |
| 500 | Server Error | Internal error |

---

## 🔍 Main Query Endpoint

### POST `/api/v1/query`

Main entry point for all user queries to the Athar system.

#### Request Body

```json
{
  "query": "string (required)",
  "language": "ar | en (optional, default: auto-detect)",
  "location": {
    "lat": "number (optional)",
    "lng": "number (optional)",
    "city": "string (optional)",
    "country": "string (optional)"
  },
  "madhhab": "hanafi | maliki | shafii | hanbali | auto (optional)",
  "session_id": "string (optional)",
  "stream": "boolean (optional, default: false)"
}
```

#### Response

```json
{
  "query_id": "uuid",
  "intent": "string",
  "intent_confidence": "float (0.0-1.0)",
  "answer": "string",
  "citations": [
    {
      "id": "string (C1, C2, etc.)",
      "type": "quran | hadith | fatwa | fiqh_book | dua",
      "source": "string",
      "reference": "string",
      "url": "string (optional)",
      "text_excerpt": "string (optional)"
    }
  ],
  "metadata": {
    "agent": "string",
    "processing_time_ms": "int",
    "classification_method": "keyword | llm | embedding"
  },
  "follow_up_suggestions": ["string"]
}
```

#### Example

**Request:**
```bash
curl -X POST http://localhost:8000/api/v1/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "ما حكم زكاة الأسهم؟",
    "language": "ar",
    "madhhab": "shafii"
  }'
```

**Response:**
```json
{
  "query_id": "550e8400-e29b-41d4-a716-446655440000",
  "intent": "zakat",
  "intent_confidence": 0.95,
  "answer": "زكاة الأسهم تعتمد على نوع الأسهم...",
  "citations": [
    {
      "id": "C1",
      "type": "fatwa",
      "source": "IslamWeb Fatwa",
      "reference": "Fatwa #12345",
      "url": "https://www.islamweb.net/fatwa/12345"
    }
  ],
  "metadata": {
    "agent": "zakat_tool",
    "processing_time_ms": 250
  }
}
```

---

## 🛠️ Tool Endpoints

### POST `/api/v1/tools/zakat`

Calculate zakat on wealth, gold, silver, and other assets.

#### Request

```json
{
  "assets": {
    "cash": "number",
    "gold_grams": "number",
    "silver_grams": "number",
    "trade_goods_value": "number",
    "stocks_value": "number"
  },
  "debts": "number",
  "madhhab": "hanafi | maliki | shafii | hanbali | general"
}
```

#### Response

```json
{
  "nisab": {
    "gold": "number",
    "silver": "number",
    "effective": "number"
  },
  "total_assets": "number",
  "debts_deducted": "number",
  "zakatable_wealth": "number",
  "is_zakatable": "boolean",
  "zakat_amount": "number",
  "breakdown": {
    "cash": "number",
    "gold_value": "number",
    "silver_value": "number"
  },
  "notes": ["string"],
  "references": ["string"]
}
```

---

### POST `/api/v1/tools/inheritance`

Calculate inheritance distribution based on fara'id rules.

#### Request

```json
{
  "estate_value": "number",
  "heirs": {
    "husband": "boolean",
    "wife_count": "number",
    "father": "boolean",
    "mother": "boolean",
    "sons": "number",
    "daughters": "number",
    "full_brothers": "number",
    "full_sisters": "number"
  },
  "madhhab": "hanafi | jumhur",
  "debts": "number"
}
```

#### Response

```json
{
  "distribution": [
    {
      "heir": "string",
      "fraction": "string (e.g., '1/4')",
      "percentage": "float",
      "amount": "number",
      "basis": "fard | asabah | radd"
    }
  ],
  "total_distributed": "number",
  "remaining": "number",
  "method": "standard | awl | radd",
  "school_opinion": "string (optional)",
  "notes": ["string"],
  "references": ["string"]
}
```

---

### POST `/api/v1/tools/prayer-times`

Calculate prayer times and Qibla direction for a location.

#### Request

```json
{
  "lat": "number (-90 to 90)",
  "lng": "number (-180 to 180)",
  "date": "string (YYYY-MM-DD, optional, default: today)",
  "method": "egyptian | mwl | isna | umm_al_qura | karachi | dubai"
}
```

#### Response

```json
{
  "date": "string",
  "location": {
    "lat": "number",
    "lng": "number"
  },
  "method": "string",
  "times": {
    "fajr": "string (HH:MM)",
    "sunrise": "string",
    "dhuhr": "string",
    "asr": "string",
    "maghrib": "string",
    "isha": "string"
  },
  "qibla_direction": "number (degrees from North)"
}
```

---

### POST `/api/v1/tools/hijri`

Convert between Gregorian and Hijri dates.

#### Request

```json
{
  "gregorian_date": "string (YYYY-MM-DD)",
  "hijri_year": "number (optional)",
  "hijri_month": "number (1-12, optional)",
  "hijri_day": "number (1-30, optional)"
}
```

#### Response

```json
{
  "gregorian_date": "string",
  "hijri_date": {
    "year": "number",
    "month": "number",
    "day": "number",
    "month_name_en": "string",
    "month_name_ar": "string",
    "formatted_en": "string",
    "formatted_ar": "string"
  },
  "is_ramadan": "boolean",
  "is_dhul_hijjah": "boolean",
  "is_eid": "boolean",
  "is_leap_year": "boolean",
  "special_day": {
    "name_en": "string",
    "name_ar": "string"
  }
}
```

---

### POST `/api/v1/tools/duas`

Retrieve verified duas and adhkar.

#### Request

```json
{
  "query": "string (optional)",
  "occasion": "string (optional)",
  "category": "string (optional)",
  "limit": "number (1-20, default: 5)"
}
```

#### Response

```json
{
  "duas": [
    {
      "id": "number",
      "category": "string",
      "occasion": "string",
      "arabic_text": "string",
      "translation": "string",
      "transliteration": "string",
      "source": "string",
      "reference": "string",
      "repeat_count": "number"
    }
  ],
  "count": "number",
  "sources": {
    "hisn_al_muslim": "number",
    "azkar_db": "number"
  }
}
```

---

## 📖 Quran Endpoints

### GET `/api/v1/quran/surahs`

List all 114 surahs.

#### Response

```json
[
  {
    "number": 1,
    "name_ar": "الفاتحة",
    "name_en": "Al-Fatihah",
    "verse_count": 7,
    "revelation_type": "meccan"
  }
]
```

---

### GET `/api/v1/quran/surahs/{number}`

Get details for a specific surah.

#### Response

```json
{
  "number": 1,
  "name_ar": "الفاتحة",
  "name_en": "Al-Fatihah",
  "verse_count": 7,
  "revelation_type": "meccan",
  "ayahs": [
    {
      "number": 1,
      "text_uthmani": "بِسْمِ ٱللَّهِ ٱلرَّحْمَـٰنِ ٱلرَّحِيمِ",
      "juz": 1,
      "page": 1
    }
  ]
}
```

---

### GET `/api/v1/quran/ayah/{surah}:{ayah}`

Get a specific ayah by surah:ayah reference.

#### Example

```bash
curl http://localhost:8000/api/v1/quran/ayah/2:255
```

#### Response

```json
{
  "surah_number": 2,
  "surah_name_en": "Al-Baqarah",
  "ayah_number": 255,
  "text_uthmani": "ٱللَّهُ لَآ إِلَـٰهَ إِلَّا هُوَ ٱلْحَىُّ ٱلْقَيُّومُ...",
  "text_simple": "...",
  "juz": 3,
  "page": 42,
  "quran_url": "https://quran.com/2/255",
  "translations": [
    {
      "language": "en",
      "translator": "Saheeh International",
      "text": "Allah - there is no deity except Him..."
    }
  ]
}
```

---

### POST `/api/v1/quran/search`

Search Quran verses by text.

#### Request

```json
{
  "query": "string",
  "limit": "number (1-20, default: 5)"
}
```

#### Response

```json
{
  "verses": [
    {
      "surah_number": 2,
      "surah_name_en": "Al-Baqarah",
      "ayah_number": 255,
      "text_uthmani": "...",
      "juz": 3,
      "page": 42,
      "quran_url": "https://quran.com/2/255"
    }
  ],
  "count": "number"
}
```

---

### POST `/api/v1/quran/validate`

Validate if text is from the Quran.

#### Request

```json
{
  "text": "string"
}
```

#### Response

```json
{
  "is_quran": "boolean",
  "confidence": "float (0.0-1.0)",
  "matched_ayah": {
    "surah_number": "number",
    "surah_name_en": "string",
    "ayah_number": "number",
    "text_uthmani": "string",
    "quran_url": "string"
  },
  "suggestion": "string"
}
```

---

### POST `/api/v1/quran/analytics`

Execute analytics queries on Quran data (NL2SQL).

#### Request

```json
{
  "query": "string"
}
```

#### Examples

**Query:** "كم عدد آيات سورة البقرة؟"

**Response:**
```json
{
  "sql": "SELECT verse_count FROM surahs WHERE number = 2",
  "result": [{"verse_count": 286}],
  "formatted_answer": "The answer is: 286",
  "row_count": 1
}
```

---

### GET `/api/v1/quran/tafsir/{surah}:{ayah}`

Get tafsir (commentary) for a specific ayah.

#### Response

```json
{
  "ayah": {
    "surah_number": 2,
    "ayah_number": 255,
    "text_uthmani": "..."
  },
  "tafsirs": [
    {
      "source": "ibn-kathir",
      "author": "Ismail ibn Kathir",
      "text": "...",
      "language": "ar"
    }
  ],
  "available_sources": ["ibn-kathir", "al-jalalayn"]
}
```

---

## 🧠 RAG Endpoints

### POST `/api/v1/rag/fiqh`

Ask a fiqh question with RAG retrieval.

#### Request

```json
{
  "query": "string",
  "language": "ar | en",
  "madhhab": "hanafi | maliki | shafii | hanbali",
  "top_k": "number (1-20, default: 10)"
}
```

#### Response

```json
{
  "answer": "string",
  "citations": [
    {
      "id": "C1",
      "type": "hadith",
      "source": "Sahih Bukhari",
      "reference": "Hadith #1234",
      "url": "https://sunnah.com/bukhari/1234"
    }
  ],
  "metadata": {
    "retrieved_count": 15,
    "used_count": 5,
    "collection": "fiqh_passages",
    "scores": [0.92, 0.88, 0.85, 0.82, 0.80]
  },
  "confidence": 0.85,
  "requires_human_review": false
}
```

---

### POST `/api/v1/rag/general`

Ask a general Islamic knowledge question.

#### Request

```json
{
  "query": "string",
  "language": "ar | en"
}
```

#### Response

Same format as `/rag/fiqh` but from `general_islamic` collection.

---

### GET `/api/v1/rag/stats`

Get RAG system statistics.

#### Response

```json
{
  "collections": {
    "fiqh_passages": {
      "vectors_count": 500000,
      "indexed_vectors_count": 500000
    },
    "hadith_passages": {
      "vectors_count": 50000
    }
  },
  "total_documents": 550000,
  "embedding_model": "Qwen/Qwen3-Embedding-0.5B"
}
```

---

## ❤️ Health Endpoints

### GET `/health`

Basic health check.

#### Response

```json
{
  "status": "ok",
  "version": "0.5.0",
  "services": {
    "api": "healthy",
    "postgres": "healthy",
    "redis": "healthy",
    "qdrant": "healthy"
  }
}
```

---

### GET `/ready`

Readiness probe (all dependencies OK).

#### Response

Same as `/health` but returns 503 if any dependency is down.

---

### GET `/`

Root endpoint with API information.

#### Response

```json
{
  "name": "Athar",
  "version": "0.5.0",
  "phase": "5 - Frontend & Deployment",
  "docs": "/docs",
  "health": "/health",
  "query_endpoint": "/api/v1/query",
  "quran_endpoints": {
    "surahs": "/api/v1/quran/surahs",
    "ayah": "/api/v1/quran/ayah/{surah}:{ayah}"
  },
  "tool_endpoints": {
    "zakat": "/api/v1/tools/zakat",
    "inheritance": "/api/v1/tools/inheritance"
  }
}
```

---

## 🚦 Rate Limiting

**Phase 1-5:** No rate limiting (development mode)

**Phase 6+ (Planned):**
- 100 requests/minute for free tier
- 1000 requests/minute for premium tier
- Rate limit headers in response:
  ```
  X-RateLimit-Limit: 100
  X-RateLimit-Remaining: 95
  X-RateLimit-Reset: 1234567890
  ```

---

## 📝 Examples

### Example 1: Fiqh Question

```bash
curl -X POST http://localhost:8000/api/v1/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "هل يجوز الجمع بين الصلاتين؟"
  }'
```

### Example 2: Quran Verse

```bash
curl http://localhost:8000/api/v1/quran/ayah/112:1
```

### Example 3: Zakat Calculation

```bash
curl -X POST http://localhost:8000/api/v1/tools/zakat \
  -H "Content-Type: application/json" \
  -d '{
    "assets": {
      "cash": 50000,
      "gold_grams": 100
    },
    "debts": 5000,
    "madhhab": "shafii"
  }'
```

### Example 4: Prayer Times

```bash
curl -X POST http://localhost:8000/api/v1/tools/prayer-times \
  -H "Content-Type: application/json" \
  -d '{
    "lat": 25.2854,
    "lng": 51.5310,
    "method": "egyptian"
  }'
```

---

<div align="center">

**API Version:** 0.5.0  
**Last Updated:** Phase 5 Complete  
**Interactive Docs:** http://localhost:8000/docs

</div>
