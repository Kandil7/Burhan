# 🕌 دليل الاختبارات

## شرح الاختبارات

---

## 1. أنواع الاختبارات

### 1.1 Unit Tests

```python
# tests/test_zakat_calculator.py

def test_zakat_calculation():
    calc = ZakatCalculator()
    result = calc.calculate({
        "gold_amount_grams": 100,
        "gold_price_per_gram": 300,
    })
    assert result["is_zakat_due"] == True
    assert result["total_zakat"] == 1112.5
```

### 1.2 Integration Tests

```python
# tests/test_ask_endpoint.py

@pytest.mark.asyncio
async def test_ask_endpoint():
    response = await client.post("/api/v1/ask", json={
        "query": "ما حكم الصلاة؟"
    })
    assert response.status_code == 200
```

---

## 2. تشغيل الاختبارات

```bash
# تشغيل الكل
pytest

# تشغيل مع Coverage
pytest --cov=src

# تشغيل اختبار معين
pytest tests/test_zakat_calculator.py
```

---

## 3. التغطية

```
Unit Tests: 80%
Integration Tests: 70%
E2E Tests: 50%
```

---

**آخر تحديث**: أبريل 2026