# 🕌 دليل الـ Router والتصنيف

## شرح نظام التوجيه

---

## 1. Core Router

### 1.1 Router

```python
# src/core/router.py

class Router:
    """موجه الأسئلة."""
    
    def __init__(self, intent_classifier):
        self._classifier = intent_classifier
        self._intent_to_agent = {
            IntentType.ZAKAT: "fiqh:rag",
            IntentType.INHERITANCE: "fiqh:rag",
            IntentType.FIQH_HUKM: "fiqh:rag",
            IntentType.FIQH_MASAIL: "fiqh:rag",
            IntentType.HADITH_TAKHRIJ: "hadith:rag",
            IntentType.QURAN_VERSE: "tafsir:rag",
            IntentType.TAFSIR: "tafsir:rag",
            IntentType.AQEEDAH: "aqeedah:rag",
            IntentType.SEERAH: "seerah:rag",
            IntentType.HISTORY: "history:rag",
            IntentType.GENERAL_ISLAMIC: "general:rag",
        }
    
    def route(self, intent: IntentType) -> str:
        """توجيه."""
        return self._intent_to_agent.get(intent, "general:rag")
    
    def get_intent(self, query: str) -> IntentType:
        """الحصول على النية."""
        return self._classifier.classify(query).intent
```

---

## 2. Application Router

### 2.1 router Agent

```python
# src/application/router.py

class RouterAgent:
    """وكيل التوجيه."""
    
    def __init__(self, classifier):
        self._classifier = classifier
    
    async def route(self, query: str) -> RoutingDecision:
        """توجيه سؤال."""
        result = await self._classifier.classify(query)
        
        return RoutingDecision(
            intent=result.intent,
            confidence=result.confidence,
            agent_name=self._get_agent(result.intent),
            collection=self._get_collection(result.intent),
            requires_retrieval=result.requires_retrieval,
        )
```

---

## 3. Hybrid Classifier

### 3.1 MasterHybridClassifier

```python
# src/application/hybrid_classifier.py

class MasterHybridClassifier:
    """مصنف هجين."""
    
    def __init__(self, embedding_model=None):
        self._keyword = KeywordBasedClassifier()
        self._embedding = EmbeddingClassifier(embedding_model) if embedding_model else None
    
    async def classify(self, query: str) -> ClassificationResult:
        """تصنيف."""
        # Keyword first
        kw_result = await self._keyword.classify(query)
        
        if kw_result.confidence >= 0.85:
            return kw_result
        
        # Embedding fallback
        if self._embedding:
            emb_result = await self._embedding.classify(query)
            if emb_result.confidence > kw_result.confidence:
                return emb_result
        
        return kw_result
```

---

**آخر تحديث**: أبريل 2026