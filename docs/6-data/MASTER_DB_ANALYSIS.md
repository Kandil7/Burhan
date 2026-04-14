# 🔍 MASTER.DB & COVER.DB — Complete Analysis Report

**Date:** April 7, 2026  
**Files Analyzed:** 
- `datasets/system_book_datasets/master.db` (Version 6)
- `datasets/system_book_datasets/cover.db` (Version 1)

---

## 📊 Executive Summary

**master.db is the PRIMARY metadata source.** It contains the complete catalog of 8,425 books with full structured metadata including categories, authors, death years, PDF links, and hierarchical relationships. This is the definitive source that was missing — it maps every book ID to its category, author, and rich metadata.

---

## 1. MASTER.DB — Full Schema Analysis

### 1.1 Tables Overview

| Table | Rows | Purpose |
|-------|------|---------|
| `book` | **8,425** | All books in the library |
| `category` | **41** (+ 1 special `#`) | Book categories |
| `author` | **3,146** | All authors |
| `author_book` | **8,465** | Book → Author mapping (main) |
| `coauthor_book` | **53** | Book → Co-author mapping |
| `version` | **5** | Component version tracking |
| `db_ver` | **1** | Database version (6) |

### 1.2 `book` Table Schema (24 columns)

```sql
CREATE TABLE book (
    book_id INTEGER PRIMARY KEY,      -- Unique book ID (1..151203)
    book_name TEXT,                    -- Full Arabic title
    book_category INTEGER,             -- FK → category.category_id
    book_type INTEGER,                 -- Type: 1=main, 2=supplement, 3=collection, 4=article, 5=series, 6=lecture
    book_date INTEGER,                 -- Author death year (Hijri) or 99999=unknown
    authors TEXT,                      -- Author ID string
    main_author INTEGER,               -- FK → author.author_id
    printed INTEGER,                   -- 1=printed/published, 3=manuscript
    group_id INTEGER,                  -- Edition group ID
    hidden INTEGER,                    -- 0=visible
    major_online INTEGER,              -- Online availability flag
    minor_online INTEGER,
    major_ondisk INTEGER,              -- On-disk availability flag
    minor_ondisk INTEGER,
    pdf_links TEXT,                    -- JSON: {"files": [...], "cover": N, "size": N, "root": "..."}
    pdf_ondisk INTEGER,
    pdf_online INTEGER,
    cover_ondisk INTEGER,              -- Cover image on disk
    cover_online INTEGER,              -- Cover image online
    meta_data TEXT,                    -- JSON: {"date": "DDMMYYYY", "group": N, "prefix": "...", "suffix": "...", "coauthor": [...], "shorts": {...}}
    parent INTEGER,                    -- FK → book.book_id (for sub-books/chapters)
    alpha INTEGER,                     -- Alphabetical sort order
    group_order INTEGER,
    book_up INTEGER                    -- Last update timestamp
);
```

### 1.3 `category` Table — ALL 41 Categories

| ID | Arabic Name | English Translation | Books |
|----|-------------|-------------------|-------|
| 1 | العقيدة | Creed/Aqeedah | 794 |
| 2 | الفرق والردود | Sects & Refutations | 151 |
| 3 | التفسير | Quranic Exegesis (Tafsir) | 270 |
| 4 | علوم القرآن وأصول التفسير | Quran Sciences & Tafsir Principles | 308 |
| 5 | التجويد والقراءات | Tajweed & Quran Recitations | 147 |
| 6 | كتب السنة | Hadith Collections | **1,226** |
| 7 | شروح الحديث | Hadith Commentaries | 262 |
| 8 | التخريج والأطراف | Hadith Grading & References | 123 |
| 9 | العلل والسؤلات الحديثية | Hadith Defects & Q&A | 74 |
| 10 | علوم الحديث | Hadith Sciences | 315 |
| 11 | أصول الفقه | Usul al-Fiqh (Jurisprudence Principles) | 247 |
| 12 | علوم الفقه والقواعد الفقهية | Fiqh Sciences & Legal Maxims | 55 |
| 13 | المنطق | Logic | 11 |
| 14 | الفقه الحنفي | Hanafi Fiqh | 83 |
| 15 | الفقه المالكي | Maliki Fiqh | 85 |
| 16 | الفقه الشافعي | Shafi'i Fiqh | 86 |
| 17 | الفقه الحنبلي | Hanbali Fiqh | 147 |
| 18 | الفقه العام | General Fiqh | 204 |
| 19 | مسائل فقهية | Fiqh Issues | 420 |
| 20 | السياسة الشرعية والقضاء | Islamic Governance & Judiciary | 100 |
| 21 | الفرائض والوصايا | Inheritance & Wills | 28 |
| 22 | الفتاوى | Fatwas | 64 |
| 23 | الرقائق والآداب والأذكار | Spiritual Softeners & Supplications | 619 |
| 24 | السيرة النبوية | Prophet's Biography (Seerah) | 184 |
| 25 | التاريخ | History | 188 |
| 26 | التراجم والطبقات | Biographies & Generations | 556 |
| 27 | الأنساب | Genealogy | 52 |
| 28 | البلدان والرحلات | Geography & Travel | 92 |
| 29 | كتب اللغة | Language Books | 79 |
| 30 | الغريب والمعاجم | Rare Words & Dictionaries | 129 |
| 31 | النحو والصرف | Grammar & Morphology | 212 |
| 32 | الأدب | Literature | 415 |
| 33 | العروض والقوافي | Prosody & Rhyme | 9 |
| 34 | الدواوين الشعرية | Poetry Collections | 25 |
| 35 | البلاغة | Rhetoric | 35 |
| 36 | الجوامع | Compilations/Anthologies | 135 |
| 37 | فهارس الكتب والأدلة | Book Indexes & References | 100 |
| 38 | الطب | Medicine | 14 |
| 39 | كتب عامة | General Books | 355 |
| 40 | علوم أخرى | Other Sciences | 26 |
| 42 | # | (Special/uncategorized) | 0 |

**Note:** Category 41 does NOT exist — it jumps from 40 to 42 (which is a placeholder `#`).

### 1.4 `author` Table Schema

```sql
CREATE TABLE author (
    author_id INTEGER PRIMARY KEY,    -- Unique author ID
    author_name TEXT,                  -- Full Arabic name
    death_number INTEGER,             -- Death year (Hijri). 99999 = unknown/alive
    death_text TEXT,                   -- Death year as text
    alpha INTEGER                      -- Alphabetical sort order
);
```

**Key findings:**
- 3,146 authors, ALL of them have at least one book
- Death years range from **-81** (pre-Islamic poets like امرؤ القيس) to **1440** (recent scholars)
- `99999` = unknown or living author (used for modern scholars like سعيد بن وهف القحطاني d.1440)
- Some authors have "مجموعة من المؤلفين" (Group of Authors) as name

### 1.5 Relationship Tables

**`author_book`** (8,465 rows) — Main author-to-book mapping:
```sql
(author_id INTEGER, book_id INTEGER)
```

**`coauthor_book`** (53 rows) — Co-author mapping:
```sql
(author_id INTEGER, book_id INTEGER)
```

### 1.6 `meta_data` JSON Field

Contains structured metadata as JSON:
- `date`: Publication/upload date (DDMMYYYY format, e.g., "08121431")
- `group`: Group ID for edition grouping
- `prefix`: Title prefix (for multi-edition books)
- `suffix`: Title suffix (e.g., "ط 4" = 4th edition)
- `coauthor`: Array of co-author IDs
- `shorts`: Short reference names

### 1.7 `pdf_links` JSON Field

Contains PDF download information:
```json
{
  "files": ["https://archive.org/download/41557/41557.pdf"],
  "cover": 2,
  "size": 1445468
}
```
or for multi-volume books:
```json
{
  "cover": 1,
  "root": "https://archive.org/download/02-171742/",
  "files": ["00_171741.pdf|#2", "01_171741.pdf|#2", ...],
  "size": 88024687
}
```

- **1,377 books** have PDF links
- **957 books** have cover images (cover_online=1 AND cover_ondisk=1)
- **7,011 books** are marked as `printed=1`
- **84 books** have parent relationships (sub-books/chapters)

### 1.8 Book Types

| Type | Count | Likely Meaning |
|------|-------|----------------|
| 1 | 7,170 (85%) | Main/complete books |
| 2 | 320 | Supplements/Addenda |
| 3 | 7 | Collections/Anthologies |
| 4 | 95 | Articles/Research papers |
| 5 | 536 | Series parts |
| 6 | 297 | Lectures/Duroos |

---

## 2. COVER.DB — Analysis

### 2.1 Schema

```sql
CREATE TABLE cover (id INTEGER PRIMARY KEY, cover BLOB);
CREATE TABLE db_ver (value INTEGER);  -- Version: 1
```

### 2.2 Key Findings

- **1,004 cover images** stored as BLOBs
- Cover sizes range from ~15KB to ~51KB (likely JPEG/PNG images)
- IDs are sparse (not sequential: 1, 3, 9, 10, 11, 14, 17...)
- The `id` maps to the `cover` field in `pdf_links` JSON (not book_id)
- **957 books** reference covers, but only 1,004 exist in cover.db

**Cover Reference Mapping:**
- Books with `pdf_links` contain `"cover": N` where N is the cover.db `id`
- Books with `cover_online=1` AND `cover_ondisk=1` = 957 have covers

---

## 3. Cross-Reference with books.json

### 3.1 books.json Structure

```json
{
  "total": 8425,
  "extracted": 8423,
  "generated": "2026-03-24T18:46:57.714030",
  "books": [
    {
      "id": 1,
      "guid": "ace0dc28-7030-5890-8962-fdaf7a448647",
      "short_id": "6B86B2",
      "title": "الفواكه العذاب...",
      "cat_id": 1,
      "cat_name": "العقيدة",
      "type": 1,
      "date": 1225,
      "author_str": "513",
      "extracted": true,
      "file": "1_الفواكه_العذاب...txt",
      "size_mb": 0.196,
      "authors": [
        {
          "id": 513,
          "guid": "...",
          "name": "حمد بن ناصر آل معمر",
          "death": 1225,
          "role": "main"
        }
      ]
    }
  ]
}
```

### 3.2 What books.json has that master.db does NOT:
- ✅ `guid` (UUID v5)
- ✅ `short_id` (6-char hash)
- ✅ `file` (extracted .txt filename)
- ✅ `size_mb` (file size in MB)
- ✅ `extracted` (boolean flag)
- ✅ Denormalized `authors` array with full details

### 3.3 What master.db has that books.json does NOT:
- ✅ `pdf_links` (Archive.org URLs)
- ✅ `group_id` and edition grouping
- ✅ `parent` (hierarchical book relationships)
- ✅ Availability flags (major_online, minor_online, pdf_ondisk, etc.)
- ✅ `meta_data` with publication dates, prefixes, suffixes
- ✅ `printed` flag (published vs manuscript)
- ✅ `coauthor_book` for co-authored works
- ✅ `alpha` and `group_order` for sorting
- ✅ All 41 categories with ordering
- ✅ Author `alpha` sort values

### 3.4 What they SHARE:
- ✅ book_id (same IDs)
- ✅ book_name / title (same)
- ✅ book_category / cat_id (same)
- ✅ category_name / cat_name (same)
- ✅ book_type / type (same)
- ✅ book_date / date (same)
- ✅ main_author / author_str (same author IDs)
- ✅ author death years (same values)

---

## 4. Category Mapping: 41 → 11

master.db contains all **41 original categories**. The mapping to 11 consolidated categories must be applied externally. Here's the recommended mapping:

| Consolidated Category | master.db category_ids | Book Count |
|----------------------|----------------------|------------|
| **العقيدة والفرق** (Creed & Sects) | 1, 2 | 945 |
| **القرآن وعلومه** (Quran & Sciences) | 3, 4, 5 | 725 |
| **الحديث وعلومه** (Hadith & Sciences) | 6, 7, 8, 9, 10 | 2,000 |
| **الفقه وأصوله** (Fiqh & Principles) | 11, 12, 14, 15, 16, 17, 18, 19, 20, 21, 22 | 1,638 |
| **السيرة والتاريخ** (Seerah & History) | 24, 25, 26, 27 | 1,084 |
| **اللغة والأدب** (Language & Literature) | 29, 30, 31, 32, 33, 34, 35 | 1,304 |
| **الرقائق والآداب** (Spirituality & Manners) | 23 | 619 |
| **البلدان والجغرافيا** (Geography & Travel) | 28 | 92 |
| **الطب والعلوم** (Medicine & Sciences) | 13, 38, 40 | 51 |
| **كتب عامة وفهارس** (General & Indexes) | 36, 37, 39 | 590 |
| **المنطق** (Logic) | 13 | 11 |

---

## 5. Complete Extraction Strategy

### 5.1 Primary Data Sources

```
master.db (PRIMARY)
  ├── book (8,425 records) — Core book metadata
  ├── category (41 records) — Category names & order
  ├── author (3,146 records) — Author names & death years
  ├── author_book (8,465 records) — Book→Author mapping
  └── coauthor_book (53 records) — Co-author mapping

cover.db (SECONDARY)
  └── cover (1,004 BLOBs) — Cover images

Lucene indexes (CONTENT)
  └── book/*.db — Full text content per book
```

### 5.2 Recommended Extraction Pipeline

```python
import sqlite3
import json

# 1. Load master metadata
master = sqlite3.connect('system_book_datasets/master.db')

# 2. Build complete book catalog with all metadata
query = """
SELECT 
    b.book_id,
    b.book_name as title,
    c.category_id,
    c.category_name,
    b.book_type,
    b.book_date as author_death_year,
    b.main_author as author_id,
    a.author_name,
    a.death_number,
    b.pdf_links,
    b.meta_data,
    b.printed,
    b.parent,
    b.group_id,
    b.major_online,
    b.cover_online
FROM book b
JOIN category c ON b.book_category = c.category_id
LEFT JOIN author a ON b.main_author = a.author_id
ORDER BY b.book_id
"""

# 3. For co-authored books, join coauthor_book
coauthors_query = """
SELECT ab.book_id, GROUP_CONCAT(ar.author_name, '; ') as coauthors
FROM coauthor_book ab
JOIN author ar ON ab.author_id = ar.author_id
GROUP BY ab.book_id
"""

# 4. Load cover images (if needed)
covers = sqlite3.connect('system_book_datasets/cover.db')
cover_query = "SELECT id, cover FROM cover WHERE id = ?"
```

### 5.3 Can master.db replace books.json?

**Yes, with enhancements.** master.db is the MORE authoritative source because:
1. It's the application's native database (version 6, actively maintained)
2. It has PDF links, edition info, and hierarchical relationships
3. books.json was extracted FROM master.db (same 8,425 total, 8,423 extracted)
4. The GUIDs and short_ids in books.json can be regenerated from master.db data

**books.json adds:** file paths to extracted .txt files and sizes — these are computed during extraction, not from the source.

### 5.4 Recommended Unified Data Model

```json
{
  "id": 1,
  "title": "الفواكه العذاب...",
  "category": {
    "id": 1,
    "name": "العقيدة",
    "consolidated": "العقيدة والفرق"
  },
  "type": 1,
  "author": {
    "id": 513,
    "name": "حمد بن ناصر آل معمر",
    "death_year": 1225
  },
  "coauthors": [],
  "pdf_links": {
    "files": ["https://archive.org/..."],
    "cover_id": 2,
    "size": 1445468
  },
  "meta": {
    "date": "08121431",
    "printed": true,
    "parent_id": null,
    "group_id": null
  },
  "extracted": {
    "file": "1_title.txt",
    "size_mb": 0.196,
    "guid": "...",
    "short_id": "6B86B2"
  }
}
```

---

## 6. Key Answers to Original Questions

| Question | Answer |
|----------|--------|
| Can master.db link book IDs to categories? | ✅ YES — `book.book_category → category.category_id` |
| Can it provide missing metadata? | ✅ YES — Has death years, types, PDF links, editions |
| Does it have 41→11 mapping built-in? | ❌ NO — Has 41 categories; mapping must be applied |
| Does it have author death years? | ✅ YES — `author.death_number` (Hijri years) |
| Does it have book editions? | ✅ YES — `group_id`, `meta_data` with prefix/suffix |
| Can we use it as PRIMARY source? | ✅ YES — It IS the primary source |
| Can we join with Lucene indexes? | ✅ YES — `book_id` is the join key |
| Can we replace books.json? | ✅ YES — master.db is more authoritative |
| Does it have all 8,425/8,427 books? | ✅ YES — 8,425 records (matches books.json total) |

---

## 7. SQL Quick Reference

```sql
-- Get complete book info with author and category
SELECT b.book_id, b.book_name, c.category_name, a.author_name, a.death_number
FROM book b
JOIN category c ON b.book_category = c.category_id
JOIN author a ON b.main_author = a.author_id
WHERE b.book_id = ?;

-- Get all books by an author
SELECT b.book_id, b.book_name, c.category_name
FROM book b
JOIN category c ON b.book_category = c.category_id
WHERE b.main_author = ?;

-- Get books in a category
SELECT b.book_id, b.book_name, a.author_name
FROM book b
JOIN author a ON b.main_author = a.author_id
WHERE b.book_category = ?;

-- Get co-authored books
SELECT b.book_id, b.book_name, GROUP_CONCAT(a.author_name, ', ')
FROM book b
JOIN coauthor_book cb ON b.book_id = cb.book_id
JOIN author a ON cb.author_id = a.author_id
GROUP BY b.book_id;

-- Get books with PDF links
SELECT book_id, book_name, pdf_links
FROM book
WHERE pdf_links IS NOT NULL;

-- Get books with parent (chapters/sub-books)
SELECT b.book_id, b.book_name, p.book_name as parent_name
FROM book b
JOIN book p ON b.parent = p.book_id;
```

---

## 8. Data Quality Notes

1. **Author death year `99999`** = Unknown or living (used for modern editors/compilers)
2. **`printed` field**: 1 = Published/printed, 3 = Manuscript
3. **`hidden` field**: Always 0 in current data (no hidden books)
4. **Category 41 doesn't exist** — jumps from 40 to 42 (`#`)
5. **Book IDs are sparse**: Max is 151,203 but only 8,425 records exist
6. **Cover IDs are sparse**: 1,004 covers for 8,425 books (only 957 books have covers)
7. **`meta_data.coauthor`** array exists in some records — these should be cross-referenced with `coauthor_book`
8. **`authors` field** in book table appears to be the same as `main_author` (string representation)
