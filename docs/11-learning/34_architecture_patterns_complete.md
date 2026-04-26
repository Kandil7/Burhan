# 🕌 دليل أنماط التصميم الكامل

## أنماط التصميم المستخدمة في Burhan

---

## جدول المحتويات

1. [/Singleton Pattern](#1-singleton-pattern)
2. [/Factory Pattern](#2-factory-pattern)
3. [/Strategy Pattern](#3-strategy-pattern)
4. [/Repository Pattern](#4-repository-pattern)
5. [/Dependency Injection](#5-dependency-injection)

---

## 1. Singleton Pattern

### 1.1 Registry

```python
# src/core/registry.py

_registry: Optional[AgentRegistry] = None

def get_registry() -> AgentRegistry:
    """الحصول على instance الوحيد."""
    global _registry
    if _registry is None:
        _registry = AgentRegistry()
    return _registry
```

---

## 2. Factory Pattern

### 2.1 Vector Store Factory

```python
# src/indexing/vectorstores/factory.py

def create_vector_store(
    provider: str,
    **config,
) -> VectorStore:
    """Factory لـ Vector Stores."""
    
    if provider == "qdrant":
        return QdrantVectorStore(**config)
    elif provider == "weaviate":
        return WeaviateVectorStore(**config)
    else:
        raise ValueError(f"Provider not supported: {provider}")
```

### 2.2 Classifier Factory

```python
# src/application/classifier_factory.py

def build_classifier(
    embedding_model=None,
) -> FallbackChainClassifier:
    """Factory لـ Classifiers."""
    
    keyword = KeywordBasedClassifier()
    
    if embedding_model:
        return FallbackChainClassifier(
            primary=keyword,
            fallback=EmbeddingClassifier(embedding_model),
        )
    
    return keyword
```

---

## 3. Strategy Pattern

### 3.1 Retrieval Strategies

```python
# src/retrieval/strategies.py

RETRIEVAL_MATRIX = {
    "fiqh_agent": RetrievalStrategy(
        collection="fiqh_passages",
        top_k=15,
        rerank=True,
    ),
    "hadith_agent": RetrievalStrategy(
        collection="hadith_passages",
        top_k=10,
        rerank=True,
    ),
}

def get_strategy(agent_name: str) -> RetrievalStrategy:
    """الحصول على strategy."""
    return RETRIEVAL_MATRIX.get(agent_name, DEFAULT_STRATEGY)
```

---

## 4. Repository Pattern

### 4.1 Citation Repository

```python
# src/services/citation_service.py

class CitationRepository:
    """Repository للاقتباسات."""
    
    def __init__(self, db):
        self._db = db
    
    async def get_by_ids(self, ids: list[str]) -> list[Citation]:
        """الحصول على الاقتباسات."""
        pass
    
    async def save(self, citation: Citation) -> None:
        """حفظ الاقتباس."""
        pass
```

---

## 5. Dependency Injection

### 5.1 Service Locator

```python
# src/application/container.py

class Container:
    """Service Locator."""
    
    def __init__(self):
        self._services: dict = {}
    
    def register(self, name: str, service: Any) -> None:
        """تسجيل الخدمة."""
        self._services[name] = service
    
    def get(self, name: str) -> Any:
        """الحصول على الخدمة."""
        return self._services[name]
```

---

## ملخص الأنماط

| النمط | الاستخدام |
|--------|-----------|
| Singleton | Registry, Config |
| Factory | Vector Store, Classifier |
| Strategy | Retrieval, Verification |
| Repository | Citations, Documents |
| DI | Services, Use Cases |

---

**آخر تحديث**: أبريل 2026