# 🕌 دليل الاسترجاع والعناصر

## شرح أنظمة الاسترجاع

---

## 1. Retrieval Schemas

### 1.1 RetrievalResult

```python
# src/retrieval/schemas.py

class RetrievalResult(BaseModel):
    """نتيجة الاسترجاع."""
    
    id: str
    text: str
    score: float
    collection: str
    metadata: dict
    
    # Additional fields
    rank: Optional[int]
    rerank_score: Optional[float]
```

### 1.2 QueryType

```python
class QueryType(str, Enum):
    """نوع الاستعلام."""
    
    SEMANTIC = "semantic"      # Embedding-based
    KEYWORD = "keyword"       # BM25
    HYBRID = "hybrid"          # Combined
```

### 1.3 RetrievalPassage

```python
class RetrievalPassage(BaseModel):
    """مقطع مسترجع."""
    
    id: str
    text: str
    collection: str
    source: str
    book_title: Optional[str]
    page: Optional[int]
    confidence: float
```

---

## 2. Retrieval Strategies

### 2.1 RetrievalStrategy

```python
# src/retrieval/strategies.py

class RetrievalStrategy(BaseModel):
    """استراتيجية الاسترجاع."""
    
    collection: str
    top_k: int
    filters: Optional[dict]
    rerank: bool
    query_type: QueryType = QueryType.HYBRID

# Collection-specific
RETRIEVAL_MATRIX = {
    "fiqh_agent": RetrievalStrategy(
        collection="fiqh_machinations",
        top_k=15,
        filters={"type": "fiqh"},
        rerank=True,
    ),
    "hadith_agent": RetrievalStrategy(
        collection="hadith_passages",
        top_k=10,
        filters={"grade$in": ["sahih", "hasan"]},
        rerank=True,
    ),
}
```

---

**آخر تحديث**: أبريل 2026