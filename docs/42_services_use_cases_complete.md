# 🕌 دليل الخدمات والـ Use Cases

## شرح الخدمات

---

## 1.Ask Service

### 1.1Ask Service

```python
# src/application/services/ask_service.py

class AskService:
    """خدمة الإجابة على الأسئلة."""
    
    def __init__(self, answer_query_use_case):
        self._use_case = answer_query_use_case
    
    async def execute(self, request: AskRequest) -> AskResponse:
        """تنفيذ."""
        return await self._use_case.execute(request)
```

---

## 2. Search Service

### 2.1 Search Service

```python
# src/application/services/search_service.py

class SearchService:
    """خدمة البحث."""
    
    def __init__(self, retriever):
        self._retriever = retriever
    
    async def search(self, request: SearchRequest) -> SearchResponse:
        """بحث."""
        results = await self._retriever.search(
            query=request.query,
            collection=request.collection,
            top_k=request.top_k,
            filters=request.filters,
        )
        return SearchResponse(results=results)
```

---

## 3. Tool Service

### 3.1 Tool Service

```python
# src/application/services/tool_service.py

class ToolService:
    """خدمة الأدوات."""
    
    def __init__(self):
        self._tools: dict = {}
    
    def register_tool(self, name: str, tool):
        """تسجيل الأداة."""
        self._tools[name] = tool
    
    async def execute(self, tool_name: str, parameters: dict) -> dict:
        """تنفيذ."""
        return await self._tools[tool_name].execute(parameters)
```

---

## 4. Classify Service

### 4.1 Classify Service

```python
# src/application/services/classify_service.py

class ClassifyService:
    """خدمة التصنيف."""
    
    def __init__(self, classifier):
        self._classifier = classifier
    
    async def classify(self, query: str) -> ClassificationResult:
        """تصنيف."""
        return await self._classifier.classify(query)
```

---

## 5. Use Cases

### 5.1 AnswerQueryUseCase

```python
# src/application/use_cases/answer_query.py

class AnswerQueryUseCase:
    """حالة استخدام الإجابة."""
    
    def __init__(self, agent_registry, router):
        self._agents = agent_registry
        self._router = router
    
    async def execute(self, request) -> AnswerQueryOutput:
        """تنفيذ."""
        # 1. Classification
        decision = await self._router.route(request.query)
        
        # 2. Get Agent
        agent = self._agents.get(decision.route)
        
        # 3. Execute
        result = await agent.execute(AgentInput.from_request(request))
        
        # 4. Response
        return AnswerQueryOutput.from_result(result)
```

---

### 5.2 RunRetrievalUseCase

```python
# src/application/use_cases/run_retrieval.py

class RunRetrievalUseCase:
    """حالة استخدام الاسترجاع."""
    
    def __init__(self, retriever):
        self._retriever = retriever
    
    async def execute(self, request) -> list[RetrievalResult]:
        """تنفيذ."""
        return await self._retriever.search(
            query=request.query,
            collection=request.collection,
            top_k=request.top_k,
        )
```

---

### 5.3 ClassifyQueryUseCase

```python
# src/application/use_cases/classify_query.py

class ClassifyQueryUseCase:
    """حالة استخدام التصنيف."""
    
    def __init__(self, classifier):
        self._classifier = classifier
    
    async def execute(self, query: str) -> ClassificationResult:
        """تصنيف."""
        return await self._classifier.classify(query)
```

---

### 5.4 RunToolUseCase

```python
# src/application/use_cases/run_tool.py

class RunToolUseCase:
    """حالة استخدام الأدوات."""
    
    def __init__(self, tool_service):
        self._tool_service = tool_service
    
    async def execute(self, tool_name: str, parameters: dict) -> dict:
        """تنفيذ."""
        return await self._tool_service.execute(tool_name, parameters)
```

---

**آخر تحديث**: أبريل 2026