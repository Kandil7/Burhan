# 🕌 Athar Source Code Complete Guide

## Complete Module-by-Module Documentation

This document provides a comprehensive explanation of every module and file in the `src/` directory.

---

## 📁 src/agents/

### Purpose
Contains all AI agents that process user queries. Each agent is specialized for a specific Islamic knowledge domain.

### Files

#### `src/agents/base.py` (CORE - Created April 2026)
**Purpose**: Core types used by all agents - this file was missing and has been created to fix broken imports.

**Exports**:
```python
class Citation(BaseModel):
    source_id: str          # Document ID
    text: str              # Quoted text
    book_title: str | None
    page: int | None
    grade: str | None     # Hadith grade (sahih, hasan, daif)
    url: str | None
    metadata: dict

class AgentInput(BaseModel):
    query: str             # User query
    language: str        # "ar" or "en"
    collection: str | None
    metadata: dict

class AgentOutput(BaseModel):
    answer: str           # Generated answer
    citations: list[Citation]
    metadata: dict
    confidence: float
    requires_human_review: bool

class BaseAgent:
    async def execute(self, input: AgentInput) -> AgentOutput

def strip_cot_leakage(text: str) -> str:
    """Removes chain-of-thought markers from generated text"""
```

**Usage**: Imported by 60+ files throughout the codebase.

---

#### `src/agents/collection_agent.py` (ALIAS)
**Purpose**: Legacy alias for backward compatibility.

**Exports**:
```python
from src.agents.collection.base import (
    RetrievalStrategy,
    VerificationCheck,
    VerificationSuite,
    VerificationReport,
)
```

---

#### `src/agents/collection/` (v2 Architecture)

**Purpose**: Config-backed CollectionAgents using YAML configuration + prompt templates.

##### `src/agents/collection/__init__.py`
Exports all CollectionAgents:
- FiQHCollectionAgent
- HadithCollectionAgent  
- TafsirCollectionAgent
- AqeedahCollectionAgent
- SeerahCollectionAgent
- UsulFiqhCollectionAgent
- HistoryCollectionAgent
- LanguageCollectionAgent
- GeneralCollectionAgent
- TazkiyahCollectionAgent

---

##### `src/agents/collection/base.py` (CORE)
**Purpose**: Base classes for all CollectionAgents.

**Key Classes**:
```python
class CollectionAgentConfig(BaseModel):
    name: str           # Agent name
    collection: str    # Qdrant collection name
    top_k: int         # Number of passages to retrieve
    prompt_template: str
    system_prompt: str
    verification_enabled: bool

class RetrievalStrategy(BaseModel):
    collection: str
    top_k: int
    filters: dict | None
    rerank: bool

class VerificationCheck(BaseModel):
    name: str
    fail_policy: str    # "abstain", "warn", "proceed"
    enabled: bool

class VerificationSuite(BaseModel):
    checks: list[VerificationCheck]

class IntentLabel(str, Enum):
    # Domain-specific intents
```

**Key Functions**:
- `load_config(name)` - Load agent config from YAML
- `get_verification_suite(agent_name)` - Get verification checks

---

##### `src/agents/collection/fiqh.py`
**Purpose**: FiQH (Islamic Jurisprudence) agent - handles questions about halal/haram, rulings, etc.

**Key Methods**:
- `_load_shared_preamble()` - Load common preamble
- `_get_system_prompt()` - Build system prompt
- `_get_retrieval_query(user_query)` - Create retrieval query
- `execute(input: AgentInput)` - Main execution

**Config**: `config/agents/fiqh.yaml`
**Prompt**: `prompts/fiqh_agent.txt`

---

##### Other CollectionAgents
| Agent | Collection | Purpose |
|-------|-------------|---------|
| `hadith.py` | hadith | Hadith questions |
| `tafsir.py` | tafsir | Quran interpretation |
| `aqeedah.py` | aqeedah | Islamic theology |
| `seerah.py` | seerah | Prophet biography |
| `history.py` | history | Islamic history |
| `usul_fiqh.py` | usul_fiqh | Principles of jurisprudence |
| `language.py` | language | Arabic language |
| `general.py` | general | General Islamic knowledge |
| `tazkiyah.py` | tazkiyah | Spiritual purification |

---

## 📁 src/api/

### Purpose
FastAPI application and routes - the HTTP interface.

### Files

#### `src/api/main.py`
**Purpose**: FastAPI app creation and router setup.

**Key Code**:
```python
app = FastAPI(
    title="Athar Islamic QA API",
    version="0.5.0",
    docs_url="/docs"
)

# Include routers
app.include_router(ask_router, prefix="/api/v1")  # /api/v1/ask
app.include_router(search_router, prefix="/api/v1") # /api/v1/search
app.include_router(tools_router, prefix="/api/v1")  # /api/v1/tools
app.include_router(quran_router, prefix="/api/v1")  # /api/v1/quran
```

---

#### `src/api/routes/`

| File | Endpoint | Purpose |
|------|----------|---------|
| `ask.py` | POST /api/v1/ask | Main Q&A endpoint |
| `search.py` | POST /api/v1/search | Search documents |
| `tools.py` | POST /api/v1/tools | Execute tools (zakat, inheritance) |
| `quran.py` | POST /api/v1/quran | Quran queries |
| `classify.py` | POST /classify | Intent classification (Phase 8) |
| `health.py` | GET /health | Health check |
| `fiqh.py` | GET /api/v1/fiqh/* | FiQH-specific endpoints |

---

#### `src/api/schemas/`

**Purpose**: Pydantic models for request/response validation.

| File | Schema |
|------|--------|
| `ask.py` | AskRequest, AskResponse |
| `search.py` | SearchRequest, SearchResponse |
| `tools.py` | ToolRequest, ToolResponse |
| `quran.py` | QuranRequest, QuranResponse |
| `common.py` | CitationResponse, ErrorResponse |
| `classification.py` | ClassificationRequest, ClassificationResponse |

---

#### `src/api/middleware/`

| File | Purpose |
|------|---------|
| `security.py` | CORS, rate limiting |
| `request_logging.py` | Request/response logging |
| `request_id.py` | Add unique request ID |
| `error_handler.py` | Global error handling |

---

#### `src/api/lifespan.py`
**Purpose**: App startup/shutdown lifecycle - initializes services.

**Key Initialization**:
```python
async def lifespan(app: FastAPI):
    # 1. Load settings
    # 2. Initialize registry
    # 3. Start infrastructure (Qdrant, Redis, PostgreSQL)
    # 4. Create classifier and router
    # 5. Register agents
    yield
    # Cleanup on shutdown
```

---

## 📁 src/application/

### Purpose
Use cases, services, and application logic - the business layer.

### Subdirectories

#### `src/application/use_cases/`

| File | Purpose |
|------|---------|
| `answer_query.py` | Main query answering use case |
| `classify_query.py` | Intent classification use case |
| `run_tool.py` | Tool execution use case |
| `run_retrieval.py` | Document retrieval use case |
| `build_trace.py` | Trace building use case |

---

#### `src/application/services/`

| File | Purpose |
|------|---------|
| `ask_service.py` | Orchestrates answer query |
| `search_service.py` | Orchestrates search |
| `tool_service.py` | Executes Islamic tools |
| `classify_service.py` | Intent classification service |
| `trace_service.py` | Trace management |

---

#### `src/application/router/`

**Purpose**: Query routing and classification (Phase 8 - Hybrid Classifier).

| File | Purpose |
|------|---------|
| `router_agent.py` | Main RouterAgent |
| `hybrid_classifier.py` | MasterHybridClassifier (keyword + embedding) |
| `classifier_factory.py` | KeywordBasedClassifier |
| `embedding_classifier.py` | Embedding-based classifier |
| `orchestration.py` | Multi-agent orchestration |
| `multi_agent.py` | MultiAgentRouter |
| `risk_policy.py` | Risk assessment |

---

#### `src/application/routing/`

| File | Purpose |
|------|---------|
| `executor.py` | Execute agent queries |
| `planner.py` | Query planning |
| `intent_router.py` | Route based on intent |

---

#### `src/application/classifier_factory.py` vs `router/classifier_factory.py`

**Note**: There are TWO classifier factory files:
- `src/application/classifier_factory.py` - Creates classifier instances (FallbackChainClassifier)
- `src/application/router/classifier_factory.py` - Keyword-based classifier (QueryClassifier, KeywordBasedClassifier)

These serve different purposes and are intentionally separate.

---

## 📁 src/core/

### Purpose
Core system components: registry, exceptions, router, citation.

### Files

| File | Purpose |
|------|---------|
| `registry.py` | Agent registry - manages all agents |
| `exceptions.py` | Custom exceptions (AtharError, ConfigurationError) |
| `router.py` | Legacy query router |
| `citation.py` | Citation normalization |

---

## 📁 src/domain/

### Purpose
Domain models: intents, enums, schemas.

### Files

| File | Purpose |
|------|---------|
| `intents.py` | 16 Intent types + routing |
| `models.py` | ClassificationResult, etc. |
| `citations.py` | Citation types |

---

## 📁 src/retrieval/ (v2 Architecture)

### Purpose
Complete retrieval pipeline - well organized with subdirectories.

### Structure

```
src/retrieval/
├── __init__.py              # Main exports
├── schemas.py              # RetrievalResult, QueryType
├── strategies.py          # Retrieval strategies per agent
│
├── retrievers/           # Different retriever types
│   ├── hybrid_retriever.py
│   ├── bm25_retriever.py
│   ├── dense_retriever.py
│   ├── sparse_retriever.py
│   ├── hierarchical_retriever.py
│   └── multi_collection_retriever.py
│
├── filters/             # Query filtering
│   ├── builder.py
│   └── presets.py
│
├── fusion/              # Result fusion (RRF)
│   └── rrf.py
│
├── ranking/             # Re-ranking
│   ├── reranker.py
│   ├── book_weighter.py
│   ├── authority_scorer.py
│   └── score_fusion.py
│
├── aggregation/         # Result aggregation
│   ├── clusterer.py
│   ├── deduper.py
│   └── evidence_aggregator.py
│
├── planning/            # Retrieval planning
│   └── retrieval_plan.py
│
├── expanders            # Query expansion
│   ├── query_expander.py
│   └── islamic_synonyms.py
│
└── policies/           # Retrieval policies
    ├── collection_policy.py
    └── retrieval_policy.py
```

---

### Key Classes

```python
# src/retrieval/schemas.py
class RetrievalResult(BaseModel):
    id: str
    text: str
    score: float
    collection: str
    metadata: dict

class QueryType(str, Enum):
    SEMANTIC = "semantic"
    KEYWORD = "keyword"
    HYBRID = "hybrid"
```

---

## 📁 src/verification/ vs src/verifiers/

### Purpose
Two verification modules exist for historical reasons.

#### `src/verification/` (Wrapper - New)
**Purpose**: Empty wrapper - placeholder for future v2 verification layer.

**Exports**:
```python
from src.verification.schemas import (
    VerificationStatus,
    CheckResult,
    VerificationReport,
)
from src.verification.trace import (
    VerificationStep,
    VerificationTrace,
    generate_trace_id,
)
```

#### `src/verifiers/` (Active Implementation)
**Purpose**: Full verification implementation with deprecation warning.

**Files**:

| File | Checks |
|------|-------|
| `suite_builder.py` | Build verification suites |
| `exact_quote.py` | Quote validation |
| `source_attribution.py` | Source verification |
| `hadith_grade.py` | Hadith authenticity |
| `contradiction.py` | Check contradictions |
| `evidence_sufficiency.py` | Evidence check |
| `temporal_consistency.py` | Time-based checks |
| `school_consistency.py` | Madhhab consistency |
| `groundedness_judge.py` | Grounding check |

**Usage Note**: All collection agents import from `src.verifiers/`.

---

## 📁 src/knowledge/ (Legacy Wrapper)

### Purpose
Legacy facade that wraps `src/retrieval/`. Kept for backward compatibility.

**Files**:
- `embedding_model.py` - Embedding generation
- `vector_store.py` - Qdrant operations
- `hybrid_search.py` - Hybrid search
- `bm25_retriever.py` - BM25 search
- `query_expander.py` - Query expansion
- `hierarchical_retriever.py` - Hierarchical retrieval
- `hadith_grader.py` - Hadith grading

**Note**: Many of these wrap `src/retrieval/` modules.

---

## 📁 src/infrastructure/

### Purpose
External service integrations.

| Directory | Purpose |
|-----------|---------|
| `qdrant/` | Vector database client |
| `llm/` | LLM clients (OpenAI, Groq) |
| `redis.py` | Caching |
| `database.py` | PostgreSQL |
| `config_loader.py` | YAML config loading |

---

## 📁 src/config/ & src/config_runtime/

### Purpose
Configuration management.

| File | Purpose |
|------|---------|
| `settings.py` | App settings |
| `loader.py` | Config loader |
| `intents.py` | Intent definitions |
| `constants.py` | Constants |

---

## 📁 Other Modules

| Module | Purpose |
|--------|---------|
| `src/generation/` | Answer generation, prompts |
| `src/tools/` | Islamic tools (zakat, inheritance) |
| `src/quran/` | Quran-specific logic |
| `src/domain/` | Domain models |
| `src/evaluation/` | Evaluation metrics |
| `src/indexing/` | Document indexing |
| `src/data/` | Data processing |
| `src/utils/` | Utilities |

---

## 🚀 Quick Start

### Learning Order

1. **Start Here**:
   - `src/api/main.py` - Entry point
   - `src/api/routes/ask.py` - Main endpoint

2. **Then**:
   - `src/application/use_cases/answer_query.py` - Business logic
   - `src/application/services/ask_service.py` - Service layer

3. **Then**:
   - `src/agents/collection/` - Agent implementations
   - `src/retrieval/` - Retrieval layer

4. **Advanced**:
   - `src/application/router/hybrid_classifier.py` - Intent classification
   - `src/verifiers/` - Verification

---

## 📖 Related Documentation

- [01_project_overview.md](01_project_overview.md)
- [02_folder_structure.md](02_folder_structure.md)
- [03_api_main_entrypoint.md](03_api_main_entrypoint.md)
- [learning_path.md](learning_path.md)

---

**Last Updated**: April 2026
**Version**: 2.0