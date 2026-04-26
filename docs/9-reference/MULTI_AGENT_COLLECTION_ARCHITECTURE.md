# Burhan Multi-Agent Collection-Aware RAG Architecture

## Overview

This document describes the implementation of the Multi-Agent Collection-Aware RAG system for Burhan Islamic QA. The architecture enables hybrid dense/sparse retrieval with per-agent verification and orchestration.

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              CLIENT REQUEST                                  │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         ROUTER & ORCHESTRATION                               │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────────────────┐  │
│  │ RouterAgent     │  │ MultiAgent      │  │ Orchestration Patterns     │  │
│  │ (intent class)  │  │ Orchestrator    │  │ SEQUENTIAL/PARALLEL/HIER   │  │
│  └─────────────────┘  └─────────────────┘  └─────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                    ┌─────────────────┼─────────────────┐
                    │                 │                 │
                    ▼                 ▼                 ▼
        ┌───────────────────┐ ┌───────────────────┐ ┌───────────────────┐
        │   FiqhCollection  │ │ HadithCollection  │ │   TafsirCollection│
        │      Agent       │ │      Agent        │ │      Agent        │
        └───────────────────┘ └───────────────────┘ └───────────────────┘
                    │                 │                 │
                    ▼                 ▼                 ▼
        ┌───────────────────────────────────────────────────────────────────┐
        │                    RETRIEVAL LAYER                               │
        │  ┌─────────────┐  ┌─────────────┐  ┌──────────────────────────┐  │
        │  │ Retrieval   │  │ Hybrid      │  │ RetrievalStrategy       │  │
        │  │ Strategies  │  │ Qdrant      │  │ (per-agent config)      │  │
        │  │ (matrix)    │  │ Client      │  │                          │  │
        │  └─────────────┘  └─────────────┘  └──────────────────────────┘  │
        └───────────────────────────────────────────────────────────────────┘
                                      │
                    ┌─────────────────┼─────────────────┐
                    │                 │                 │
                    ▼                 ▼                 ▼
        ┌───────────────────────────────────────────────────────────────────┐
        │                    VERIFICATION LAYER                             │
        │  ┌─────────────┐  ┌─────────────┐  ┌──────────────────────────┐  │
        │  │ Quote       │  │ Source      │  │ Evidence                 │  │
        │  │ Validator   │  │ Attributor  │  │ Sufficiency              │  │
        │  └─────────────┘  └─────────────┘  └──────────────────────────┘  │
        │  ┌─────────────┐  ┌─────────────┐  ┌──────────────────────────┐  │
        │  │ Contradic-  │  │ Hadith      │  │ School                   │  │
        │  │ tion        │  │ Grade       │  │ Consistency              │  │
        │  └─────────────┘  └─────────────┘  └──────────────────────────┘  │
        └───────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
        ┌───────────────────────────────────────────────────────────────────┐
        │                    GENERATION LAYER                               │
        │  ┌─────────────────────────────────────────────────────────────┐  │
        │  │ LLM Generation with Citations                              │  │
        │  └─────────────────────────────────────────────────────────────┘  │
        └───────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
        ┌───────────────────────────────────────────────────────────────────┐
        │                         RESPONSE                                  │
        │  { answer, citations[], confidence, metadata, trace_id }        │
        └───────────────────────────────────────────────────────────────────┘
```

---

## Core Components

### 1. CollectionAgent Base Class

**Location**: `src/agents/collection_agent.py`

The abstract base class providing the full RAG pipeline:

```python
class CollectionAgent(ABC):
    name: str = "collection_agent"
    COLLECTION: str = ""

    # 7-stage pipeline
    def query_intake(self, query: str) -> str: ...
    def classify_intent(self, query: str) -> IntentLabel: ...
    async def retrieve_candidates(self, query: str) -> list[dict]: ...
    async def rerank_candidates(self, query: str, candidates: list[dict]) -> list[dict]: ...
    async def run_verification(self, query: str, candidates: list[dict]) -> VerificationReport: ...
    async def generate_answer(self, query: str, verified_passages: list[dict], language: str) -> str: ...
    def assemble_citations(self, passages: list[dict]) -> list[Citation]: ...

    # End-to-end execution
    async def run(self, raw_question: str, meta: dict | None = None) -> AgentOutput: ...
```

#### IntentLabel Enum

Agent-specific intents for each domain:

```python
class IntentLabel(str, Enum):
    # Fiqh
    FiqhHukm = "fiqh_hukm"
    FiqhMasaail = "fiqh_masaail"
    
    # Hadith
    HadithTakhrij = "hadith_takhrij"
    HadithSanad = "hadith_sanad"
    HadithMatn = "hadith_matn"
    
    # Tafsir
    TafsirAyah = "tafsir_ayah"
    TafsirMaqasid = "tafsir_maqasid"
    
    # Aqeedah
    AqeedahTawhid = "aqeedah_tawhid"
    AqeedahIman = "aqeedah_iman"
    
    # Seerah
    SeerahEvent = "seerah_event"
    SeerahMilad = "seerah_milad"
    
    # Usul Fiqh
    UsulFiqhIjtihad = "usul_fiqh_ijtihad"
    UsulFiqhQiyas = "usul_fiqh_qiyas"
    
    # History & Language
    IslamicHistoryEvent = "islamic_history_event"
    IslamicHistoryDynasty = "islamic_history_dynasty"
    ArabicGrammar = "arabic_grammar"
    ArabicMorphology = "arabic_morphology"
    ArabicBalaghah = "arabic_balaghah"
```

---

### 2. Retrieval Strategies Matrix

**Location**: `src/retrieval/strategies.py`

Per-agent retrieval configurations:

| Agent | Dense | Sparse | Top K | Rerank | Threshold | Collection |
|-------|-------|--------|-------|--------|-----------|------------|
| fiqh_agent | 0.6 | 0.4 | 80 | True | 0.65 | fiqh |
| hadith_agent | 0.5 | 0.5 | 60 | True | 0.70 | hadith |
| tafsir_agent | 0.7 | 0.3 | 40 | True | 0.75 | quran |
| aqeedah_agent | 0.6 | 0.4 | 50 | True | 0.65 | aqeedah |
| seerah_agent | 0.5 | 0.5 | 50 | True | 0.60 | seerah |
| usul_fiqh_agent | 0.7 | 0.3 | 60 | True | 0.70 | usul_fiqh |
| history_agent | 0.5 | 0.5 | 50 | True | 0.60 | islamic_history |
| language_agent | 0.4 | 0.6 | 40 | True | 0.65 | arabic_language |
| general_islamic_agent | 0.5 | 0.5 | 30 | False | 0.55 | general_islamic |

```python
def get_strategy_for_agent(agent_name: str) -> RetrievalStrategy:
    """Get retrieval strategy for an agent."""
    ...

def get_collection_for_agent(agent_name: str) -> str:
    """Get Qdrant collection for an agent."""
    ...
```

---

### 3. Verification Suite

**Location**: `src/verifiers/suite_builder.py`

Each agent has a verification suite with fail policies:

```python
VerificationSuite(
    checks=[
        VerificationCheck(name="quote_validator", fail_policy="abstain", enabled=True),
        VerificationCheck(name="source_attributor", fail_policy="warn", enabled=True),
        VerificationCheck(name="contradiction_detector", fail_policy="proceed", enabled=True),
        VerificationCheck(name="evidence_sufficiency", fail_policy="abstain", enabled=True),
    ],
    fail_fast=True
)
```

#### Fail Policies

| Policy | Behavior |
|--------|----------|
| `abstain` | Return empty verified_passages, do not generate answer |
| `warn` | Continue but add warning to metadata |
| `proceed` | Continue with verification results |

#### Available Verifiers

- **QuoteValidator**: Verifies exact quote matching
- **SourceAttributor**: Verifies source attribution
- **ContradictionDetector**: Detects contradictions in passages
- **EvidenceSufficiency**: Verifies evidence is sufficient
- **HadithGradeChecker**: Verifies hadith authenticity grades
- **SchoolConsistency**: Verifies madhhab consistency
- **TemporalConsistency**: Verifies era consistency
- **GroundednessJudge**: Verifies answer is grounded in sources

---

### 4. Multi-Agent Orchestration

**Location**: `src/application/router/orchestration.py`

#### Orchestration Patterns

```python
class OrchestrationPattern(str, Enum):
    SEQUENTIAL = "sequential"   # Agent → Agent → ...
    PARALLEL = "parallel"      # Agent + Agent + ...
    HIERARCHICAL = "hierarchical"  # Primary + Secondary agents
```

#### Thresholds

```python
PRIMARY_THRESHOLD = 0.7       # High confidence - direct routing
SECONDARY_THRESHOLD = 0.4     # Medium confidence - multiple agents
LOW_CONFIDENCE_THRESHOLD = 0.2  # Low confidence - fallback to GeneralIslamicAgent
```

#### Decision Tree Routing

Rule-based routing by keyword detection:

| Keyword | Agent |
|---------|-------|
| آية, قرآن, سورة | tafsir_agent |
| حديث, سنن, صحيح | hadith_agent |
| حكم, فقه, حلال | fiqh_agent |
| عقيدة, توحيد | aqeedah_agent |
| سيرة, غزوة | seerah_agent |

---

### 5. Collection Agents

| Agent | File | Collection | Intents |
|-------|------|------------|---------|
| FiqhCollectionAgent | `fiqh_collection_agent.py` | fiqh | FiqhHukm, FiqhMasaail |
| HadithCollectionAgent | `hadith_collection_agent.py` | hadith | HadithTakhrij, HadithSanad, HadithMatn |
| TafsirCollectionAgent | `tafsir_collection_agent.py` | quran | TafsirAyah, TafsirMaqasid |
| AqeedahCollectionAgent | `aqeedah_collection_agent.py` | aqeedah | AqeedahTawhid, AqeedahIman |
| SeerahCollectionAgent | `seerah_collection_agent.py` | seerah | SeerahEvent, SeerahMilad |
| UsulFiqhCollectionAgent | `usul_fiqh_collection_agent.py` | usul_fiqh | UsulFiqhIjtihad, UsulFiqhQiyas |
| HistoryCollectionAgent | `history_collection_agent.py` | islamic_history | IslamicHistoryEvent, IslamicHistoryDynasty |
| LanguageCollectionAgent | `language_collection_agent.py` | arabic_language | ArabicGrammar, ArabicMorphology, ArabicBalaghah |

---

### 6. API Endpoints

**Location**: `src/api/routes/`

#### Main Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/fiqh/answer` | POST | Fiqh-specific query answering |
| `/ask` | POST | General query answering |
| `/classify` | POST | Intent classification only |
| `/search` | POST | Search operations |
| `/health` | GET | Health check |

#### Fiqh Endpoint

```bash
POST /fiqh/answer
{
  "query": "ما حكم صلاة الجمعة؟",
  "language": "ar",
  "madhhab": "hanafi"  # optional
}

Response:
{
  "answer": "...",
  "citations": [...],
  "confidence": 0.95,
  "ikhtilaf_detected": true,
  "metadata": {...},
  "trace_id": "...",
  "processing_time_ms": 150
}
```

---

### 7. Metadata Enrichment

**Location**: `src/indexing/metadata/enrichment.py`

Era classification for Islamic scholars:

| Era | Death Year (AH) | Example |
|-----|-----------------|---------|
| Prophetic | 0-100 | Companions |
| Tabi'un | 100-200 | Successors |
| Classical | 200-500 | Golden Age scholars |
| Medieval | 500-900 | Post-classical |
| Ottoman | 900-1300 | Ottoman-era |
| Modern | 1300+ | Contemporary |

Enriched fields:
- book_title, author_name, author_death_year
- madhhab, aqeedah_school, era
- category_main, category_sub
- collection, hierarchy

---

### 8. Hybrid Qdrant Configuration

**Location**: `src/indexing/vectorstores/hybrid_config.py`

Collection configurations with HNSW and quantization:

```python
class HNSWPreset:
    SMALL = {"m": 8, "ef_construct": 64, "full_scan_threshold": 10000}
    MEDIUM = {"m": 16, "ef_construct": 128, "full_scan_threshold": 10000}
    LARGE = {"m": 32, "ef_construct": 256, "full_scan_threshold": 10000}

# Example: Fiqh collection
COLLECTION_CONFIGS["fiqh"] = CollectionConfig(
    dense=DenseVectorConfig(size=1024, distance=Distance.COSINE),
    sparse=SparseVectorConfig(type="BM25", k1=1.5, b=0.75),
    quantization=QuantizationConfig(type="INT8", always_ram=False),
    hnsw=HNSWConfig(**HNSWPreset.LARGE),
)
```

---

### 9. Evaluation Framework

**Location**: `src/evaluation/`

#### Metrics

| Metric | Description |
|--------|-------------|
| Precision@k | Retrieval precision |
| Recall@k | Retrieval recall |
| Citation Accuracy | Citation correctness |
| Ikhtilaf Coverage | School differences coverage |
| Abstention Rate | When model refuses to answer |
| Hadith Grade Accuracy | Authenticity grade accuracy |

#### Golden Set Schema

```python
@dataclass
class GoldenSetItem:
    id: str
    question: str
    domains: list[str]
    ikhtilaf_required: bool
    abstention_expected: bool
    gold_evidence_ids: list[str]
    gold_answer_outline: str
    metrics_flags: dict
```

---

## Usage Examples

### 1. Using FiqhCollectionAgent

```python
from src.agents.fiqh_collection_agent import FiqhCollectionAgent
from src.agents.base import AgentInput

agent = FiqhCollectionAgent(
    embedding_model=embedding_model,
    llm_client=llm_client,
    vector_store=vector_store
)

result = await agent.run(
    raw_question="ما حكم أداء صلاة العصر في جماعة؟",
    meta={"language": "ar", "madhhab": "hanafi"}
)

print(result.answer)
print(result.citations)
print(result.confidence)
```

### 2. Using Router with Orchestration

```python
from src.application.router.orchestration import (
    create_orchestration_plan,
    MultiAgentOrchestrator
)
from src.domain.intents import Intent

# Create plan for query
plan = create_orchestration_plan(
    query="ما حكم الصلاة وما صحة هذا الحديث",
    intent=Intent.FIQH
)

# Execute orchestration
orchestrator = MultiAgentOrchestrator(registry=agent_registry)
result = await orchestrator.execute_plan(plan, query)
```

### 3. Running Evaluation

```python
from src.evaluation.metrics import run_evaluation
from src.evaluation.golden_set_schema import load_golden_set

golden_set = load_golden_set("data/fiqh_golden_set.json")
results = await run_evaluation(fiqh_agent, golden_set)

print(f"Precision@5: {results.precision}")
print(f"Recall@5: {results.recall}")
print(f"Overall Score: {results.overall_score}")
```

---

## Testing

Run the collection agent tests:

```bash
# All new implementation tests
pytest tests/test_agents/ tests/test_retrieval/ tests/test_verifiers/ -v

# Specific agent tests
pytest tests/test_agents/test_fiqh_collection_agent.py -v
pytest tests/test_agents/test_collection_agents.py -v

# Evaluation tests
pytest tests/test_evaluation/ -v

# Orchestration tests
pytest tests/test_router/test_orchestration.py -v
```

---

## Configuration

### Environment Variables

```bash
# Qdrant
QDRANT_URL=http://localhost:6333
QDRANT_API_KEY=your_key

# LLM
LLM_MODEL=gpt-4
LLM_TEMPERATURE=0.15

# Embeddings
EMBEDDING_MODEL=bge-m3
EMBEDDING_DIM=1024

# Agent Settings
AGENT_TIMEOUT_SECONDS=30
RATE_LIMIT_RPM=60
```

---

## Migration from Old Architecture

The new architecture maintains backward compatibility through:

1. **Compatibility shims** in `src/knowledge/` that re-export from new locations
2. **Existing agents** (FiqhAgent, HadithAgent, etc.) still work
3. **Router integration** with both old and new agents

```python
# Old way (still works)
from src.agents.fiqh_agent import FiqhAgent
agent = FiqhAgent()

# New way (recommended)
from src.agents.fiqh_collection_agent import FiqhCollectionAgent
agent = FiqhCollectionAgent()
```

---

## Future Enhancements

1. **LLM-based Classifier** - Replace keyword routing with LLM intent classification
2. **LangGraph Integration** - Add stateful orchestration with LangGraph
3. **Cross-Encoder Reranking** - Implement proper reranking with cross-encoder models
4. **More Verification Checks** - Add more domain-specific verifiers
5. **Agent Tool Integration** - Enable agents to call tools (zakat calculator, etc.)

---

## File Structure

```
src/
├── agents/
│   ├── base.py                    # BaseAgent, Citation, AgentInput, AgentOutput
│   ├── base_rag_agent.py         # BaseRAGAgent (legacy)
│   ├── collection_agent.py       # CollectionAgent abstract base
│   ├── fiqh_collection_agent.py  # FiqhCollectionAgent
│   ├── hadith_collection_agent.py
│   ├── tafsir_collection_agent.py
│   ├── aqeedah_collection_agent.py
│   ├── seerah_collection_agent.py
│   ├── usul_fiqh_collection_agent.py
│   ├── history_collection_agent.py
│   ├── language_collection_agent.py
│   └── registry.py               # Agent registry
├── retrieval/
│   ├── strategies.py             # Retrieval strategy matrix
│   ├── retrievers/               # Dense, sparse, hybrid retrievers
│   ├── ranking/                  # Reranking, scoring
│   └── policies/                 # Collection policies
├── verifiers/
│   ├── base.py                   # BaseVerifier, VerificationResult
│   ├── suite_builder.py          # Verification suite builder
│   ├── fiqh_checks.py            # Fiqh-specific verifiers
│   ├── exact_quote.py            # Quote validation
│   ├── hadith_grade.py           # Hadith grading
│   └── ...                       # Other verifiers
├── application/
│   └── router/
│       ├── router_agent.py       # RouterAgent
│       ├── orchestration.py      # Multi-agent orchestration
│       └── multi_agent.py        # Multi-agent router
├── evaluation/
│   ├── golden_set_schema.py      # Golden set data model
│   ├── metrics.py                # Evaluation metrics
│   └── cli.py                    # Evaluation CLI
└── indexing/
    ├── metadata/
    │   └── enrichment.py         # Metadata enrichment
    └── vectorstores/
        ├── hybrid_config.py      # Collection configs
        └── hybrid_client.py      # Hybrid Qdrant client
```

---

## See Also

- [Phase 10 Index](./PHASE10_INDEX.md) - Navigation guide for all Phase 10 docs
- [API Collections](./API_COLLECTIONS.md) - API endpoints reference
- [Retrieval Strategies](./RETRIEVAL_STRATEGIES.md) - Retrieval configuration
- [Verification Framework](./VERIFICATION_FRAMEWORK.md) - Verification system
- [Orchestration Patterns](./ORCHESTRATION_PATTERNS.md) - Multi-agent patterns
- [Refactor Plan](./refactor_plan_add_multi_agent_collection_ware.md) - Implementation plan
- [CollectionAgent Architecture](./Burhan%20CollectionAgent%20Architecture%20and%20Multi-Agent%20RAG%20Design.md) - Design reference
- [API Documentation](../5-api/COMPLETE_DOCUMENTATION.md)