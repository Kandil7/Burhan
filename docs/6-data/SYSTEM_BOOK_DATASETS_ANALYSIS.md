# System Book Datasets - Comprehensive Analysis Report

**Date:** April 7, 2026  
**Source:** Shamela Islamic Library Software Databases  
**Location:** `K:\business\projects_v2\Burhan\datasets\system_book_datasets`

---

## 1. DIRECTORY STRUCTURE

### Overview
```
system_book_datasets/
├── book/           # 8,427 individual book databases (671.8 MB)
│   ├── 000/        # Category 000
│   ├── 001/        # Category 001
│   ├── ...
│   └── 999/        # Category 999
├── service/        # 5 service databases (148.0 MB)
│   ├── hadeeth.db  # Hadith cross-references (1.8 MB)
│   ├── tafseer.db  # Tafsir cross-references (3.2 MB)
│   ├── trajim.db   # Biographical entries (0.0 MB - empty)
│   ├── S1.db       # Metadata/links database (34.6 MB)
│   └── S2.db       # Arabic morphological roots (108.2 MB)
├── store/          # Lucene search indexes (13.7 GB)
│   ├── page/       # Main content index (13.2 GB)
│   ├── title/      # Title index (56 MB)
│   ├── author/     # Author index (1.9 MB)
│   ├── esnad/      # Hadith chain index (0.5 MB)
│   ├── aya/        # Quran verse index
│   ├── book/       # Book index
│   ├── s_author/   # Author search index
│   └── s_book/     # Book search index
├── update/         # Update tracking
└── user/           # User data (bookmarks, history)
    └── data.db     # User preferences (124 KB)
```

### Key Statistics
- **Total .db files:** 8,432
- **Total book databases:** 8,427 (organized in 1,000 categories: 000-999)
- **Total size:** ~14.4 GB
  - Book databases: 671.8 MB
  - Service databases: 148.0 MB
  - Lucene indexes: 13.7 GB
- **Categories:** 1,000 (000-999), likely representing book types/genres

### Database Naming Pattern
- **Book databases:** `{book_id}.db` stored in `book/{category_id}/`
  - Example: `book/001/1001.db` = Book ID 1001, Category 001
- **Category assignment:** Book ID modulo 1000 determines category folder
  - Book 1001 → category 001
  - Book 22002 → category 002
  - Book 37004 → category 004

---

## 2. DATABASE SCHEMA ANALYSIS

### Book Databases (8,427 files)
**Consistent schema across all book databases:**

#### `page` table
| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Page sequence number (1, 2, 3, ...) |
| part | TEXT | Volume/part number (usually "1") |
| page | INTEGER | Page number within the book |
| number | NULL | Always NULL (unused) |
| services | NULL | Always NULL (unused) |

**Sample data:**
```
id=1, part="1", page=1, number=NULL, services=NULL
id=2, part="1", page=2, number=NULL, services=NULL
```

#### `title` table
| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Title/section ID |
| page | INTEGER | Page number where title appears |
| parent | INTEGER | Parent title ID (0 = root, >0 = child) |

**Title hierarchy example:**
```
id=1, page=1, parent=0     ← Root title (chapter)
id=2, page=1, parent=1     ← Child of title 1
id=3, page=10, parent=1    ← Child of title 1
id=5, page=17, parent=0    ← Another root title
id=6, page=19, parent=5    ← Child of title 5
```

**Title depth distribution (varies by book):**
- Simple books: 1 level (root + children)
- Complex books: 2-3 levels (root → chapter → section → subsection)

### Service Databases

#### `hadeeth.db` (1.8 MB)
**Tables:**
- `db_ver`: Database version (value=1)
- `inservice`: 10 hadith book IDs marked as active
- `service`: 37,076 mappings linking hadith to book pages

**Service table schema:**
| Column | Type | Description |
|--------|------|-------------|
| key_id | INTEGER | Hadith identifier |
| book_id | INTEGER | Book containing this hadith |
| page_id | INTEGER | Page number in the book |

**Purpose:** Cross-references hadith mentions across books. Multiple books can reference the same hadith (key_id).

**Sample relationships:**
```
key_id=323, book_id=28107, page_id=421
key_id=323, book_id=28107, page_id=422
key_id=1030, book_id=711, page_id=234  ← Hadith 1030 appears 115 times across books
```

#### `tafseer.db` (3.2 MB)
**Tables:** Same structure as hadeeth.db
- `service`: 65,964 mappings linking Quran verses to tafsir content

**Key ID range:** 1 to 6,236 (likely maps to 6,236 Quran verse groups)

**Sample:**
```
key_id=1, book_id=23619, page_id=10   ← Verse 1 in tafsir book 23619, page 10
key_id=2, book_id=23619, page_id=10   ← Verse 2 in same location
key_id=8, book_id=23619, page_id=17   ← Verse 8 on page 17
```

#### `S2.db` - Arabic Morphological Roots (108.2 MB)
**Table: `roots`**
| Column | Type | Description |
|--------|------|-------------|
| token | BLOB | Arabic word form (Windows-1256 encoded) |
| root | BLOB | Root letters (Windows-1256 encoded) |

**Statistics:**
- **Total entries:** 3,249,267
- **Unique roots:** 96,710
- **Token length distribution:**
  - Length 5-8: Most common (2,677,621 tokens)
  - Length 6: 819,214 tokens (peak)

**Sample mappings:**
```
token: آباء → root: ءبو
token: آباءكم → root: ءبو
token: آتاك → root: ءتي,ءتو,ءتت
token: علم → root: علم
token: عمل → root: عمل
```

**Purpose:** Morphological dictionary mapping Arabic word forms to their triliteral/quadriliteral roots. Essential for Arabic text search.

#### `S1.db` - Metadata/Links Database (34.6 MB)
**Table: `b`**
| Column | Type | Description |
|--------|------|-------------|
| i | INTEGER | Primary key |
| s | BLOB | Source data (encrypted/compressed) |
| l | BLOB | Link data (encrypted/compressed) |
| d | INTEGER | Destination ID (9,190 non-null, 9,799 null) |
| a | BLOB | Additional data (15,160 non-null, 3,829 null) |
| b | BLOB | Binary data (all 18,989 non-null) |

**Note:** BLOB data appears to be compressed/encoded, not directly readable as text.

#### `user/data.db` - User Preferences (124 KB)
**15 tables** storing user-specific data:
- `favorite_book`: Bookmarked books
- `favorite_folder`: Bookmark folders
- `last_viewed`: Last read positions
- `search_history`: Search queries
- `session`: Reading sessions
- `diacritic`: Diacritic display settings

---

## 3. CONTENT ANALYSIS

### What's NOT in the SQLite databases
**Critical finding:** The SQLite book databases do NOT contain actual book content (Arabic text). They only store:
- Page structure (page numbers, parts)
- Title/section hierarchy (chapter structure with parent-child relationships)

### Where the actual content IS stored
**Lucene search indexes** contain all the actual book text:

| Index | Size | Fields |
|-------|------|--------|
| page | 13.2 GB | book_key, date, author, group, book, page, body, m_body, n_body |
| title | 56.0 MB | book_key, date, author, group, book, page, parent, body, m_body, n_body |
| esnad | 0.5 MB | book_key, hadeeth, esnad |
| author | 1.9 MB | date, author_id, body, m_body, body_store, n_body |

**Lucene field types:**
- `body`: Main text content (indexed, not stored)
- `m_body`: Modified body (indexed, not stored)
- `n_body`: Normalized body (indexed, not stored)
- `book_key`: Book identifier
- `page`: Page number
- `title`, `parent`: Title hierarchy

---

## 4. DATA QUALITY

### Strengths
✅ **Consistent schema** across all 8,427 book databases  
✅ **Rich title hierarchy** with parent-child relationships (2-3 levels deep)  
✅ **Cross-reference databases** for hadith and tafsir  
✅ **Morphological dictionary** with 3.2M Arabic word-root mappings  
✅ **Lucene indexes** with full-text search capability  

### Limitations
⚠️ **No actual text in SQLite** - content is only in Lucene binary format  
⚠️ **Lucene format is complex** - requires Lucene library to read  
⚠️ **BLOB data in S1.db** is compressed/encoded  
⚠️ **Many NULL fields** in page table (number, services always NULL)  
⚠️ **No explicit author metadata** in book databases  

---

## 5. VALUE COMPARISON: system_book_datasets vs extracted_books

| Aspect | system_book_datasets | extracted_books |
|--------|---------------------|-----------------|
| **Structure** | ✅ Hierarchical titles with parent-child | ❌ Flat text files |
| **Metadata** | ✅ Page numbers, parts, categories | ❌ Minimal |
| **Cross-refs** | ✅ Hadith & tafsir mappings | ❌ None |
| **Morphology** | ✅ 3.2M word-root mappings | ❌ None |
| **Search** | ✅ Lucene full-text index | ❌ Manual parsing needed |
| **Readability** | ❌ Binary Lucene format | ✅ Plain text |
| **Processing** | ❌ Requires Lucene library | ✅ Easy to parse |
| **RAG Ready** | ⚠️ Needs extraction first | ⚠️ Needs chunking |

**Winner:** system_book_datasets has FAR better structure and metadata, but requires Lucene extraction first.

---

## 6. EXTRACTION POTENTIAL

### What CAN be extracted (with Lucene library):

1. **Structured book content**
   - Full text organized by book, page, and section
   - Title hierarchy preserved (chapters, sections, subsections)
   - Page-level granularity

2. **Hadith cross-references**
   - Which hadith appear in which books/pages
   - Multiple occurrences of same hadith across books

3. **Tafsir mappings**
   - Quran verse → tafsir book/page mappings
   - 6,236 verse groups across 10 tafsir books

4. **Arabic morphology**
   - Word form → root mappings
   - Useful for search normalization

5. **Author information**
   - From Lucene author index

### What CANNOT be extracted:
- Hadith sanad/matn separation (not explicitly structured)
- Explicit verse boundaries in Quran text
- Footnotes as separate entities
- Book metadata (publication, edition, etc.)

---

## 7. RECOMMENDATIONS

### Priority 1: Extract Lucene Index Content
**Action:** Use Java Lucene library or Python pyLucene to extract all text from Lucene indexes.

**Expected output:**
```json
{
  "book_id": 1001,
  "page": 42,
  "title": "Chapter 5",
  "title_path": ["Book Title", "Part 2", "Chapter 5"],
  "body": "Arabic text content here...",
  "services": {
    "hadith": [323, 1030],
    "tafseer": [45, 46]
  }
}
```

### Priority 2: Build Structured Dataset
**Action:** Combine SQLite structure with Lucene content to create:
- Book → Part → Chapter → Section → Page hierarchy
- Hadith cross-reference index
- Tafsir verse mapping index
- Arabic morphology dictionary

### Priority 3: Create RAG-Ready Chunks
**Action:** Chunk extracted content by:
- Title boundaries (natural sections)
- Page boundaries (if titles too long)
- Hadith boundaries (using cross-reference data)

**Chunk metadata:**
```json
{
  "chunk_id": "book_1001_page_42_title_5",
  "book_id": 1001,
  "book_title": "...",
  "page": 42,
  "title": "Chapter 5",
  "title_path": ["...", "...", "..."],
  "category": "001",
  "hadith_refs": [323, 1030],
  "tafseer_refs": [],
  "text": "..."
}
```

---

## 8. TECHNICAL NOTES

### Lucene Index Details
- **Version:** Lucene 9.0/9.4
- **Codec:** Lucene90StoredFields, Lucene94FieldInfos
- **Posting format:** Lucene90
- **Doc values format:** Lucene90

### Encoding
- **S2.db tokens:** Windows-1256 (Arabic)
- **Lucene content:** Likely UTF-8 (needs verification)

### Book Categories
Categories (000-999) likely represent:
- 000-099: Quran and tafsir
- 100-199: Hadith collections
- 200-299: Fiqh (jurisprudence)
- 300-399: Tafsir
- 400-499: History
- 500-599: Language/grammar
- 600-699: Theology
- 700-799: Biography
- 800-899: Various
- 900-999: Modern works

*(This is speculative - needs verification)*

---

## 9. CONCLUSION

The system_book_datasets are a **GOLD MINE** of structured Islamic text data, but the actual content is locked in Lucene binary indexes. The SQLite databases provide excellent structure (page numbers, title hierarchy, cross-references), while the Lucene indexes contain the full text content.

**Next step:** Extract content from Lucene indexes using Java Lucene library, then combine with SQLite structure to create a comprehensive, RAG-ready dataset.

**Estimated extraction effort:** 2-3 days with proper Lucene setup
**Expected dataset size:** ~10-15 GB of structured JSON
**Expected chunks:** 500K-2M chunks (depending on chunking strategy)
