# 🕌 دليل الأمان

## الأمان في Burhan

---

## 1. Authentication

### 1.1 API Keys

```python
# Middleware للتحقق من المفاتيح
async def verify_api_key(request: Request):
    key = request.headers.get("X-API-Key")
    if not key:
        raise HTTPException(status_code=401)
    return key
```

---

## 2. Rate Limiting

### 2.1 Per-User

```python
from fastapi_limiter import Limiter

limiter = Limiter(key_func=get_user_id)

@limiter.limit("10/minute")
async def ask_question(request):
    pass
```

---

## 3. Input Validation

### 3.1 Sanitization

```python
def sanitize_input(text: str) -> str:
    # إزالة أي JavaScript
    text = re.sub(r"<script.*?</script>", "", text)
    return text.strip()
```

---

## 4. Data Privacy

### 4.1 PII Handling

```python
# عدم تخزين أسئلة المستخدمين
async def log_question(query: str, intent: str):
    # Log بدون السؤال الفعلي
    logger.info(f"Intent: {intent}")
```

---

**آخر تحديث**: أبريل 2026