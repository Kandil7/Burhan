# 🕌 Athar - Complete File-by-File Documentation

## Every Single File Explained in Detail

This document provides an exhaustive explanation of every file in the `src/` directory.

---

# 📁 src/agents/

## src/agents/base.py

**Purpose**: CORE TYPES - This file was MISSING and has been CREATED (April 2026) to fix broken imports.

**Why Created**: 60+ files throughout the codebase import from `src.agents.base` but the file didn't exist. This was a pre-existing issue from v1→v2 migration.

**Full Content**:

```python
"""
Base types for Athar agents.

This module provides core types that were expected to be migrated from v1
but were never implemented. Re-exports from canonical locations.
"""

from __future__ import annotations

import re
from typing import Any

from pydantic import BaseModel, Field
```

### Class: Citation

```python
class Citation(BaseModel):
    """Source citation for agent answers."""
    source_id: str = Field(description="Source document ID")
    text: str = Field(description="Quoted text from source")
    book_title: str | None = Field(default=None, description="Book title")
    page: int | None = Field(default=None, description="Page number")
    grade: str | None = Field(default=None, description="Hadith grade (sahih, hasan, daif)")
    url: str | None = Field(default=None, description="Source URL")
    metadata: dict = Field(default_factory=dict)
    model_config = {"extra": "allow"}
```

**Used by**: All CollectionAgents, retrieval layer, evaluation metrics

**Example**:
```python
citation = Citation(
    source_id="sahih_bukhari_tafsir",
    text="الصلاة عماد الدين",
    book_title="صحيح البخاري",
    page=580,
    grade="sahih"
)
```

---

### Class: AgentInput

```python
class AgentInput(BaseModel):
    """Standard input for agents."""
    query: str = Field(description="User query")
    language: str = Field(default="ar", description="Query language (ar/en)")
    collection: str | None = Field(default=None, description="Target collection")
    metadata: dict = Field(default_factory=dict)
    model_config = {"extra": "allow"}
```

**Used by**: All CollectionAgent.execute() methods

**Example**:
```python
input = AgentInput(
    query="ما حكم الزكاة؟",
    language="ar",
    metadata={"madhhab": "hanafi"}
)
```

---

### Class: AgentOutput

```python
class AgentOutput(BaseModel):
    """Standard output for agents."""
    answer: str = Field(description="Agent answer text")
    citations: list[Citation] = Field(default_factory=list)
    metadata: dict = Field(default_factory=dict)
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    requires_human_review: bool = Field(default=False)
    model_config = {"extra": "allow"}
```

**Used by**: All CollectionAgent.execute() returns

---

### Class: BaseAgent

```python
class BaseAgent:
    """Base class for agents (placeholder)."""
    async def execute(self, input: AgentInput) -> AgentOutput:
        """Execute the agent."""
        raise NotImplementedError
```

**Note**: This is just a placeholder. Real agents inherit from CollectionAgent in `collection/base.py`.

---

### Function: strip_cot_leakage()

```python
_COT_PATTERNS = [
    re.compile(r"##?\s*(Analysis|Reasoning|Thought|Chain of Thought).*?\n\n", re.IGNORECASE | re.DOTALL),
    re.compile(r"<\s*(analysis|reasoning|thought)\s*>\s*", re.IGNORECASE),
    re.compile(r"###\s*(?:Let me|I'll|I will).*?\n\s*", re.IGNORECASE),
]

def strip_cot_leakage(text: str) -> str:
    """Remove chain-of-thought leakage from generated text.
    
    Strips patterns like:
    - "## Analysis\n...", "## Reasoning\n..."
    - <analysis>...</analysis>
    - "### Let me...\n"
    """
    if not text:
        return text
    result = text
    for pattern in _COT_PATTERNS:
        result = pattern.sub("", result)
    return result.strip()
```

**Used by**: All CollectionAgents to clean LLM output

**Purpose**: Removes internal reasoning markers that might leak to users

---

## src/agents/collection_agent.py

**Purpose**: Legacy alias for backward compatibility.

**Why Created**: Many files import from `src.agents.collection_agent` which didn't exist. Created as alias to `src.agents.collection.base`.

**Content**:
```python
"""
Alias for retrieval strategy (legacy v1 path re-export).

This module exists for backward compatibility. The canonical location
is now src.agents.collection.base.RetrievalStrategy
"""

from src.agents.collection.base import (
    RetrievalStrategy,
    VerificationCheck,
    VerificationSuite,
    VerificationReport,
)

__all__ = [
    "RetrievalStrategy", 
    "VerificationCheck",
    "VerificationSuite", 
    "VerificationReport",
]
```

**Imported by**: 
- `src/verifiers/suite_builder.py`
- `src/retrieval/strategies.py`
- Various test files

---

## src/agents/collection/__init__.py

**Purpose**: Export all CollectionAgents.

**Content**:
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

__all__ = [
    "FiQHCollectionAgent",
    "HadithCollectionAgent",
    "TafsirCollectionAgent",
    "AqeedahCollectionAgent",
    "SeerahCollectionAgent",
    "HistoryCollectionAgent",
    "UsulFiqhCollectionAgent",
    "LanguageCollectionAgent",
    "GeneralCollectionAgent",
    "TazkiyahCollectionAgent",
]
```

---

## src/agents/collection/base.py

**Purpose**: BASE CLASSES for all CollectionAgents - Most important file in agents/.

**Lines**: ~546

### Key Classes

```python
class CollectionAgentConfig(BaseModel):
    """Configuration for a CollectionAgent."""
    name: str
    collection: str              # Qdrant collection name
    top_k: int
    prompt_template: str
    system_prompt: str
    verification_enabled: bool
```

```python
class RetrievalStrategy(BaseModel):
    """How to retrieve documents."""
    collection: str
    top_k: int
    filters: dict | None
    rerank: bool
```

```python
class VerificationCheck(BaseModel):
    """A single verification check."""
    name: str                    # e.g., "quote_validator"
    fail_policy: str            # "abstain", "warn", "proceed"
    enabled: bool
```

```python
class VerificationSuite(BaseModel):
    """Collection of verification checks."""
    checks: list[VerificationCheck]
```

```python
class VerificationReport(BaseModel):
    """Results from verification."""
    status: str               # "passed", "failed", "abstained"
    confidence: float
    verified_passages: list[str]
    abstained: bool
    abstention_reason: str | None
```

```python
class IntentLabel(str, Enum):
    """Domain-specific intents."""
    FiqhHukm = "fiqh_hukm"
    FiqhMasaail = "fiqh_masaail"
    HadithTakhrij = "hadith_takhrij"
    # ... more intents
```

### Abstract Base: CollectionAgent

```python
class CollectionAgent(ABC):
    """Abstract CollectionAgent with full RAG pipeline."""
    
    @property
    @abstractmethod
    def config(self) -> CollectionAgentConfig:
        """Agent configuration."""
        pass
    
    @abstractmethod
    async def execute(self, input: AgentInput) -> AgentOutput:
        """Execute the agent."""
        pass
    
    async def retrieve(self, query: str) -> list[RetrievalResult]:
        """Retrieve relevant passages."""
        pass
    
    async def verify(self, answer: str, passages: list) -> VerificationReport:
        """Verify answer against passages."""
        pass
    
    async def generate(self, query: str, passages: list) -> str:
        """Generate answer from passages."""
        pass
    
    def _load_prompt_template(self) -> str:
        """Load prompt template from file."""
        pass
    
    def _build_prompt(self, query: str, contexts: list[str]) -> str:
        """Build full prompt with contexts."""
        pass
```

### Key Methods

| Method | Purpose |
|--------|---------|
| `execute()` | Main entry point |
| `retrieve()` | Search Qdrant |
| `verify()` | Run verification checks |
| `generate()` | Call LLM |
| `_load_prompt_template()` | Load from prompts/*.txt |
| `_build_prompt()` | Combine template + contexts |
| `_get_system_prompt()` | Build system prompt |
| `_get_retrieval_query()` | Transform user query |
| `_parse_response()` | Parse LLM output |

---

## src/agents/collection/fiqh.py

**Purpose**: FiQH (Islamic Jurisprudence) CollectionAgent.

**Lines**: ~280

**Config File**: `config/agents/fiqh.yaml`

**Prompt File**: `prompts/fiqh_agent.txt`

### Key Methods

```python
class FiQHCollectionAgent(CollectionAgent):
    async def execute(self, input: AgentInput) -> AgentOutput:
        # 1. Get retrieval query
        retrieval_query = self._get_retrieval_query(input.query)
        
        # 2. Retrieve passages
        passages = await self.retrieve(retrieval_query)
        
        # 3. Verify if enabled
        if self.config.verification_enabled:
            verification = await self.verify(input.query, passages)
        
        # 4. Generate answer
        raw_answer = await self.generate(input.query, passages)
        
        # 5. Strip CoT leakage
        answer = strip_cot_leakage(raw_answer)
        
        # 6. Build citations
        citations = self._build_citations(passages)
        
        return AgentOutput(
            answer=answer,
            citations=citations,
            confidence=verification.confidence if self.config.verification_enabled else 0.9,
        )
```

### Quran References Detection

```python
def _detect_quran_references(self, text: str) -> list[dict]:
    """Detect Quran verse references in text."""
    # Patterns like "Surah Al-Baqarah:173", "البقرة 173"
    quran_pattern = re.compile(r"(?:سورة|sورة) (\w+):?(\d+)")
    # ...
```

---

## Other CollectionAgents

| File | Domain | Config | Key Feature |
|------|--------|--------|------------|
| `hadith.py` | Hadith | hadith.yaml | Sanad/matn separation |
| `tafsir.py` | Tafsir | tafsir.yaml | Verse context |
| `aqeedah.py` | Theology | aqeedah.yaml | School-specific |
| `seerah.py` | Biography | seerah.yaml | Timeline events |
| `history.py` | History | history.yaml | Chronological |
| `usul_fiqh.py` | Principles | usul_fiqh.yaml | Evidence types |
| `language.py` | Arabic | language.yaml | Morphology |
| `general.py` | General | general.yaml | Fallback agent |
| `tazkiyah.py` | Spirituality | tazkiyah.yaml | Dhikr/dua |

---

# 📁 src/api/

## src/api/main.py

**Purpose**: FastAPI app creation and router setup.

**Lines**: ~120

### Key Code

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
app.include_router(search_router, prefix=v1)      # /api/v1/search
app.include_router(tools_router, prefix=v1)       # /api/v1/tools
app.include_router(quran_router, prefix=v1)         # /api/v1/quran

@app.get("/")
async def root():
    return {"message": "Athar API", "version": app.version}
```

---

## src/api/lifespan.py

**Purpose**: Startup/shutdown lifecycle - initializes all services.

**Lines**: ~90

### Initialization Sequence

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
    
    # ── 6. Use Case & Service ───────────────────────
    use_case = AnswerQueryUseCase(agent_registry=registry, router=router)
    app.state.ask_service = AskService(answer_query_use_case=use_case)
    
    # ── 7. Standard Agents (Static) ────────────────────
    # Register collection agents
    registry.register("fiqh:rag", FiQHCollectionAgent(config))
    # ... more agents
    
    yield
    
    # ── Cleanup ────────────────────────────────────────
    await app.state.qdrant.close()
    await app.state.redis.close()
```

---

## src/api/routes/ask.py

**Purpose**: POST /api/v1/ask - Main Q&A endpoint.

**Lines**: ~200

### Request

```python
class AskRequest(BaseModel):
    query: str = Field(..., description="User question")
    language: str = Field(default="ar", description="Query language")
    collection: str | None = Field(default=None, description="Target collection")
    madhhab: str | None = Field(default=None, description="Preferred madhhab")
```

### Response

```python
class AskResponse(BaseModel):
    answer: str
    citations: list[CitationResponse]
    intent: str
    confidence: float
    processing_time_ms: int
```

### Endpoint

```python
@ask_router.post("", response_model=AskResponse)
async def ask_question(request: AskRequest) -> AskResponse:
    # 1. Validate
    
    # 2. Route to agent
    result = await app.state.ask_service.execute(request)
    
    # 3. Build response
    return AskResponse(
        answer=result.answer,
        citations=[CitationResponse(...) for ...],
        intent=result.metadata.get("intent"),
        confidence=result.confidence,
        processing_time_ms=elapsed_ms,
    )
```

---

## src/api/routes/classify.py

**Purpose**: POST /classify - Intent classification (Phase 8).

**Lines**: ~150

### New in Phase 8

```python
@classify_router.post("/classify", response_model=ClassificationResponse)
async def classify_query(request: ClassificationRequest):
    """Classify user intent using Hybrid Intent Classifier."""
    
    # Use the Hybrid Intent Classifier (keyword + embedding)
    result = await classifier.classify(request.query)
    
    return ClassificationResponse(
        intent=result.intent.value,
        confidence=result.confidence,
        language=result.language,
        requires_retrieval=result.requires_retrieval,
    )
```

---

## Other API Route Files

| File | Endpoint | Purpose |
|------|----------|--------|
| `search.py` | POST /api/v1/search | Document search |
| `tools.py` | POST /api/v1/tools | Execute tools |
| `quran.py` | POST /api/v1/quran | Quran queries |
| `health.py` | GET /health | Health check |
| `fiqh.py` | GET /api/v1/fiqh/* | FiQH-specific |

---

# 📁 src/application/

## src/application/use_cases/answer_query.py

**Purpose**: Main query answering use case.

**Lines**: ~150

### Classes

```python
@dataclass
class AnswerQueryInput:
    query: str
    language: str = "ar"
    collection: str | None = None
    metadata: dict = field(default_factory=dict)

@dataclass  
class AnswerQueryOutput:
    answer: str
    citations: list[Citation]
    intent: str
    confidence: float
    processing_time_ms: int

class AnswerQueryUseCase:
    """Main use case for answering queries."""
    
    def __init__(self, agent_registry, router):
        self.agents = agent_registry
        self.router = router
    
    async def execute(self, input: AnswerQueryInput) -> AnswerQueryOutput:
        # 1. Classify intent
        decision = await self.router.route(input.query)
        
        # 2. Get agent
        agent = self.agents.get(decision.route)
        
        # 3. Execute
        result = await agent.execute(AgentInput(
            query=input.query,
            language=input.language,
            metadata=input.metadata,
        ))
        
        # 4. Return
        return AnswerQueryOutput(
            answer=result.answer,
            citations=result.citations,
            intent=decision.result.intent.value,
            confidence=result.confidence,
            processing_time_ms=elapsed,
        )
```

---

## src/application/router/hybrid_classifier.py

**Purpose**: Hybrid Intent Classifier (Phase 8) - keyword + embedding.

**Lines**: ~200

### Algorithm

```
1. Keyword Fast-Path (high priority matches like "حكم", "ميراث")
   ↓
2. Embedding Fallback (BGE-M3 semantic)
   ↓
3. Confidence Gating (if keyword >= 0.85, use immediately)
   ↓
4. Return highest confidence result
```

### Key Classes

```python
class MasterHybridClassifier(IntentClassifier):
    """Consolidated Hybrid Classifier combining Keyword and Semantic tiers."""
    
    def __init__(self, embedding_model=None, low_conf_threshold=0.65):
        self._keyword_classifier = KeywordBasedClassifier()
        self._embedding_classifier = None
        if embedding_model:
            self._embedding_classifier = EmbeddingClassifier(embedding_model)
    
    async def classify(self, query: str) -> ClassificationResult:
        # Tier 1: Keyword
        kw_result = await self._keyword_classifier.classify(query)
        
        if kw_result.confidence >= 0.85:
            return kw_result
        
        # Tier 2: Embedding
        if self._embedding_classifier:
            emb_result = await self._embedding_classifier.classify(query)
            if emb_result.confidence > kw_result.confidence:
                return emb_result
        
        # Tier 3: Return keyword
        return kw_result
```

### Utility Functions (Added during cleanup)

```python
def _detect_language(text: str) -> str:
    """Detect Arabic/English."""
    # Count Arabic vs Latin characters
    
def _classify_quran_subintent(text: str) -> tuple[QuranSubIntent, float]:
    """Determine Quran sub-intent."""
    
def _infer_requires_retrieval(intent, sub) -> bool:
    """Determine if retrieval needed."""
```

---

## src/application/router/classifier_factory.py

**Purpose**: Keyword-based classifier with Arabic normalization.

**Lines**: ~160

### QueryClassifier (Abstract)

```python
class QueryClassifier(ABC):
    @abstractmethod
    async def classify(self, query: str) -> ClassificationResult:
        pass
```

### KeywordBasedClassifier

```python
class KeywordBasedClassifier(QueryClassifier):
    """High-Precision Keyword-Based Classifier."""
    
    def __init__(self):
        self._keywords = KEYWORD_PATTERNS  # Dict of intent → patterns
    
    async def classify(self, query: str) -> ClassificationResult:
        # 1. Normalize Arabic
        normalized = _normalize_arabic(query)
        
        # 2. Check each intent's keywords
        for intent, patterns in KEYWORD_PATTERNS.items():
            matches = sum(1 for p in patterns if p.search(normalized))
            if matches >= 2:
                return ClassificationResult(
                    intent=intent,
                    confidence=min(0.85 + (matches * 0.05),  # 0.85-0.95
                    requires_retrieval=True,
                )
        
        # 3. Default fallback
        return ClassificationResult(..., confidence=0.3)
```

---

# 📁 src/retrieval/

## src/retrieval/__init__.py

**Purpose**: Central export point.

```python
from src.retrieval.strategies import (
    get_strategy_for_agent,
    get_collection_for_agent,
    DEFAULT_STRATEGY,
    RetrievalStrategy,
)
from src.retrieval.retrievers.hybrid_retriever import HybridSearcher
from src.retrieval.retrievers.bm25_retriever import BM25Retriever
from src.retrieval.retrievers.dense_retriever import DenseRetriever
from src.retrieval.schemas import RetrievalResult, QueryType, RetrievalPassage
```

---

## src/retrieval/strategies.py

**Purpose**: Retrieval strategies per agent.

**Lines**: ~150

### Default Strategy

```python
DEFAULT_STRATEGY = RetrievalStrategy(
    collection="default",
    top_k=10,
    filters=None,
    rerank=False,
)

RETRIEVAL_MATRIX = {
    "fiqh_agent": RetrievalStrategy(
        collection="fiqh_passages",
        top_k=15,
        filters={"type": "fiqh"},
        rerank=True,
    ),
    "hadith_agent": RetrievalStrategy(
        collection="hadith_passages", 
        top_k=10,
        filters={"grade": "sahih"},
        rerank=True,
    ),
    # ... more agents
}

def get_strategy_for_agent(agent_name: str) -> RetrievalStrategy:
    return RETRIEVAL_MATRIX.get(agent_name, DEFAULT_STRATEGY)
```

---

## src/retrieval/retrievers/

### hybrid_retriever.py

**Purpose**: Hybrid search combining semantic + BM25.

**Key Method**:

```python
class HybridSearcher:
    """Combines semantic and keyword search via RRF."""
    
    async def search(
        self,
        query: str,
        collection: str,
        top_k: int = 10,
        filters: dict | None = None,
    ) -> list[RetrievalResult]:
        # 1. Semantic search (vector)
        semantic_results = await self._semantic.search(query, collection, top_k)
        
        # 2. BM25 search (keyword)
        keyword_results = await self._bm25.search(query, collection, top_k)
        
        # 3. Reciprocal Rank Fusion
        fused = self._rrf.fuse(semantic_results, keyword_results, k=60)
        
        return fused[:top_k]
```

### bm25_retriever.py

**Purpose**: BM25 keyword search.

```python
class BM25Retriever:
    """Classic BM25 ranking."""
    
    async def search(self, query, collection, top_k):
        # Uses rank_bm25 library
        results = self._index.rank(query, top_k)
        return [self._to_result(r) for r in results]
```

### dense_retriever.py

**Purpose**: Semantic search using embeddings.

```python
class DenseRetriever:
    """Embedding-based similarity search."""
    
    async def search(self, query, collection, top_k):
        # 1. Embed query
        query_embedding = await self._embedding_model.encode([query])
        
        # 2. Search Qdrant
        results = await self._qdrant.search(
            collection=collection,
            query_vector=query_embedding[0].tolist(),
            limit=top_k,
        )
        
        return [self._to_result(r) for r in results]
```

---

# 📁 src/verification/ vs src/verifiers/

## src/verification/__init__.py

**Purpose**: Empty wrapper - placeholder for future.

```python
"""Verification module - first-class verification layer."""

from src.verification.schemas import (
    VerificationStatus,
    CheckResult,
    VerificationReport,
    AbstentionReason,
    Abstention,
)
from src.verification.trace import VerificationStep, VerificationTrace, generate_trace_id

__all__ = [
    "VerificationStatus",
    "CheckResult", 
    "VerificationReport",
    "AbstentionReason",
    "Abstention",
    "VerificationStep",
    "VerificationTrace",
    "generate_trace_id",
]
```

**Note**: Just re-exports from `src/verifiers/`.

---

## src/verifiers/suite_builder.py

**Purpose**: Build and run verification suites.

**Lines**: ~475

### Build Functions

```python
def build_verification_suite_for(agent_name: str) -> VerificationSuite:
    """Build verification suite for specific agent."""
    
    SUITES = {
        "fiqh": VerificationSuite(checks=[
            VerificationCheck(name="quote_validator", fail_policy="abstain", enabled=True),
            VerificationCheck(name="source_attributor", fail_policy="warn", enabled=True),
            VerificationCheck(name="contradiction_detector", fail_policy="proceed", enabled=True),
            VerificationCheck(name="evidence_sufficiency", fail_policy="abstain", enabled=True),
        ]),
        "hadith": VerificationSuite(checks=[
            VerificationCheck(name="quote_validator", fail_policy="abstain", enabled=True),
            VerificationCheck(name="hadith_grade_checker", fail_policy="abstain", enabled=True),
            # ...
        ]),
        # ... more agents
    }
    
    return SUITES.get(agent_name, VerificationSuite(checks=[]))
```

### Run Functions

```python
async def run_verification_suite(
    answer: str,
    passages: list[RetrievalPassage],
    suite: VerificationSuite,
) -> VerificationReport:
    """Run all checks in suite."""
    
    results = []
    abstentions = []
    
    for check in suite.checks:
        if not check.enabled:
            continue
        
        result = await _run_check(check.name, answer, passages)
        results.append(result)
        
        if result.status == "abstained":
            abstentions.append(result)
    
    # Aggregate
    confidence = _compute_confidence(results)
    
    return VerificationReport(
        status="passed" if confidence > 0.7 else "failed",
        confidence=confidence,
        verified_passages=[r for r in results if r.passed],
        abstained=len(abstentions) > 0,
    )
```

---

## Other Verifier Files

| File | Check |
|------|-------|
| `exact_quote.py` | Quote validation |
| `source_attribution.py` | Source verification |
| `hadith_grade.py` | Hadith grading |
| `contradiction.py` | Check contradictions |
| `evidence_sufficiency.py` | Evidence check |
| `temporal_consistency.py` | Time checks |
| `school_consistency.py` | Madhhab check |
| `groundedness_judge.py` | Grounding check |

---

# 📁 Remaining Files

Due to length constraints, here are quick references for remaining modules:

| Module | Files | Purpose |
|--------|-------|---------|
| `src/core/` | 4 | Registry, exceptions, router |
| `src/domain/` | 10+ | Intents, models |
| `src/infrastructure/` | 15+ | Qdrant, LLM, DB |
| `src/knowledge/` | 14 | Legacy wrapper |
| `src/tools/` | 10 | Islamic tools |
| `src/generation/` | 15 | Answer generation |
| `src/quran/` | 10 | Quran logic |

---

**Last Updated**: April 2026

**Related**:
- [18_src_modules_complete_guide.md](18_src_modules_complete_guide.md)
- [19_complete_file_index.md](19_complete_file_index.md)