# Athar Phase 10 - Documentation Index

## Overview

This document provides a comprehensive index and navigation guide for the Multi-Agent Collection-Aware RAG system (Phase 10).

---

## 📚 Documentation Structure

### Core Documentation

| Document | Description | Key Topics |
|----------|-------------|------------|
| [MULTI_AGENT_COLLECTION_ARCHITECTURE](./MULTI_AGENT_COLLECTION_ARCHITECTURE.md) | Main architecture document | Architecture diagram, components, usage examples |
| [API_COLLECTIONS](./API_COLLECTIONS.md) | API endpoints reference | Request/response formats, examples, error handling |
| [RETRIEVAL_STRATEGIES](./RETRIEVAL_STRATEGIES.md) | Retrieval configuration | Strategy matrix, Qdrant config, filtering |
| [VERIFICATION_FRAMEWORK](./VERIFICATION_FRAMEWORK.md) | Verification system | Verifiers, fail policies, suites |
| [ORCHESTRATION_PATTERNS](./ORCHESTRATION_PATTERNS.md) | Multi-agent patterns | SEQUENTIAL/PARALLEL/HIERARCHICAL |
| [CONFIG_BACKED_AGENTS](./CONFIG_BACKED_AGENTS.md) | Declarative agent config | YAML configs, prompt files, config loader |
| [DOMAIN_KEYWORDS](./DOMAIN_KEYWORDS.md) | Routing keywords | Keyword patterns, confidence calculation |

---

## 🔑 Key Concepts

### 1. CollectionAgent

The abstract base class providing a 7-stage RAG pipeline:

```python
class CollectionAgent(ABC):
    async def run(self, raw_question: str, meta: dict) -> AgentOutput:
        # 1. query_intake    - Normalize query
        # 2. classify_intent - Classify to IntentLabel
        # 3. retrieve_candidates - Get passages
        # 4. rerank_candidates - Apply reranking
        # 5. run_verification  - Verify candidates
        # 6. generate_answer  - Generate from verified
        # 7. assemble_citations - Build citations
```

**Location**: `src/agents/collection_agent.py`

### 2. Retrieval Strategy Matrix

Each agent has optimized retrieval configuration:

| Agent | Dense | Sparse | Top K | Threshold |
|-------|-------|--------|-------|-----------|
| fiqh_agent | 0.6 | 0.4 | 80 | 0.65 |
| hadith_agent | 0.5 | 0.5 | 60 | 0.70 |
| tafsir_agent | 0.7 | 0.3 | 40 | 0.75 |

**Location**: `src/retrieval/strategies.py`

### 3. Verification Suite

Each agent has a verification suite with fail policies:

```python
VerificationSuite(
    checks=[
        VerificationCheck(name="quote_validator", fail_policy="abstain"),
        VerificationCheck(name="evidence_sufficiency", fail_policy="abstain"),
    ],
    fail_fast=True
)
```

**Location**: `src/verifiers/suite_builder.py`

---

## 📁 File Locations

### New Files (Phase 10)

```
src/agents/
├── collection_agent.py              # Base class + IntentLabel
├── fiqh_collection_agent.py        # FiqhCollectionAgent
├── hadith_collection_agent.py      # HadithCollectionAgent
├── tafsir_collection_agent.py      # TafsirCollectionAgent
├── aqeedah_collection_agent.py     # AqeedahCollectionAgent
├── seerah_collection_agent.py      # SeerahCollectionAgent
├── usul_fiqh_collection_agent.py   # UsulFiqhCollectionAgent
├── history_collection_agent.py     # HistoryCollectionAgent
└── language_collection_agent.py    # LanguageCollectionAgent

src/retrieval/
├── __init__.py                     # Module exports
└── strategies.py                   # Retrieval strategy matrix

src/verifiers/
├── suite_builder.py                # Verification suite builder
└── fiqh_checks.py                  # Fiqh verification stubs

src/application/router/
├── orchestration.py                # Multi-agent orchestration
├── multi_agent.py                  # Multi-agent router
└── config_router.py                # Config-backed keyword router

src/evaluation/
├── golden_set_schema.py           # Golden set data model
├── metrics.py                      # Evaluation metrics
└── cli.py                         # Evaluation CLI

src/indexing/
├── metadata/
│   └── enrichment.py              # Metadata enrichment
└── vectorstores/
    ├── hybrid_config.py           # Collection configs
    └── hybrid_client.py           # Hybrid Qdrant client

config/
├── agents/                        # Agent YAML configs (10 files)
│   ├── fiqh.yaml
│   ├── hadith.yaml
│   ├── tafsir.yaml
│   └── ... (10 agents total)
└── (future: router.yaml)

prompts/
├── _shared_preamble.txt          # Common rules
├── fiqh_agent.txt                # Agent prompts (10 files)
└── ... (10 agents total)

src/config/
├── __init__.py                   # AgentConfigManager
└── loader.py                     # Config loading utilities
```

---

## 🚀 Quick Start Examples

### 1. Using Collection Agent

```python
from src.agents.fiqh_collection_agent import FiqhCollectionAgent

agent = FiqhCollectionAgent(
    embedding_model=embedding_model,
    llm_client=llm_client,
    vector_store=vector_store
)

result = await agent.run(
    raw_question="ما حكم صلاة الجمعة؟",
    meta={"language": "ar"}
)

print(result.answer)
print(result.citations)
```

### 2. Using Retrieval Strategy

```python
from src.retrieval.strategies import get_strategy_for_agent

strategy = get_strategy_for_agent("fiqh_agent")
print(f"Top K: {strategy.top_k}")
print(f"Dense weight: {strategy.dense_weight}")
```

### 3. Using Verification Suite

```python
from src.verifiers.suite_builder import build_verification_suite_for

suite = build_verification_suite_for("fiqh_agent")
print(f"Checks: {[c.name for c in suite.checks]}")
```

### 4. Using Orchestration

```python
from src.application.router.orchestration import create_orchestration_plan
from src.domain.intents import Intent

plan = create_orchestration_plan(
    query="ما حكم الزكاة؟",
    intent=Intent.FIQH
)
print(f"Pattern: {plan.pattern}")
print(f"Tasks: {[t.agent_name for t in plan.tasks]}")
```

### 5. Running Evaluation

```python
from src.evaluation.metrics import run_evaluation

results = await run_evaluation(agent, golden_set)
print(f"Precision: {results.precision}")
print(f"Recall: {results.recall}")
```

### 6. Using Config-Backed Agents

```python
from src.config import get_config_manager

cm = get_config_manager()

# Load agent config
config = cm.load_config("fiqh")
print(config.retrieval.alpha)  # 0.6

# Load system prompt
prompt = cm.load_system_prompt("fiqh")
print(len(prompt))  # ~2355 chars

# Get CollectionAgentConfig
agent_config = cm.get_collection_agent_config("fiqh")
```

### 7. Using Config Router

```python
from src.application.router.config_router import get_config_router

router = get_config_router()

# Route a query
result = router.route("ما حكم صلاة الجماعة؟")
print(result.agent_name)  # "fiqh_agent"
print(result.confidence)  # 0.85
```

---

## 🧪 Testing

### Run All Phase 10 Tests

```bash
# Core agent tests
pytest tests/test_agents/test_collection_agent_base.py -v
pytest tests/test_agents/test_fiqh_collection_agent.py -v
pytest tests/test_agents/test_collection_agents.py -v

# Retrieval tests
pytest tests/test_retrieval/test_strategies.py -v

# Verifier tests
pytest tests/test_verifiers/test_suite_builder.py -v

# Orchestration tests
pytest tests/test_router/test_orchestration.py -v

# Evaluation tests
pytest tests/test_evaluation/test_metrics.py -v

# API tests
pytest tests/test_api/test_fiqh.py -v

# Config-backed agent tests
pytest tests/test_config_backed_agents.py -v
```

### Test Coverage

| Module | Tests |
|--------|-------|
| `test_collection_agent_base.py` | 27 tests |
| `test_fiqh_collection_agent.py` | 29 tests |
| `test_collection_agents.py` | 52 tests |
| `test_strategies.py` | 24 tests |
| `test_suite_builder.py` | 27 tests |
| `test_orchestration.py` | 24 tests |
| `test_metrics.py` | 25 tests |
| `test_fiqh.py` | 20 tests |
| `test_config_backed_agents.py` | 27 tests |

**Total**: 255+ tests

---

## 🔧 Configuration

### Environment Variables

```bash
# Required
GROQ_API_KEY=your_key
HF_TOKEN=your_token
QDRANT_URL=http://localhost:6333

# Optional
LLM_MODEL=gpt-4
LLM_TEMPERATURE=0.15
AGENT_TIMEOUT_SECONDS=30
RATE_LIMIT_RPM=60
```

### Key Constants

Located in `src/config/constants.py`:

- `RetrievalConfig` - Top-K, score thresholds
- `LLMConfig` - Temperature, max tokens
- `EmbeddingConfig` - Model, dimensions
- `CollectionNames` - Qdrant collections

---

## 🔄 Migration Guide

### From Legacy to Collection Agent

```python
# OLD WAY (still works)
from src.agents.fiqh_agent import FiqhAgent
agent = FiqhAgent()
result = await agent.execute(AgentInput(query="..."))

# NEW WAY (recommended)
from src.agents.fiqh_collection_agent import FiqhCollectionAgent
agent = FiqhCollectionAgent()
result = await agent.run(raw_question="...")
```

---

## 📊 Metrics

### Retrieval Metrics

- **Precision@k** - Percentage of relevant results in top-k
- **Recall@k** - Percentage of relevant results retrieved in top-k
- **Score Threshold** - Minimum similarity to include

### Verification Metrics

- **Quote Validation** - Exact quote matching
- **Source Attribution** - Author/source recognition
- **Evidence Sufficiency** - Minimum evidence check

### Generation Metrics

- **Citation Accuracy** - Correct citation format
- **Ikhtilaf Coverage** - Multiple madhhab views
- **Abstention Rate** - When model refuses to answer
- **Hadith Grade Accuracy** - Authenticity grade correct

---

## 🔮 Future Enhancements

1. **LLM-based Classifier** - Replace keyword routing
2. **LangGraph Integration** - Stateful orchestration
3. **Cross-Encoder Reranking** - Better reranking
4. **More Verifiers** - Domain-specific checks
5. **Tool Integration** - Agents call tools

---

## 📞 Support

### Finding Help

| Topic | File |
|-------|------|
| Agent implementation | `src/agents/collection_agent.py` |
| Retrieval configuration | `src/retrieval/strategies.py` |
| Verification logic | `src/verifiers/suite_builder.py` |
| Orchestration patterns | `src/application/router/orchestration.py` |
| API endpoints | `src/api/routes/fiqh.py` |

### Running Tests

```bash
# Quick test
pytest tests/test_agents/test_fiqh_collection_agent.py -v

# Full test suite
pytest tests/test_agents/ tests/test_retrieval/ tests/test_verifiers/ -v
```

---

## 📋 Changelog

### Phase 10 (April 18, 2026)

- ✅ Added CollectionAgent base class
- ✅ Added 8 Collection Agents (Fiqh, Hadith, Tafsir, etc.)
- ✅ Added RetrievalStrategy matrix
- ✅ Added VerificationSuite system
- ✅ Added MultiAgentOrchestrator
- ✅ Added Evaluation framework
- ✅ Added Hybrid Qdrant configuration
- ✅ Added Metadata enrichment
- ✅ Added Config-backed agent system (YAML + Prompts)
- ✅ Added ConfigRouter with DOMAIN_KEYWORDS
- ✅ Added AgentConfigManager for config loading
- ✅ Added 7 comprehensive documentation files

### Previous Phases

- Phase 9: Production Ready (April 16, 2026)
- Phase 8: Hybrid Intent Classifier
- Phase 7: Full Lucene Merge
- Phase 6: 13 Agents, 10 Collections
- Phase 5: Next.js Frontend
- Phase 4: RAG Pipelines
- Phase 3: Quran Pipeline
- Phase 2: 6 Tools
- Phase 1: Foundation

---

## See Also

- [Main README](../../README.md)
- [Architecture Overview](../2-architecture/01_ARCHITECTURE_OVERVIEW.md)
- [API Documentation](../5-api/COMPLETE_DOCUMENTATION.md)
- [Refactor Plan](../8-development/refactoring/refactor_plan_add_multi_agent_collection_ware.md)