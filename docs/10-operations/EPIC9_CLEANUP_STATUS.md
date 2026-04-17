# Epic 9 Cleanup Summary - Deferred Due to Test Failures

## Current Status: Tests Failing - Cleanup Deferred

The regression tests fail with critical import errors, so the cleanup cannot proceed. 
Below is a detailed analysis and recommended cleanup actions once tests pass.

---

## Test Failure Analysis

### 1. Circular Import in Router Module
**File**: `src/application/router/router_agent.py:13`
```python
from src.application.router import RouterAgent as _OriginalRouterAgent
```
**Problem**: This creates a circular import because:
- `src/application/router/__init__.py` imports from `router_agent.py`
- `router_agent.py` imports from `src.application.router` (itself via __init__)

**Root Cause**: The `RouterAgent` class was supposed to exist in `src/core/router.py` but it's not there. 
The code references a class that was never migrated properly.

### 2. Missing Intent.ZAKAT
**Test**: `tests/test_router.py` expects `Intent.ZAKAT`
**Problem**: `src/domain/intents.py` defines intents but doesn't include `ZAKAT` - it's in the old `src/config/intents.py` which is a re-export shim that may not work correctly.

---

## Phase 1: Fix Test Failures First (Required before cleanup)

### A. Fix Circular Import in router_agent.py
**Option 1**: Create a proper RouterAgent class in `src/application/router/router_agent.py`
**Option 2**: Remove the circular reference and implement routing logic directly

### B. Add missing intent values to domain/intents.py
The old config/intents.py re-exports from domain, but the test expects `Intent.ZAKAT` which may have been removed during refactoring.

---

## Phase 2: After Tests Pass - Cleanup Actions

### 1. Remove Compatibility Shims from src/knowledge/ files

The following files in `src/knowledge/` are deprecated wrappers that re-export from new locations:

| File | New Location | Status |
|------|---------------|--------|
| `hybrid_search.py` | `src/retrieval/retrievers/hybrid_retriever.py` | Wrapper - DELETE |
| `bm25_retriever.py` | `src/retrieval/retrievers/bm25_retriever.py` | Wrapper - DELETE |
| `hierarchical_retriever.py` | `src/retrieval/retrievers/hierarchical_retriever.py` | Wrapper - DELETE |
| `query_expander.py` | `src/retrieval/expanders/query_expander.py` | Wrapper - DELETE |
| `book_weighter.py` | `src/retrieval/ranking/book_weighter.py` | Wrapper - DELETE |
| `reranker.py` | `src/retrieval/ranking/reranker.py` | Wrapper - DELETE |
| `embedding_model.py` | `src/indexing/embeddings/embedding_model.py` | Wrapper - DELETE |
| `embedding_cache.py` | `src/indexing/embeddings/embedding_cache.py` | Wrapper - DELETE |
| `vector_store.py` | `src/indexing/vectorstores/qdrant_store.py` | Wrapper - DELETE |
| `title_loader.py` | `src/indexing/metadata/title_loader.py` | Wrapper - DELETE |
| `hadith_grader.py` | `src/verifiers/hadith_grade.py` | Wrapper - DELETE |

**Original implementations to KEEP**:
- `hadith_grader_original.py` - Original implementation, review if still needed

### 2. Remove src/core/router.py
**Status**: This file exists but doesn't contain the expected `RouterAgent` class
**Action**: DELETE this file after verifying no imports depend on it

**Current imports** (none found):
```bash
grep -r "from src.core.router import" --include="*.py"
# Returns no results
```

### 3. Update src/application/router/__init__.py and router_agent.py
The circular import issue needs resolution. After fixing, verify the structure is correct.

### 4. Clean up duplicate registry implementations
**Files**:
- `src/core/registry.py` - Main registry (2 imports in lifespan.py)
- `src/agents/registry.py` - Agent registry

**Recommendation**: Consolidate to `src/agents/registry.py` as primary, update imports from `lifespan.py` to use `src.agents.registry`

### 5. Update Imports Across Codebase

After removing deprecated paths, update these import statements:

| Old Import | New Import |
|------------|------------|
| `from src.knowledge.hybrid_search import HybridSearcher` | `from src.retrieval.retrievers.hybrid_retriever import HybridSearcher` |
| `from src.knowledge.bm25_retriever import BM25Retriever` | `from src.retrieval.retrievers.bm25_retriever import BM25Retriever` |
| `from src.knowledge.hierarchical_retriever import HierarchicalRetriever` | `from src.retrieval.retrievers.hierarchical_retriever import HierarchicalRetriever` |
| `from src.knowledge.query_expander import QueryExpander` | `from src.retrieval.expanders.query_expander import QueryExpander` |
| `from src.knowledge.book_weighter import BookImportanceWeighter` | `from src.retrieval.ranking.book_weighter import BookImportanceWeighter` |
| `from src.knowledge.reranker import Reranker` | `from src.retrieval.ranking.reranker import Reranker` |
| `from src.knowledge.embedding_model import EmbeddingModel` | `from src.indexing.embeddings.embedding_model import EmbeddingModel` |
| `from src.knowledge.embedding_cache import EmbeddingCache` | `from src.indexing.embeddings.embedding_cache import EmbeddingCache` |
| `from src.knowledge.vector_store import VectorStore` | `from src.indexing.vectorstores.qdrant_store import VectorStore` |
| `from src.knowledge.title_loader import TitleLoader` | `from src.indexing.metadata.title_loader import TitleLoader` |
| `from src.knowledge.hadith_grader import HadithAuthenticityGrader` | `from src.verifiers.hadith_grade import HadithAuthenticityGrader` |
| `from src.core.router import HybridQueryClassifier` | Already migrated to `src/application/router/hybrid_classifier.py` |
| `from src.application.router import RouterAgent` | `from src.application.router.router_agent import RouterAgent` |
| `from src.application.hybrid_classifier import HybridIntentClassifier` | `from src.application.router.hybrid_classifier import HybridIntentClassifier` |

---

## Files Currently Using Deprecated Imports (18 instances)

```
src/agents/registry.py:20 - src.knowledge.vector_store
src/agents/registry.py:21 - src.knowledge.embedding_model
src/verifiers/hadith_grade.py:86 - src.knowledge.hadith_grader
src/indexing/pipelines/build_collection_indexes.py:198 - src.knowledge.hierarchical_chunker
src/application/container.py:20 - src.knowledge.vector_store
src/application/container.py:21 - src.knowledge.embedding_model
src/application/container.py:122 - src.knowledge.vector_store
src/application/container.py:129 - src.knowledge.embedding_model
src/application/container.py:168 - src.knowledge.embedding_cache
src/api/lifespan.py:66 - src.knowledge.embedding_model
src/api/lifespan.py:67 - src.knowledge.vector_store
src/agents/base_rag_agent.py:22 - src.knowledge.book_weighter
src/agents/base_rag_agent.py:23 - src.knowledge.hadith_grader
src/agents/base_rag_agent.py:24 - src.knowledge.hierarchical_retriever
src/agents/base_rag_agent.py:25 - src.knowledge.hybrid_search
src/agents/base_rag_agent.py:26 - src.knowledge.title_loader
```

---

## Recommended Cleanup Order

1. **Fix circular import** - Resolve `router_agent.py` import issue
2. **Add missing Intent values** - Ensure all expected intents exist
3. **Update all deprecated imports** - Fix 18 import references
4. **Run tests** - Verify all tests pass
5. **Delete deprecated wrappers** in `src/knowledge/`
6. **Delete `src/core/router.py`** - If not needed
7. **Consolidate registry** - Prefer `src/agents/registry.py`
8. **Final verification** - Run full test suite

---

## New Module Structure (Post-Cleanup)

```
src/
├── api/                    # Transport layer (FastAPI)
├── application/           # Use cases, services, orchestration
│   ├── router/           # RouterAgent, classifiers, risk policy
│   ├── services/         # Ask, Search, Classify, Tool, Trace services
│   └── use_cases/        # Answer, Classify, Run Retrieval, Run Tool, Build Trace
├── domain/               # Business entities, intents, collections
├── agents/               # Agent implementations, registry
├── retrieval/            # Retrievers, rankers, expanders, policies
├── indexing/             # Embeddings, vector stores, metadata
├── verifiers/            # Verification pipeline, validators
├── generation/           # LLM client, prompts, composers
├── tools/                # Tool implementations
├── infrastructure/       # Database, Redis, telemetry
├── config/               # Settings, constants, logging
├── core/                 # Exceptions, types (minimal)
└── utils/                # Utilities
```

---

## Summary

| Action | Status | Notes |
|--------|--------|-------|
| Fix circular import | **BLOCKED** | Required before any cleanup |
| Add missing Intent.ZAKAT | **BLOCKED** | Required by tests |
| Update 18 deprecated imports | **BLOCKED** | Must do after fixing circular import |
| Delete 11 deprecated knowledge wrappers | **DEFERRED** | After tests pass |
| Delete src/core/router.py | **DEFERRED** | After verifying no imports |
| Consolidate registry | **DEFERRED** | Prefer agents/registry.py |
| Final architecture verification | **DEFERRED** | After all changes |

---

*Generated: 2026-04-17*
*Epic 9 - Remove Deprecated Code*