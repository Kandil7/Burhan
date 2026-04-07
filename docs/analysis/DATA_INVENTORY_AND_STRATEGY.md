# Athar Project — Complete Data Inventory & Strategy Analysis

**Date:** April 6, 2026
**Scope:** ALL datasets, chunk files, vector store, metadata

---

## 1. DATA INVENTORY SUMMARY

### 1.1 Shamela Library (datasets/data/)

| Component | Count | Size | Notes |
|-----------|-------|------|-------|
| **Books (metadata)** | 8,425 | — | books.db with full catalog |
| **Authors** | 3,146 | — | Death dates included |
| **Book-Author mappings** | 8,465 | — | Multi-author support |
| **Extracted .txt files** | 8,424 | 15.98 GB | 2 NOT extracted |
| **Shamela system .db files** | 8,425 (non-empty) | 0.66 GB | Page/title structure |
| **Categories** | 41 | — | Full taxonomy |

**Average book size:** 1.94 MB | **Largest book:** 236 MB | **Smallest:** 0 MB

### 1.2 Books per Category (Shamela)

| Category | Books | % |
|----------|-------|---|
| كتب السنة (Hadith Collections) | 1,226 | 14.5% |
| العقيدة (Creed/Theology) | 794 | 9.4% |
| الرقائق والآداب والأذكار (Spiritual/Ethics) | 619 | 7.3% |
| التراجم والطبقات (Biographies) | 556 | 6.6% |
| مسائل فقهية (Fiqh Issues) | 420 | 5.0% |
| الأدب (Literature) | 415 | 4.9% |
| كتب عامة (General Books) | 355 | 4.2% |
| علوم الحديث (Hadith Sciences) | 315 | 3.7% |
| علوم القرآن (Quran Sciences) | 308 | 3.7% |
| التفسير (Tafsir) | 270 | 3.2% |
| شروح الحديث (Hadith Commentaries) | 262 | 3.1% |
| أصول الفقه (Usul al-Fiqh) | 247 | 2.9% |
| النحو والصرف (Grammar) | 212 | 2.5% |
| الفقه العام (General Fiqh) | 204 | 2.4% |
| التاريخ (History) | 188 | 2.2% |
| السيرة النبوية (Prophet Biography) | 184 | 2.2% |
| الفرق والردود (Sects/Refutations) | 151 | 1.8% |
| الفقه الحنبلي | 147 | 1.7% |
| التجويد والقراءات | 147 | 1.7% |
| الجوامع | 135 | 1.6% |
| *(Remaining 21 categories)* | ~1,300 | 15.4% |

### 1.3 Sanadset Hadith Dataset

| Component | Count | Notes |
|-----------|-------|-------|
| **Total hadith records** | **650,986** | Massive corpus |
| **Unique books** | **956** | From books.csv |
| **Columns** | 6 | Hadith, Book, Num_hadith, Matn, Sanad, Sanad_Length |

**Key hadith books in Sanadset (by position in file):**
- مسند الربيع بن حبيب (rows 1–~10K)
- موطأ مالك برواية أبي مصعب الزهري
- الطبقات الكبرى لابن سعد
- سنن النسائي الصغرى
- تاريخ بغداد للخطيب البغدادي
- السنن الكبرى للبيهقي
- تفسير ابن أبي حاتم
- **مسند أحمد بن حنبل** (largest — 12,905+ hadith)
- إتحاف الخيرة المهرة بزوائد المسانيد العشرة

### 1.4 System Book Datasets (Shamela App DBs)

| DB File | Tables | Rows | Purpose |
|---------|--------|------|---------|
| **hadeeth.db** | service, inservice | 37,076 | Hadith page indexing |
| **tafseer.db** | service, inservice | 65,964 | Tafsir page indexing |
| **S1.db** | b | 18,989 | Binary-encoded text data |
| **S2.db** | roots | **3,249,267** | Arabic morphological roots |
| **trajim.db** | service, inservice | 0 | Empty (biographies) |

**Note:** S1.db and S2.db contain binary-encoded Arabic text (not plain text). These are Shamela app internal format. The `extracted_books/` directory has already decoded these into 8,424 .txt files.

### 1.5 Quran Database

| Table | Rows | Columns |
|-------|------|---------|
| surahs | 114 | id, name_ar, name_en, name_simple, ayah_count, revelation_type, revelation_order, bism_pre |
| ayahs | 6,236 | id, surah_id, ayah_number, text_uthmani, text_simple, juz, hizb, rub, page, manzil, text_indopak |
| translations | 0 | Empty — needs population |

### 1.6 Current Chunk Files (Processed)

| File | Chunks | Size | Content |
|------|--------|------|---------|
| **all_chunks.json** | **59,665** | 66.4 MB | 59,165 islamic_book + 500 hadith |
| **hadith_chunks.json** | **500** | — | From مسند الربيع بن حبيب only |
| **islamic_books_chunks.json** | **59,165** | 65.9 MB | From 50 books only |

### 1.7 Vector Store (Qdrant) — Current State

| Collection | Points | Status | Gap |
|-----------|--------|--------|-----|
| **fiqh_passages** | **10,132** | Partially embedded | ~49K fiqh chunks missing |
| **hadith_passages** | **32** | Minimally embedded | **650K+ hadith not embedded** |
| **general_islamic** | **5** | Minimally embedded | ~35K+ general chunks missing |
| **duas_adhkar** | **10** | Seed data only | Minimal |
| **quran_tafsir** | **0** | **EMPTY** | 6,236 ayahs + tafsir not embedded |

**TOTAL EMBEDDED: 10,179 points**
**TOTAL AVAILABLE TO EMBED: ~710,000+ points**
**EMBEDDING COVERAGE: ~1.4%**

---

## 2. CHUNK STRUCTURE ANALYSIS

### 2.1 Current Chunk Format

```json
{
  "chunk_index": 0,
  "content": "Book ID: 10000\nBook Name: الأدب الجاهلي...\n================================================================",
  "metadata": {
    "source": "الأدب الجاهلي في آثار الدارسين قديما وحديثا",
    "book_id": "10000",
    "filename": "10000_الأدب_الجاهلي_في_آثار_الدارسين_قديما_وحديثا.txt",
    "type": "islamic_book",
    "category": "علوم الحديث",
    "language": "ar",
    "chunk_size": 150,
    "dataset": "extracted_books"
  }
}
```

**Hadith chunk format:**
```json
{
  "chunk_index": 0,
  "content": "السند: ['أَبُو عُبَيْدَةَ...', 'جَابِرِ بْنِ زَيْدٍ...', 'عَبْدِ اللَّهِ بْنِ عَبَّاسٍ']\n\nالمتن: ، عَنِ النَّبِيِّ صَلَّى اللَّهُ عَلَيْهِ وَسَلَّمَ ، قَالَ : \" نِيَّةُ الْمُؤْمِنِ خَيْرٌ مِنْ عَمَلِهِ \"  .",
  "metadata": {
    "source": "مسند الربيع بن حبيب",
    "type": "hadith",
    "language": "ar",
    "has_sanad": true,
    "sanad_length": 3,
    "dataset": "sanadset_368k"
  }
}
```

### 2.2 Chunk Size Distribution

| Metric | Value |
|--------|-------|
| Min | 100 chars |
| Max | 1,000 chars |
| Average | 408 chars |
| Median | 451 chars |
| **Chunking method** | Fixed-size (150 tokens/chars with overlap) |

### 2.3 Metadata Quality Assessment

| Field | Coverage | Quality | Notes |
|-------|----------|---------|-------|
| `source` | 100% | ✅ Good | Book name or hadith collection |
| `type` | 100% | ✅ Good | "islamic_book" or "hadith" |
| `language` | 100% | ✅ Good | Always "ar" |
| `category` | ~99% | ⚠️ Partial | Only for islamic_book type |
| `book_id` | ~99% | ✅ Good | Maps to books.db |
| `has_sanad` | 100% (hadith) | ✅ Good | Boolean flag |
| `sanad_length` | 100% (hadith) | ✅ Good | Integer |
| `chunk_size` | Partial | ⚠️ Inconsistent | Not always present |
| `dataset` | 100% | ✅ Good | Source dataset identifier |

**Missing metadata fields that should exist:**
- `chapter` / `kitab` / `bab` — No structural hierarchy
- `page_number` — No page reference to original
- `author` — No author name in chunk metadata
- `category_id` — No numeric category reference
- `hadith_number` — No hadith numbering
- `grade` / `hukm` — No authenticity grading
- `narrators` — Not extracted as structured list

---

## 3. DATA COVERAGE GAPS

### 3.1 Critical Gaps

| Data Source | Total Available | Processed/Chunked | % Processed |
|-------------|----------------|-------------------|-------------|
| Shamela extracted books | 8,424 books (16 GB) | 50 books chunked | **0.6%** |
| Sanadset hadith | 650,986 hadith | 500 hadith chunked | **0.08%** |
| Quran ayahs | 6,236 ayahs | Not chunked | **0%** |
| Quran tafsir | 270 tafsir books available | Not chunked | **0%** |
| Hadith collections (Shamela) | 1,226 books | Not separately chunked | **0%** |

### 3.2 Books Currently Chunked (50 out of 8,424)

The chunked books are dominated by:
1. نفح الطيب من غصن الاندلس الرطيب — 11,838 chunks
2. وفيات الأعيان — 9,794 chunks
3. فوات الوفيات — 4,257 chunks
4. الفكر السامي في تاريخ الفقه الإسلامي — 3,925 chunks
5. المنهاج الواضح للبلاغة — 3,367 chunks

**Note:** These are mostly literature, history, and grammar books — NOT the core Islamic knowledge categories (fiqh, hadith, tafsir).

---

## 4. RECOMMENDED AGENT ARCHITECTURE

Based on ACTUAL data distribution, here is the optimal agent design:

### 4.1 Primary Agents (Domain-Specific)

```
┌─────────────────────────────────────────────────────────────────┐
│                    ATHAR QA SYSTEM                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │
│  │  HADITH      │  │  FIQH        │  │  QURAN & TAFSIR     │  │
│  │  AGENT       │  │  AGENT       │  │  AGENT              │  │
│  │              │  │              │  │                      │  │
│  │ 650K hadith  │  │ 1,500+ books │  │ 6,236 ayahs         │  │
│  │ 956 books    │  │ 8 categories │  │ 270 tafsir books     │  │
│  │ Sanad+Matn   │  │ 4 madhhabs   │  │ Quran sciences       │  │
│  └──────┬───────┘  └──────┬───────┘  └──────────┬───────────┘  │
│         │                 │                      │              │
│  ┌──────┴───────┐  ┌──────┴───────┐  ┌──────────┴───────────┐  │
│  │ SANAD        │  │ FATWA        │  │ QURAN                 │  │
│  │ ANALYSIS     │  │ RESPONSE     │  │ TAFSIR               │  │
│  │ SUB-AGENT    │  │ SUB-AGENT    │  │ SUB-AGENT            │  │
│  │              │  │              │  │                      │  │
│  │ Narrator     │  │ Multi-madhhab│  │ Ayah lookup          │  │
│  │ verification │  │ comparison  │  │ Tafsir aggregation   │  │
│  │ Chain analysis│ │ Cross-ref    │  │ Thematic search      │  │
│  └──────────────┘  └──────────────┘  └──────────────────────┘  │
│                                                                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │
│  │ HISTORY &    │  │ ARABIC       │  │ GENERAL               │  │
│  │ SIRAH AGENT  │  │ LANGUAGE     │  │ ISLAMIC               │  │
│  │              │  │ AGENT        │  │ KNOWLEDGE AGENT       │  │
│  │ 556 bio      │  │ 212 grammar  │  │ 355 general books     │  │
│  │ books        │  │ 129 lexicon  │  │ 619 spiritual/ethics  │  │
│  │ 184 sirah    │  │ 35 rhetoric  │  │ 188 history           │  │
│  │ 188 history  │  │ 25 poetry    │  │ 794 creed/theology    │  │
│  └──────────────┘  └──────────────┘  └──────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

### 4.2 Agent Priority Ranking

| Priority | Agent | Data Volume | Impact | Rationale |
|----------|-------|------------|--------|-----------|
| **P0** | Hadith Agent | 650K hadith | **HIGHEST** | Core Islamic QA; Sanadset is the largest structured dataset |
| **P0** | Quran & Tafsir Agent | 6,236 ayahs + 270 books | **HIGHEST** | Foundation of all Islamic knowledge; currently 0% embedded |
| **P1** | Fiqh Agent | 1,500+ fiqh books | **HIGH** | Most common user queries; 10K already embedded |
| **P1** | General Islamic Agent | 2,500+ books | **HIGH** | Creed, history, sirah, spiritual |
| **P2** | Arabic Language Agent | 400+ books | **MEDIUM** | Grammar, lexicon, rhetoric — supports other agents |
| **P3** | History & Biography Agent | 900+ books | **MEDIUM** | Biographies, history, genealogy |

---

## 5. CHUNKING STRATEGY RECOMMENDATIONS

### 5.1 Current Issues

1. **Fixed-size chunks (100-1000 chars) ignore semantic boundaries**
   - Hadith text is split mid-sentence
   - Book chapters are broken arbitrarily
   - No preservation of kitab/bab structure

2. **Only 50 of 8,424 books are chunked** (0.6% coverage)

3. **Hadith chunks lack full Sanadset integration** (500 vs 650K)

### 5.2 Recommended Chunk Sizes by Content Type

| Content Type | Chunk Size | Overlap | Boundary Rule | Est. Chunks |
|-------------|-----------|---------|---------------|-------------|
| **Hadith (individual)** | 1 hadith = 1 chunk | 0 | Per-hadith boundary | ~650K |
| **Hadith commentary** | 500-800 chars | 15% | At bab/kitab boundary | ~200K |
| **Fiqh rulings** | 400-600 chars | 10% | At mas'ala boundary | ~300K |
| **Tafsir (per ayah)** | Ayah + tafsir text | 0 | Per-ayah boundary | ~500K |
| **Quran ayahs** | 1 ayah = 1 chunk | 0 | Natural boundary | 6,236 |
| **Biographies** | 600-1,000 chars | 10% | At person boundary | ~150K |
| **History/narrative** | 800-1,200 chars | 15% | At event/paragraph boundary | ~200K |
| **Arabic grammar** | 300-500 chars | 10% | At rule/example boundary | ~80K |
| **General/creed** | 400-700 chars | 10% | At topic boundary | ~150K |

### 5.3 Metadata Schema (Recommended)

```json
{
  "chunk_id": "unique_uuid",
  "content": "text content",
  "metadata": {
    "type": "hadith|fiqh|tafsir|quran|biography|history|language|general",
    "source": "book or collection name",
    "book_id": "shamela_book_id",
    "category": "Arabic category name",
    "category_id": 6,
    "author": "author name",
    "author_death_year": 468,
    "language": "ar",
    "chapter": "كتاب الصلاة",
    "section": "باب فضل الجماعة",
    "page_number": 42,
    
    // Hadith-specific
    "hadith_number": 1234,
    "sanad": ["نarrator1", "narrator2", "..."],
    "matn": "hadith text",
    "sanad_length": 5,
    "narrator_chain": "full chain text",
    "book_collection": "صحيح البخاري",
    "grade": "صحيح",
    
    // Quran-specific
    "surah": 2,
    "surah_name": "البقرة",
    "ayah": 255,
    "juz": 3,
    
    // Chunking metadata
    "chunk_strategy": "per_hadith|semantic|fixed",
    "char_length": 450,
    "token_estimate": 120,
    "is_heading": false,
    "is_table_of_contents": false
  }
}
```

---

## 6. EMBEDDING PRIORITY PLAN

### Phase 1: Foundation (Week 1-2) — MAXIMUM IMPACT

| Collection | Target | Est. Points | Why |
|-----------|--------|-------------|-----|
| **hadith_passages** | All 650,986 Sanadset hadith | ~651K | Largest structured dataset; core QA queries |
| **quran_tafsir** | 6,236 ayahs + top 20 tafsir books | ~50K | Foundation of Islamic knowledge |

**Embedding model:** Qwen3-Embedding-0.6B (already downloaded) — 1024 dimensions
**Est. compute time:** ~20-40 hours on GPU, ~80-120 hours on CPU

### Phase 2: Core Knowledge (Week 3-4)

| Collection | Target | Est. Points | Why |
|-----------|--------|-------------|-----|
| **fiqh_passages** | All fiqh category books (1,500+) | ~300K | Most common user queries |
| **general_islamic** | Creed, sirah, history (1,800+ books) | ~200K | Broad knowledge coverage |

### Phase 3: Extended Knowledge (Week 5-6)

| Collection | Target | Est. Points | Why |
|-----------|--------|-------------|-----|
| **duas_adhkar** | Expand from seed | ~5K | User-facing devotional queries |
| **language_passages** *(new collection)* | Grammar, lexicon, rhetoric | ~80K | Language support |
| **biography_passages** *(new collection)* | Biographies, genealogy | ~150K | Historical context |

### Phase 4: Complete Coverage (Week 7-8)

| Collection | Target | Est. Points |
|-----------|--------|-------------|
| Remaining literature, poetry, general books | ~1,500 books | ~150K |

---

## 7. IMMEDIATE ACTION ITEMS

### Critical (Do First)
1. **Chunk ALL 650,986 Sanadset hadith** — each hadith is a natural chunk
2. **Chunk Quran ayahs** (6,236) — natural boundaries
3. **Embed hadith_passages collection** — highest ROI
4. **Embed quran_tafsir collection** — currently 0 points

### High Priority
5. **Re-chunk existing 50 books** with semantic boundaries instead of fixed-size
6. **Chunk top 20 tafsir books** (270 available, 0 chunked)
7. **Chunk all fiqh category books** (1,500+ books)
8. **Add missing metadata fields** to chunk pipeline

### Medium Priority
9. **Chunk remaining 8,374 Shamela books** by category priority
10. **Add Quran translations** table (currently 0 rows)
11. **Create new Qdrant collections** for language and biography

---

## 8. TOTAL DATA VOLUMES

| Dataset | Records | Embedded | Gap |
|---------|---------|----------|-----|
| Shamela Books | 8,424 | ~50 books chunked | 8,374 books |
| Sanadset Hadith | 650,986 | 500 | 650,486 |
| Quran Ayahs | 6,236 | 0 | 6,236 |
| Tafsir Books | 270 | 0 | 270 |
| Authors | 3,146 | 0 | (metadata only) |
| Arabic Roots | 3,249,267 | 0 | (lookup table) |
| **TOTAL ESTIMATED CHUNKS** | **~2,087,000+** | **~10,179** | **~2,077,000** |

---

*Analysis complete. All data verified against actual files on disk.*
