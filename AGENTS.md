# AGENTS.md - Agentic Coding Guidelines for Burhan

This file provides guidelines and commands for agentic coding agents working on the Burhan Islamic QA system.

---

## Project Overview

Burhan is a multi-agent Islamic QA system with ~200+ Python files, built on FastAPI with:
- **Config-backed agents**: YAML configs in `config/agents/`, prompts in `prompts/`
- **v2 Architecture**: Collection agents in `src/agents/collection/`
- **Retrieval layer**: `src/retrieval/` (hybrid, BM25, dense)
- **Verification layer**: `src/verification/` (quote validation, hadith grading)

---

## Build/Lint/Test Commands

### Running Tests

```bash
# All tests
pytest

# Single test file
pytest tests/test_config_backed_agents.py

# Single test function
pytest tests/test_config_backed_agents.py::test_fiqh_agent_config -v

# With coverage
pytest --cov=src --cov-report=term-missing

# Fast: skip slow tests
pytest -m "not slow"

# Run only integration tests
pytest tests/integration/
```

### Linting

```bash
# Ruff (fast linter)
ruff check src/ tests/

# Auto-fix
ruff check src/ --fix

# Type checking
mypy src/

# All checks (ruff + mypy)
ruff check src/ && mypy src/
```

### Development Server

```bash
# Run API server
uvicorn src.api.main:app --reload --port 8000

# With custom host
uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload
```

---

## Code Style Guidelines

### Import Organization (PEP 8 + Ruff)

```python
# 1. Standard library
import os
import re
from typing import Optional, List

# 2. Third-party
import structlog
from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

# 3. Local application
from src.agents.collection.base import CollectionAgent
from src.config import settings
from src.retrieval import HybridSearcher

# 4. Relative imports (when needed)
from ..utils import helper_function
```

### Naming Conventions

| Element | Convention | Example |
|---------|------------|---------|
| Classes | PascalCase | `FiqhCollectionAgent` |
| Functions | snake_case | `get_config_manager()` |
| Variables | snake_case | `agent_config` |
| Constants | UPPER_SNAKE | `MAX_RETRIEVAL_RESULTS` |
| Private | prefix `_` | `_private_function()` |
| Type aliases | PascalCase | `AgentRegistry` |

### Type Annotations

**Always use type hints for:**
- Function arguments and return values
- Class attributes (in dataclasses/Pydantic)
- Complex variables

```python
# Good
def process_query(
    query: str,
    top_k: int = 10,
    filters: Optional[Dict[str, Any]] = None,
) -> List[RetrievalResult]:
    ...

# Avoid
def process_query(query, top_k=10, filters=None):
    ...
```

### Pydantic Models

```python
from pydantic import BaseModel, Field
from typing import Optional

class AgentConfig(BaseModel):
    """Agent configuration model."""
    
    name: str = Field(description="Agent name")
    collection: str = Field(default="default")
    top_k: int = Field(default=10, ge=1, le=100)
    
    model_config = {"extra": "forbid"}  # No extra fields
```

### Error Handling

```python
# Use custom exceptions for domain errors
from src.core.exceptions import BurhanError, ConfigurationError

# Raise with context
raise ConfigurationError(
    f"Config not found for agent: {agent_name}"
) from None

# Handle gracefully
try:
    result = await agent.execute(input)
except BurhanError as e:
    logger.warning(f"Agent failed: {e}")
    return fallback_response()
```

### Async/Await

```python
# Use async for I/O operations
async def get_embeddings(texts: List[str]) -> List[List[float]]:
    return await embedding_model.encode(texts)

# Don't block in async functions - use await
async def process():
    results = await asyncio.gather(*[fetch(i) for i in items])
    return results
```

### Documentation

```python
def retrieve_passages(
    query: str,
    collection: str,
    top_k: int = 10,
) -> List[Passage]:
    """
    Retrieve relevant passages for a query.
    
    Args:
        query: User query string
        collection: Qdrant collection name
        top_k: Number of results to return
        
    Returns:
        List of passage objects with content and metadata
    """
    ...
```

---

## v2 Architecture Patterns

### Collection Agents (Canonical)

```python
# Use config-backed agents
from src.agents.collection import FiqhCollectionAgent, CollectionAgentConfig
from src.config import get_config_manager

# Load config and create agent
manager = get_config_manager()
config = manager.get_collection_agent_config("fiqh")
agent = FiqhCollectionAgent(config=config)
```

### Legacy vs v2

- **v2 (recommended)**: `src/agents/collection/fiqh.py`
- **Legacy (deprecated)**: `src/agents/fiqh_agent.py`

Use v2 paths for new code. Legacy imports still work with warnings.

---

## Common Patterns

### FastAPI Routes (Thin)

```python
# Routes should only validate and delegate
ask_router = APIRouter(prefix="/ask")

@ask_router.post("", response_model=AskResponse)
async def ask_question(request: AskRequest) -> AskResponse:
    # 1. Validate (Pydantic does this)
    # 2. Delegate to use case
    result = await answer_query_use_case.execute(request)
    # 3. Return response
    return result
```

### Use Cases

```python
# src/application/use_cases/answer_query.py
class AnswerQueryUseCase:
    def __init__(self, agent_registry: AgentRegistry):
        self.agents = agent_registry
        
    async def execute(self, request: AskRequest) -> AskResponse:
        # Business logic here
        ...
```

---

## File Structure (Quick Reference)

```
src/
├── agents/collection/     # v2 CollectionAgents (use this)
├── application/           # Use cases, routing, services
├── config/               # Agent config manager, YAML loader
├── config_runtime/      # Settings, runtime config
├── domain/              # Domain models (intents, etc.)
├── retrieval/            # Hybrid, BM25, dense retrievers
├── verification/         # Quote validation, hadith grading
├── infrastructure/      # Qdrant, LLM, Redis clients
├── generation/          # Answer composers, prompts
├── tools/               # Zakat, inheritance calculators
└── api/                 # FastAPI routes, schemas, middleware
```

---

## Important Notes

1. **Configuration**: All agent configs are in YAML (`config/agents/*.yaml`), prompts in `prompts/`
2. **Lazy Deprecation**: Legacy imports show warnings but still work
3. **Verification First**: Generation only consumes verified evidence
4. **Async First**: Use async/await for all I/O operations
5. **Type Safety**: Enable mypy checks before committing

---

## Testing Guidelines

- Name test files: `test_*.py`
- Name test functions: `test_*`
- Use `pytest.mark.asyncio` for async tests
- Group related tests in classes: `class TestAgentConfig:`
- Use fixtures from `conftest.py` when available