# 🕌 دليل البنية التحتية

## شرح التكاملات الخارجية

---

## 1. Qdrant Client

### 1.1 Qdrant Client

```python
# src/infrastructure/qdrant/client.py

class QdrantClient:
    """عميل Qdrant."""
    
    def __init__(self, host: str, port: int, api_key: str):
        self._client = Qdrant(host=host, port=port, api_key=api_key)
    
    async def search(
        self,
        collection: str,
        query_vector: list[float],
        limit: int = 10,
        query_filter: dict = None,
        with_payload: bool = True,
    ) -> list[SearchResult]:
        """بحث."""
        return await self._client.search(
            collection_name=collection,
            query_vector=query_vector,
            limit=limit,
            query_filter=query_filter,
            with_payload=with_payload,
        )
    
    async def upsert(self, collection: str, points: list[Point]) -> None:
        """تخزين."""
        await self._client.upsert(
            collection_name=collection,
            points=points,
        )
    
    async def create_collection(
        self,
        name: str,
        vector_size: int = 1024,
    ) -> None:
        """إنشاء مجموعة."""
        await self._client.create_collection(
            collection_name=name,
            vectors_config=VectorParams(size=vector_size),
        )
```

---

## 2. Qdrant Collections

### 2.1 Collections Manager

```python
# src/infrastructure/qdrant/collections.py

class QdrantCollections:
    """مدير المجموعات."""
    
    COLLECTIONS = {
        "fiqh_passages": {
            "description": "FiQH passages",
            "vector_size": 1024,
        },
        "hadith_passages": {
            "description": "Hadith passages",
            "vector_size": 1024,
        },
        "tafsir_passages": {
            "description": "Tafsir passages",
            "vector_size": 1024,
        },
    }
```

---

## 3. Redis Client

### 3.1 Redis Cache

```python
# src/infrastructure/redis.py

class RedisClient:
    """عميل Redis."""
    
    def __init__(self, url: str):
        self._client = Redis.from_url(url)
    
    async def get(self, key: str) -> Optional[str]:
        """الحصول."""
        return await self._client.get(key)
    
    async def set(
        self,
        key: str,
        value: str,
        ex: int = 3600,
    ) -> None:
        """تعيين."""
        await self._client.set(key, value, ex=ex)
    
    async def delete(self, key: str) -> None:
        """حذف."""
        await self._client.delete(key)
```

---

## 4. LLM Clients

### 4.1 OpenAI Client

```python
# src/infrastructure/llm/openai_client.py

class OpenAIClient:
    """عميل OpenAI."""
    
    def __init__(self, api_key: str):
        import openai
        openai.api_key = api_key
    
    async def generate(
        self,
        messages: list,
        model: str = "gpt-4",
        temperature: float = 0.7,
    ) -> str:
        """توليد."""
        response = await openai.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
        )
        return response.choices[0].message.content
```

---

## 5. Container / DI

### 5.1 Container

```python
# src/application/container.py

class Container:
    """حاوية الخدمات."""
    
    def __init__(self):
        self._services: dict = {}
        self._singletons: dict = {}
    
    def register(self, name: str, factory) -> None:
        """تسجيل."""
        self._services[name] = factory
    
    def register_singleton(self, name: str, instance) -> None:
        """تسجيل Singleton."""
        self._singletons[name] = instance
    
    def get(self, name: str):
        """الحصول على الخدمة."""
        if name in self._singletons:
            return self._singletons[name]
        
        factory = self._services[name]
        return factory(self)
```

---

**آخر تحديث**: أبريل 2026