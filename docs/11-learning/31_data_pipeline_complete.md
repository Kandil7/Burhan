# 🕌 دليل خطوط البيانات مفصل جداً

## شرح كل جزء في خط البيانات

---

## جدول المحتويات

1. [/مقدمة](#1-مقدمة)
2. [/مخططات البيانات](#2-مخططات-البيانات)
3. [/Ingestion Pipeline](#3-ingestion-pipeline)
4. [/Build Indexes](#4-build-indexes)
5. [/Qdrant Collections](#5-qdrant-collections)
6. [/Metadata Sync](#6-metadata-sync)
7. [/ملخص](#7-ملخص)

---

## 1. مقدمة

### 1.1 ما هو خط البيانات؟

خط البيانات هو النظام الذي يحول documents raw إلى vectors مخزنة في Qdrant.

### 1.2流程

```
المصادر (PDF, TXT, Markdown)
    ↓
استخراج النص
    ↓
تقسيم إلى chunks
    ↓
توليد التضمينات
    ↓
Qdrant
    ↓
API
```

---

## 2. مخططات البيانات

```
src/
├── indexing/              ← خط البيانات
│   ├── __init__.py
│   ├── pipelines/
│   │   ├── ingest_Burhan.py    ← الاست ingestion الرئيسي
│   │   ├── build_catalog_indexes.py
│   │   ├── build_seerah_chunks_camel.py
│   │   ├── analyze_chunks.py
│   │   └── sync_metadata.py
│   │
│   └── vectorstores/        ← تخزين المتجهات
│       ├── base.py
│       ├── qdrant_store.py
│       ├── factory.py
│       ├── hybrid_client.py
│       └── hybrid_config.py
```

---

## 3. Ingestion Pipeline

### 3.1 الوصف

```python
# src/indexing/pipelines/ingest_Burhan.py

class IngestAthropipeline:
    """خط است ingestion."""
    
    async def run(
        self,
        source_dir: str,
        collection: str,
    ) -> IngestResult:
        """تشغيل الخط."""
        
        # 1. قراءة المصادر
        documents = await self._load_documents(source_dir)
        
        # 2. استخراج النص
        texts = await self._extract_texts(documents)
        
        # 3. تقسيم إلى chunks
        chunks = await self._split_chunks(texts)
        
        # 4. توليد التضمينات
        embeddings = await self._generate_embeddings(chunks)
        
        # 5. تخزينفي Qdrant
        await self._store_in_qdrant(collection, chunks, embeddings)
        
        return IngestResult(
            documents=len(documents),
            chunks=len(chunks),
            stored=len(chunks),
        )
```

### 3.2 تقسيم التقسيم (Chunking)

```python
def _split_chunks(self, texts: list[Text]) -> list[Chunk]:
    """تقسيم إلى chunks."""
    
    chunks = []
    
    for text in texts:
        # تقسيم by length
        if len(text) > self.chunk_size:
            sub_chunks = self._split_by_length(
                text,
                self.chunk_size,
                self.overlap,
            )
            chunks.extend(sub_chunks)
        else:
            chunks.append(Chunk(text))
    
    return chunks

def _split_by_length(
    self,
    text: str,
    chunk_size: int,
    overlap: int,
) -> list[Chunk]:
    """تقسيم by length."""
    
    chunks = []
    start = 0
    
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]
        
        chunks.append(Chunk(
            text=chunk,
            metadata={"start": start, "end": end}
        ))
        
        start += chunk_size - overlap
    
    return chunks
```

---

## 4. Build Indexes

### 4.1 Build Collection Indexes

```python
# src/indexing/pipelines/build_catalog_indexes.py

class BuildCatalogIndexes:
    """بناء فهارس المجموعة."""
    
    async def run(
        self,
        collection: str,
    ) -> IndexResult:
        """بناء الفهرس."""
        
        # 1. تحميل documents
        documents = await load_collection_documents(collection)
        
        # 2. استخراج
        texts = [doc.text for doc in documents]
        
        # 3. BM25 Index
        bm25_index = self._build_bm25_index(texts)
        
        # 4. حفظ
        await self._save_index(collection, bm25_index)
        
        return IndexResult(documents=len(documents))
```

---

## 5. Qdrant Collections

### 5.1 المجموعات

```
Qdrant:
├── fiqh_passages         ← 1.2M vectors
├── hadith_passages      ← 800K vectors
├── tafsir_passages     ← 500K vectors
├── aqeedah_passages    ← 300K vectors
├── seerah_passages    ← 400K vectors
├── history_passages   ← 500K vectors
├── usul_fiqh_passages ← 200K vectors
├── language_passages ← 300K vectors
├── general_passages  ← 1M vectors
└── tazkiyah_passages ← 200K vectors
```

### 5.2 Configuration

```python
# Collection config
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

---

## 6. Metadata Sync

### 6.1 مزامنة البيانات الوصفية

```python
# src/indexing/pipelines/sync_metadata.py

class SyncMetadata:
    """مزامنة البيانات الوصفية."""
    
    async def run(self) -> SyncResult:
        """تشغيل المزامنة."""
        
        # 1. تحميل من Qdrant
        qdrant_ids = await self._get_all_ids()
        
        # 2. تحميل من catalog
        catalog_ids = await self._get_catalog_ids()
        
        # 3. مقارنة
        missing = set(catalog_ids) - set(qdrant_ids)
        extra = set(qdrant_ids) - set(catalog_ids)
        
        # 4. تقرير
        return SyncResult(
            missing=list(missing),
            extra=list(extra),
            synced=len(catalog_ids),
        )
```

---

## 7. ملخص

### 7.1 إحصائيات

| Collection | Vectors | Size |
|-----------|---------|------|
| fiqh_passages | 1.2M | 4.8 GB |
| hadith_passages | 800K | 3.2 GB |
| tafsir_passages | 500K | 2 GB |
| aqeedah_passages | 300K | 1.2 GB |
| general_passages | 1M | 4 GB |

### 7.2 Process Flow

```
Source → Extract → Chunk → Embed → Store → Serve
```

---

**آخر تحديث**: أبريل 2026