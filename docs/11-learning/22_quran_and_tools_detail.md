# 📖 Master Class: The Quranic Engine & Deterministic Tools

## 🕌 Introduction
This document provides a line-by-line and logic-deep-dive into the Quranic processing pipeline and the deterministic Islamic calculators. These components are unique because they rely on **Exact Truth** rather than LLM inference.

---

## 📁 src/quran/ - The Divine Pipeline

### 1. `src/quran/verse_retrieval.py`
**Purpose**: The primary engine for finding Quranic text. It supports named verses (Ayat al-Kursi), numeric refs (2:255), and fuzzy text matching.

**Deep Logic**:
- **Named Verse Resolution**: Uses `named_verses.json` with a 4-pass priority lookup (Exact Key -> Exact Alias -> Partial Key -> Partial Alias).
- **Number Normalization**: Handles Arabic-Indic digits (١٢٣) by converting them to ASCII (123) before DB query.
- **Search Tiers**: 
    - *Tier 1*: SQL `LIKE` on `text_simple` (diacritic-free).
    - *Tier 2*: Python-side normalized scan using `SequenceMatcher` for maximum fuzzy precision.

**Key File Interaction**: Uses `joinedload(Ayah.surah)` to prevent N+1 query problems when fetching surah names.

### 2. `src/quran/nl2sql.py`
**Purpose**: Converts "How many verses in Surah Baqarah?" into `SELECT verse_count FROM surahs WHERE number = 2`.

**Deep Logic**:
- **Security (SQL Injection)**: Implements a strict `_FORBIDDEN_SQL` regex that blocks `UNION`, `EXEC`, `--`, and `;`.
- **Extraction Priority**: Surah name lookup happens *before* digit extraction to avoid confusing page numbers or Juz numbers in the query with surah numbers.
- **Few-Shot Prompting**: Uses `SCHEMA_CONTEXT` to teach the LLM exactly what columns are available, ensuring the generated SQL is valid for our PostgreSQL schema.

### 3. `src/quran/quotation_validator.py`
**Purpose**: Validates if a user's text is a real Quranic quote.

**Deep Logic**:
- **Normalization Engine**: Strips all *Tashkeel* (diacritics), unifies all Alef variants (إأآ), and unifies Ya (ى -> ي) to create a "searchable base".
- **Fragment Matching**: Specifically designed to catch partial verses, common in user queries.
- **Fuzzy Threshold**: Defaults to `0.85` similarity. Anything above is considered a match, preventing "False Quran" attribution.

---

## 📁 src/tools/ - Deterministic Logic

### 1. `src/tools/zakat_calculator.py`
**Purpose**: Precise mathematical calculation of Zakat based on current gold/silver prices.

**Mathematical Logic**:
- **Nisab Calculation**: `85g * gold_price` vs `595g * silver_price`.
- **Effective Nisab**: Uses the *lower* of the two (default) to maximize benefit for the poor, as per many scholarly opinions.
- **Livestock Logic**: Implements the fixed-rate tables from *Sahih Bukhari* (e.g., 5 camels = 1 sheep, 25 camels = 1 Bint Makhad).
- **Crops Logic**: Checks `irrigation_type`. 10% for natural (rain) vs 5% for artificial irrigation, based on the Hadith: "What the heavens water is a tenth...".

### 2. `src/tools/inheritance_calculator.py`
**Purpose**: Implementation of *Fara'id* (Islamic Inheritance Law).

**Algorithmic Logic**:
- **Exact Arithmetic**: Uses Python's `fractions.Fraction` to avoid floating-point errors (e.g., `1/3 + 1/6` is exactly `1/2`).
- **The 'Awl (Reduction)**: If the sum of shares > 1, it automatically increases the common denominator proportionally.
- **The Radd (Redistribution)**: If sum < 1 and no residuaries (*Asabah*), it redistributes the remainder to the fixed-share heirs.
- **Blocking Rules**: Complex hierarchy where sons block grandsons, and fathers block brothers.

---

## 📊 Summary of File Responsibilities

| File | Core Logic | Data Source |
|------|------------|-------------|
| `verse_retrieval.py` | Named/Numeric Lookup | PostgreSQL (`ayahs`, `surahs`) |
| `nl2sql.py` | NLP to SQL Mapping | LLM + Schema Definition |
| `quotation_validator.py` | Fuzzy String Alignment | PostgreSQL (`text_simple`) |
| `zakat_calculator.py` | Rate-based math | Metal Price APIs |
| `inheritance_calculator.py` | Fractional Algebra | Quran 4:11-12 |

---

**Next:** Doc 23 will cover the Infrastructure and Knowledge facades.
