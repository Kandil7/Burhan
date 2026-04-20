# 🕌 دليل الواجهات والـ Interfaces

## شرح الواجهات

---

## 1. Application Interfaces

### 1.1 Intent Classifier Interface

```python
# src/application/interfaces.py

class IIntentClassifier(ABC):
    """واجهة المصنف."""
    
    @abstractmethod
    async def classify(self, query: str) -> ClassificationResult:
        """تصنيف."""
        pass
```

### 1.2 Retriever Interface

```python
class IRetriever(ABC):
    """واجهة المسترجع."""
    
    @abstractmethod
    async def search(
        self,
        query: str,
        collection: str,
        top_k: int,
    ) -> list[RetrievalResult]:
        """بحث."""
        pass
```

### 1.3 Verifier Interface

```python
class IVerifier(ABC):
    """واجهة المدقق."""
    
    @abstractmethod
    async def verify(
        self,
        answer: str,
        passages: list,
    ) -> VerificationReport:
        """تحقق."""
        pass
```

### 1.4 LLM Client Interface

```python
class ILLMClient(ABC):
    """واجهة LLM."""
    
    @abstractmethod
    async def generate(
        self,
        prompt: str,
        system_prompt: str = None,
    ) -> str:
        """توليد."""
        pass
```

---

## 2. Agent Interface

### 2.1 Collection Agent Interface

```python
# src/agents/collection/base.py

class ICollectionAgent(ABC):
    """واجهة الوكيل."""
    
    @property
    @abstractmethod
    def config(self) -> CollectionAgentConfig:
        """التكوين."""
        pass
    
    @abstractmethod
    async def execute(self, input: AgentInput) -> AgentOutput:
        """تنفيذ."""
        pass
```

---

## 3. Tool Interface

### 3.1 Tool Interface

```python
# src/tools/base.py

class ITool(ABC):
    """واجهة الأداة."""
    
    @property
    @abstractmethod
    def name(self) -> str:
        """الاسم."""
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        """الوصف."""
        pass
    
    @abstractmethod
    async def execute(self, parameters: dict) -> dict:
        """تنفيذ."""
        pass
```

---

**آخر تحديث**: أبريل 2026