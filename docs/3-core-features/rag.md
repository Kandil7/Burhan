# 🧠 Burhan RAG Guide

Complete guide to the Retrieval-Augmented Generation (RAG) system in Burhan.

---

## 📋 Table of Contents

- [Overview](#overview)
- [RAG Architecture](#rag-architecture)
- [Embedding Pipeline](#embedding-pipeline)
- [Vector Store](#vector-store)
- [Hybrid Search](#hybrid-search)
- [Fiqh RAG Agent](#fiqh-rag-agent)
- [General Islamic Knowledge Agent](#general-islamic-knowledge-agent)
- [Citation System](#citation-system)
- [Performance Optimization](#performance-optimization)
- [Troubleshooting](#troubleshooting)

---

## 🎯 Overview

RAG (Retrieval-Augmented Generation) enables Burhan to answer fiqh and general Islamic knowledge questions using **verified sources** only, with proper citations.

### Key Principles

1. **Grounded Answers**: Answers based only on retrieved passages
2. **Citation Tracking**: Every claim linked to a source [C1], [C2]
3. **No Hallucination**: Temperature 0.1 for deterministic responses
4. **Metadata Filtering**: Filter by madhhab, source type, language

---

## 🏗️ RAG Architecture

### Complete Flow

```
User Question
    │
    ▼
┌──────────────────┐
│ Encode Query     │  Qwen3-Embedding-0.5B
└────────┬─────────┘
         │ 1024-dim vector
         ▼
┌──────────────────┐
│ Hybrid Search    │  Semantic + BM25 keyword
└────────┬─────────┘
         │ Top-15 passages
         ▼
┌──────────────────┐
│ Re-ranking       │  Cross-encoder (optional)
└────────┬─────────┘
         │ Top-5 passages
         ▼
┌──────────────────┐
│ Format Passages  │  Prepare for LLM prompt
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ LLM Generation   │  Grounded answer (temp 0.1)
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ Citations        │  Normalize to [C1], [C2]
└────────┬─────────┘
         │
         ▼
    Final Answer
```

---

## 🔢 Embedding Pipeline

### Qwen3-Embedding-0.5B

**Configuration:**
```python
MODEL_NAME = "Qwen/Qwen3-Embedding-0.5B"
DIMENSION = 1024
MAX_LENGTH = 512 tokens
BATCH_SIZE = 32
```

**Features:**
- Strong Arabic language support
- GPU acceleration (CUDA/MPS)
- Redis-based caching (7-day TTL)
- Batch processing optimization

**Usage:**
```python
from src.knowledge.embedding_model import EmbeddingModel

model = EmbeddingModel()
await model.load_model()

# Encode single query
embedding = await model.encode_query("ما حكم زكاة الأسهم؟")

# Encode batch
embeddings = await model.encode(texts)
```

### Embedding Cache

**File:** `src/knowledge/embedding_cache.py`

- **Storage**: Redis
- **TTL**: 7 days
- **Key**: SHA-256 hash of text
- **Hit Rate**: ~60% for repeated queries

---

## 🗄️ Vector Store

### Qdrant Configuration

**File:** `src/knowledge/vector_store.py`

**Collections:**

| Collection | Purpose | Estimated Size |
|------------|---------|----------------|
| `fiqh_passages` | Fiqh books, fatwas | 500k+ vectors |
| `hadith_passages` | Hadith collections | 50k+ vectors |
| `quran_tafsir` | Tafsir passages | 100k+ vectors |
| `general_islamic` | History, biography | 200k+ vectors |
| `duas_adhkar` | Duas collection | 5k+ vectors |

**Index Configuration:**
```python
from qdrant_client.models import VectorParams, Distance

client.create_collection(
    collection_name="fiqh_passages",
    vectors_config=VectorParams(
        size=1024,
        distance=Distance.COSINE,
    ),
)
```

### Usage

```python
from src.knowledge.vector_store import VectorStore

store = VectorStore()
await store.initialize()

# Upsert documents
await store.upsert(
    collection="fiqh_passages",
    documents=chunks,
    embeddings=embeddings
)

# Search
results = await store.search(
    collection="fiqh_passages",
    query_embedding=query_embedding,
    top_k=10,
    filters={"madhhab": "hanafi"}
)
```

---

## 🔍 Hybrid Search

### Semantic + Keyword Search

**File:** `src/knowledge/hybrid_search.py`

**Process:**
1. **Semantic Search**: Cosine similarity in vector space
2. **Keyword Search**: BM25-like scoring on text
3. **Reciprocal Rank Fusion**: Combine both scores

**Formula:**
```
score = 1 / (k + rank_semantic) + 1 / (k + rank_keyword)
```

**Usage:**
```python
from src.knowledge.hybrid_search import HybridSearcher

searcher = HybridSearcher(vector_store)

results = await searcher.search(
    query="ما حكم زكاة الأسهم؟",
    query_embedding=embedding,
    collection="fiqh_passages",
    top_k=10
)
```

---

## 📖 Fiqh RAG Agent

### Configuration

**File:** `src/agents/fiqh_agent.py`

```python
class FiqhAgent(BaseAgent):
    TOP_K_RETRIEVAL = 15
    TOP_K_RERANK = 5
    SCORE_THRESHOLD = 0.7
    TEMPERATURE = 0.1  # Very low for fiqh
```

### Prompt Template

```python
FIQH_GENERATION_PROMPT = """
أنت مساعد إسلامي متخصص في الفقه. أجب بناءً ONLY على النصوص المسترجاعة.

السؤال: {query}
اللغة: {language}

النصوص المسترجاعة:
{passages}

التعليمات:
1. أجب بناءً على النصوص فقط
2. اذكر الافتراضات إن وجدت
3. إذا كانت النصوص لا تجيب بشكل كافٍ، قل ذلك صراحة
4. اذكر المذهب إذا كان موجوداً في النصوص
5. استخدم المراجع [C1]، [C2]، إلخ. لكل دليل
6. لا تخترع أو تضيف مصادر خارجية
7. إذا كانت هناك آراء مختلفة، اذكرها
8. أضف تنبيه باستشارة العالم للحالات الخاصة

أجب بـ {language}.
"""
```

### Usage

```python
from src.agents.fiqh_agent import FiqhAgent
from src.agents.base import AgentInput

agent = FiqhAgent()

result = await agent.execute(AgentInput(
    query="ما حكم زكاة الأسهم؟",
    language="ar",
    metadata={"madhhab": "hanafi"}
))

print(result.answer)
print(result.citations)
```

---

## 📚 General Islamic Knowledge Agent

### Configuration

**File:** `src/agents/general_islamic_agent.py`

```python
class GeneralIslamicAgent(BaseAgent):
    TEMPERATURE = 0.3  # Slightly higher for educational tone
    COLLECTION = "general_islamic"
```

### Differences from Fiqh Agent

| Feature | Fiqh Agent | General Agent |
|---------|------------|---------------|
| Temperature | 0.1 | 0.3 |
| Collection | fiqh_passages | general_islamic |
| Tone | Legal ruling | Educational |
| Disclaimers | Required | Optional |
| Citations | Strict | Moderate |

---

## 🔗 Citation System

### Citation Normalization

**File:** `src/core/citation.py`

**Process:**
1. Detect citation patterns in LLM output
2. Map to passage metadata
3. Generate standardized format [C1], [C2]
4. Build structured citation objects

**Pattern Detection:**
```python
PATTERNS = [
    # Quran: "Quran 2:255"
    (r'(?:quran|القرآن)\s*(\d+)\s*[:\-]\s*(\d+)', "quran"),
    
    # Hadith: "صحيح البخاري، حديث 1234"
    (r'(?:صحيح|سنن)\s+(البخاري|مسلم)\s*.*?(\d+)', "hadith"),
    
    # Fatwa: "فتوى رقم 12345"
    (r'(?:فتوى|fatwa)\s*(\d+)', "fatwa"),
]
```

**Citation Object:**
```python
@dataclass
class Citation:
    id: str              # "C1", "C2", etc.
    type: str            # "quran", "hadith", "fatwa"
    source: str          # "Sahih Bukhari"
    reference: str       # "Hadith #1234"
    url: Optional[str]   # "https://sunnah.com/bukhari/1234"
    text_excerpt: Optional[str]  # Quoted passage
```

---

## ⚡ Performance Optimization

### Caching Strategy

| Cache Type | TTL | Hit Rate | Purpose |
|------------|-----|----------|---------|
| **Response Cache** | 1 hour | ~30% | Identical queries |
| **Embedding Cache** | 7 days | ~60% | Repeated texts |
| **Intent Cache** | 1 day | ~40% | Frequent intents |

### Batch Processing

```python
# Encode in batches of 32
for i in range(0, len(texts), 32):
    batch = texts[i:i+32]
    embeddings = await model.encode(batch)
```

### Database Indexes

```sql
-- Full-text search
CREATE INDEX idx_ayah_text_search ON ayahs 
    USING GIN (to_tsvector('simple', text_uthmani));

-- Vector similarity (Qdrant HNSW)
-- Auto-configured on collection creation
```

---

## 🔧 Troubleshooting

### Common Issues

**1. Empty Retrievals**

```
Warning: No passages retrieved
```

**Solution:**
- Check if collection has documents
- Verify embedding model is loaded
- Check Qdrant connection

---

**2. Low Citation Confidence**

```
Confidence: 0.3
```

**Solution:**
- Increase `TOP_K_RETRIEVAL`
- Lower `SCORE_THRESHOLD`
- Check embedding quality

---

**3. Hallucination Detected**

```
Warning: Answer not grounded in passages
```

**Solution:**
- Lower temperature (0.1)
- Strengthen prompt instructions
- Add more retrieval passages

---

### Performance Tuning

**GPU Acceleration:**
```python
# Automatically uses GPU if available
device = "cuda" if torch.cuda.is_available() else "cpu"
```

**Batch Size:**
```python
# Optimal batch size depends on GPU memory
BATCH_SIZE = 32  # 8GB GPU
BATCH_SIZE = 64  # 16GB GPU
```

---

<div align="center">

**RAG Guide Version:** 1.0  
**Last Updated:** Phase 4 Complete  
**Status:** Production-Ready

</div>
