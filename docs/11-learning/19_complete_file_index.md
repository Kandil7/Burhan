# 📋 Complete File Index - src/ Directory

This document provides a detailed index of every file in the `src/` directory with explanations.

---

## 🗂️ src/agents/ (14 files)

### Core Files

| File | Lines | Purpose | Key Exports |
|------|-------|---------|------------|
| `base.py` | ~100 | **CORE TYPES** - missing module created to fix 60+ imports | `AgentInput`, `AgentOutput`, `Citation`, `BaseAgent`, `strip_cot_leakage` |
| `collection_agent.py` | ~15 | Legacy alias | `RetrievalStrategy`, `VerificationCheck` |

### CollectionAgents (v2)

| File | Lines | Domain | Config |
|------|-------|--------|---------|
| `collection/__init__.py` | ~50 | Export all agents | - |
| `collection/base.py` | ~546 | **BASE** - CollectionAgent base classes | `CollectionAgentConfig`, `RetrievalStrategy`, `IntentLabel` |
| `collection/fiqh.py` | ~280 | FiQH (jurisprudence) | `fiqh.yaml` |
| `collection/hadith.py` | ~240 | Hadith | `hadith.yaml` |
| `collection/tafsir.py` | ~180 | Tafsir (Quran exegesis) | `tafsir.yaml` |
| `collection/aqeedah.py` | ~170 | Aqeedah (theology) | `aqeedah.yaml` |
| `collection/seerah.py` | ~180 | Seerah (biography) | `seerah.yaml` |
| `collection/history.py` | ~150 | Islamic history | `history.yaml` |
| `collection/usul_fiqh.py` | ~170 | Usul al-Fiqh | `usul_fiqh.yaml` |
| `collection/language.py` | ~160 | Arabic language | `language.yaml` |
| `collection/general.py` | ~160 | General Islamic | `general.yaml` |
| `collection/tazkiyah.py` | ~150 | Tazkiyah (spirituality) | `tazkiyah.yaml` |

---

## 🗂️ src/api/ (25 files)

### Entry Point

| File | Lines | Purpose |
|------|-------|---------|
| `main.py` | ~120 | FastAPI app creation |

### Lifespan

| File | Lines | Purpose |
|------|-------|---------|
| `lifespan.py` | ~90 | Startup/shutdown lifecycle |

### Routes

| File | Lines | Endpoint | Purpose |
|------|-------|----------|---------|
| `routes/ask.py` | ~200 | POST /api/v1/ask | Main Q&A |
| `routes/search.py` | ~500 | POST /api/v1/search | Search |
| `routes/tools.py` | ~200 | POST /api/v1/tools | Tools |
| `routes/quran.py` | ~300 | POST /api/v1/quran | Quran |
| `routes/classify.py` | ~150 | POST /classify | Intent (Phase 8) |
| `routes/health.py` | ~50 | GET /health | Health |
| `routes/fiqh.py` | ~100 | FiQH specific | FiQH endpoints |

### Schemas

| File | Lines | Schema |
|------|-------|-------|
| `schemas/ask.py` | ~200 | AskRequest, AskResponse |
| `schemas/search.py` | ~150 | SearchRequest, SearchResponse |
| `schemas/tools.py` | ~150 | ToolRequest, ToolResponse |
| `schemas/quran.py` | ~150 | QuranRequest, QuranResponse |
| `schemas/common.py` | ~250 | CitationResponse, ErrorResponse |
| `schemas/response.py` | ~50 | Generic response |
| `schemas/trace.py` | ~100 | Trace schemas |
| `schemas/traces.py` | ~100 | Trace request/response |
| `schemas/classification.py` | ~100 | Classification schemas |
| `schemas/classify.py` | ~80 | Classify request/response |

### Middleware

| File | Lines | Purpose |
|------|-------|---------|
| `middleware/security.py` | ~250 | CORS, rate limiting |
| `middleware/request_logging.py` | ~100 | Logging |
| `middleware/request_id.py` | ~50 | Request ID |
| `middleware/error_handler.py` | ~100 | Global errors |

---

## 🗂️ src/application/ (30 files)

### Use Cases

| File | Lines | Purpose |
|------|-------|---------|
| `use_cases/answer_query.py` | ~150 | Main query answering |
| `use_cases/classify_query.py` | ~100 | Intent classification |
| `use_cases/run_tool.py` | ~80 | Tool execution |
| `use_cases/run_retrieval.py` | ~60 | Retrieval only |
| `use_cases/build_trace.py` | ~80 | Trace building |

### Services

| File | Lines | Purpose |
|------|-------|---------|
| `services/ask_service.py` | ~100 | Answers queries |
| `services/search_service.py` | ~80 | Searches |
| `services/tool_service.py` | ~150 | Executes tools |
| `services/classify_service.py` | ~100 | Classifies intents |
| `services/trace_service.py` | ~80 | Manages traces |

### Router (Classification)

| File | Lines | Purpose |
|------|-------|---------|
| `router/router_agent.py` | ~106 | RouterAgent |
| `router/hybrid_classifier.py` | ~200 | MasterHybridClassifier ⚠️ **DUPLICATE NAME** with below |
| `router/classifier_factory.py` | ~160 | KeywordBasedClassifier |
| `router/embedding_classifier.py` | ~100 | Embedding classifier |
| `router/orchestration.py` | ~300 | Multi-agent orchestration |
| `router/multi_agent.py` | ~150 | MultiAgentRouter |
| `router/risk_policy.py` | ~100 | Risk assessment |
| `router/config_router.py` | ~300 | Config-based routing |

### Other Application Files

| File | Lines | Purpose |
|------|-------|---------|
| `classifier_factory.py` | ~102 | FallbackChainClassifier |
| `interfaces.py` | ~250 | Protocol definitions |
| `models.py` | ~50 | RoutingDecision |
| `container.py` | ~200 | Dependency injection |

---

## 🗂️ src/core/ (4 files)

| File | Lines | Purpose |
|------|-------|---------|
| `registry.py` | ~200 | Agent registry |
| `exceptions.py` | ~100 | Custom exceptions |
| `router.py` | ~300 | Query router (legacy) |
| `citation.py` | ~150 | Citation normalization |

---

## 🗂️ src/domain/ (~10 files)

| File | Lines | Purpose |
|------|-------|---------|
| `intents.py` | ~378 | 16 Intent types + routing |
| `models.py` | ~150 | Domain models |
| `citations.py` | ~100 | Citation types |

---

## 🗂️ src/retrieval/ (38 files - Well Organized)

### Main

| File | Lines | Purpose |
|------|-------|---------|
| `__init__.py` | ~20 | Exports |
| `schemas.py` | ~100 | RetrievalResult, QueryType |
| `strategies.py` | ~150 | Per-agent strategies |

### Retrievers

| File | Lines | Purpose |
|------|-------|---------|
| `retrievers/hybrid_retriever.py` | ~200 | Hybrid (semantic + BM25) |
| `retrievers/bm25_retriever.py` | ~150 | BM25 keyword |
| `retrievers/dense_retriever.py` | ~100 | Semantic search |
| `retrievers/sparse_retriever.py` | ~100 | Sparse retriever |
| `retrievers/hierarchical_retriever.py` | ~200 | Hierarchical |
| `retrievers/multi_collection_retriever.py` | ~150 | Cross-collection |

### Filters

| File | Lines | Purpose |
|------|-------|---------|
| `filters/builder.py` | ~100 | Filter builder |
| `filters/presets.py` | ~100 | Preset filters |

### Fusion

| File | Lines | Purpose |
|------|-------|---------|
| `fusion/rrf.py` | ~100 | Reciprocal Rank Fusion |

### Ranking

| File | Lines | Purpose |
|------|-------|---------|
| `ranking/reranker.py` | ~150 | Re-ranking |
| `ranking/book_weighter.py` | ~100 | Book importance |
| `ranking/authority_scorer.py` | ~100 | Authority scoring |
| `ranking/score_fusion.py` | ~80 | Score fusion |

### Aggregation

| File | Lines | Purpose |
|------|-------|---------|
| `aggregation/clusterer.py` | ~100 | Result clustering |
| `aggregation/deduper.py` | ~100 | De-duplication |
| `aggregation/evidence_aggregator.py` | ~150 | Evidence aggregation |

### Planning

| File | Lines | Purpose |
|------|-------|---------|
| `planning/retrieval_plan.py` | ~100 | Retrieval planning |

### Expanders

| File | Lines | Purpose |
|------|-------|---------|
| `expanders/query_expander.py` | ~100 | Query expansion |
| `expanders/islamic_synonyms.py` | ~100 | Islamic synonyms |

### Policies

| File | Lines | Purpose |
|------|-------|---------|
| `policies/collection_policy.py` | ~100 | Collection policies |
| `policies/retrieval_policy.py` | ~100 | Retrieval policies |

---

## 🗂️ src/verification/ vs src/verifiers/

### verification/ (Wrapper - Empty)

| File | Lines | Purpose |
|------|-------|---------|
| `__init__.py` | ~21 | Re-exports |
| `schemas.py` | ~100 | Verification schemas |
| `trace.py` | ~100 | Trace |
| `checks/__init__.py` | ~30 | Checks wrapper |

### verifiers/ (Active - Deprecated)

| File | Lines | Purpose |
|------|-------|---------|
| `__init__.py` | ~30 | ⚠️ DEPRECATED notice |
| `suite_builder.py` | ~475 | Build/Run verification |
| `base.py` | ~100 | Base classes |
| `exact_quote.py` | ~200 | Quote validation |
| `source_attribution.py` | ~200 | Source verification |
| `hadith_grade.py` | ~200 | Hadith grading |
| `contradiction.py` | ~150 | Check contradictions |
| `evidence_sufficiency.py` | ~150 | Evidence check |
| `temporal_consistency.py` | ~100 | Time checks |
| `school_consistency.py` | ~100 | Madhhab checks |
| `groundedness_judge.py` | ~100 | Grounding check |
| `quote_span.py` | ~100 | Quote spans |
| `policies.py` | ~100 | Verification policies |
| `pipeline.py` | ~100 | Pipeline |
| `fiqh_checks.py` | ~100 | FiQH checks |

---

## 🗂️ src/knowledge/ (Legacy Wrapper - 14 files)

**Purpose**: Legacy facade wrapping `src/retrieval/`. Kept for backward compatibility.

| File | Purpose |
|------|---------|
| `__init__.py` | Re-exports |
| `embedding_model.py` | BGE-M3 embeddings |
| `vector_store.py` | Qdrant client |
| `hybrid_search.py` | Hybrid search |
| `bm25_retriever.py` | BM25 (wraps retrieval) |
| `query_expander.py` | Query expansion |
| `hierarchical_retriever.py` | Hierarchical |
| `reranker.py` | Re-ranking |
| `book_weighter.py` | Book weighting |
| `title_loader.py` | Load titles |
| `hadith_grader.py` | Hadith grading |
| `hadith_grader_original.py` | Original grader |
| `embedding_cache.py` | Embedding cache |
| `hierarchical_chunker.py` | Text chunking |

---

## 🗂️ src/infrastructure/ (~15 files)

| Directory | Files | Purpose |
|-----------|-------|---------|
| `qdrant/` | 5 | Qdrant client |
| `llm/` | 5 | LLM clients |
| `database.py` | 1 | PostgreSQL |
| `redis.py` | 1 | Redis cache |

---

## 🗂️ Other Modules

| Module | Files | Purpose |
|--------|-------|---------|
| `src/config/` | ~10 | Configuration |
| `src/config_runtime/` | ~5 | Runtime config |
| `src/generation/` | ~15 | Answer generation |
| `src/tools/` | ~10 | Islamic tools |
| `src/quran/` | ~10 | Quran logic |
| `src/evaluation/` | ~10 | Metrics |
| `src/indexing/` | ~10 | Indexing |
| `src/data/` | ~10 | Data processing |
| `src/utils/` | ~10 | Utilities |

---

## 📊 Statistics

| Category | Count |
|----------|-------|
| Total files | ~200 |
| Total lines | ~15,500 |
| Agents | 11 |
| API endpoints | 20 |
| Tools | 5 |
| Verification checks | 8 |
| Intent types | 16 + 4 Quran |

---

## 🔗 Related

- [18_src_modules_complete_guide.md](18_src_modules_complete_guide.md)
- [INDEX.md](INDEX.md)
- [learning_path.md](learning_path.md)

**Last Updated**: April 2026