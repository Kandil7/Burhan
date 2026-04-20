# 🕌 دليل نماذج الاستجابة الكاملة

## نماذج الاستجابة والطلب

---

## 1. Request Models

### 1.1 AskRequest

```python
# src/api/schemas/request.py

class AskRequest(BaseModel):
    """طلب السؤال."""
    
    query: str
    language: str = "ar"
    collection: Optional[str]
    madhhab: Optional[str]
    
    model_config = {"extra": "forbid"}
```

### 1.2 SearchRequest

```python
class SearchRequest(BaseModel):
    """طلب البحث."""
    
    query: str
    collection: Optional[str]
    top_k: int = Field(default=10, ge=1, le=100)
    filters: Optional[dict]
```

---

## 2. Response Models

### 2.1 AskResponse

```python
# src/api/schemas/response.py

class AskResponse(BaseModel):
    """استجابة السؤال."""
    
    answer: str
    citations: list[CitationResponse]
    intent: str
    confidence: float
    processing_time_ms: int
```

### 2.2 SearchResponse

```python
class SearchResponse(BaseModel):
    """استجابة البحث."""
    
    results: list[SearchResult]
    total: int
    query: str
    processing_time_ms: int
```

---

## 3. Citation Response

### 3.1 CitationResponse

```python
class CitationResponse(BaseModel):
    """نموذج الاقتباس."""
    
    source_id: str
    text: str
    book_title: Optional[str]
    page: Optional[int]
    grade: Optional[str]
    url: Optional[str]
```

---

## 4. Common Models

### 4.1 ErrorResponse

```python
class ErrorResponse(BaseModel):
    """نموذج الخطأ."""
    
    error: str
    message: str
    details: Optional[dict]
    request_id: Optional[str]
```

### 4.2 HealthResponse

```python
class HealthResponse(BaseModel):
    """نموذج الصحة."""
    
    status: str  # ok, degraded, down
    version: str
    timestamp: datetime
    dependencies: dict
```

---

## 5. Trace Models

### 5.1 TraceRequest

```python
# src/api/schemas/trace.py

class TraceRequest(BaseModel):
    """طلب التتبع."""
    
    query: str
    intent: str
    agent: str
    duration_ms: int
```

### 5.2 TraceResponse

```python
class TraceResponse(BaseModel):
    """استجابة التتبع."""
    
    trace_id: str
    steps: list[TraceStep]
    total_duration_ms: int
```

---

**آخر تحديث**: أبريل 2026
