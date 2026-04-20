# 📖 Master Class: The Indexing & Data Engine

## 🕌 Introduction
This document explains the "Heart of Knowledge" in Athar: the Indexing Pipeline and the Data Models. This engine transforms 8,000+ raw books into a high-performance vector search system.

---

## 📁 src/data/models/ - The Persistence Schema

### 1. `src/data/models/quran.py`
**Purpose**: SQLAlchemy definition for the Quranic knowledge base.
**Deep Logic**:
- **Hierarchical Tables**: Maps `Surah` (Chapter) -> `Ayah` (Verse).
- **Secondary Tables**: `Translation` and `Tafsir` (Commentary) are linked via Foreign Keys to `Ayah`, allowing for granular lookup of interpretations.
- **text_simple Column**: Crucial for search performance. It stores a normalized, diacritic-free version of the Arabic text, used for fast SQL `LIKE` queries.

### 2. `src/data/models/query_log.py`
**Purpose**: Tracking user interactions for evaluation.
**Deep Logic**:
- Stores the `intent_confidence` and `latency_ms` to help identify "slow" or "uncertain" query patterns for later optimization.

---

## 📁 src/indexing/ - The Transformation Engine

### 1. `src/indexing/pipelines/`
**Purpose**: Orchestrating the end-to-end indexing of books.
**Deep Logic**:
- **build_seerah_chunks_camel.py**: Uses advanced NLP heuristics to detect "Index Pages" (table of contents) and exclude them from RAG, as they contain no meaningful scholarship.
- **Broken Span Repair**: Implements logic to detect if a Quranic bracket `﴿` was cut off by a chunk boundary and re-merges it with the next chunk to preserve the full verse.

### 2. `src/indexing/metadata/`
**Purpose**: Enrichment of raw data with scholarly context.
**Deep Logic**:
- **EraClassifier**: Bins scholars into periods like "Classical" (200-500 AH) or "Medieval" (500-900 AH). This metadata is then searchable in Qdrant.
- **AuthorCatalog**: Maps author IDs to their specific Madhhab (Hanafi, Shafi'i, etc.), allowing the RAG system to filter answers based on the user's preferred school.

### 3. `src/indexing/vectorstores/`
**Purpose**: Low-level implementation of vector storage.
**Deep Logic**:
- **HNSW Optimization**: Configures Qdrant with `m=16` and `ef_construct=100` for "Medium" collections, balancing search speed with memory usage.
- **Quantization**: Uses `INT8` quantization to compress vectors by 4x while maintaining >95% retrieval accuracy, crucial for managing the 5.7M document knowledge base.

---

## 📁 src/retrieval/ (v2) - Advanced Search Logic

### 1. `src/retrieval/fusion/rrf.py`
**Purpose**: Mathematical implementation of **Reciprocal Rank Fusion**.
**Deep Logic**:
- Combines the *Rank* of a document from Semantic search and Keyword search.
- Formula: `score = 1 / (60 + rank_semantic) + 1 / (60 + rank_keyword)`.
- This ensures that a document appearing high in *both* lists is favored, even if its raw scores vary wildly.

---

## 📊 Summary of File Responsibilities

| File | Innovation | Benefit |
|------|------------|---------|
| `quran.py` | Dual-Text Storage | Fast & Accurate Search |
| `build_seerah_chunks_camel.py` | Content Heuristics | Clean Knowledge Base |
| `enrichment.py` | Scholarly Metadata | Madhhab-Aware RAG |
| `rrf.py` | Ranking Math | Superior Answer Relevance |

---

**Next:** Doc 25 will cover Utilities, Generation, and Evaluation.
