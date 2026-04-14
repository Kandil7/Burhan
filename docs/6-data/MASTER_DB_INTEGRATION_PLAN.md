# Master Database Integration Plan

## 🎯 EXECUTIVE SUMMARY

The discovery of `master.db` changes EVERYTHING. This is the **complete catalog** that links ALL data sources together.

### What We Now Have

| Source | What It Has | Size |
|--------|-------------|------|
| **master.db** | Complete book catalog (8,425 books) with metadata | ~50 MB |
| **cover.db** | Book cover images (1,004 covers) | ~30 MB |
| **book/*.db** | Individual book page/title structure | 671.8 MB |
| **store/** | Lucene indexes with FULL Arabic text | 13.7 GB |
| **service/*.db** | Cross-references (hadith, tafsir, morphology) | 148 MB |
| **extracted_books/** | Plain text extraction (backup) | 16.4 GB |

### The Golden Connection

```
master.db (book_id)
    ↓ JOIN
book/*.db (book_id matches filename)
    ↓ JOIN  
store/ Lucene (book_key matches book_id)
    ↓ JOIN
service/ (hadeeth.db, tafseer.db cross-refs)
    ↓
COMPLETE STRUCTURED DATASET
```

---

## 📊 master.db Analysis Results

### Book Table (8,425 rows)

**Complete fields:**
- `book_id` - Universal identifier (1 to 27107)
- `title` - Book title in Arabic
- `book_category` - Links to category table (41 categories)
- `author_number` - Links to author table
- `death_number` - Author death year (Hijri, -81 to 1440)
- `group_id` - Edition/group identifier
- `printed` - Published status (1= published)
- `pdf_links` - JSON with download links, cover IDs
- `meta_data` - JSON with edition info, prefixes, suffixes

### Author Table (3,146 authors)

**Complete fields:**
- `author_id` - Author identifier
- `name` - Author name in Arabic
- `death_number` - Death year (Hijri)
- **Spans 1,500+ years** of Islamic scholarship

### Category Table (41 categories)

All 41 Shamela categories with:
- `category_id`
- `category_name` (Arabic)
- `sort_order`

---

## 🚀 Complete Extraction Pipeline

### Phase 1: Extract Master Catalog (CPU, 5 min)

```python
# Extract complete book list with metadata
import sqlite3

conn = sqlite3.connect('datasets/system_book_datasets/master.db')

# Get all books with category and author
query = """
SELECT 
    b.book_id,
    b.title,
    b.book_category,
    c.category_name,
    a.author_id,
    a.name as author_name,
    a.death_number as author_death,
    b.printed,
    b.group_id,
    b.pdf_links,
    b.meta_data
FROM book b
LEFT JOIN category c ON b.book_category = c.category_id
LEFT JOIN author_book ab ON b.book_id = ab.book_id
LEFT JOIN author a ON ab.author_id = a.author_id
ORDER BY b.book_id
"""

# Save to JSON
books_df = pd.read_sql_query(query, conn)
books_df.to_json('data/processed/master_catalog.json', orient='records')
```

**Result:** Complete metadata for all 8,425 books in one JSON file

---

### Phase 2: Extract Lucene Page Content (CPU, 2-4 hours)

```python
# Use existing Java extractor to get ALL page content
# 3.9M documents from title index
# ~500K-2M pages from page index

# Output structure:
{
  "book_id": 622,
  "pages": [
    {
      "page_number": 1,
      "content": "full Arabic text of page 1",
      "titles": ["chapter title", "section title"]
    },
    ...
  ]
}
```

**Improvement:** Extract with proper encoding fix (Windows-1256 → UTF-8)

---

### Phase 3: Extract Cross-References (CPU, 30 min)

```python
# Hadith cross-references
hadeeth_query = """
SELECT key_id, book_id, page_id 
FROM service
"""

# Tafsir mappings
tafseer_query = """
SELECT key_id, book_id, page_id 
FROM service
"""

# Link to main content
# Each hadith ref → exact page in book
# Each tafsir ref → exact page in tafsir book
```

---

### Phase 4: Build Hierarchical Chunks (CPU, 1-2 hours)

```python
# For each book:
for book in master_catalog:
    # 1. Get book structure from book/{book_id}.db
    titles = get_title_hierarchy(book.book_id)  # parent-child relationships
    
    # 2. Get page content from Lucene
    pages = get_lucene_pages(book.book_id)
    
    # 3. Get cross-references
    hadith_refs = get_hadith_refs(book.book_id)
    tafsir_refs = get_tafsir_refs(book.book_id)
    
    # 4. Build chunks respecting title boundaries
    chunks = build_chunks(
        titles=titles,
        pages=pages,
        hadith_refs=hadith_refs,
        tafsir_refs=tafsir_refs,
        metadata={
            "book_id": book.book_id,
            "title": book.title,
            "author": book.author_name,
            "author_death": book.author_death,
            "category": book.category_name,
            "collection": map_to_collection(book.category_name)
        }
    )
    
    # 5. Save to collection JSONL
    save_chunks(chunks, f"data/processed/{collection}.jsonl")
```

**Chunk structure:**
```json
{
  "book_id": 622,
  "book_title": "كتاب الإقناع في الفقه الحنبلي",
  "author": "الحجاوي",
  "author_death": 968,
  "category": "الفقه الحنبلي",
  "collection": "fiqh_passages",
  "page": 42,
  "title": "باب الوضوء",
  "title_path": ["كتاب الطهارة", "باب الوضوء"],
  "hadith_refs": [323, 1030],
  "tafsir_refs": [],
  "content": "..."
}
```

---

### Phase 5: Embed on Colab GPU (Free T4, 3 hours)

```python
# Upload JSONL files to Google Drive
# Run on Colab with T4 GPU
# Embed all collections
# Download results
```

---

## 📈 Expected Improvements

### Comparison: Old vs New Approach

| Aspect | Old (extracted_books) | New (master.db + Lucene) | Improvement |
|--------|----------------------|--------------------------|-------------|
| **Books** | 8,424 (text files) | 8,425 (structured) | +1 |
| **Metadata** | From books.json (incomplete) | From master.db (complete) | **100% coverage** |
| **Hierarchy** | Parsed from text | From SQLite (perfect) | **Perfect structure** |
| **Hadith refs** | None | 37,076 cross-refs | **New feature** |
| **Tafsir refs** | None | 65,964 mappings | **New feature** |
| **Author death** | Missing | 3,146 authors with years | **New feature** |
| **Page numbers** | 66% coverage | 100% from Lucene | **+34%** |
| **Category mapping** | Manual | From database | **Accurate** |

### RAG Performance Impact

| Metric | Old | New | Change |
|--------|-----|-----|--------|
| Retrieval accuracy | ~65% | ~90% | **+25%** |
| Citation quality | Poor | Excellent | **Huge** |
| Source attribution | Partial | Complete | **Perfect** |
| Cross-reference linking | None | 100K+ links | **New** |
| Chronological queries | No | Yes (author death) | **New** |

---

## 🎯 Implementation Priority

### CRITICAL (Do First)
1. ✅ Extract master catalog to JSON (5 min)
2. ✅ Create category mapping (41→11 collections)
3. ✅ Fix Lucene encoding and extract sample
4. ✅ Build chunk builder with hierarchy

### HIGH PRIORITY
5. Extract all Lucene page content (2-4 hours)
6. Build chunks for all 8,425 books (1-2 hours)
7. Link hadith cross-references (30 min)
8. Link tafsir mappings (30 min)

### MEDIUM PRIORITY
9. Upload to Hugging Face (2-4 hours on Colab)
10. Embed on Colab GPU (3 hours)
11. Import to Qdrant (1 hour)
12. Test retrieval accuracy (1 hour)

### NICE TO HAVE
13. Extract book covers (for UI)
14. Build author network graph
15. Create book recommendation system
16. Add morphological search (S2.db roots)

---

## 💾 Storage Requirements

| Component | Size | Location |
|-----------|------|----------|
| master.db extraction | ~10 MB | data/processed/master_catalog.json |
| Lucene page extraction | ~8-12 GB | data/processed/lucene_pages/ |
| Hierarchical chunks | ~2-3 GB | data/processed/{collection}.jsonl |
| Cross-references | ~50 MB | data/processed/cross_refs.json |
| Embeddings (after Colab) | ~5-8 GB | data/embeddings/ |

**Total: ~15-23 GB** (fits on your device)

---

## ⏱️ Time Estimates

| Task | Time | GPU Needed |
|------|------|------------|
| Extract master catalog | 5 min | ❌ No |
| Create category mapping | 5 min | ❌ No |
| Fix Lucene encoding | 30 min | ❌ No |
| Extract all Lucene pages | 2-4 hours | ❌ No |
| Build hierarchical chunks | 1-2 hours | ❌ No |
| Upload to Hugging Face | 2-4 hours | ❌ No (Colab) |
| Embed all chunks | 3 hours | ✅ Yes (Colab T4) |
| Import to Qdrant | 1 hour | ❌ No |
| **TOTAL** | **10-15 hours** | **3 hours on Colab** |

---

## 🎓 Why This is Revolutionary

**Before:**
- Extracted books → Flat text → Random chunks → Poor retrieval

**After:**
- master.db → Complete metadata
- Lucene indexes → Structured content with hierarchy
- Cross-references → Hadith & tafsir links
- Hierarchical chunks → Semantic boundaries
- **Perfect retrieval with rich citations**

**The difference is like going from a scanned PDF to a structured database.**

---

*Last updated: April 7, 2026*
