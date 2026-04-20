# 🕌 دليل نظام التتبع

## شرح التتبع والـ Tracing

---

## 1. Trace Service

### 1.1 TraceService

```python
# src/application/services/trace_service.py

class TraceService:
    """خدمة التتبع."""
    
    def __init__(self, storage):
        self._storage = storage
    
    async def create_trace(self, query: str) -> str:
        """إنشاء تتبع."""
        trace_id = generate_trace_id()
        await self._storage.save({
            "trace_id": trace_id,
            "query": query,
            "steps": [],
        })
        return trace_id
    
    async def add_step(self, trace_id: str, step: dict) -> None:
        """إضافة خطوة."""
        trace = await self._storage.get(trace_id)
        trace["steps"].append(step)
        await self._storage.save(trace)
```

---

## 2. Verification Trace

### 2.1 VerificationTrace

```python
# src/verification/trace.py

class VerificationTrace(BaseModel):
    """تتبع التحقق."""
    
    trace_id: str
    steps: list[VerificationStep]
    total_duration_ms: int


class VerificationStep(BaseModel):
    """خطوة التحقق."""
    
    name: str
    status: str  # passed, failed, skipped
    duration_ms: int
    message: Optional[str]
```

---

**آخر تحديث**: أبريل 2026