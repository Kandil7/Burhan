# 📖 Burhan Quran Pipeline Guide

Complete guide to the Quran processing system in Burhan.

---

## 📋 Table of Contents

- [Overview](#overview)
- [Quran Database](#quran-database)
- [Verse Retrieval](#verse-retrieval)
- [NL2SQL Engine](#nl2sql-engine)
- [Quotation Validation](#quotation-validation)
- [Tafsir Retrieval](#tafsir-retrieval)
- [Named Verses](#named-verses)
- [Data Ingestion](#data-ingestion)
- [API Endpoints](#api-endpoints)
- [Examples](#examples)

---

## 🎯 Overview

The Quran Pipeline provides comprehensive Quran-related functionality:
- Exact verse lookup (2:255 format)
- Natural language analytics (NL2SQL)
- Quotation validation
- Tafsir retrieval
- Named verse support

---

## 🗄️ Quran Database

### Schema

**Tables:**

| Table | Rows | Purpose |
|-------|------|---------|
| `surahs` | 114 | Chapter metadata |
| `ayahs` | 6,236 | Verse text and metadata |
| `translations` | 20k+ | Multi-language translations |
| `tafsirs` | 50k+ | Scholarly commentaries |

### Surahs Table

```sql
CREATE TABLE surahs (
    id SERIAL PRIMARY KEY,
    number INT UNIQUE,           -- 1-114
    name_ar VARCHAR(100),        -- البقرة
    name_en VARCHAR(100),        -- Al-Baqarah
    verse_count INT,             -- 286
    revelation_type VARCHAR(7)   -- meccan/medinan
);
```

### Ayahs Table

```sql
CREATE TABLE ayahs (
    id SERIAL PRIMARY KEY,
    surah_id INT REFERENCES surahs(id),
    number_in_surah INT,         -- 1, 2, 3...
    text_uthmani TEXT,           -- Uthmani script
    text_simple TEXT,            -- Simplified text
    juz INT,                     -- 1-30
    page INT,                    -- 1-604
    UNIQUE(surah_id, number_in_surah)
);

-- Full-text search index
CREATE INDEX idx_ayah_text_search ON ayahs 
    USING GIN (to_tsvector('simple', text_uthmani));
```

---

## 🔍 Verse Retrieval

### Supported Input Formats

| Format | Example | Description |
|--------|---------|-------------|
| Number | `2:255` | Surah:Ayah |
| Arabic Name | `البقرة 255` | Surah name + number |
| English Name | `Al-Baqarah 255` | English name + number |
| Named Verse | `Ayat al-Kursi` | Common names |
| Fuzzy Search | `لا يكلف الله` | Partial text |

### Usage

```python
from src.quran.verse_retrieval import VerseRetrievalEngine

engine = VerseRetrievalEngine(session)

# Number format
verse = await engine.lookup("2:255")

# Arabic name
verse = await engine.lookup("البقرة 255")

# Named verse
verses = await engine.lookup("Ayat al-Kursi")

# Fuzzy search
results = await engine.search_verses("رحمة", limit=5)
```

### Response Format

```json
{
  "surah_number": 2,
  "surah_name_ar": "البقرة",
  "surah_name_en": "Al-Baqarah",
  "ayah_number": 255,
  "text_uthmani": "ٱللَّهُ لَآ إِلَـٰهَ إِلَّا هُوَ...",
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

## 💻 NL2SQL Engine

### Purpose

Convert natural language questions to SQL queries for analytics.

### Supported Query Types

| Query Type | Example | SQL |
|------------|---------|-----|
| Verse Count | "كم عدد آيات سورة البقرة؟" | `SELECT verse_count FROM surahs WHERE number = 2` |
| Longest Surah | "ما أطول سورة؟" | `SELECT name_en FROM surahs ORDER BY verse_count DESC LIMIT 1` |
| Meccan Count | "كم سورة مكية؟" | `SELECT COUNT(*) FROM surahs WHERE revelation_type = 'meccan'` |
| Word Frequency | "كم مرة ذُكرت رحمة؟" | `SELECT COUNT(*) FROM ayahs WHERE text_uthmani LIKE '%رحمة%'` |

### Usage

```python
from src.quran.nl2sql import NL2SQLEngine

engine = NL2SQLEngine(session)

result = await engine.execute("كم عدد آيات سورة البقرة؟")

print(result["sql"])
print(result["formatted_answer"])
```

### Security

**SQL Validation:**
```python
def _validate_sql(self, sql: str):
    # Only SELECT allowed
    if not sql.strip().upper().startswith("SELECT"):
        raise NL2SQLQueryError("Only SELECT queries allowed")
    
    # Block dangerous keywords
    dangerous = ["DROP", "DELETE", "INSERT", "UPDATE"]
    if any(kw in sql.upper() for kw in dangerous):
        raise NL2SQLQueryError("Query contains forbidden keywords")
```

---

## ✅ Quotation Validation

### Purpose

Verify if user-provided text is actually from the Quran.

### Process

1. Normalize Arabic text (remove diacritics, standardize letters)
2. Search in Quran corpus
3. Calculate similarity score
4. Return match or rejection

### Usage

```python
from src.quran.quotation_validator import QuotationValidator

validator = QuotationValidator(session)

result = await validator.validate("بسم الله الرحمن الرحيم")

print(result["is_quran"])  # True
print(result["confidence"])  # 1.0
print(result["matched_ayah"])  # Surah 1, Ayah 1
```

### Response

```json
{
  "is_quran": true,
  "confidence": 1.0,
  "matched_ayah": {
    "surah_number": 1,
    "surah_name_en": "Al-Fatihah",
    "ayah_number": 1,
    "text_uthmani": "بِسْمِ ٱللَّهِ ٱلرَّحْمَـٰنِ ٱلرَّحِيمِ",
    "quran_url": "https://quran.com/1/1"
  },
  "suggestion": null
}
```

---

## 📚 Tafsir Retrieval

### Supported Sources

| Source | Author | Language |
|--------|--------|----------|
| Ibn Kathir | Ismail ibn Kathir | Arabic |
| Al-Jalalayn | Al-Mahalli & As-Suyuti | Arabic |
| Al-Qurtubi | Abu 'Abdullah Al-Qurtubi | Arabic |

### Usage

```python
from src.quran.tafsir_retrieval import TafsirRetrievalEngine

engine = TafsirRetrievalEngine(session)

# Get specific tafsir
tafsir = await engine.get_tafsir("2:255", source="ibn-kathir")

# Get all available tafsirs
tafsir = await engine.get_tafsir("2:255")

# Search tafsir
results = await engine.search_tafsir("توحيد", limit=5)
```

---

## ⭐ Named Verses

### Database

**File:** `src/quran/named_verses.json`

```json
{
  "ayat_al_kursi": {
    "surah": 2,
    "ayah": 255,
    "name_ar": "آية الكرسي",
    "name_en": "Ayat al-Kursi"
  },
  "ayat_ad_dayn": {
    "surah": 2,
    "ayah": 282,
    "name_ar": "آية الدين",
    "name_en": "Ayat ad-Dayn"
  },
  "al_fatihah": {
    "surah": 1,
    "ayah_range": [1, 7],
    "name_ar": "الفاتحة",
    "name_en": "Al-Fatihah"
  }
}
```

### Supported Named Verses

| Name | Surah | Ayah(s) |
|------|-------|---------|
| Ayat al-Kursi | 2 | 255 |
| Ayat ad-Dayn | 2 | 282 |
| Al-Fatihah | 1 | 1-7 |
| Al-Ikhlas | 112 | 1-4 |
| Al-Falaq | 113 | 1-5 |
| An-Nas | 114 | 1-6 |
| Al-Asr | 103 | 1-3 |
| Al-Kawthar | 108 | 1-3 |
| Ar-Rahman | 55 | 1-78 |
| Yasin | 36 | 1-83 |
| Al-Mulk | 67 | 1-30 |

---

## 📥 Data Ingestion

### From Quran.com API

```bash
python scripts/seed_quran_data.py --source api
```

**Process:**
1. Fetch surahs from API
2. For each surah, fetch ayahs page by page
3. Insert ayahs with metadata
4. Insert translations
5. Verify counts (114 surahs, 6,236 ayahs)

### From Local JSON

```bash
python scripts/seed_quran_data.py --source json --file data/seed/quran_full.json
```

### Sample Data

```bash
python scripts/seed_quran_data.py --sample
```

Loads 4 complete surahs for testing:
- Al-Fatihah (7 ayahs)
- Al-Ikhlas (4 ayahs)
- Al-Falaq (5 ayahs)
- An-Nas (6 ayahs)

---

## 🌐 API Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/v1/quran/surahs` | GET | List all 114 surahs |
| `/api/v1/quran/surahs/{number}` | GET | Surah details |
| `/api/v1/quran/ayah/{surah}:{ayah}` | GET | Specific ayah |
| `/api/v1/quran/search` | POST | Verse search |
| `/api/v1/quran/validate` | POST | Quotation validation |
| `/api/v1/quran/analytics` | POST | NL2SQL queries |
| `/api/v1/quran/tafsir/{surah}:{ayah}` | GET | Tafsir retrieval |

---

## 📝 Examples

### Example 1: Get Ayat al-Kursi

```bash
curl http://localhost:8000/api/v1/quran/ayah/2:255
```

### Example 2: Search for "Mercy"

```bash
curl -X POST http://localhost:8000/api/v1/quran/search \
  -H "Content-Type: application/json" \
  -d '{"query": "رحمة", "limit": 5}'
```

### Example 3: Validate Quran Quote

```bash
curl -X POST http://localhost:8000/api/v1/quran/validate \
  -H "Content-Type: application/json" \
  -d '{"text": "بسم الله الرحمن الرحيم"}'
```

### Example 4: NL2SQL Analytics

```bash
curl -X POST http://localhost:8000/api/v1/quran/analytics \
  -H "Content-Type: application/json" \
  -d '{"query": "كم عدد آيات سورة البقرة؟"}'
```

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

<div align="center">

**Quran Pipeline Version:** 1.0  
**Last Updated:** Phase 3 Complete  
**Status:** Production-Ready

</div>
