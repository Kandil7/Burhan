# 🧪 Athar API - Comprehensive Test Results & Endpoint Guide

## ✅ Infrastructure Status

| Service | Status | Port | Details |
|---------|--------|------|---------|
| **PostgreSQL** | ✅ Running | 5432 | Quran data, query logs |
| **Redis** | ✅ Running | 6379 | Cache, sessions |
| **Qdrant** | ✅ Running | 6333 | Vector embeddings |
| **Backend API** | ⚠️ Needs deps | 8000 | FastAPI application |

---

## 📋 Required Dependencies

Before starting the API, ensure these are installed:

```bash
# Core dependencies
pip install fastapi uvicorn[standard] pydantic pydantic-settings
pip install sqlalchemy asyncpg
pip install redis qdrant-client
pip install openai

# Optional (for Groq support)
pip install groq

# For embedding generation
pip install torch transformers numpy
```

**Or install all at once:**
```bash
pip install -e ".[dev,rag]"
```

---

## 🔍 Complete Endpoint Reference

### 1. Health & Info Endpoints

#### GET `/health`
**Purpose:** Check API health

**Request:**
```bash
curl http://localhost:8000/health
```

**Expected Response (200):**
```json
{
  "status": "healthy",
  "service": "athar-api",
  "version": "0.5.0",
  "timestamp": "2026-04-05T06:00:00",
  "components": {
    "postgres": "connected",
    "redis": "connected",
    "qdrant": "connected",
    "api": "running"
  }
}
```

---

#### GET `/`
**Purpose:** Root endpoint with API information

**Request:**
```bash
curl http://localhost:8000/
```

**Expected Response (200):**
```json
{
  "name": "Athar",
  "version": "0.5.0",
  "phase": "5 - Frontend & Deployment",
  "docs": "/docs",
  "health": "/health",
  "query_endpoint": "/api/v1/query",
  "tool_endpoints": {
    "zakat": "/api/v1/tools/zakat",
    "inheritance": "/api/v1/tools/inheritance"
  }
}
```

---

### 2. Main Query Endpoint

#### POST `/api/v1/query`
**Purpose:** Main entry point for all Islamic QA questions

**Request:**
```json
{
  "query": "ما حكم صلاة الجمعة؟",
  "language": "ar",
  "madhhab": "shafii"
}
```

**Expected Response (200):**
```json
{
  "query_id": "uuid-string",
  "intent": "fiqh",
  "intent_confidence": 0.92,
  "answer": "صلاة الجمعة فرض عين على كل مسلم...",
  "citations": [
    {
      "id": "C1",
      "type": "quran",
      "source": "Quran 62:9",
      "reference": "Surah Al-Jumu'ah, Ayah 9",
      "url": "https://quran.com/62/9"
    }
  ],
  "metadata": {
    "agent": "fiqh_agent",
    "processing_time_ms": 250
  }
}
```

**Test Cases:**

| Query | Expected Intent | Description |
|-------|-----------------|-------------|
| السلام عليكم | greeting | Greeting |
| ما حكم الزكاة؟ | zakat | Zakat question |
| كم عدد آيات البقرة؟ | quran | Quran question |
| أعطني دعاء السفر | dua | Dua request |
| ما حكم صلاة الجمعة؟ | fiqh | Fiqh ruling |

---

### 3. Tool Endpoints

#### POST `/api/v1/tools/zakat`
**Purpose:** Calculate zakat on wealth

**Request:**
```json
{
  "assets": {
    "cash": 50000,
    "gold_grams": 100,
    "silver_grams": 500,
    "trade_goods_value": 10000,
    "stocks_value": 20000
  },
  "debts": 5000,
  "madhhab": "shafii"
}
```

**Expected Response (200):**
```json
{
  "nisab": {
    "gold": 7500,
    "silver": 595,
    "effective": 595
  },
  "total_assets": 85000,
  "debts_deducted": 5000,
  "zakatable_wealth": 80000,
  "is_zakatable": true,
  "zakat_amount": 2000,
  "breakdown": {
    "cash": 50000,
    "gold_value": 10000,
    "silver_value": 500
  },
  "notes": [
    "Nisab calculated based on silver standard",
    "Zakat rate: 2.5%"
  ],
  "references": [
    "Quran 9:103"
  ]
}
```

---

#### POST `/api/v1/tools/prayer-times`
**Purpose:** Get prayer times for a location

**Request:**
```json
{
  "lat": 25.2854,
  "lng": 51.5310,
  "date": "2026-04-05",
  "method": "egyptian"
}
```

**Expected Response (200):**
```json
{
  "date": "2026-04-05",
  "location": {
    "lat": 25.2854,
    "lng": 51.5310,
    "city": "Doha, Qatar"
  },
  "method": "egyptian",
  "times": {
    "fajr": "04:15",
    "sunrise": "05:35",
    "dhuhr": "11:45",
    "asr": "15:10",
    "maghrib": "18:05",
    "isha": "19:35"
  },
  "qibla_direction": 275.5
}
```

---

#### POST `/api/v1/tools/hijri`
**Purpose:** Convert Gregorian to Hijri date

**Request:**
```json
{
  "gregorian_date": "2026-04-05"
}
```

**Expected Response (200):**
```json
{
  "gregorian_date": "2026-04-05",
  "hijri_date": {
    "year": 1447,
    "month": 10,
    "day": 15,
    "month_name_en": "Shawwal",
    "month_name_ar": "شوال",
    "formatted_en": "15 Shawwal 1447",
    "formatted_ar": "١٥ شوال ١٤٤٧"
  },
  "is_ramadan": false,
  "is_eid": false,
  "is_leap_year": false
}
```

---

#### POST `/api/v1/tools/duas`
**Purpose:** Retrieve verified duas

**Request:**
```json
{
  "occasion": "morning",
  "category": "adhkar",
  "limit": 3
}
```

**Expected Response (200):**
```json
{
  "duas": [
    {
      "id": 1,
      "category": "morning",
      "occasion": "أذكار الصباح",
      "arabic_text": "أَصْبَحْنَا وَأَصْبَحَ الْمُلْكُ لِلَّهِ",
      "translation": "We have reached the morning...",
      "transliteration": "Asbahna wa asbahal mulku lillah",
      "source": "Hisn al-Muslim",
      "reference": "Book 1, Hadith 1",
      "repeat_count": 1
    }
  ],
  "count": 3
}
```

---

#### POST `/api/v1/tools/inheritance`
**Purpose:** Calculate inheritance distribution

**Request:**
```json
{
  "estate_value": 100000,
  "heirs": {
    "husband": true,
    "father": true,
    "mother": true,
    "sons": 1,
    "daughters": 1
  },
  "debts": 5000,
  "madhhab": "hanafi"
}
```

**Expected Response (200):**
```json
{
  "distribution": [
    {
      "heir": "Husband",
      "fraction": "1/4",
      "percentage": 25.0,
      "amount": 25000,
      "basis": "fard"
    },
    {
      "heir": "Mother",
      "fraction": "1/6",
      "percentage": 16.67,
      "amount": 16670,
      "basis": "fard"
    }
  ],
  "total_distributed": 95000,
  "remaining": 0,
  "method": "standard",
  "notes": [
    "Estate after debts: 95,000",
    "Distribution according to Hanafi school"
  ]
}
```

---

### 4. Quran Endpoints

#### GET `/api/v1/quran/surahs`
**Purpose:** List all 114 surahs

**Expected Response (200):**
```json
[
  {
    "number": 1,
    "name_ar": "الفاتحة",
    "name_en": "Al-Fatihah",
    "verse_count": 7,
    "revelation_type": "meccan"
  },
  {
    "number": 2,
    "name_ar": "البقرة",
    "name_en": "Al-Baqarah",
    "verse_count": 286,
    "revelation_type": "medinan"
  }
]
```

---

#### GET `/api/v1/quran/surahs/{number}`
**Purpose:** Get specific surah details

**Example:** `/api/v1/quran/surahs/1`

**Expected Response (200):**
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

#### GET `/api/v1/quran/ayah/{surah}:{ayah}`
**Purpose:** Get specific ayah

**Example:** `/api/v1/quran/ayah/2:255` (Ayat al-Kursi)

**Expected Response (200):**
```json
{
  "surah_number": 2,
  "surah_name_en": "Al-Baqarah",
  "ayah_number": 255,
  "text_uthmani": "ٱللَّهُ لَآ إِلَـٰهَ إِلَّا هُوَ...",
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

#### POST `/api/v1/quran/search`
**Purpose:** Search Quran verses

**Request:**
```json
{
  "query": "رحمة",
  "limit": 5
}
```

**Expected Response (200):**
```json
{
  "verses": [
    {
      "surah_number": 1,
      "ayah_number": 1,
      "text_uthmani": "بِسْمِ ٱللَّهِ ٱلرَّحْمَـٰنِ ٱلرَّحِيمِ",
      "juz": 1,
      "quran_url": "https://quran.com/1/1"
    }
  ],
  "count": 5
}
```

---

#### POST `/api/v1/quran/validate`
**Purpose:** Validate if text is from Quran

**Request:**
```json
{
  "text": "بسم الله الرحمن الرحيم"
}
```

**Expected Response (200):**
```json
{
  "is_quran": true,
  "confidence": 1.0,
  "matched_ayah": {
    "surah_number": 1,
    "ayah_number": 1,
    "text_uthmani": "بِسْمِ ٱللَّهِ ٱلرَّحْمَـٰنِ ٱلرَّحِيمِ",
    "quran_url": "https://quran.com/1/1"
  }
}
```

---

#### POST `/api/v1/quran/analytics`
**Purpose:** NL2SQL analytics on Quran

**Request:**
```json
{
  "query": "كم عدد آيات سورة البقرة؟"
}
```

**Expected Response (200):**
```json
{
  "sql": "SELECT verse_count FROM surahs WHERE number = 2",
  "result": [{"verse_count": 286}],
  "formatted_answer": "The answer is: 286",
  "row_count": 1
}
```

---

#### GET `/api/v1/quran/tafsir/{surah}:{ayah}`
**Purpose:** Get tafsir for ayah

**Example:** `/api/v1/quran/tafsir/1:1`

**Expected Response (200):**
```json
{
  "ayah": {
    "surah_number": 1,
    "ayah_number": 1,
    "text_uthmani": "بِسْمِ ٱللَّهِ ٱلرَّحْمَـٰنِ ٱلرَّحِيمِ"
  },
  "tafsirs": [
    {
      "source": "ibn-kathir",
      "author": "Ismail ibn Kathir",
      "text": "قال ابن كثير...",
      "language": "ar"
    }
  ]
}
```

---

### 5. RAG Endpoints

#### POST `/api/v1/rag/fiqh`
**Purpose:** Fiqh question with RAG retrieval

**Request:**
```json
{
  "query": "ما حكم صلاة الجماعة؟",
  "language": "ar",
  "madhhab": "hanafi"
}
```

**Expected Response (200):**
```json
{
  "answer": "صلاة الجماعة سنة مؤكدة...",
  "citations": [
    {
      "id": "C1",
      "type": "hadith",
      "source": "Sahih Bukhari",
      "reference": "Hadith #647"
    }
  ],
  "metadata": {
    "retrieved_count": 15,
    "used_count": 5,
    "collection": "fiqh_passages",
    "scores": [0.92, 0.88, 0.85]
  },
  "confidence": 0.88,
  "requires_human_review": false
}
```

---

#### POST `/api/v1/rag/general`
**Purpose:** General Islamic knowledge

**Request:**
```json
{
  "query": "من هو عمر بن الخطاب؟",
  "language": "ar"
}
```

**Expected Response (200):**
```json
{
  "answer": "عمر بن الخطاب هو ثاني الخلفاء الراشدين...",
  "citations": [...],
  "confidence": 0.85
}
```

---

#### GET `/api/v1/rag/stats`
**Purpose:** RAG system statistics

**Expected Response (200):**
```json
{
  "collections": {
    "fiqh_passages": {
      "vectors_count": 114316,
      "indexed_vectors_count": 114316
    }
  },
  "total_documents": 115316,
  "embedding_model": "Qwen/Qwen3-Embedding-0.5B"
}
```

---

## 🧪 Quick Test Script

Save this as `quick_test.sh` or run manually:

```bash
#!/bin/bash
BASE_URL="http://localhost:8000"

echo "Testing Athar API..."

# Test 1: Health
echo -e "\n1. Health Check:"
curl -s $BASE_URL/health | jq .

# Test 2: Query
echo -e "\n2. Greeting Query:"
curl -s -X POST $BASE_URL/api/v1/query \
  -H "Content-Type: application/json" \
  -d '{"query": "السلام عليكم", "language": "ar"}' | jq .

# Test 3: Zakat
echo -e "\n3. Zakat Calculator:"
curl -s -X POST $BASE_URL/api/v1/tools/zakat \
  -H "Content-Type: application/json" \
  -d '{"assets": {"cash": 50000}, "debts": 5000}' | jq .

# Test 4: Prayer Times
echo -e "\n4. Prayer Times:"
curl -s -X POST $BASE_URL/api/v1/tools/prayer-times \
  -H "Content-Type: application/json" \
  -d '{"lat": 25.2854, "lng": 51.5310}' | jq .

# Test 5: Quran Surahs
echo -e "\n5. List Surahs:"
curl -s $BASE_URL/api/v1/quran/surahs | jq '.[0:2]'

echo -e "\n✓ Tests complete!"
```

---

## ✅ Success Criteria

| Endpoint | Expected Status | Key Fields |
|----------|----------------|------------|
| GET /health | 200 | status, version, components |
| GET / | 200 | name, version, docs |
| POST /api/v1/query | 200 | query_id, intent, answer |
| POST /api/v1/tools/zakat | 200 | is_zakatable, zakat_amount |
| POST /api/v1/tools/prayer-times | 200 | times, qibla_direction |
| POST /api/v1/tools/hijri | 200 | hijri_date |
| POST /api/v1/tools/duas | 200 | duas, count |
| POST /api/v1/tools/inheritance | 200 | distribution |
| GET /api/v1/quran/surahs | 200 | Array of 114 surahs |
| GET /api/v1/quran/ayah/2:255 | 200 | text_uthmani, quran_url |
| POST /api/v1/quran/search | 200 | verses, count |
| POST /api/v1/quran/validate | 200 | is_quran, confidence |
| POST /api/v1/quran/analytics | 200 | sql, result |
| GET /api/v1/quran/tafsir/1:1 | 200 | ayah, tafsirs |
| POST /api/v1/rag/fiqh | 200 | answer, citations |
| POST /api/v1/rag/general | 200 | answer, citations |
| GET /api/v1/rag/stats | 200 | collections, total_documents |

---

**Total Endpoints: 19**  
**All endpoints documented with request/response examples** ✅
