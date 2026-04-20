# 🕌 دليل نظام الاسترجاع المفصل جداً

## شرح كل جزء بالتفصيل المطلق

هذا الدليل يشرح نظام الاسترجاع (Retrieval System) في Athar بالتفصيل، بما في ذلك البحث الدلالي، BM25، والدمج.

---

## جدول المحتويات

1. [/مقدمة](#1-مقدمة)
2. [/البحث الدلالي (Dense Retrieval)](#2-البحث-الدلالي-dense-retrieval)
3. [/البحث بالكلمات (BM25)](#3-البحث-بالكلمات-bm25)
4. [/دمج النتائج (RRF)](#4-دمج-النتائج-rrf)
5. [/التصفية والترتيب](#5-التصفية-والترتيب)
6. [/ Qdrant Integration](#6- qdrant-integration)
7. [/ملخص](#7-ملخص)

---

## 1. مقدمة

### 1.1 ما هو نظام الاسترجاع؟

نظام الاسترجاع هو النظام الذي يبحث في قاعدة البيانات عن الوثائق ذات الصلة بسؤال المستخدم.

### 1.2 المكونات

```
src/retrieval/
    ├── __init__.py              # التصدير
    ├── schemas.py              # الأنماط
    ├── strategies.py         # الاستراتيجيات
    
    ├── retrievers/           # أنواع البحث
    │   ├── dense_retriever.py
    │   ├── bm25_retriever.py
    │   ├── hybrid_retriever.py
    │   ├── sparse_retriever.py
    │   ├── hierarchical_retriever.py
    │   └── multi_collection_retriever.py
    │
    ├── fusion/              # دمج النتائج
    │   └── rrf.py
    │
    ├── ranking/            # الترتيب
    │   ├── reranker.py
    │   ├── book_weighter.py
    │   ├── authority_scorer.py
    │   └── score_fusion.py
    │
    ├── aggregation/        # التجميع
    │   ├── deduper.py
    │   ├── clusterer.py
    │   └── evidence_aggregator.py
```

---

## 2. البحث الدلالي (Dense Retrieval)

### 2.1 الوصف

البحث الدلالي يستخدم التضمينات (Embeddings) للبحث عن الوثائق ذات المعنى المماثل.

### 2.2 كيف يعمل؟

```
نص السؤال: "ما حكم صلاة الجماعة؟"
    ↓
Embedding Model (BGE-M3)
    ↓
متجه السؤال: [0.1, -0.3, 0.5, ...]
    ↓
Qdrant Vector Search
    ↓
متجهات مشابهة
    ↓
ترتيب حسب التشابه
```

### 2.3 نموذج التضمين

```python
# في src/knowledge/embedding_model.py

class EmbeddingModel:
    """نموذج التضمين."""
    
    def __init__(
        self,
        model_name: str = "BAAI/bge-m3",
        device: str = "cuda",
    ):
        self.model_name = model_name
        self.device = device
        
        # تحميل النموذج
        self._model = AutoModel.from_pretrained(
            model_name,
            device_map=device,
        )
        
        #_dimension = 1024
        self.dimension = 1024
    
    async def encode(
        self,
        texts: list[str],
        batch_size: int = 32,
    ) -> list[list[float]]:
        """تشفير النصوص إلى متجهات."""
        
        # تقسيم الدفعات
        batches = self._create_batches(texts, batch_size)
        
        results = []
        for batch in batches:
            # Encode
            embeddings = self._model.encode(batch)
            results.extend(embeddings)
        
        return results
```

### 2.4 البحث في Qdrant

```python
# في src/retrieval/retrievers/dense_retriever.py

class DenseRetriever:
    """بائع البحث الدلالي."""
    
    def __init__(self, embedding_model, qdrant_client):
        self._model = embedding_model
        self._qdrant = qdrant_client
    
    async def search(
        self,
        query: str,
        collection: str,
        top_k: int = 10,
        filters: dict | None = None,
    ) -> list[RetrievalResult]:
        """بحث دلالي."""
        
        # 1. التضمين
        query_vectors = await self._model.encode([query])
        query_vector = query_vectors[0].tolist()
        
        # 2. البحث
        results = await self._qdrant.search(
            collection=collection,
            query_vector=query_vector,
            limit=top_k,
            query_filter=filters,
            with_payload=True,
        )
        
        # 3. التحويل
        return [
            RetrievalResult(
                id=result.id,
                text=result.payload.get("text", ""),
                score=result.score,
                collection=collection,
                metadata=result.payload,
            )
            for result in results
        ]
```

### 2.5 مزايا وعيوب

| المزايا | العيوب |
|--------|--------|
| يفهم المعنى | يحتاج GPU |
| يبحث بالمعنى وليس بالكلمة | أبطأ |
| يكتشف علاقات | أقل دقة للكلمات التقنية |

---

## 3. البحث بالكلمات (BM25)

### 3.1 الوصف

BM25 هو خوارزمية بحث بالكلمات المفتاحية используется في محركات البحث.

### 3.2 صيغة BM25

```
BM25 = Σ IDF(qi) × (f(qi, D) × (k1 + 1)) / 
           (f(qi, D) + k1 × (1 - b + b × |D| / avgdl))

Where:
- f(qi, D) = تردد المصطلح qi في الوثيقة D
- |D| = طول الوثيقة
- avgdl = متوسط أطوال الوثائق
- k1 = معامل التردد (typically 1.5)
- b = معيار الطول (typically 0.75)
- IDF = Log((N - n(qi) + 0.5) / (n(qi) + 0.5))
```

### 3.3 التنفيذ

```python
# في src/retrieval/retrievers/bm25_retriever.py

import math

class BM25Retriever:
    """بائع BM25."""
    
    def __init__(self, index):
        self._index = index
        self._k1 = 1.5
        self._b = 0.75
    
    async def search(
        self,
        query: str,
        collection: str,
        top_k: int = 10,
    ) -> list[RetrievalResult]:
        """بحث BM25."""
        
        # 1. تقسيم السؤال
        query_tokens = self._tokenize(query)
        
        # 2. حساب Scores
        scores = {}
        
        for doc_id, doc in self._index.documents.items():
            doc_tokens = self._tokenize(doc.text)
            score = self._bm25_score(query_tokens, doc_tokens)
            if score > 0:
                scores[doc_id] = score
        
        # 3. ترتيب
        sorted_docs = sorted(
            scores.items(),
            key=lambda x: x[1],
            reverse=True,
        )[:top_k]
        
        return [
            RetrievalResult(
                id=doc_id,
                text=self._index.documents[doc_id].text,
                score=score,
                collection=collection,
                metadata=self._index.documents[doc_id].metadata,
            )
            for doc_id, score in sorted_docs
        ]
    
    def _tokenize(self, text: str) -> list[str]:
        """تقسيم إلى كلمات."""
        # إزالة التشكيل
        text = re.sub(r"[\u064B-\u0652]", "", text)
        # التقسيم
        return re.findall(r"[\u0600-\u06FFa-zA-Z]+", text.lower())
    
    def _bm25_score(
        self,
        query_tokens: list[str],
        doc_tokens: list[str],
    ) -> float:
        """حسابScore BM25."""
        
        doc_len = len(doc_tokens)
        avg_doc_len = self._index.avg_doc_len
        
        score = 0.0
        
        for term in query_tokens:
            # تردد المصطلح
            tf = doc_tokens.count(term)
            if tf == 0:
                continue
            
            # IDF
            df = self._index.doc_freq.get(term, 0)
            idf = math.log(
                (self._index.num_docs - df + 0.5) / (df + 0.5) + 1
            )
            
            # BM25
            numerator = tf * (self._k1 + tf)
            denominator = tf + self._k1 * (
                1 - self._b + self._b * doc_len / avg_doc_len
            )
            
            score += idf * (numerator / denominator)
        
        return score
```

### 3.4 مزايا وعيوب

| المزايا | العيوب |
|--------|--------|
| سريع جداً | لا يفهم المعنى |
| لا يحتاج GPU | يبحث بالكلمة حرفياً |
| دقة عالية للكلمات التقنية | يفقد المرادفات |

---

## 4. دمج النتائج (RRF)

### 4.1 الوصف

Reciprocal Rank Fusion يدمج نتائج طرق بحث متعددة في قائمة واحدة مرتبة.

### 4.2 الصيغة

```
RRF(doc) = Σ 1 / (k + rank(doc))

Where:
- k = معامل الانتظام (typically 60)
- rank(doc) = ترتيب الوثيقة في القائمة i
```

### 4.3 التنفيذ

```python
# في src/retrieval/fusion/rrf.py

class ReciprocalRankFusion:
    """دمج الترتيب المتبادل."""
    
    def __init__(self, k: int = 60):
        self._k = k
    
    def fuse(
        self,
        result_lists: list[list[RetrievalResult]],
    ) -> list[RetrievalResult]:
        """دمج النتائج."""
        
        # 1. حساب Scores
        doc_scores: dict[str, float] = {}
        
        for results in result_lists:
            for rank, result in enumerate(results):
                doc_id = result.id
                
                # RRF
                contribution = 1.0 / (self._k + rank + 1)
                doc_scores[doc_id] = (
                    doc_scores.get(doc_id, 0.0) + contribution
                )
        
        # 2. ترتيب
        sorted_docs = sorted(
            doc_scores.items(),
            key=lambda x: x[1],
            reverse=True,
        )
        
        # 3. إعادة النتائج
        return [doc_id for doc_id, _ in sorted_docs]
```

### 4.4 مثال

```
البحث الدلالي:
1. Doc A - 0.95
2. Doc B - 0.90
3. Doc C - 0.85

البحث BM25:
1. Doc B - 0.85
2. Doc D - 0.80
3. Doc A - 0.75

RRF (k=60):
Doc A: 1/(60+0) + 1/(60+2) = 0.0164 + 0.0161 = 0.0325
Doc B: 1/(60+1) + 1/(60+0) = 0.0164 + 0.0161 = 0.0325
Doc C: 1/(60+2)              = 0.0161
Doc D: 1/(60+1)              = 0.0164

Final Order: A, B, C, D
```

---

## 5. التصفية والترتيب

### 5.1 التصفية

```python
# filters can be applied to search
filters = {
    "type": "fiqh",           #필tering by field
    "grade$in": ["sahih", "hasan"],  # Filtering by list
    "book_title$eq": "الموسوعة",   # Equality
    "page$gte": 100,           # Greater than
}
```

### 5.2 الترتيب

```python
# Reranker يعيد الترتيب
class Reranker:
    """معید الترتيب."""
    
    async def rerank(
        self,
        query: str,
        results: list[RetrievalResult],
    ) -> list[RetrievalResult]:
        """إعادة الترتيب."""
        
        # Encode query and results
        query_emb = await self._model.encode([query])
        result_embs = await self._model.encode([r.text for r in results])
        
        # Calculate similarity
        scores = [
            cosine_similarity(query_emb, result_emb)
            for result_emb in result_embs
        ]
        
        # Sort
        sorted_results = sorted(
            zip(results, scores),
            key=lambda x: x[1],
            reverse=True,
        )
        
        return [r for r, _ in sorted_results]
```

---

## 6. Qdrant Integration

### 6.1 الوصف

Qdrant هو قاعدة البيانات التي ت storing المتجهات والبحث.

### 6.2 المجموعات

```
Qdrant Collections:
- fiqh_passages: 1.2M vectors
- hadith_passages: 800K vectors
- tafsir_passages: 500K vectors
- aqeedah_passages: 300K vectors
- general_passages: 1M vectors
```

### 6.3 هيكل المجموعات

```python
# Collection Structure
{
    "name": "fiqh_passages",
    "vector_size": 1024,
    "distance": "Cosine",
    "hnsw": {
        "m": 16,
        "ef_construct": 128,
        "ef": 200
    }
}
```

### 6.4 البحث

```python
# في src/infrastructure/qdrant/client.py

class QdrantClient:
    """عميل Qdrant."""
    
    async def search(
        self,
        collection: str,
        query_vector: list[float],
        limit: int = 10,
        query_filter: dict | None = None,
        with_payload: bool = True,
    ) -> list[SearchResult]:
        """بحث."""
        
        results = await self._client.search(
            collection_name=collection,
            query_vector=query_vector,
            limit=limit,
            query_filter=query_filter,
            with_payload=with_payload,
        )
        
        return results
```

---

## 7. ملخص

### 7.1 المخطط العام

```
User Query
    │
    ├─ Semantic Search (Dense)
    │   └─ Query Embedding + Qdrant
    │
    ├─ Keyword Search (BM25)
    │   └─ Tokenize + BM25 Score
    │
    └─ RRF Merge
        └─ Combined Results
```

### 7.2 جدول الأزمنة

| الخطوة | الزمن (ms) |
|---------|-----------|
| Dense Embedding | 50-100 |
| Qdrant Search | 10-50 |
| BM25 Tokenize | 1-5 |
| BM25 Score | 5-20 |
| RRF Merge | 1-5 |
| **الإجمالي** | **70-200** |

### 7.3 تكوين الاسترجاع

```python
RETRIEVAL_CONFIG = {
    "hybrid": {
        "dense_top_k": 20,
        "bm25_top_k": 20,
        "fusion_top_k": 10,
        "rrf_k": 60,
    },
    "filters": {
        "type": "fiqh",
        "source": "trusted",
    },
    "rerank": True,
}
```

---

**آخر تحديث**: أبريل 2026

**الإصدار**: 1.0