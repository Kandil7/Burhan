# Athar Complete Source Code Reference

## Every File Explained in Detail

This document provides the most comprehensive explanation of every single file in the `src/` directory. Each file is documented with its purpose, key components, dependencies, and how it fits into the overall architecture.

---

## Table of Contents

1. [Overview](#overview)
2. [Directory Structure](#directory-structure)
3. [Detailed File Documentation](#detailed-file-documentation)
   - [src/agents/](#srcagents)
   - [src/api/](#srcapi)
   - [src/application/](#srcapplication)
   - [src/config/](#srcconfig)
   - [src/config_runtime/](#srcconfig_runtime)
   - [src/core/](#srccore)
   - [src/data/](#srcdata)
   - [src/domain/](#srcdomain)
   - [src/evaluation/](#srcevaluation)
   - [src/generation/](#srcgeneration)
   - [src/indexing/](#srcindexing)
   - [src/infrastructure/](#srcinfrastructure)
   - [src/knowledge/](#srcknowledge)
   - [src/quran/](#srcquran)
   - [src/retrieval/](#srcretrieval)
   - [src/services/](#srcservices)
   - [src/tools/](#srctools)
   - [src/utils/](#srcutils)
   - [src/verification/](#srcverification)
   - [src/verifiers/](#srcverifiers)
4. [Execution Flows](#execution-flows)
5. [Key Patterns](#key-patterns)

---

## Overview

The Athar Islamic QA system is built with a multi-agent architecture that combines:

- **Retrieval-Augmented Generation (RAG)**: Semantic and keyword search to find relevant Islamic texts
- **Multi-Agent System**: Specialized agents for different Islamic domains (Fiqh, Hadith, Tafsir, etc.)
- **Verification Layer**: Multiple checks to ensure answer accuracy and citation validity
- **Hybrid Classification**: Intent routing using both keyword matching and semantic embeddings

The `src/` directory contains approximately 130+ Python files organized into 21 modules.

---

## Directory Structure

```
src/
├── agents/           # AI agents for different Islamic domains
├── api/             # FastAPI routes, schemas, middleware
├── application/    # Use cases, services, classifiers
├── config/         # YAML loaders, settings, constants
├── config_runtime/ # Runtime configuration
├── core/           # Registry, exceptions, router
├── data/           # Data processing utilities
├── domain/         # Domain models (intents, collections)
├── evaluation/    # Evaluation metrics and golden sets
├── generation/    # LLM clients, prompts, composers
├── indexing/      # Document indexing pipelines
├── infrastructure/# External services (Qdrant, Redis)
├── knowledge/     # Legacy knowledge base wrappers
├── quran/         # Quran-specific logic
├── retrieval/     # Retrieval pipeline (hybrid, BM25, dense)
├── services/      # Business services
├── tools/         # Islamic tools (zakat, inheritance)
├── utils/         # Utility functions
├── verification/  # Verification schemas and traces
└── verifiers/     # Verification implementations
```

---

## Detailed File Documentation

### src/agents/

The agents module contains all AI agents that process user queries. Each agent is specialized for a specific Islamic knowledge domain.

#### src/agents/base.py

**Purpose**: CORE TYPES - Provides base classes and types used by all agents throughout the codebase. This file was created to fix broken imports from v1→v2 migration.

**Key Components**:

| Class | Purpose |
|-------|---------|
| `Citation` | Source citation with source_id, text, book_title, page, grade, url |
| `AgentInput` | Standard input for agents with query, language, collection, metadata |
| `AgentOutput` | Standard output with answer, citations, confidence, requires_human_review |
| `BaseAgent` | Abstract base class for all agents |

**Function**: `strip_cot_leakage(text: str) -> str`
- Removes chain-of-thought leakage from generated text
- Strips patterns like "## Analysis", "<analysis>", "### Let me..."

**Why Created**: 60+ files import from `src.agents.base` but the file didn't exist during v1→v2 migration.

**Dependencies**: pydantic

**Usage**:
```python
from src.agents.base import AgentInput, AgentOutput, Citation, strip_cot_leakage
```

---

#### src/agents/collection_agent.py

**Purpose**: Legacy alias for backward compatibility. Many existing files import from this path.

**What It Does**: Re-exports from `src.agents.collection.base`

**Exports**:
```python
from src.agents.collection.base import (
    RetrievalStrategy,
    VerificationCheck,
    VerificationSuite,
    VerificationReport,
)
```

**Used By**: 
- `src/verifiers/suite_builder.py`
- `src/retrieval/strategies.py`
- Various test files

---

#### src/agents/chatbot_agent.py

**Purpose**: Main chatbot agent that orchestrates the conversation flow. Handles multi-turn conversations and maintains context.

**Key Responsibilities**:
- Manage conversation history
- Handle follow-up questions
- Maintain user context across turns
- Route to appropriate collection agents

**Main Methods**:
- `chat(message: str, history: list) -> AgentOutput`
- `_build_context(history: list) -> str`
- `_route_query(query: str) -> str`

---

#### src/agents/collection/__init__.py

**Purpose**: Central export point for all CollectionAgents in the v2 architecture.

**Exports All**:
```python
from src.agents.collection.fiqh import FiQHCollectionAgent
from src.agents.collection.hadith import HadithCollectionAgent
from src.agents.collection.tafsir import TafsirCollectionAgent
from src.agents.collection.aqeedah import AqeedahCollectionAgent
from src.agents.collection.seerah import SeerahCollectionAgent
from src.agents.collection.history import HistoryCollectionAgent
from src.agents.collection.usul_fiqh import UsulFiqhCollectionAgent
from src.agents.collection.language import LanguageCollectionAgent
from src.agents_collection.general import GeneralCollectionAgent
from src.agents.collection.tazkiyah import TazkiyahCollectionAgent
```

---

#### src/agents/collection/base.py

**Purpose**: BASE CLASSES for all CollectionAgents - Most important file in the agents module.

**Lines**: ~546

**Key Classes**:

| Class | Purpose |
|-------|---------|
| `CollectionAgentConfig` | Configuration for a CollectionAgent (name, collection, top_k, prompts) |
| `RetrievalStrategy` | How to retrieve documents (collection, top_k, filters, rerank) |
| `VerificationCheck` | A single verification check (name, fail_policy, enabled) |
| `VerificationSuite` | Collection of verification checks |
| `VerificationReport` | Results from verification (status, confidence, verified_passages) |
| `IntentLabel` | Domain-specific intents enum |

**Abstract Base Class**: `CollectionAgent`

The core abstract class that all domain agents inherit from. Key methods:

| Method | Purpose |
|--------|---------|
| `execute(input: AgentInput)` | Main entry point - orchestrates retrieve→verify→generate |
| `retrieve(query: str)` | Search Qdrant for relevant passages |
| `verify(answer: str, passages: list)` | Run verification checks |
| `generate(query: str, passages: list)` | Call LLM to generate answer |
| `_load_prompt_template()` | Load from prompts/*.txt files |
| `_build_prompt(query: str, contexts: list)` | Combine template + contexts |
| `_get_system_prompt()` | Build system prompt |
| `_get_retrieval_query()` | Transform user query for retrieval |
| `_parse_response()` | Parse LLM output |

**Key Method Execution Flow**:
```
execute(input)
    ↓
1. _get_retrieval_query(input.query)     # Transform query
    ↓
2. retrieve(retrieval_query)             # Search Qdrant
    ↓
3. verify(input.query, passages)        # Run checks (if enabled)
    ↓
4. generate(input.query, passages)       # Call LLM
    ↓
5. strip_cot_leakage(raw_answer)         # Clean output
    ↓
6. _build_citations(passages)            # Build citations
    ↓
return AgentOutput(answer, citations, confidence)
```

---

#### src/agents/collection/fiqh.py

**Purpose**: FiQH (Islamic Jurisprudence) CollectionAgent - handles questions about halal/haram, rulings, and practical Islamic law.

**Lines**: ~280

**Config File**: `config/agents/fiqh.yaml`
**Prompt File**: `prompts/fiqh_agent.txt`

**Key Methods**:

```python
class FiQHCollectionAgent(CollectionAgent):
    async def execute(self, input: AgentInput) -> AgentOutput:
        # Step 1: Get retrieval query
        retrieval_query = self._get_retrieval_query(input.query)
        
        # Step 2: Retrieve passages
        passages = await self.retrieve(retrieval_query)
        
        # Step 3: Verify if enabled
        if self.config.verification_enabled:
            verification = await self.verify(input.query, passages)
        
        # Step 4: Generate answer
        raw_answer = await self.generate(input.query, passages)
        
        # Step 5: Strip CoT leakage
        answer = strip_cot_leakage(raw_answer)
        
        # Step 6: Build citations
        citations = self._build_citations(passages)
        
        return AgentOutput(
            answer=answer,
            citations=citations,
            confidence=verification.confidence if self.config.verification_enabled else 0.9,
        )
```

**Special Features**:
- Quran references detection: `_detect_quran_references(text: str) -> list[dict]`
- Madhhab-specific responses based on user preference
- Evidence hierarchy handling (Quran → Sunnah → Ijma → Qiyas)

---

#### src/agents/collection/hadith.py

**Purpose**: Hadith CollectionAgent - handles questions about Prophetic traditions, hadith grading, and sanad (chain of transmission).

**Config File**: `config/agents/hadith.yaml`
**Prompt File**: `prompts/hadith_agent.txt`

**Key Features**:
- Sanad/matn separation (chain of transmission vs text)
- Hadith grading (Sahih, Hasan, Daif, Mawdu)
- Takhrij (finding hadith sources)
- Narrator reliability assessment

**Special Methods**:
- `_grade_hadith(passage: RetrievalPassage) -> str`
- `_extract_sanad(text: str) -> list[str]`
- `_verify_matn(text: str, passages: list) -> bool`

---

#### src/agents/collection/tafsir.py

**Purpose**: Tafsir (Quranic Exegesis) CollectionAgent - handles questions about Quran interpretation and tafsir.

**Config File**: `config/agents/tafsir.yaml`
**Prompt File**: `prompts/tafsir_agent.txt`

**Key Features**:
- Verse-by-verse interpretation
- Multiple tafsir sources (Ibn Kathir, Al-Qurtubi, etc.)
- Context and asbab al-nuzul (occasions of revelation)
- Morphological analysis (tafsir bil-mathur vs bil-ra'y)

---

#### src/agents/collection/aqeedah.py

**Purpose**: Aqeedah (Islamic Theology) CollectionAgent - handles questions about Islamic beliefs, faith, and theology.

**Config File**: `config/agents/aqeedah.yaml`
**Prompt File**: `prompts/aqeedah_agent.txt`

**Key Features**:
- Sunni aqeedah (Ash'ari/Maturidi)
- Attributes of Allah
- Names and Attributes (Asma al-Husna)
- Beliefs about unseen (ghayb)

---

#### src/agents/collection/seerah.py

**Purpose**: Seerah (Prophet Biography) CollectionAgent - handles questions about the life of Prophet Muhammad (peace be upon him).

**Config File**: `config/agents/seerah.yaml`
**Prompt File`: `prompts/seerah_agent.txt`

**Key Features**:
- Timeline-based retrieval
- Event classification (battles, treaties, revelations)
- Geographic context (locations in the Arabian Peninsula)

---

#### src/agents/collection/history.py

**Purpose**: Islamic History CollectionAgent - handles questions about Islamic history, caliphates, and historical events.

**Config File**: `config/agents/history.yaml`
**Prompt File**: `prompts/history_agent.txt`

**Key Features**:
- Chronological retrieval
- Era classification (Rashidun, Umayyad, Abbasid, Ottoman)
- Event causation chains

---

#### src/agents/collection/usul_fiqh.py

**Purpose**: Usul al-Fiqh (Principles of Islamic Jurisprudence) CollectionAgent - handles questions about the methodology of deriving Islamic rulings.

**Config File**: `config/agents/usul_fiqh.yaml`
**Prompt File**: `prompts/usul_fiqh_agent.txt`

**Key Features**:
- Evidence types (Quran, Sunnah, Ijma, Qiyas)
- Maslaha (public interest)
- Istihsan (juristic preference)
- Sadd al-Dhara'i (blocking the means)

---

#### src/agents/collection/language.py

**Purpose**: Arabic Language CollectionAgent - handles questions about Arabic grammar, morphology, and vocabulary.

**Config File**: `config/agents/language.yaml`
**Prompt File**: `prompts/language_agent.txt`

**Key Features**:
- Morphological analysis (sarf)
- Grammatical analysis (nahw)
- Root word identification (wazan)
- Lexical meaning (mu'jam)

---

#### src/agents/collection/general.py

**Purpose**: General Islamic Knowledge CollectionAgent - fallback agent for questions that don't fit other domains.

**Config File**: `config/agents/general.yaml`
**Prompt File**: `prompts/general_agent.txt`

**Key Features**:
- Broad coverage of Islamic topics
- Used when no specific agent matches

---

#### src/agents/collection/tazkiyah.py

**Purpose**: Tazkiyah (Spiritual Purification) CollectionAgent - handles questions about Islamic spirituality, dhikr, and dua.

**Config File**: `config/agents/tazkiyah.yaml`
**Prompt File**: `prompts/tazkiyah_agent.txt`

**Key Features**:
- Dhikr remembrances
- Supplications (dua)
- Spiritual stations (maqamat)
- Heart purification

---

### src/api/

The API module contains FastAPI application setup, routes, schemas, and middleware.

#### src/api/main.py

**Purpose**: FastAPI application creation and router setup - the main entry point for the API.

**Lines**: ~120

**Key Code**:
```python
from fastapi import FastAPI
from src.api.routes import ask_router, search_router, tools_router, quran_router

app = FastAPI(
    title="Athar Islamic QA API",
    version="0.5.0",
    description="Islamic QA System with RAG",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Health + classification: intentionally without api_v1_prefix (public endpoints)
app.include_router(health_router)
app.include_router(classify_router)

# v1 endpoints
v1 = settings.api_v1_prefix  # "/api/v1"

app.include_router(ask_router, prefix=v1)      # /api/v1/ask
app.include_router(search_router, prefix=v1)   # /api/v1/search
app.include_router(tools_router, prefix=v1)    # /api/v1/tools
app.include_router(quran_router, prefix=v1)    # /api/v1/quran
```

**Router Registration**:
| Router | Prefix | Endpoint |
|--------|--------|----------|
| `health_router` | (none) | `/health` |
| `classify_router` | (none) | `/classify` |
| `ask_router` | `/api/v1` | `/api/v1/ask` |
| `search_router` | `/api/v1` | `/api/v1/search` |
| `tools_router` | `/api/v1` | `/api/v1/tools` |
| `quran_router` | `/api/v1` | `/api/v1/quran` |

---

#### src/api/lifespan.py

**Purpose**: Application startup/shutdown lifecycle - initializes all services in the correct order.

**Lines**: ~90

**Initialization Sequence**:
```python
async def lifespan(app: FastAPI):
    # ── 1. Settings ─────────────────────────────────────────────
    settings = get_settings()
    
    # ── 2. Registry ───────────────────────────────────────────
    registry = get_registry()
    
    # ── 3. Infrastructure ────────────────────────────────────────
    # Qdrant
    app.state.qdrant = get_qdrant_client()
    
    # Redis
    app.state.redis = get_redis()
    
    # PostgreSQL
    app.state.db = get_database()
    
    # ── 4. Embedding Model ────────────────────────────────
    app.state.embedding_model = get_embedding_model()
    
    # ── 5. Classifier & Router ───────────────────────────
    from src.application.classifier_factory import build_classifier
    classifier = build_classifier(embedding_model=app.state.embedding_model)
    router = RouterAgent(classifier=classifier)
    app.state.router = router
    
    # ── 6. Use Case & Service ───────────────────────────
    use_case = AnswerQueryUseCase(agent_registry=registry, router=router)
    app.state.ask_service = AskService(answer_query_use_case=use_case)
    
    # ── 7. Standard Agents (Static) ──────────────────────
    # Register collection agents
    registry.register("fiqh:rag", FiQHCollectionAgent(config))
    # ... more agents
    
    yield
    
    # ── Cleanup ────────────────────────────────────────
    await app.state.qdrant.close()
    await app.state.redis.close()
```

**Why This Order**:
1. Settings first (other services depend on config)
2. Registry second (agents need to be registered)
3. Infrastructure third (depends on settings)
4. Embedding model fourth (depends on infrastructure)
5. Classifier/Router fifth (depends on embedding)
6. Use cases sixth (depends on all above)
7. Agents last (depend on retrieval, verification)

---

#### src/api/routes/ask.py

**Purpose**: POST /api/v1/ask - Main Q&A endpoint.

**Lines**: ~200

**Request Schema**:
```python
class AskRequest(BaseModel):
    query: str = Field(..., description="User question")
    language: str = Field(default="ar", description="Query language")
    collection: str | None = Field(default=None, description="Target collection")
    madhhab: str | None = Field(default=None, description="Preferred madhhab")
```

**Response Schema**:
```python
class AskResponse(BaseModel):
    answer: str
    citations: list[CitationResponse]
    intent: str
    confidence: float
    processing_time_ms: int
```

**Endpoint Logic**:
```
1. Receive AskRequest
2. Validate request
3. Delegate to AskService.execute()
4. Build response with citations
5. Return AskResponse
```

---

#### src/api/routes/search.py

**Purpose**: POST /api/v1/search - Direct document search endpoint.

**Request Schema**:
```python
class SearchRequest(BaseModel):
    query: str
    collection: str | None = None
    top_k: int = Field(default=10, ge=1, le=100)
    filters: dict | None = None
```

**Response Schema**:
```python
class SearchResponse(BaseModel):
    results: list[SearchResult]
    total: int
    query: str
```

---

#### src/api/routes/tools.py

**Purpose**: POST /api/v1/tools - Execute Islamic tools (zakat calculator, inheritance calculator, etc.).

**Supported Tools**:
- `zakat_calculator` - Calculate Zakat al-Maal
- `inheritance_calculator` - Calculate Islamic inheritance shares
- `prayer_times` - Get prayer times for location
- `hijri_calendar` - Convert Gregorian to Hijri
- `dua_retrieval` - Find appropriate duas

**Request Schema**:
```python
class ToolRequest(BaseModel):
    tool_name: str
    parameters: dict
```

---

#### src/api/routes/quran.py

**Purpose**: POST /api/v1/quran - Quran-specific queries including verse retrieval and tafsir.

**Features**:
- Verse search by text or reference
- Tafsir retrieval
- Quran quotes validation
- Cross-references between verses

---

#### src/api/routes/classify.py

**Purpose**: POST /classify - Intent classification endpoint (public, no /api/v1 prefix).

**Request Schema**:
```python
class ClassificationRequest(BaseModel):
    query: str
```

**Response Schema**:
```python
class ClassificationResponse(BaseModel):
    intent: str
    confidence: float
    language: str
    requires_retrieval: bool
```

---

#### src/api/routes/health.py

**Purpose**: GET /health - Health check endpoint.

**Response**:
```python
{"status": "healthy", "version": "0.5.0"}
```

---

#### src/api/schemas/ask.py

**Purpose**: Pydantic schemas for ask endpoint.

**Classes**:
- `AskRequest` - Request validation
- `AskResponse` - Response model
- `CitationResponse` - Citation format

---

#### src/api/schemas/search.py

**Purpose**: Pydantic schemas for search endpoint.

**Classes**:
- `SearchRequest` - Search parameters
- `SearchResult` - Individual result
- `SearchResponse` - Complete response

---

#### src/api/schemas/common.py

**Purpose**: Common schemas shared across endpoints.

**Classes**:
- `CitationResponse` - Citation format
- `ErrorResponse` - Error format
- `PaginationParams` - Pagination parameters

---

#### src/api/schemas/classification.py

**Purpose**: Classification schemas.

**Classes**:
- `ClassificationRequest`
- `ClassificationResponse`

---

#### src/api/schemas/request.py

**Purpose**: Base request schemas.

---

#### src/api/schemas/response.py

**Purpose**: Base response schemas.

---

#### src/api/schemas/trace.py

**Purpose**: Trace-related schemas for debugging and auditing.

---

#### src/api/schemas/traces.py

**Purpose**: Alternative trace schemas.

---

#### src/api/schemas/tools.py

**Purpose**: Tool-related schemas.

---

#### src/api/middleware/security.py

**Purpose**: Security middleware - CORS, rate limiting.

---

#### src/api/middleware/request_logging.py

**Purpose**: Request/response logging middleware.

---

#### src/api/middleware/request_id.py

**Purpose**: Add unique request ID to each request for tracing.

---

#### src/api/middleware/error_handler.py

**Purpose**: Global error handling middleware.

---

#### src/api/versioning.py

**Purpose**: API versioning utilities.

---

### src/application/

The application module contains use cases, services, and business logic - the core application layer.

#### src/application/container.py

**Purpose**: Dependency injection container using a service locator pattern.

**Key Functionality**:
- Registers services and dependencies
- Provides singleton instances
- Manages lifecycle of services

---

#### src/application/interfaces.py

**Purpose**: Abstract interfaces for dependency injection.

**Key Interfaces**:
- `IIntentClassifier` - Intent classification interface
- `IRetriever` - Retrieval interface
- `IVerifier` - Verification interface
- `ILLMClient` - LLM client interface

---

#### src/application/classifier_factory.py

**Purpose**: Creates classifier instances.

**Key Function**:
```python
def build_classifier(embedding_model=None) -> FallbackChainClassifier
```

---

### src/config/

Configuration management - loads YAML configs, settings, and constants.

#### src/config/__init__.py

**Purpose**: Main config exports.

---

#### src/config/settings.py

**Purpose**: Application settings using Pydantic settings.

**Key Settings**:
```python
class Settings(BaseSettings):
    # API
    api_v1_prefix: str = "/api/v1"
    
    # Database
    qdrant_host: str
    qdrant_port: int
    postgres_url: str
    redis_url: str
    
    # LLM
    openai_api_key: str
    groq_api_key: str
    default_llm: str
    
    # Embeddings
    embedding_model: str
    
    # Agent Config
    agent_config_dir: str
```

---

#### src/config/loader.py

**Purpose**: Loads YAML configuration files from config/agents/.

**Key Functions**:
```python
def load_agent_config(agent_name: str) -> dict
def load_all_configs() -> dict[str, dict]
def get_config_manager() -> ConfigManager
```

---

#### src/config/intents.py

**Purpose**: Intent definitions and keyword patterns.

**Key Contents**:
- `INTENT_KEYWORDS` - Arabic/English keywords for each intent
- `IntentType` enum
- Intent routing rules

---

#### src/config/constants.py

**Purpose**: Application constants.

**Key Constants**:
- Default collection names
- Default top_k values
- Timeout values
- Retry configurations

---

#### src/config/environment_validation.py

**Purpose**: Validates environment variables at startup.

**Key Function**:
```python
def validate_environment() -> list[str]
# Returns list of missing/invalid environment variables
```

---

#### src/config/logging_config.py

**Purpose**: Logging configuration using structlog.

---

### src/config_runtime/

Runtime configuration management.

#### src/config_runtime/__init__.py

**Purpose**: Runtime config exports.

---

### src/core/

Core system components - registry, exceptions, router, citation.

#### src/core/registry.py

**Purpose**: Agent registry - manages all registered agents.

**Key Class**:
```python
class AgentRegistry:
    def register(self, name: str, agent: CollectionAgent) -> None
    def get(self, name: str) -> CollectionAgent
    def list_all(self) -> list[str]
    def get_by_collection(self, collection: str) -> CollectionAgent
```

---

#### src/core/exceptions.py

**Purpose**: Custom exceptions.

**Key Exceptions**:
| Exception | Use Case |
|-----------|----------|
| `AtharError` | Base exception |
| `ConfigurationError` | Config not found or invalid |
| `RetrievalError` | Retrieval failure |
| `VerificationError` | Verification failure |
| `GenerationError` | LLM generation failure |

---

#### src/core/router.py

**Purpose**: Legacy query router.

---

#### src/core/citation.py

**Purpose**: Citation normalization and formatting.

**Key Function**:
```python
def normalize_citation(citation: dict) -> Citation
def format_citation(citation: Citation, style: str = "APA") -> str
```

---

### src/data/

Data processing utilities.

### src/domain/

Domain models - intents, enums, evidence, collections.

#### src/domain/intents.py

**Purpose**: Intent definitions with 16+ intent types.

**Key Contents**:
- `IntentType` enum
- Intent sub-types
- Intent routing mappings

---

#### src/domain/models.py

**Purpose**: Domain models.

---

#### src/domain/citations.py

**Purpose**: Citation domain models.

---

#### src/domain/evidence.py

**Purpose**: Evidence models.

---

#### src/domain/decisions.py

**Purpose**: Decision models for routing.

---

#### src/domain/collections.py

**Purpose**: Collection definitions and metadata.

---

### src/evaluation/

Evaluation metrics, golden sets, and CLI for testing.

#### src/evaluation/metrics.py

**Purpose**: Evaluation metrics for RAG quality.

**Key Metrics**:
```python
def calculate_recall(results: list, golden: list) -> float
def calculate_precision(results: list, golden: list) -> float
def calculate_f1(recall: float, precision: float) -> float
def calculate_answer_quality(answer: str, reference: str) -> float
```

---

#### src/evaluation/golden_set_schema.py

**Purpose**: Schema for golden test sets.

---

#### src/evaluation/cli.py

**Purpose**: CLI for running evaluations.

---

### src/generation/

LLM clients, prompts, and answer composers.

#### src/generation/__init__.py

**Purpose**: Generation exports.

---

#### src/generation/schemas.py

**Purpose**: Generation-related schemas.

---

#### src/generation/prompt_loader.py

**Purpose**: Loads prompt templates from files.

**Key Function**:
```python
def load_prompt(template_name: str) -> str
def list_prompts() -> list[str]
```

---

#### src/generation/llm_client.py

**Purpose**: LLM client for generating answers.

**Key Class**:
```python
class LLMClient:
    async def generate(
        self,
        prompt: str,
        system_prompt: str | None = None,
        model: str = "gpt-4",
        temperature: float = 0.7,
    ) -> str
```

**Supported Providers**:
- OpenAI (GPT-4, GPT-3.5)
- Groq (fast inference)

---

#### src/generation/prompts/

Prompt templates for each agent type.

| File | Purpose |
|------|---------|
| `fiqh.py` | FiQH agent prompt |
| `hadith.py` | Hadith agent prompt |
| `tafsir.py` | Tafsir agent prompt |
| `aqeedah.py` | Aqeedah agent prompt |
| `abstain.py` | Abstention prompt |
| `clarify.py` | Clarification prompt |

---

#### src/generation/composers/

Answer composition utilities.

| File | Purpose |
|------|---------|
| `answer_composer.py` | Main answer composer |
| `citation_composer.py` | Citation formatter |
| `abstention_composer.py` | Abstention response composer |
| `clarification_composer.py` | Clarification request composer |

---

#### src/generation/policies/

Generation policies.

| File | Purpose |
|------|---------|
| `answer_policy.py` | Answer generation policy |
| `formatting_policy.py` | Output formatting rules |
| `risk_policy.py` | Risk assessment policy |

---

### src/indexing/

Document indexing pipelines.

#### src/indexing/__init__.py

**Purpose**: Indexing exports.

---

#### src/indexing/vectorstores/

Vector store implementations.

| File | Purpose |
|------|---------|
| `base.py` | Base vector store interface |
| `qdrant_store.py` | Qdrant implementation |
| `factory.py` | Vector store factory |
| `hybrid_client.py` | Hybrid search client |
| `hybrid_config.py` | Hybrid search configuration |

---

#### src/indexing/pipelines/

Indexing pipelines.

| File | Purpose |
|------|---------|
| `ingest_athar.py` | Main ingestion pipeline |
| `build_collection_indexes.py` | Build collection indexes |
| `analyze_chunks.py` | Analyze document chunks |
| `sync_metadata.py` | Sync metadata |

---

### src/infrastructure/

External service integrations.

#### src/infrastructure/qdrant/client.py

**Purpose**: Qdrant vector database client.

**Key Class**:
```python
class QdrantClient:
    async def search(
        self,
        collection: str,
        query_vector: list[float],
        limit: int,
        filter: dict | None = None,
    ) -> list[SearchResult]
    
    async def upsert(self, collection: str, points: list[Point]) -> None
    async def create_collection(self, name: str, vector_size: int) -> None
```

---

#### src/infrastructure/qdrant/collections.py

**Purpose**: Collection definitions.

---

#### src/infrastructure/qdrant/payload_indexes.py

**Purpose**: Payload index definitions.

---

#### src/infrastructure/redis.py

**Purpose**: Redis caching client.

---

#### src/infrastructure/llm/ (directory)

**Purpose**: LLM provider implementations.

---

### src/knowledge/

Legacy wrapper module - facade that wraps src/retrieval/ for backward compatibility.

#### src/knowledge/vector_store.py

**Purpose**: Legacy vector store wrapper.

---

#### src/knowledge/hybrid_search.py

**Purpose**: Legacy hybrid search wrapper.

---

#### src/knowledge/hadith_grader.py

**Purpose**: Hadith grading logic.

---

### src/quran/

Quran-specific logic.

#### src/quran/__init__.py

**Purpose**: Quran module exports.

---

#### src/quran/verse_retrieval.py

**Purpose**: Retrieve Quran verses.

---

#### src/quran/tafsir_retrieval.py

**Purpose**: Retrieve tafsir for verses.

---

#### src/quran/quotation_validator.py

**Purpose**: Validate Quran quotations in answers.

---

#### src/quran/quran_router.py

**Purpose**: Route Quran-specific queries.

---

#### src/quran/nl2sql.py

**Purpose**: Natural language to SQL for Quran queries.

---

### src/retrieval/

Complete retrieval pipeline - the most well-organized module.

#### src/retrieval/__init__.py

**Purpose**: Central export point.

---

#### src/retrieval/schemas.py

**Purpose**: Retrieval-related schemas.

**Key Classes**:
```python
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

#### src/retrieval/strategies.py

**Purpose**: Retrieval strategies per agent type.

**Key Variables**:
```python
DEFAULT_STRATEGY = RetrievalStrategy(
    collection="default",
    top_k=10,
    filters=None,
    rerank=False,
)

RETRIEVAL_MATRIX = {
    "fiqh_agent": RetrievalStrategy(...),
    "hadith_agent": RetrievalStrategy(...),
    # ...
}

def get_strategy_for_agent(agent_name: str) -> RetrievalStrategy
def get_collection_for_agent(agent_name: str) -> str
```

---

#### src/retrieval/retrievers/

Retrievers for different search methods.

| File | Purpose |
|------|---------|
| `hybrid_retriever.py` | Combines semantic + keyword via RRF |
| `bm25_retriever.py` | BM25 keyword search |
| `dense_retriever.py` | Semantic search with embeddings |
| `sparse_retriever.py` | Sparse vector search |
| `hierarchical_retriever.py` | Hierarchical chunk retrieval |
| `multi_collection_retriever.py` | Multi-collection search |
| `hybrid_searcher.py` | Alternative hybrid implementation |

**Hybrid Retriever Flow**:
```
1. Semantic search (vector) → top_k results
2. BM25 search (keyword) → top_k results
3. Reciprocal Rank Fusion (k=60)
4. Return fused, reranked results
```

---

#### src/retrieval/fusion/rrf.py

**Purpose**: Reciprocal Rank Fusion algorithm.

---

#### src/retrieval/ranking/

Result ranking and reranking.

| File | Purpose |
|------|---------|
| `reranker.py` | Cross-encoder reranking |
| `book_weighter.py` | Weight by book authority |
| `authority_scorer.py` | Score by source authority |
| `score_fusion.py` | Combine multiple scores |

---

#### src/retrieval/aggregation/

Result aggregation.

| File | Purpose |
|------|---------|
| `deduper.py` | Remove duplicate results |
| `clusterer.py` | Cluster similar results |
| `evidence_aggregator.py` | Aggregate evidence |

---

#### src/retrieval/planning/

Query planning.

| File | Purpose |
|------|---------|
| `retrieval_plan.py` | Plan retrieval strategy |

---

#### src/retrieval/filters/

Query filtering.

| File | Purpose |
|------|---------|
| `builder.py` | Build filters |
| `presets.py` | Common filter presets |

---

#### src/retrieval/expanders/

Query expansion.

| File | Purpose |
|------|---------|
| `query_expander.py` | Expand queries with synonyms |
| `islamic_synonyms.py` | Islamic domain synonyms |

---

#### src/retrieval/policies/

Retrieval policies.

| File | Purpose |
|------|---------|
| `retrieval_policy.py` | Retrieval behavior policy |
| `collection_policy.py` | Collection selection policy |

---

### src/services/

Business services.

#### src/services/citation_service.py

**Purpose**: Citation management service.

---

### src/tools/

Islamic tools - calculators and utilities.

#### src/tools/base.py

**Purpose**: Base class for all tools.

**Key Interface**:
```python
class Tool(ABC):
    name: str
    description: str
    
    @abstractmethod
    async def execute(self, parameters: dict) -> dict
```

---

#### src/tools/zakat_calculator.py

**Purpose**: Zakat al-Maal calculator.

**Key Function**:
```python
class ZakatCalculator(Tool):
    async def execute(self, parameters: dict) -> dict:
        # Calculate:
        # 1. Nisab (threshold: 85g gold or 595g silver)
        # 2. Zakat amount (2.5% of excess)
        # 3. Payment due date
```

**Parameters**:
```python
{
    "gold_amount_grams": float,
    "silver_amount_grams": float,
    "cash_amount": float,
    "investments": float,
    "debts": float,
}
```

---

#### src/tools/inheritance_calculator.py

**Purpose**: Islamic inheritance calculator.

**Key Function**:
```python
class InheritanceCalculator(Tool):
    async def execute(self, parameters: dict) -> dict:
        # Calculate shares using classical fiqh rules
        # Support: Quranic heirs, asabah, dhawul-arham
```

**Parameters**:
```python
{
    "deceased_gender": "male" | "female",
    "heirs": [
        {"relationship": "wife", "count": 1},
        {"relationship": "son", "count": 2},
    ]
}
```

---

#### src/tools/prayer_times_tool.py

**Purpose**: Prayer times for location.

---

#### src/tools/hijri_calendar_tool.py

**Purpose**: Gregorian to Hijri conversion.

---

#### src/tools/dua_retrieval_tool.py

**Purpose**: Find appropriate duas.

---

### src/utils/

Utility functions.

#### src/utils/language_detection.py

**Purpose**: Detect Arabic vs English text.

---

#### src/utils/era_classifier.py

**Purpose**: Classify historical eras.

---

#### src/utils/lazy_singleton.py

**Purpose**: Lazy singleton pattern.

---

### src/verification/ vs src/verifiers/

Two verification modules exist for historical reasons.

#### src/verification/__init__.py

**Purpose**: New verification layer wrapper - re-exports from verifiers.

```python
from src.verification.schemas import (...)
from src.verification.trace import (...)
```

---

#### src/verification/schemas.py

**Purpose**: Verification schemas.

---

#### src/verification/trace.py

**Purpose**: Verification tracing.

---

#### src/verification/checks/__init__.py

**Purpose**: Verification checks.

---

### src/verifiers/

Full verification implementation.

#### src/verifiers/base.py

**Purpose**: Base verifier class.

---

#### src/verifiers/suite_builder.py

**Purpose**: Build and run verification suites.

**Key Functions**:
```python
def build_verification_suite_for(agent_name: str) -> VerificationSuite

async def run_verification_suite(
    answer: str,
    passages: list[RetrievalPassage],
    suite: VerificationSuite,
) -> VerificationReport
```

---

#### src/verifiers/exact_quote.py

**Purpose**: Verify that quotes in answer match source passages exactly.

---

#### src/verifiers/source_attribution.py

**Purpose**: Verify that sources are correctly attributed.

---

#### src/verifiers/hadith_grade.py

**Purpose**: Verify hadith grading is correct.

---

#### src/verifiers/contradiction.py

**Purpose**: Check for contradictions in answer.

---

#### src/verifiers/evidence_sufficiency.py

**Purpose**: Check if evidence is sufficient.

---

#### src/verifiers/temporal_consistency.py

**Purpose**: Time-based consistency checks.

---

#### src/verifiers/school_consistency.py

**Purpose**: Madhhab consistency checks.

---

#### src/verifiers/groundedness_judge.py

**Purpose**: Judge if answer is grounded in sources.

---

#### src/verifiers/quote_span.py

**Purpose**: Extract and validate quote spans.

---

#### src/verifiers/policies.py

**Purpose**: Verification policies.

---

#### src/verifiers/pipeline.py

**Purpose**: Verification pipeline orchestration.

---

#### src/verifiers/missing_evidence.py

**Purpose**: Check for missing evidence.

---

#### src/verifiers/misattribution.py

**Purpose**: Check for misattributed sources.

---

#### src/verifiers/fiqh_checks.py

**Purpose**: FiQH-specific verification checks.

---

#### src/verifiers/__init__.py

**Purpose**: Verifiers module exports.

---

## Execution Flows

### End-to-End Query Flow

```
User Query
    │
    ▼
┌─────────────────────────────────────────┐
│  POST /api/v1/ask                       │
│  AskRequest(query, language, ...)        │
└─────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────┐
│  AskService.execute()                   │
│  - Delegates to AnswerQueryUseCase     │
└─────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────┐
│  RouterAgent.route(query)                │
│  - Hybrid classification (keyword +     │
│    embedding)                           │
│  - Returns routing decision             │
└─────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────┐
│  AgentRegistry.get(route)               │
│  - Returns appropriate CollectionAgent │
└─────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────┐
│  CollectionAgent.execute(input)         │
│                                         │
│  1. _get_retrieval_query()              │
│     (transform user query)              │
│                                         │
│  2. retrieve(query)                    │
│     (search Qdrant)                     │
│                                         │
│  3. verify(answer, passages)            │
│     (run verification checks)           │
│                                         │
│  4. generate(query, passages)           │
│     (call LLM)                          │
│                                         │
│  5. strip_cot_leakage()                 │
│     (clean output)                      │
│                                         │
│  6. _build_citations()                  │
│     (format citations)                  │
└─────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────┐
│  AskResponse                            │
│  - answer: str                          │
│  - citations: list                     │
│  - intent: str                         │
│  - confidence: float                   │
│  - processing_time_ms: int             │
└─────────────────────────────────────────┘
```

### Retrieval Flow

```
Query
  │
  ▼
┌──────────────────┐    ┌──────────────────┐
│ DenseRetriever   │    │ BM25Retriever   │
│ (semantic)       │    │ (keyword)        │
└──────────────────┘    └──────────────────┘
  │                          │
  ▼                          ▼
┌──────────────────┐    ┌──────────────────┐
│  Top-K Results  │    │  Top-K Results  │
└──────────────────┘    └──────────────────┘
  │                          │
  └────────────┬─────────────┘
               ▼
┌──────────────────────────────┐
│  Reciprocal Rank Fusion     │
│  (k=60)                     │
└──────────────────────────────┘
               │
               ▼
┌──────────────────────────────┐
│  Optional Reranking         │
│  (Cross-Encoder)            │
└──────────────────────────────┘
               │
               ▼
┌──────────────────────────────┐
│  RetrievalResult[]          │
└──────────────────────────────┘
```

### Verification Flow

```
Answer + Passages
       │
       ▼
┌──────────────────────────────────┐
│  Build VerificationSuite         │
│  (per agent type)                │
└──────────────────────────────────┘
       │
       ▼
┌──────────────────────────────────┐
│  For each check in suite:        │
│  - exact_quote                   │
│  - source_attribution            │
│  - hadith_grade                  │
│  - contradiction                 │
│  - evidence_sufficiency          │
└──────────────────────────────────┘
       │
       ▼
┌──────────────────────────────────┐
│  VerificationReport              │
│  - status: passed/failed         │
│  - confidence: float             │
│  - verified_passages: list       │
│  - abstained: bool               │
└──────────────────────────────────┘
```

---

## Key Patterns

### Config-Backed Agents Pattern

All agents use YAML configuration:
```
config/agents/fiqh.yaml
    │
    ▼
CollectionAgentConfig
    │
    ▼
FiQHCollectionAgent
```

### Hybrid Classification Pattern

```
1. Keyword Fast-Path (high-priority keywords)
   ↓ (if confidence >= 0.85)
2. Embedding Fallback (semantic similarity)
   ↓
3. Return highest confidence result
```

### Retrieval Fusion Pattern

Combines multiple retrieval methods:
- Semantic (dense embeddings)
- Keyword (BM25)
- Hierarchical (chunked passages)

### Verification Suite Pattern

Each agent type has a verification suite:
- FiQH: quote validation, source attribution, contradiction detection
- Hadith: grade verification, sanad validation

---

## Related Documentation

- [01_project_overview.md](01_project_overview.md)
- [02_folder_structure.md](02_folder_structure.md)
- [03_api_main_entrypoint.md](03_api_main_entrypoint.md)
- [18_src_modules_complete_guide.md](18_src_modules_complete_guide.md)
- [19_complete_file_index.md](19_complete_file_index.md)
- [20_src_complete_file_by_file.md](20_src_complete_file_by_file.md)

---

**Last Updated**: April 2026

**Version**: 3.0 (Complete Reference)
