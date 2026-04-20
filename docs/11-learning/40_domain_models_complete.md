# 🕌 دليل النماذج المجال完整

## شرح النماذج المجال

---

## 1. Intent Models

### 1.1 IntentType Enum

```python
# src/domain/intents.py

class IntentType(str, Enum):
    """أنواع النية."""
    
    ZAKAT = "ZAKAT"
    INHERITANCE = "INHERITANCE"
    Fiqh_HUKM = "FIQH_HUKM"
    Fiqh_MASAIL = "FIQH_MASAIL"
    HADITH_TAKHRIJ = "HADITH_TAKHRIJ"
    QURAN_VERSE = "QURAN_VERSE"
    TAFSIR = "TAFSIR"
    AQEEDAH = "AQEEDAH"
    SEERAH = "SEERAH"
    HISTORY = "HISTORY"
    GENERAL_ISLAMIC = "ISLAMIC_KNOWLEDGE"
    USUL_FIQH = "USUL_FIQH"
    LANGUAGE = "LANGUAGE"
    TAZKIYAH = "TAZKIYAH"
```

### 1.2 Intent Priority

```python
INTENT_PRIORITY = {
    IntentType.ZAKAT: 1,
    IntentType.INHERITANCE: 2,
    IntentType.FIQH_HUKM: 3,
    IntentType.FIQH_MASAIL: 4,
    IntentType.HADITH_TAKHRIJ: 5,
    IntentType.QURAN_VERSE: 6,
    IntentType.TAFSIR: 7,
    IntentType.AQEEDAH: 8,
    IntentType.SEERAH: 9,
    IntentType.HISTORY: 10,
    IntentType.GENERAL_ISLAMIC: 20,
}
```

---

## 2. Evidence Models

### 2.1 Evidence

```python
# src/domain/evidence.py

class Evidence(BaseModel):
    """الدليل."""
    
    id: str
    text: str
    source: str
    type: str  # quran, hadith, ijma, qiyas
    strength: float  # 0-1
    metadata: dict
```

---

## 3. Citation Models

### 3.1 Citation

```python
# src/domain/citations.py

class Citation(BaseModel):
    """الاقتباس."""
    
    source_id: str
    text: str
    book_title: str
    author: str
    page: int
    chapter: str
    grade: str  # sahih, hasan, daif
```

---

## 4. Collection Models

### 4.1 Collection

```python
# src/domain/collections.py

class Collection(BaseModel):
    """المجموعة."""
    
    name: str
    description: str
    document_count: int
    vector_count: int
    embedding_model: str
    chunk_size: int
```

---

## 5. Decision Models

### 5.1 RoutingDecision

```python
# src/domain/decisions.py

class RoutingDecision(BaseModel):
    """قرار التوجيه."""
    
    intent: IntentType
    confidence: float
    agent_name: str
    collection: str
    requires_retrieval: bool
```

---

**آخر تحديث**: أبريل 2026