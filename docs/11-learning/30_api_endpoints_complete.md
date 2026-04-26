# 🕌 دليل نقاط النهاية الـ API الكامل

## شرح كل نقطة نهاية بالتفصيل

هذا الدليل يشرح كل نقاط النهاية (Endpoints) في نظام Burhan.

---

## جدول المحتويات

1. [/مقدمة](#1-مقدمة)
2. [/نقاط النهاية الرئيسية](#2-نقاط-النهاية-الرئيسية)
3. [/نقطة /ask](#3-نقطة-ask)
4. [/نقطة /search](#4-نقطة-search)
5. [/نقطة /classify](#5-نقطة-classify)
6. [/نقطة /tools](#6-نقطة-tools)
7. [/نقطة /quran](#7-نقطة-quran)
8. [/نقطة /health](#8-نقطة-health)
9. [/ملخص](#9-ملخص)

---

## 1. مقدمة

### 1.1 نظرة عامة

```
Burhan API
├── /ask                    ← سؤال وجواب (main)
├── /search                 ← بحث في الوثائق
├── /classify              ← تصنيف النية
├── /tools                ← أدوات إسلامية
├── /quran                ← أسئلة قرآنية
└── /health               ← صحة النظام
```

### 1.2.Base URL

```
Development: http://localhost:8000
Production: https://api.Burhan.islamic.ai
```

---

## 2. نقاط النهاية الرئيسية

### 2.1 جدول ملخص

| الطريقة | المسار | الوصف | الإصدار |
|---------|-------|--------|---------|
| POST | /ask | سؤال وجواب | v1 |
| POST | /api/v1/ask | سؤال وجواب | v1 |
| POST | /search | بحث | v1 |
| POST | /api/v1/search | بحث | v1 |
| POST | /classify | تصنيف النية | v1 |
| POST | /api/v1/classify | تصنيف النية | v1 |
| POST | /tools | أدوات | v1 |
| POST | /api/v1/tools | أدوات | v1 |
| POST | /quran | أسئلة قرآنية | v1 |
| POST | /api/v1/quran | أسئلة قرآنية | v1 |
| GET | /health | صحة | v1 |
| GET | / | جذر API | v1 |

---

## 3. نقطة /ask

### 3.1 الوصف

نقطة النهاية الرئيسية for answering Islamic questions.

### 3.2 الطلب

```
POST /api/v1/ask
Content-Type: application/json
```

```json
{
    "query": "ما حكم صلاة الجماعة؟",
    "language": "ar",
    "madhhab": "hanafi"
}
```

### 3.3 المعلمات

| المعلمة | النوع | مطلوب | الافتراضي | الوصف |
|---------|-------|--------|----------|-------|
| query | string | Yes | - | سؤال المستخدم |
| language | string | No | "ar" | اللغة (ar/en) |
| collection | string | No | auto | المجموعة المحددة |
| madhhab | string | No | - | المذهب المفضل |

### 3.4 الاستجابة

```json
{
    "answer": "صلاة الجماعة واجبة على كل ذكر بالغ قادر...",
    "citations": [
        {
            "source_id": "fiqh_001",
            "text": "صلاة الجماعة فرض عين...",
            "book_title": "الموسوعة الفقهية",
            "page": 150
        }
    ],
    "intent": "FIQH_HUKM",
    "confidence": 0.95,
    "processing_time_ms": 1250
}
```

### 3.5 أقسام الاستجابة

| القسم | النوع | الوصف |
|-------|-------|-------|
| answer | string | الإجابة |
| citations | list | قائمة الاقتباسات |
| intent | string | نوع النية |
| confidence | float | الثقة (0-1) |
| processing_time_ms | int | زمن المعالجة |

---

## 4. نقطة /search

### 4.1 الوصف

نقطة النهاية للبحث في الوثائق directly.

### 4.2 الطلب

```
POST /api/v1/search
Content-Type: application/json
```

```json
{
    "query": "صلاة الجماعة",
    "collection": "fiqh",
    "top_k": 5
}
```

### 4.3 المعلمات

| المعلمة | النوع | مطلوب | الافتراضي | الوصف |
|---------|-------|--------|----------|-------|
| query | string | Yes | - | عبارة البحث |
| collection | string | No | default | المجموعة |
| top_k | integer | No | 10 | عدد النتائج |
| filters | object | No | - | التصفية |

### 4.4 الاستجابة

```json
{
    "results": [
        {
            "id": "fiqh_001",
            "text": "صلاة الجماعة فرض عين...",
            "score": 0.92,
            "metadata": {
                "book_title": "الموسوعة الفقهية",
                "page": 150
            }
        }
    ],
    "total": 5,
    "query": "صلاة الجماعة"
}
```

---

## 5. نقطة /classify

### 5.1 الوصف

نقطة النهاية لتصنيف النية (Intent Classification).

### 5.2 الطلب

```
POST /classify
Content-Type: application/json
```

```json
{
    "query": "ما حكم زكاة الذهب؟"
}
```

### 5.3 المعلمات

| المعلمة | النوع | مطلوب | الوصف |
|---------|-------|-------|-------|
| query | string | Yes | السؤال |

### 5.4 الاستجابة

```json
{
    "intent": "ZAKAT",
    "confidence": 0.92,
    "language": "ar",
    "requires_retrieval": true
}
```

### 5.5 أنواع النية

```
ZAKAT                 ← زكاة
INHERITANCE           ← إرث
FIQH_HUKM             ← حكم فقهي
FIQH_MASAIL           ← مسألة فقهية
HADITH_TAKHRIJ        ← تخريج حديث
QURAN_VERSE           ← آية قرآنية
TAFSIR                ← تفسير
AQEEDAH              ← عقيدة
SEERAH               ← سيرة
HISTORY              ← تاريخ
GENERAL_ISLAMIC       ← عام
```

---

## 6. نقطة /tools

### 6.1 الوصف

نقطة النهاية لتنفيذ الأدوات الإسلامية.

### 6.2 الطلب

```
POST /api/v1/tools
Content-Type: application/json
```

```json
{
    "tool_name": "zakat_calculator",
    "parameters": {
        "gold_amount_grams": 100,
        "gold_price_per_gram": 300
    }
}
```

### 6.3 الأدوات المتاحة

| الأداة | الوصف |
|--------|-------|
| zircon_calculator | حاسبة الزكاة |
| inheritance_calculator | حاسبة الإرث |
| prayer_times | أوقات الصلاة |
| hijri_calendar | التقويم الهجري |
| dua_retrieval | الأدعية |

### 6.4 مثال - Zakat Calculator

**Input**:

```json
{
    "tool_name": "zakat_calculator",
    "parameters": {
        "gold_amount_grams": 100,
        "gold_price_per_gram": 300
    }
}
```

**Output**:

```json
{
    "success": true,
    "result": {
        "total_nisab": 25500,
        "total_zakat": 1112.5,
        "is_zakat_due": true
    }
}
```

---

## 7. نقطة /quran

### 7.1 الوصف

نقطة النهاية للأسئلة القرآنية specifically.

### 7.2 الطلب

```
POST /api/v1/quran
Content-Type: application/json
```

```json
{
    "query": "ما تفسير آية الكرسي؟"
}
```

### 7.3 المعلمات

| المعلمة | النوع | مطلوب | الوصف |
|---------|-------|-------|-------|
| query | string | Yes | السؤال |
| surah | integer | No | رقم السورة |
| verse | integer | No | رقم الآية |

### 7.4 الأنواع الفرعية

```
VERSE_LOOKUP          ← استعلام عن آية
ANALYTICS           ← إحصاءات قرآنية
INTERPRETATION      ← تفسير
QUOTATION_VALIDATION ← تحقق من اقتباس
```

---

## 8. نقطة /health

### 8.1 الوصف

نقطة النهاية للتحقق من صحة النظام.

### 8.2 الطلب

```
GET /health
```

### 8.3 الاستجابة

```json
{
    "status": "ok",
    "version": "0.5.0",
    "timestamp": "2024-04-20T10:00:00Z"
}
```

### 8.4 حالات الصحة

| الحالة | الوصف |
|--------|-------|
| ok | النظام يعمل |
| degraded | النظام يعمل but with issues |
| down | النظام متوقف |

---

## 9. نقطة / (Root)

### 9.1 الوصف

نقطة النهاية الرئيسية for API information.

### 9.2 الطلب

```
GET /
```

### 9.3 الاستجابة

```json
{
    "message": "Burhan API",
    "version": "0.5.0",
    "docs": "/docs",
    "redoc": "/redoc"
}
```

---

## 10. ملخص

### 10.1 جدول الأزمنة

| Endpoint | الزمن (ms) |
|----------|-----------|
| /ask | 500-2000 |
| /search | 50-200 |
| /classify | <50 |
| /tools | <10 |
| /quran | 100-500 |
| /health | <1 |

### 10.2 جدول الأخطاء

| الكود | الوصف |
|-------|-------|
| 400 | Bad Request - طلب غير صالح |
| 401 | Unauthorized - غير مصرح |
| 404 | Not Found - غير موجود |
| 422 | Validation Error - فشل التحقق |
| 429 | Rate Limited - كثير جداً |
| 500 | Internal Error - خطأ داخلي |
| 503 | Service Unavailable - الخدمة متوقفة |

---

**آخر تحديث**: أبريل 2026

**الإصدار**: 1.0