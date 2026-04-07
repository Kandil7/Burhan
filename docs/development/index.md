# 💻 Athar Development Guide

Complete guide for developers working on the Athar Islamic QA system.

---

## 📋 Table of Contents

- [Getting Started](#getting-started)
- [Development Workflow](#development-workflow)
- [Code Structure](#code-structure)
- [Adding New Features](#adding-new-features)
- [Testing](#testing)
- [Debugging](#debugging)
- [Code Style](#code-style)
- [Common Tasks](#common-tasks)

---

## 🚀 Getting Started

### 1. Clone and Setup

```bash
git clone https://github.com/Kandil7/Athar.git
cd Athar

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
make install-dev

# Copy environment file
cp .env.example .env
```

### 2. Start Services

```bash
# Start databases
make docker-up

# Verify services
curl http://localhost:8000/health
```

### 3. Run Tests

```bash
make test
```

---

## 🔄 Development Workflow

### Branch Strategy

```
main
├── phase-1/foundation      (merged)
├── phase-2/tools           (merged)
├── phase-3/quran-rag       (merged)
├── phase-4/rag-pipelines   (merged)
├── phase-5/frontend-deployment (merged)
└── feature/*               (new features)
```

### Creating a Feature Branch

```bash
git checkout main
git pull origin main
git checkout -b feature/my-feature
```

### Commit Message Format

```
type(scope): Description

Examples:
feat(tools): Add Zakat calculator
fix(router): Correct keyword pattern matching
docs(api): Add query endpoint examples
test(router): Add intent classification tests
refactor(orchestrator): Simplify routing logic
```

### Pull Request Process

1. **Create** feature branch
2. **Implement** changes with tests
3. **Run** linter and tests (`make lint && make test`)
4. **Push** branch to remote
5. **Open** pull request
6. **Request** review from team
7. **Merge** after approval

---

## 🗂️ Code Structure

### Backend (Python/FastAPI)

```
src/
├── config/           # Configuration
│   ├── settings.py   # Environment settings
│   └── intents.py    # Intent definitions
│
├── api/              # FastAPI application
│   ├── main.py       # App factory
│   ├── routes/       # API routes
│   └── schemas/      # Pydantic models
│
├── core/             # Core logic
│   ├── router.py     # Intent classifier
│   └── orchestrator.py # Response orchestrator
│
├── agents/           # AI agents
│   ├── base.py       # Base agent class
│   └── fiqh_agent.py # Fiqh RAG agent
│
├── tools/            # Deterministic tools
│   ├── base.py       # Base tool class
│   └── zakat_calculator.py
│
├── quran/            # Quran pipeline
│   ├── verse_retrieval.py
│   └── nl2sql.py
│
└── knowledge/        # RAG infrastructure
    ├── embedding_model.py
    └── vector_store.py
```

### Frontend (Next.js/TypeScript)

```
frontend/
├── src/
│   ├── app/          # App router pages
│   ├── components/   # React components
│   ├── lib/          # Utilities
│   └── hooks/        # React hooks
│
└── i18n/             # Internationalization
    └── messages/ar.json
```

---

## 🛠️ Adding New Features

### Adding a New Tool

**1. Create Tool Class**

```python
# src/tools/my_new_tool.py
from src.tools.base import BaseTool, ToolInput, ToolOutput

class MyNewTool(BaseTool):
    name = "my_new_tool"
    
    async def execute(self, **kwargs) -> ToolOutput:
        # Your logic here
        return ToolOutput(
            result={"message": "Hello"},
            success=True
        )
```

**2. Register with Orchestrator**

```python
# src/core/orchestrator.py
from src.tools.my_new_tool import MyNewTool

def _register_default_fallbacks(self):
    self.register_tool("my_new_tool", MyNewTool())
```

**3. Add to Intent Routing**

```python
# src/config/intents.py
INTENT_ROUTING = {
    ...
    Intent.MY_NEW_INTENT: "my_new_tool",
}
```

**4. Create API Endpoint**

```python
# src/api/routes/tools.py
@router.post("/tools/my-new-tool")
async def my_new_tool_endpoint(request: MyNewToolRequest):
    tool = MyNewTool()
    result = await tool.execute(**request.dict())
    return result
```

**5. Write Tests**

```python
# tests/test_my_new_tool.py
import pytest
from src.tools.my_new_tool import MyNewTool

@pytest.mark.asyncio
async def test_my_new_tool():
    tool = MyNewTool()
    result = await tool.execute()
    assert result.success
```

---

### Adding a New Agent

**1. Create Agent Class**

```python
# src/agents/my_new_agent.py
from src.agents.base import BaseAgent, AgentInput, AgentOutput

class MyNewAgent(BaseAgent):
    name = "my_new_agent"
    
    async def execute(self, input: AgentInput) -> AgentOutput:
        # Your logic here
        return AgentOutput(
            answer="Hello!",
            metadata={"agent": self.name}
        )
```

**2. Register with Orchestrator**

```python
# src/core/orchestrator.py
from src.agents.my_new_agent import MyNewAgent

def _register_default_fallbacks(self):
    self.register_agent("my_new_agent", MyNewAgent())
```

---

### Adding a New API Endpoint

**1. Create Route File**

```python
# src/api/routes/my_new_endpoint.py
from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(prefix="/my-endpoint", tags=["My Endpoint"])

class MyRequest(BaseModel):
    query: str

class MyResponse(BaseModel):
    answer: str

@router.post("", response_model=MyResponse)
async def my_endpoint(request: MyRequest):
    return MyResponse(answer="Hello")
```

**2. Register Router**

```python
# src/api/main.py
from src.api.routes.my_new_endpoint import router as my_endpoint_router

def create_app() -> FastAPI:
    app.include_router(my_endpoint_router, prefix=settings.api_v1_prefix)
```

---

## 🧪 Testing

### Running Tests

```bash
# All tests
make test

# Specific test file
pytest tests/test_router.py -v

# With coverage
pytest tests/ -v --cov=src --cov-report=html
```

### Writing Tests

**Unit Test Example:**

```python
import pytest
from src.tools.zakat_calculator import ZakatCalculator, ZakatAssets

class TestZakatCalculator:
    @pytest.fixture
    def calculator(self):
        return ZakatCalculator(gold_price=75, silver_price=0.9)
    
    def test_zakat_above_nisab(self, calculator):
        assets = ZakatAssets(cash=50000, gold_grams=100)
        result = calculator.calculate(assets)
        
        assert result.is_zakatable
        assert result.zakat_amount > 0
```

**Integration Test Example:**

```python
import pytest
from fastapi.testclient import TestClient
from src.api.main import app

@pytest.fixture
def client():
    return TestClient(app)

def test_query_endpoint(client):
    response = client.post(
        "/api/v1/query",
        json={"query": "ما حكم الصلاة؟"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "answer" in data
    assert "intent" in data
```

---

## 🐛 Debugging

### Backend Debugging

**1. Enable Debug Mode**

```env
# .env
DEBUG=true
LOG_LEVEL=DEBUG
```

**2. Use Python Debugger**

```python
import pdb; pdb.set_trace()
# or
breakpoint()
```

**3. View Logs**

```bash
# Docker logs
docker compose logs -f api

# Direct logs
uvicorn src.api.main:app --reload --log-level debug
```

### Frontend Debugging

**1. React DevTools**

Install React DevTools browser extension.

**2. Console Logs**

```typescript
console.log('State:', state);
console.error('Error:', error);
```

**3. Network Tab**

Use browser DevTools → Network tab to inspect API calls.

---

## 📝 Code Style

### Python Style

- Follow **PEP 8**
- Use **type hints** everywhere
- Maximum line length: **120 characters**
- Use **docstrings** for public functions

```python
async def calculate_zakat(
    assets: ZakatAssets,
    debts: float = 0.0,
    madhhab: Madhhab = Madhhab.GENERAL
) -> ZakatResult:
    """
    Calculate zakat for a complete financial picture.
    
    Args:
        assets: All zakatable assets
        debts: Outstanding debts
        madhhab: School of jurisprudence
        
    Returns:
        Complete zakat calculation result
    """
    pass
```

### TypeScript Style

- Use **strict mode**
- Prefer **const** over let
- Use **async/await** over promises
- Interface names: **PascalCase**
- Variable names: **camelCase**

```typescript
interface QueryResponse {
  query_id: string;
  intent: string;
  answer: string;
  citations: Citation[];
}
```

### Linting

```bash
# Python
make lint

# TypeScript
cd frontend && npm run lint
```

---

## 🔧 Common Tasks

### Database Operations

```bash
# Run migrations
make db-migrate

# Create new migration
make db-migrate-create message="add new table"

# Seed data
python scripts/seed_quran_data.py --sample
```

### Docker Operations

```bash
# Start services
make docker-up

# Stop services
make docker-down

# View logs
make docker-logs

# Rebuild images
docker compose -f docker/docker-compose.dev.yml build --no-cache
```

### Frontend Operations

```bash
cd frontend

# Install dependencies
npm install

# Run development server
npm run dev

# Build for production
npm run build

# Run linter
npm run lint
```

### Code Quality

```bash
# Format Python code
ruff check --fix src/ tests/
ruff format src/ tests/

# Run type checker
mypy src/

# Run all checks
make lint
```

---

## 📚 Resources

### Documentation

- [Architecture Guide](ARCHITECTURE.md)
- [API Documentation](API.md)
- [Deployment Guide](DEPLOYMENT.md)
- [RAG Guide](RAG_GUIDE.md)

### External Resources

- **FastAPI**: https://fastapi.tiangolo.com/
- **Next.js**: https://nextjs.org/
- **Qdrant**: https://qdrant.tech/
- **Fanar-Sadiq Paper**: https://arxiv.org/pdf/2603.08501.pdf

---

<div align="center">

**Development Guide Version:** 1.0  
**Last Updated:** Phase 5 Complete  
**Status:** Active Development

</div>
