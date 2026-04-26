# 🕌 دليل الاستثناءات

## شرح الاستثناءات المخصصة

---

## 1. Base Exceptions

### 1.1 BurhanError

```python
# src/core/exceptions.py

class BurhanError(Exception):
    """الخطأ الأساسي."""
    
    def __init__(self, message: str, details: dict = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message)
```

### 1.2 ConfigurationError

```python
class ConfigurationError(BurhanError):
    """خطأ التكوين."""
    pass
```

### 1.3 RetrievalError

```python
class RetrievalError(BurhanError):
    """خطأ الاسترجاع."""
    pass
```

### 1.4 VerificationError

```python
class VerificationError(BurhanError):
    """خطأ التحقق."""
    pass
```

### 1.5 GenerationError

```python
class GenerationError(BurhanError):
    """خطأ التوليد."""
    pass
```

---

## 2. Error Codes

```python
ERROR_CODES = {
    "CONFIG_001": "Configuration not found",
    "CONFIG_002": "Invalid configuration",
    "RETRIEVAL_001": "Collection not found",
    "RETRIEVAL_002": "Search failed",
    "VERIFICATION_001": "Verification failed",
    "VERIFICATION_002": "Evidence insufficient",
    "GENERATION_001": "LLM API error",
    "GENERATION_002": "Invalid response",
    "AGENT_001": "Agent not found",
    "AGENT_002": "Agent execution failed",
}
```

---

**آخر تحديث**: أبريل 2026