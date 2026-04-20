# 🕌 دليل الـ Payload والمجموعات

## شرحpayload indexes ومجموعات Qdrant

---

## 1. Payload Indexes

### 1.1 FiQH Payload

```python
# src/infrastructure/qdrant/payload_indexes.py

FIQH_PAYLOAD = {
    "text": "نص المقطع",
    "book_title": "عنوان الكتاب",
    "author": "المؤلف",
    "page": "الصفحة",
    "chapter": "الفصل",
    "type": "fiqh",
    "topic": "الموضوع",
    "madhhab": "المذهب",
    "grade": None,  # fiqh doesn't have grades
}
```

### 1.2 Hadith Payload

```python
HADITH_PAYLOAD = {
    "text": "نص الحديث",
    "book_title": "صحيح البخاري/مسلم",
    "author": "room",
    " narrator": "الراوي",
    "page": "الصفحة",
    "hadith_number": "رقم الحديث",
    "grade": "sahih | hasan | daif",
}
```

### 1.3 Tafsir Payload

```python
TAFSIR_PAYLOAD = {
    "text": "التفسير",
    "book_title": "تفسير ابن كثير",
    "author": "الماوردي",
    "page": "الصفحة",
    "surah": "السورة",
    "verse": "الآية",
    "verse_arab": "النص القرآني",
}
```

---

## 2. Collection Configs

### 2.1 FiQH Collection

```python
# src/infrastructure/qdrant/collections.py

COLLECTION_CONFIGS = {
    "fiqh_passages": CollectionConfig(
        name="fiqh_passages",
        description="فقه Islamic jurisprudence",
        vector_size=1024,
        distance="Cosine",
        hnsw_config=HNSWConfig(m=16, ef_construct=128),
    ),
    "hadith_passages": CollectionConfig(
        name="hadith_passages",
        description="أحاديث نبوية",
        vector_size=1024,
        distance="Cosine",
        hnsw_config=HNSWConfig(m=16, ef_construct=128),
    ),
}
```

---

**آخر تحديث**: أبريل 2026