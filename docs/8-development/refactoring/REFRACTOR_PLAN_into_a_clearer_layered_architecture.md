# Burhan Refactor Plan (v2)

> **Status: historical record.** This document captures the repository as it was at the
> time of writing. Some module, script, and data paths below have since been moved or
> removed.

This document defines a clean, low-risk refactor path for the Burhan backend into a clearer layered architecture suitable for FastAPI, hybrid retrieval, agentic orchestration, and explicit verification.[cite:80][cite:81][cite:83]

The current Burhan structure already contains strong building blocks such as FastAPI routes, specialized agents, hybrid search, reranking, deterministic tools, and Quran-specific validation, but several responsibilities are still too tightly grouped, especially around routing, retrieval, indexing, and verification.[cite:80][cite:82]

## Refactor goals

The refactor aims to achieve five concrete goals:[cite:80][cite:82]

- Separate HTTP transport from orchestration logic and domain behavior.[cite:80][cite:84]
- Split retrieval, indexing, and ranking into explicit modules rather than keeping them inside a broad `knowledge/` package.[cite:81][cite:83]
- Introduce a dedicated verification framework for grounded Islamic QA behavior, including exact quotation, source attribution, contradiction detection, and evidence sufficiency checks.[cite:24][cite:102]
- Make agents explicitly collection-aware so Burhan-Datasets collections map to clear retrieval and verification policies.[cite:3]
- Keep migration incremental, testable, and backward-compatible until the final cleanup phase.[cite:89][cite:99]

## Target v2 tree

```text
Burhan/
├── src/
│   ├── api/
│   │   ├── main.py
│   │   ├── lifespan.py
│   │   ├── dependencies.py
│   │   ├── middleware/
│   │   │   ├── error_handler.py
│   │   │   ├── request_context.py
│   │   │   ├── rate_limit.py
│   │   │   └── metrics.py
│   │   ├── routes/
│   │   │   ├── ask.py
│   │   │   ├── search.py
│   │   │   ├── classify.py
│   │   │   ├── tools.py
│   │   │   ├── quran.py
│   │   │   ├── admin.py
│   │   │   └── health.py
│   │   └── schemas/
│   │       ├── common.py
│   │       ├── ask.py
│   │       ├── search.py
│   │       ├── classify.py
│   │       ├── tools.py
│   │       └── traces.py
│   │
│   ├── application/
│   │   ├── container.py
│   │   ├── interfaces.py
│   │   ├── models.py
│   │   ├── services/
│   │   │   ├── ask_service.py
│   │   │   ├── search_service.py
│   │   │   ├── classify_service.py
│   │   │   ├── tool_service.py
│   │   │   └── trace_service.py
│   │   ├── use_cases/
│   │   │   ├── answer_query.py
│   │   │   ├── classify_query.py
│   │   │   ├── run_retrieval.py
│   │   │   ├── run_tool.py
│   │   │   └── build_trace.py
│   │   └── router/
│   │       ├── router_agent.py
│   │       ├── classifier_factory.py
│   │       ├── hybrid_classifier.py
│   │       └── risk_policy.py
│   │
│   ├── domain/
│   │   ├── intents.py
│   │   ├── collections.py
│   │   ├── decisions.py
│   │   ├── citations.py
│   │   ├── evidence.py
│   │   ├── tools.py
│   │   └── models.py
│   │
│   ├── agents/
│   │   ├── base.py
│   │   ├── base_rag_agent.py
│   │   ├── registry.py
│   │   ├── chatbot_agent.py
│   │   ├── fiqh_agent.py
│   │   ├── hadith_agent.py
│   │   ├── tafsir_agent.py
│   │   ├── aqeedah_agent.py
│   │   ├── seerah_agent.py
│   │   ├── history_agent.py
│   │   ├── language_agent.py
│   │   ├── tazkiyah_agent.py
│   │   ├── general_islamic_agent.py
│   │   └── usul_fiqh_agent.py
│   │
│   ├── retrieval/
│   │   ├── policies/
│   │   │   ├── collection_policy.py
│   │   │   ├── retrieval_policy.py
│   │   │   └── support_collection_policy.py
│   │   ├── planning/
│   │   │   ├── retrieval_plan.py
│   │   │   ├── fiqh_plan_builder.py
│   │   │   ├── quran_plan_builder.py
│   │   │   └── generic_plan_builder.py
│   │   ├── expanders/
│   │   │   ├── query_expander.py
│   │   │   ├── islamic_synonyms.py
│   │   │   └── era_expansion.py
│   │   ├── retrievers/
│   │   │   ├── dense_retriever.py
│   │   │   ├── sparse_retriever.py
│   │   │   ├── bm25_retriever.py
│   │   │   ├── hybrid_retriever.py
│   │   │   ├── hierarchical_retriever.py
│   │   │   └── multi_collection_retriever.py
│   │   ├── ranking/
│   │   │   ├── reranker.py
│   │   │   ├── score_fusion.py
│   │   │   ├── book_weighter.py
│   │   │   └── authority_scorer.py
│   │   └── aggregation/
│   │       ├── evidence_aggregator.py
│   │       ├── deduper.py
│   │       └── clusterer.py
│   │
│   ├── indexing/
│   │   ├── pipelines/
│   │   │   ├── ingest_Burhan.py
│   │   │   ├── build_collection_indexes.py
│   │   │   ├── build_catalog_indexes.py
│   │   │   └── sync_metadata.py
│   │   ├── embeddings/
│   │   │   ├── embedding_model.py
│   │   │   ├── bge_m3.py
│   │   │   ├── e5.py
│   │   │   └── embedding_cache.py
│   │   ├── vectorstores/
│   │   │   ├── base.py
│   │   │   ├── qdrant_store.py
│   │   │   ├── chroma_store.py
│   │   │   └── factory.py
│   │   ├── lexical/
│   │   │   ├── bm25_index.py
│   │   │   └── tantivy_index.py
│   │   └── metadata/
│   │       ├── title_loader.py
│   │       ├── author_catalog.py
│   │       ├── master_catalog.py
│   │       └── category_mapping.py
│   │
│   ├── verifiers/
│   │   ├── base.py
│   │   ├── pipeline.py
│   │   ├── policies.py
│   │   ├── quote_span.py
│   │   ├── exact_quote.py
│   │   ├── source_attribution.py
│   │   ├── evidence_sufficiency.py
│   │   ├── contradiction.py
│   │   ├── school_consistency.py
│   │   ├── temporal_consistency.py
│   │   ├── hadith_grade.py
│   │   └── groundedness_judge.py
│   │
│   ├── generation/
│   │   ├── llm_client.py
│   │   ├── prompts/
│   │   │   ├── fiqh.py
│   │   │   ├── hadith.py
│   │   │   ├── tafsir.py
│   │   │   ├── aqeedah.py
│   │   │   ├── clarify.py
│   │   │   └── abstain.py
│   │   ├── composers/
│   │   │   ├── answer_composer.py
│   │   │   ├── citation_composer.py
│   │   │   ├── clarification_composer.py
│   │   │   └── abstention_composer.py
│   │   └── policies/
│   │       ├── answer_policy.py
│   │       ├── risk_policy.py
│   │       └── formatting_policy.py
│   │
│   ├── quran/
│   │   ├── quran_router.py
│   │   ├── verse_retrieval.py
│   │   ├── tafsir_retrieval.py
│   │   ├── quotation_validator.py
│   │   └── nl2sql.py
│   │
│   ├── tools/
│   │   ├── base.py
│   │   ├── registry.py
│   │   ├── zakat_calculator.py
│   │   ├── inheritance_calculator.py
│   │   ├── prayer_times_tool.py
│   │   ├── hijri_calendar_tool.py
│   │   └── dua_retrieval_tool.py
│   │
│   ├── infrastructure/
│   │   ├── database.py
│   │   ├── redis.py
│   │   ├── telemetry.py
│   │   ├── storage.py
│   │   └── llm/
│   │       ├── openai_client.py
│   │       ├── groq_client.py
│   │       └── base.py
│   │
│   ├── config/
│   │   ├── settings.py
│   │   ├── constants.py
│   │   ├── logging_config.py
│   │   └── environment_validation.py
│   │
│   ├── core/
│   │   ├── exceptions.py
│   │   ├── result.py
│   │   └── types.py
│   │
│   └── utils/
│       ├── arabic.py
│       ├── language_detection.py
│       ├── era_classifier.py
│       ├── lazy_singleton.py
│       └── ids.py
│
├── tests/
│   ├── unit/
│   ├── integration/
│   ├── regression/
│   └── conftest.py
│
├── scripts/
├── docs/
├── docker/
├── .github/
├── Makefile
└── pyproject.toml
```

This target tree keeps the codebase modular and testable while matching common clean architecture guidance for FastAPI and modular backend systems.[cite:80][cite:82][cite:84]

## Layer rules

The architecture should follow strict one-directional dependency rules so that transport and infrastructure do not leak into domain behavior.[cite:80][cite:103]

- `api/` may depend on `application/` and API schemas only.[cite:80]
- `application/` may depend on `domain/`, `agents/`, `retrieval/`, `generation/`, `verifiers/`, `tools/`, and interfaces.[cite:80][cite:84]
- `agents/` may depend on domain, retrieval, generation, and verifier abstractions but should not import FastAPI concerns directly.[cite:80]
- `retrieval/` and `indexing/` should remain infrastructure-aware but HTTP-agnostic.[cite:81][cite:83]
- `core/` should stay tiny and contain only generic shared primitives, not business orchestration.[cite:84]

## Migration principles

The refactor should be incremental, not disruptive.[cite:89][cite:99]

- Move files first, then clean internal code later.[cite:89]
- Keep compatibility shims during the migration window.[cite:99]
- Do not rename public API behavior and internal structure in the same commit.[cite:82]
- Add regression tests before deleting old module paths.[cite:90]
- Prefer many small commits over one large rewrite.[cite:80]

## GitHub issues checklist

### Epic 1: Establish target architecture
- [ ] Create new top-level modules under `src/`: `retrieval/`, `indexing/`, `verifiers/`
- [ ] Create `application/services/` and `application/use_cases/`
- [ ] Create `docs/architecture.md`
- [ ] Create `docs/decisions/adr-002-structure-v2.md`
- [ ] Document layer rules: `api -> application -> agents/retrieval/generation`
- [ ] Document deprecation policy for legacy module paths

### Epic 2: Extract retrieval from `knowledge/`
- [ ] Move `knowledge/hybrid_search.py` -> `retrieval/retrievers/hybrid_retriever.py`
- [ ] Move `knowledge/bm25_retriever.py` -> `retrieval/retrievers/bm25_retriever.py`
- [ ] Move `knowledge/hierarchical_retriever.py` -> `retrieval/retrievers/hierarchical_retriever.py`
- [ ] Move `knowledge/query_expander.py` -> `retrieval/expanders/query_expander.py`
- [ ] Move `knowledge/book_weighter.py` -> `retrieval/ranking/book_weighter.py`
- [ ] Move `knowledge/reranker.py` -> `retrieval/ranking/reranker.py`
- [ ] Add `retrieval/ranking/score_fusion.py`
- [ ] Add `retrieval/policies/collection_policy.py`
- [ ] Add compatibility shims in old `knowledge/*` files
- [ ] Add unit tests for moved retrieval modules

### Epic 3: Extract indexing from `knowledge/`
- [ ] Move `knowledge/embedding_model.py` -> `indexing/embeddings/embedding_model.py`
- [ ] Move `knowledge/embedding_cache.py` -> `indexing/embeddings/embedding_cache.py`
- [ ] Move `knowledge/vector_store.py` -> `indexing/vectorstores/qdrant_store.py`
- [ ] Move `knowledge/title_loader.py` -> `indexing/metadata/title_loader.py`
- [ ] Add `indexing/vectorstores/base.py`
- [ ] Add `indexing/vectorstores/chroma_store.py`
- [ ] Add `indexing/vectorstores/factory.py`
- [ ] Add `indexing/lexical/bm25_index.py`
- [ ] Add `indexing/pipelines/build_collection_indexes.py`
- [ ] Add `indexing/pipelines/build_catalog_indexes.py`
- [ ] Add smoke tests for indexing pipeline

### Epic 4: Introduce verification framework
- [ ] Create `verifiers/base.py`
- [ ] Create `verifiers/pipeline.py`
- [ ] Create `verifiers/policies.py`
- [ ] Move/adapt `quran/quotation_validator.py` -> `verifiers/exact_quote.py`
- [ ] Move/adapt `knowledge/hadith_grader.py` -> `verifiers/hadith_grade.py`
- [ ] Add `verifiers/source_attribution.py`
- [ ] Add `verifiers/quote_span.py`
- [ ] Add `verifiers/evidence_sufficiency.py`
- [ ] Add `verifiers/contradiction.py`
- [ ] Add `verifiers/school_consistency.py`
- [ ] Add `verifiers/temporal_consistency.py`
- [ ] Add verifier pipeline integration tests

### Epic 5: Consolidate routing and orchestration
- [ ] Make `application/router/router_agent.py` the single routing entrypoint
- [ ] Move classifier orchestration from scattered files into `application/router/`
- [ ] Deprecate/remove `core/router.py`
- [ ] Deprecate duplicate registry implementations
- [ ] Add `application/use_cases/answer_query.py`
- [ ] Add `application/use_cases/classify_query.py`
- [ ] Add `application/use_cases/run_retrieval.py`
- [ ] Add `application/use_cases/run_tool.py`
- [ ] Make API routes call use-cases only
- [ ] Add orchestration tests for routing decisions

### Epic 6: Make agents collection-aware
- [ ] Add explicit collection-to-agent mapping
- [ ] Create `agents/tafsir_agent.py`
- [ ] Create `agents/aqeedah_agent.py`
- [ ] Create `agents/history_agent.py`
- [ ] Create `agents/language_agent.py`
- [ ] Create `agents/tazkiyah_agent.py`
- [ ] Create `agents/usul_fiqh_agent.py`
- [ ] Update `agents/registry.py` to register all collection-aware agents
- [ ] Add regression tests for agent selection by query type

### Epic 7: Simplify API layer
- [ ] Keep API routes thin and transport-only
- [ ] Merge/normalize endpoints into: `/ask`, `/search`, `/classify`, `/tools/*`, `/health`
- [ ] Split schemas into `ask.py`, `search.py`, `classify.py`, `tools.py`, `traces.py`
- [ ] Remove business logic from route handlers
- [ ] Add structured error responses across API
- [ ] Add request tracing metadata to responses

### Epic 8: Add regression safety net
- [ ] Add `tests/regression/fiqh_cases.jsonl`
- [ ] Add `tests/regression/hadith_cases.jsonl`
- [ ] Add `tests/regression/quran_cases.jsonl`
- [ ] Assert selected agent for each golden case
- [ ] Assert selected collections for each golden case
- [ ] Assert verification outcome for each golden case
- [ ] Assert final mode: `answer | clarify | abstain`
- [ ] Add CI job for regression suite

### Epic 9: Remove deprecated code
- [ ] Remove compatibility shims after migration stabilizes
- [ ] Delete deprecated `knowledge/*` wrappers
- [ ] Delete deprecated `core/router.py`
- [ ] Delete duplicate registry files
- [ ] Update imports across codebase
- [ ] Final architecture cleanup pass

## Suggested issue labels

Use a fixed label system to make the migration board navigable and prioritizable.[cite:99]

- `refactor`
- `architecture`
- `retrieval`
- `indexing`
- `verification`
- `api`
- `agents`
- `tests`
- `docs`
- `breaking-change`
- `good-first-issue`
- `priority:P0`
- `priority:P1`
- `priority:P2`

## Migration table

| Current file | New file | Why | Priority |
|---|---|---|---|
| `src/knowledge/hybrid_search.py` | `src/retrieval/retrievers/hybrid_retriever.py` | Hybrid retrieval belongs in a dedicated retrieval layer, especially when using modular Qdrant-based hybrid search and reranking flows.[cite:81][cite:83] | P0 |
| `src/knowledge/bm25_retriever.py` | `src/retrieval/retrievers/bm25_retriever.py` | Lexical retrieval should live beside other retrievers, not inside a general knowledge package.[cite:81] | P0 |
| `src/knowledge/hierarchical_retriever.py` | `src/retrieval/retrievers/hierarchical_retriever.py` | Keeps all retriever strategies under a single namespace. | P1 |
| `src/knowledge/query_expander.py` | `src/retrieval/expanders/query_expander.py` | Query expansion is retrieval planning logic, not a generic knowledge concern. | P0 |
| `src/knowledge/reranker.py` | `src/retrieval/ranking/reranker.py` | Reranking is a separate ranking stage in modern hybrid retrieval systems.[cite:83] | P0 |
| `src/knowledge/book_weighter.py` | `src/retrieval/ranking/book_weighter.py` | Authority weighting is a ranking policy concern. | P1 |
| `src/knowledge/embedding_model.py` | `src/indexing/embeddings/embedding_model.py` | Embedding generation belongs to indexing/query encoding infrastructure. | P0 |
| `src/knowledge/embedding_cache.py` | `src/indexing/embeddings/embedding_cache.py` | Cache locality should follow the embedding subsystem. | P1 |
| `src/knowledge/vector_store.py` | `src/indexing/vectorstores/qdrant_store.py` | Vector-store adapters belong in explicit storage/indexing modules.[cite:106] | P0 |
| `src/knowledge/title_loader.py` | `src/indexing/metadata/title_loader.py` | Metadata loaders should live with other metadata/indexing concerns. | P1 |
| `src/knowledge/hadith_grader.py` | `src/verifiers/hadith_grade.py` | Hadith grading is a verification concern, not a retrieval concern. | P0 |
| `src/quran/quotation_validator.py` | `src/verifiers/exact_quote.py` with Quran adapter retained | Exact quotation validation should be part of a general verification framework, while Quran can keep a small adapter if needed.[cite:24] | P0 |
| `src/application/router.py` | `src/application/router/router_agent.py` | Routing should have one canonical entrypoint. | P0 |
| `src/application/classifier_factory.py` | `src/application/router/classifier_factory.py` | Keeps routing-related files grouped together. | P1 |
| `src/application/hybrid_classifier.py` | `src/application/router/hybrid_classifier.py` | Same reason: routing cohesion. | P1 |
| `src/api/routes/classification.py` | `src/api/routes/classify.py` + `application/use_cases/classify_query.py` | API route stays transport-only while orchestration moves to use-cases.[cite:82] | P0 |
| `src/api/routes/query.py` | `src/api/routes/ask.py` | Improves naming clarity for the main ask flow. | P1 |
| `src/api/routes/rag.py` | `src/api/routes/search.py` or partial merge into `ask.py` | Reduces ambiguity between ask, query, and retrieval debugging. | P1 |
| `src/core/router.py` | Remove after migration | Prevents duplicate routing responsibility. | P0 |
| `src/core/registry.py` | Remove or merge into `src/agents/registry.py` | One registry should exist for clarity and maintainability. | P0 |
| `src/core/citation.py` | `src/domain/citations.py` or `src/generation/composers/citation_composer.py` | Citation code should be clearly domain-level or output-formatting-specific. | P1 |
| `src/agents/registry.py` | Keep and extend | This is the natural home for agent registration. | P0 |
| `src/infrastructure/llm_client.py` | `src/generation/llm_client.py` or `src/infrastructure/llm/openai_client.py` | Place depends on whether the file is an orchestration client or a raw provider adapter. | P1 |
| `src/tools/*.py` | Keep, add `src/tools/registry.py` | The tools layer is already well placed; it only needs a registry and consistent interfaces. | P1 |
| `src/domain/intents.py` | Keep | Clear domain primitive; no urgent change needed. | P2 |
| `src/domain/models.py` | Keep for now | Can be split later after higher-priority cleanup. | P2 |
| `src/utils/language_detection.py` | Keep | Utility placement is acceptable for now. | P2 |
| `src/utils/era_classifier.py` | Keep or later move to retrieval expansion | This depends on usage patterns and can wait until later cleanup. | P2 |

## Recommended commit order

The following order minimizes breakage and preserves deployability during the migration.[cite:80][cite:89]

1. Create the new folders and architecture docs.[cite:80]
2. Move retrieval files with compatibility shims.[cite:81]
3. Move indexing files and storage adapters.[cite:106]
4. Introduce the verifier pipeline and adapt existing Quran/Hadith validators into it.[cite:24][cite:102]
5. Consolidate routing into `application/router/` and move logic into use-cases.[cite:80][cite:82]
6. Add collection-aware agent registration and regression tests.[cite:3][cite:90]
7. Delete deprecated paths only after test stability is confirmed.[cite:89][cite:99]

## Safety rules during migration

These rules reduce the chance of breaking production behavior during the refactor.[cite:89][cite:99]

- Never move and rewrite behavior in the same commit.[cite:89]
- Leave compatibility wrappers for one migration phase before deleting them.[cite:99]
- Run unit tests and smoke tests after every P0 migration batch.[cite:90]
- Add golden regression cases for fiqh, hadith, and Quran flows before deleting old code paths.[cite:90]
- Keep external API behavior stable until the internal migration settles.[cite:82]

## Success criteria

The refactor is successful when the codebase achieves the following state:[cite:80][cite:81][cite:90]

- Routing responsibility exists in one clear place.
- Retrieval, indexing, ranking, and verification are independent and testable.
- Agents are explicitly linked to Burhan collections and collection policies.[cite:3]
- Exact quotation and evidence validation are reusable across Quran, hadith, and other grounded flows.[cite:24][cite:102]
- Legacy wrappers can be safely removed without breaking tests.
- New contributors can understand module boundaries without guessing.
