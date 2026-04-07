# API Reference - Complete Endpoint Documentation

## Table of Contents

1. [Query Endpoints](#query-endpoints)
2. [Quran Endpoints](#quran-endpoints)
3. [Tool Endpoints](#tool-endpoints)
4. [RAG Endpoints](#rag-endpoints)
5. [Health Endpoints](#health-endpoints)
6. [Schemas](#schemas)

---

# 1. Query Endpoints

## POST /api/v1/query

Main query endpoint for the Islamic QA system.

### Request Body

```json
{
    "query": "string (required)",
    "language": "ar | en | both (default: ar)",
    "madhhab": "hanafi | maliki | shafii | hanbali | general (optional)",
    "location": {
        "latitude": -90 to 90,
        "longitude": -180 to 180,
        "city": "string (optional)",
        "country": "string (optional)"
    },
    "session_id": "string (optional)"
}
```

### Response

```json
{
    "query_id": "uuid",
    "intent": "fiqh | quran | islamic_knowledge | greeting | ...",
    "intent_confidence": 0.0 to 1.0,
    "answer": "string",
    "citations": [
        {
            "id": "C1",
            "type": "quran | hadith | fatwa | fiqh_book | dua",
            "source": "string",
            "reference": "string",
            "url": "string (optional)",
            "text_excerpt": "string (optional)"
        }
    ],
    "metadata": {
        "agent": "string",
        "processing_time_ms": 1234,
        "classification_method": "keyword | llm | embedding"
    },
    "follow_up_suggestions": ["string"]
}
```

### Examples

**Arabic Fiqh Query:**
```bash
curl -X POST http://localhost:8000/api/v1/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "ما حكم زكاة الذهب؟",
    "language": "ar",
    "madhhab": "hanafi"
  }'
```

**English General Query:**
```bash
curl -X POST http://localhost:8000/api/v1/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Who was Abu Bakr?",
    "language": "en"
  }'
```

**Zakat Calculation:**
```bash
curl -X POST http://localhost:8000/api/v1/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Calculate zakat on 50000 SAR cash and 100g gold"
  }'
```

---

# 2. Quran Endpoints

## GET /api/v1/quran/surahs

List all 114 surahs.

### Response

```json
[
    {
        "number": 1,
        "name_ar": "الفاتحة",
        "name_en": "Al-Fatiha",
        "verse_count": 7,
        "revelation_type": "Meccan"
    },
    ...
]
```

## GET /api/v1/quran/surahs/{surah_number}

Get details for a specific surah.

### Response

```json
{
    "number": 1,
    "name_ar": "الفاتحة",
    "name_en": "Al-Fatiha",
    "verse_count": 7,
    "revelation_type": "Meccan",
    "ayahs": [
        {
            "number": 1,
            "text_uthmani": "بِسْمِ اللَّهِ الرَّحْمَنِ الرَّحِيمِ",
            "juz": 1,
            "page": 1
        },
        ...
    ]
}
```

## GET /api/v1/quran/ayah/{surah}:{ayah}

Get a specific ayah.

### Parameters

- `surah`: Surah number (1-114)
- `ayah`: Ayah number in surah

### Response

```json
{
    "surah_number": 2,
    "surah_name_en": "Al-Baqarah",
    "ayah_number": 255,
    "text_uthmani": "اللَّهُ لَا إِلَهَ إِلَّا هُوَ الْحَيُّ الْقَيُّومُ...",
    "juz": 3,
    "page": 42,
    "quran_url": "https://quran.com/2:255",
    "translations": [
        {"language": "en", "text": "Allah - there is no deity except Him..."},
        {"language": "ar", "text": "الله لا إله إلا هو الحي القيوم..."}
    ]
}
```

## POST /api/v1/quran/search

Search Quran verses by text.

### Request

```json
{
    "query": "string",
    "limit": 5
}
```

### Response

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
            "quran_url": "https://quran.com/2:255"
        }
    ],
    "count": 1
}
```

## POST /api/v1/quran/analytics

Execute natural language queries on Quran data.

### Request

```json
{
    "query": "كم عدد آيات سورة البقرة؟"
}
```

### Response

```json
{
    "sql": "SELECT verse_count FROM surahs WHERE number = 2",
    "result": [{"verse_count": 286}],
    "formatted_answer": "سورة البقرة فيها 286 آية",
    "row_count": 1
}
```

### Example Queries

| Query | SQL |
|-------|-----|
| كم عدد آيات سورة البقرة؟ | SELECT verse_count FROM surahs WHERE number = 2 |
| ما أطول سورة؟ | SELECT name_en, verse_count FROM surahs ORDER BY verse_count DESC LIMIT 1 |
| كم سورة مكية؟ | SELECT COUNT(*) FROM surahs WHERE revelation_type = 'Meccan' |
| كم سورة مدنية؟ | SELECT COUNT(*) FROM surahs WHERE revelation_type = 'Medinan' |

## GET /api/v1/quran/tafsir/{surah}:{ayah}

Get tafsir for specific ayah.

### Query Parameters

- `source`: Tafsir source (ibn-kathir, al-jalalayn, al-qurtubi)

### Response

```json
{
    "ayah": {...},
    "tafsirs": [
        {
            "source": "ibn-kathir",
            "text": "تفسير ابن كثير..."
        }
    ],
    "available_sources": ["ibn-kathir", "al-jalalayn"]
}
```

## POST /api/v1/quran/validate

Validate if text is from the Quran.

### Request

```json
{
    "text": "إن الله على كل شيء قدير"
}
```

### Response

```json
{
    "is_quran": true,
    "confidence": 0.98,
    "matched_ayah": {
        "surah_number": 2,
        "surah_name_en": "Al-Baqarah",
        "ayah_number": 284,
        "text_uthmani": "إِنَّ اللَّهَ عَلَى كُلِّ شَيْءٍ قَدِيرٌ"
    },
    "suggestion": null
}
```

## GET /api/v1/quran/tafsir-sources

List available tafsir sources.

### Response

```json
[
    {
        "source": "ibn-kathir",
        "name": "Tafsir Ibn Kathir",
        "language": "ar",
        "description": "..."
    }
]
```

---

# 3. Tool Endpoints

## POST /api/v1/tools/zakat

Calculate Zakat on wealth.

### Request

```json
{
    "assets": {
        "cash": 50000,
        "bank_accounts": 10000,
        "gold_grams": 100,
        "silver_grams": 500,
        "trade_goods_value": 0,
        "stocks_value": 0,
        "receivables": 0
    },
    "debts": 5000,
    "madhhab": "hanafi"
}
```

### Response

```json
{
    "nisab_gold": 6375,
    "nisab_silver": 535.5,
    "nisab_effective": 535.5,
    "total_assets": 59100,
    "debts_deducted": 5000,
    "zakatable_wealth": 54100,
    "is_zakatable": true,
    "zakat_amount": 1352.5,
    "breakdown": {
        "cash": 60000,
        "gold_value": 7500,
        "silver_value": 450,
        "trade_goods": 0,
        "stocks": 0,
        "receivables": 0,
        "other": 0
    },
    "madhhab": "hanafi",
    "gold_price_per_gram": 75,
    "silver_price_per_gram": 0.9,
    "notes": [
        "Your wealth (54100) exceeds the nisab threshold (535.5). Zakat is due at 2.5%."
    ],
    "references": [
        "Quran 9:103",
        "Hadith: No zakat is due until one year passes"
    ]
}
```

## POST /api/v1/tools/inheritance

Calculate inheritance distribution.

### Request

```json
{
    "estate_value": 100000,
    "heirs": {
        "husband": true,
        "wife_count": 0,
        "father": false,
        "mother": true,
        "sons": 2,
        "daughters": 1
    },
    "madhhab": "general",
    "debts": 5000,
    "wasiyyah": 0
}
```

### Response

```json
{
    "distribution": [
        {
            "heir_name": "Husband",
            "fraction": "1/4",
            "percentage": 25,
            "amount": 23750,
            "basis": "fard",
            "notes": "Quran 4:12"
        },
        {
            "heir_name": "Mother",
            "fraction": "1/3",
            "percentage": 33.33,
            "amount": 31666.67,
            "basis": "fard",
            "notes": "Quran 4:11"
        },
        {
            "heir_name": "Son's",
            "fraction": "2/3",
            "percentage": 28.89,
            "amount": 27444.44,
            "basis": "asabah",
            "notes": "Residuary heir (2:1 ratio with 1 daughter)"
        }
    ],
    "total_distributed": 95000,
    "remaining": 0,
    "method": "standard",
    "estate_value": 95000,
    "total_heirs": 4,
    "notes": [
        "This is a mathematical calculation based on fara'id rules.",
        "Consult a qualified scholar for complex cases."
    ],
    "references": [
        "Quran 4:11-12",
        "Sahih Bukhari - Kitab al-Fara'id"
    ]
}
```

## GET /api/v1/tools/prayer-times

Get prayer times for location.

### Query Parameters

- `latitude`: -90 to 90 (required)
- `longitude`: -180 to 180 (required)
- `date`: YYYY-MM-DD (optional, default: today)
- `method`: MWL, ISNA, Egypt, Makkah, Karachi, Tehran (optional)

### Response

```json
{
    "location": {
        "latitude": 21.4858,
        "longitude": 39.1925,
        "city": "Mecca",
        "country": "Saudi Arabia"
    },
    "date": "2024-01-15",
    "times": {
        "fajr": "05:15",
        "sunrise": "06:38",
        "dhuhr": "12:23",
        "asr": "15:47",
        "maghrib": "18:03",
        "isha": "19:28"
    },
    "qibla": {
        "direction": 95,
        "latitude": 21.4858,
        "longitude": 39.1925
    },
    "method": "MWL"
}
```

## GET /api/v1/tools/hijri

Get Hijri date.

### Query Parameters

- `gregorian_date`: YYYY-MM-DD (optional)
- `hijri_year`: 1-1500 (optional)
- `hijri_month`: 1-12 (optional)
- `hijri_day`: 1-30 (optional)

### Response

```json
{
    "gregorian": {
        "date": "2024-01-15",
        "weekday": "Monday"
    },
    "hijri": {
        "year": 1445,
        "month": 6,
        "month_name": "Jumada al-Thani",
        "day": 15,
        "weekday": "Al-Ahad"
    },
    "events": [],
    "special_dates": []
}
```

## GET /api/v1/tools/duas

Get duas and adhkar.

### Query Parameters

- `category`: morning, evening, prayer, sleep, travel, general (optional)
- `limit`: 1-50 (optional)

### Response

```json
{
    "duas": [
        {
            "id": 1,
            "arabic_text": "بِسْمِ اللَّهِ الرَّحْمَنِ الرَّحِيمِ",
            "transliteration": "Bismillah al-Rahman al-Rahim",
            "translation": "In the name of Allah, the Most Gracious, the Most Merciful",
            "source": "Quran 1:1",
            "category": "general"
        }
    ],
    "count": 1
}
```

---

# 4. RAG Endpoints

## POST /api/v1/rag/query

Direct RAG query without intent classification.

### Request

```json
{
    "query": "ما حكم الصلاة؟",
    "collection": "fiqh_passages",
    "top_k": 5
}
```

### Response

```json
{
    "answer": "الصلاة...",
    "passages": [
        {
            "content": "...",
            "score": 0.92,
            "metadata": {
                "source": "Islamic Fiqh",
                "madhhab": "hanafi"
            }
        }
    ],
    "total_passages": 5
}
```

## GET /api/v1/rag/stats

Get RAG collection statistics.

### Response

```json
{
    "collections": {
        "fiqh_passages": {
            "vectors_count": 1500,
            "status": "ready"
        },
        "general_islamic": {
            "vectors_count": 800,
            "status": "ready"
        }
    }
}
```

---

# 5. Health Endpoints

## GET /health

Basic health check.

### Response

```json
{
    "status": "healthy",
    "version": "0.5.0"
}
```

## GET /health/ready

Readiness check with dependency status.

### Response

```json
{
    "status": "ready",
    "checks": {
        "database": "connected",
        "redis": "connected",
        "qdrant": "connected",
        "llm": "available"
    }
}
```

---

# 6. Schemas

## Request Schemas

### QueryRequest
```python
class QueryRequest(BaseModel):
    query: str = Field(min_length=1, max_length=1000)
    language: str = Field(default="ar")
    madhhab: Optional[str] = Field(default=None, max_length=20)
    session_id: Optional[str] = Field(default=None, max_length=100)
    location: Optional[LocationInput] = None
```

### ZakatRequest
```python
class ZakatRequest(BaseModel):
    assets: ZakatAssetsInput
    debts: float = Field(ge=0)
    madhhab: str = Field(default="general")
```

### InheritanceRequest
```python
class InheritanceRequest(BaseModel):
    estate_value: float = Field(gt=0)
    heirs: HeirsInput
    madhhab: str = Field(default="general")
    debts: float = Field(ge=0, default=0)
    wasiyyah: float = Field(ge=0, default=0)
```

## Response Schemas

### QueryResponse
```python
class QueryResponse(BaseModel):
    query_id: str
    intent: str
    intent_confidence: float
    answer: str
    citations: list[CitationResponse]
    metadata: dict
    follow_up_suggestions: list[str]
```

### CitationResponse
```python
class CitationResponse(BaseModel):
    id: str  # C1, C2, etc.
    type: str  # quran, hadith, fatwa, fiqh_book, dua
    source: str
    reference: str
    url: Optional[str]
    text_excerpt: Optional[str]
```

---

# Error Codes

| Code | Description | HTTP Status |
|------|-------------|-------------|
| VALIDATION_ERROR | Invalid input data | 400 |
| NOT_FOUND | Resource not found | 404 |
| AUTH_REQUIRED | API key required | 401 |
| AUTH_INVALID | Invalid API key | 403 |
| RATE_LIMIT_EXCEEDED | Too many requests | 429 |
| PROCESSING_ERROR | Error processing request | 500 |
| EXTERNAL_SERVICE_ERROR | External service error | 502 |

---

*Last Updated: April 2026*
*Version: 0.5.0*
