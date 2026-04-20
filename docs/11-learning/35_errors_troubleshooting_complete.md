# 🕌 دليل الأخطاء واستكشاف المشاكل

## حل المشاكل الشائعة

---

## جدول المحتويات

1. [/أخطاء API](#1-أخطاء-api)
2. [/أخطاء LLM](#2-أخطاء-llm)
3. [/أخطاء Qdrant](#3-أخطاء-qdrant)
4. [/أخطاء الوكلاء](#4-أخطاء-الوكلاء)

---

## 1. أخطاء API

### 1.1 400 Bad Request

**السبب**: طلب غير صالح

**الحل**: تحقق من أن `query` موجود:

```json
{
    "query": "ما حكم الصلاة؟"
}
```

### 1.2 422 Validation Error

**السبب**: فشل التحقق من صحة البيانات

**الحل**: تحقق من أنواع البيانات:

```json
{
    "query": 123  // خطأ - يجب أن يكون string
}
```

---

## 2. أخطاء LLM

### 2.1 Rate Limit Exceeded

**السبب**: تجاوز حد الاستخدام

**الحل**: انتظر 或者 استخدم نموذج آخر

### 2.2 Invalid API Key

**السبب**: مفتاح API خاطئ

**الحل**: تحقق منOPENAI_API_KEY في .env

---

## 3. أخطاء Qdrant

### 3.1 Collection Not Found

**السبب**: المجموعة غير موجودة

**الحل**: أنشئ المجموعة:

```python
await client.create_collection(
    name="fiqh_passages",
    vector_size=1024,
)
```

### 3.2 Connection Refused

**السبب**: Qdrant لا يعمل

**الحل**: تحقق من الخدمة:

```bash
docker ps | grep qdrant
```

---

## 4. أخطاء الوكلاء

### 4.1 Agent Not Found

**السبب**: الوكيل غير مسجل

**الحل**: تحقق من التسجيل:

```python
registry.list_all()
```

### 4.2 Empty Response

**الcause**: لا توجد نتائج

**الحل**: تحقق من السؤال أوDatabase

---

## ملخص رسائل الخطأ

| الرمز | الرسالة | الحل |
|-------|---------|------|
| 400 | Bad Request | تحقق من الطلب |
| 401 | Invalid API Key | تحقق من المفتاح |
| 404 | Not Found | تحقق من المصدر |
| 422 | Validation Error | تحقق من البيانات |
| 429 | Rate Limit | انتظر |
| 500 | Internal Error | تحقق من Logs |
| 503 | Service Unavailable | تحقق من الخدمات |

---

**آخر تحديث**: أبريل 2026