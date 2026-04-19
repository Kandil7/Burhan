# Athar v2 Migration Pack

## 1) PR Review Checklist for `refactor/athar-v2-architecture`

### Architecture correctness
- [ ] `CollectionAgent` is the default path for new RAG agents, not `BaseRAGAgent`.
- [ ] Legacy agents are clearly isolated and marked transitional/deprecated.
- [ ] `retrieval/` is the canonical retrieval layer; old `knowledge/` logic is either migrated or explicitly wrapped.
- [ ] `verification/` is a first-class layer with schemas, policies, checks, and suite composition.
- [ ] `application/routing/` owns routing/planning logic; API routes do not contain business logic.
- [ ] `generation/` consumes verified evidence only.
- [ ] `config/` files are declarative and loaded through runtime code, not duplicated in Python constants.

### Boundaries and coupling
- [ ] API layer is thin: validate request -> call use case -> return response.
- [ ] Agents do not directly know FastAPI request/response objects.
- [ ] Retrieval layer does not depend on API layer.
- [ ] Verification layer does not depend on FastAPI or route handlers.
- [ ] Prompts are loaded from files, not hardcoded in multiple places.
- [ ] Qdrant client creation is centralized, not duplicated across modules.

### Retrieval quality
- [ ] Hybrid retrieval exists for fiqh/hadith paths.
- [ ] Metadata filters are domain-specific and config-backed.
- [ ] Reranking happens after initial retrieval and before verification.
- [ ] Payload mapping into a unified evidence schema is implemented.
- [ ] Fallback policy is explicit when retrieval recall is weak.

### Verification quality
- [ ] Quote validation exists for exact religious text usage.
- [ ] Source attribution is normalized.
- [ ] Evidence sufficiency is checked before generation.
- [ ] Contradiction detection exists where khilaf matters.
- [ ] Hadith grade checks are enforced on hadith paths.
- [ ] Abstention path is explicit and testable.

### Routing and orchestration
- [ ] Intent classifier output is represented by typed models.
- [ ] Router supports at least single-domain + multi-domain path distinction.
- [ ] Fallbacks are not hidden inside unrelated modules.
- [ ] Sequential/parallel/hierarchical orchestration lives in dedicated modules.

### Naming and consistency
- [ ] One canonical term is used: `verification/` not mixed with `verifiers/`.
- [ ] One canonical runtime config package is used; root `config/` is file config only.
- [ ] Agent file naming is consistent (`fiqh.py`, `hadith.py`, etc. or another unified pattern).
- [ ] Legacy files are visibly grouped under `legacy/`.

### Tests and safety
- [ ] Unit tests cover retrieval, verification, routing, and generation modules.
- [ ] Integration tests cover `/query` or `/router/answer` end-to-end.
- [ ] At least one abstention case is tested.
- [ ] At least one khilaf case is tested.
- [ ] At least one hadith-grade restriction case is tested.
- [ ] Migration does not break existing API contracts without documentation.

### Documentation
- [ ] `ARCHITECTURE.md` matches the actual code layout.
- [ ] `REFACTOR_PLAN.md` reflects current migration status.
- [ ] A migration note explains what moved from legacy to v2.
- [ ] New contributors can identify the canonical execution path in under 5 minutes.

---

## 2) Migration Map: current tree -> Athar v2

### API
- `src/api/main.py` -> keep in place
- `src/api/lifespan.py` -> keep in place
- `src/api/routes/query.py` -> keep, but move business logic into `src/application/use_cases/answer_query.py`
- `src/api/routes/classification.py` -> keep, backed by `src/application/use_cases/classify_intent.py`
- `src/api/routes/quran.py` -> keep in place
- `src/api/routes/rag.py` -> merge responsibilities into `query.py` or deprecate after v2 routing stabilizes
- `src/api/routes/tools.py` -> keep in place
- `src/api/routes/health.py` -> keep in place
- `src/api/middleware/error_handler.py` -> keep in place
- `src/api/middleware/security.py` -> keep in place
- `src/api/schemas/request.py` -> keep in place
- `src/api/schemas/response.py` -> keep in place
- add `src/api/middleware/request_id.py`
- add `src/api/middleware/logging_middleware.py`
- add `src/api/schemas/trace.py`

### Config
- `src/config/__init__.py` -> move to `src/config_runtime/__init__.py`
- `src/config/loader.py` -> keep as runtime loader but rename location to `src/config_runtime/loader.py`
- `src/config/settings.py` -> move to `src/config_runtime/settings.py`
- `src/config/constants.py` -> move to `src/config_runtime/constants.py`
- `src/config/logging_config.py` -> move to `src/config_runtime/logging_config.py`
- `src/config/environment_validation.py` -> move to `src/config_runtime/environment_validation.py`
- root `config/agents/*.yaml` -> keep in place as declarative file config
- add root `config/retrieval/*.yaml`
- add root `config/verification/*.yaml`

### Retrieval / Knowledge
- `src/knowledge/embedding_model.py` -> move to `src/indexing/embeddings/embedding_model.py`
- `src/knowledge/vector_store.py` -> split into `src/infrastructure/qdrant/client.py` and `src/infrastructure/qdrant/collections.py`
- `src/knowledge/hybrid_search.py` -> move to `src/retrieval/retrievers/hybrid.py`
- `src/knowledge/embedding_cache.py` -> move to `src/infrastructure/redis.py` or `src/retrieval/caching/embedding_cache.py`
- `src/knowledge/bm25_retriever.py` -> move to `src/retrieval/retrievers/sparse.py`
- `src/knowledge/query_expander.py` -> move to `src/retrieval/expanders/base.py` + domain expanders
- `src/knowledge/reranker.py` -> move to `src/retrieval/ranking/reranker.py`
- `src/knowledge/hierarchical_retriever.py` -> move to `src/retrieval/retrievers/hierarchical.py`
- `src/knowledge/title_loader.py` -> move to `src/retrieval/mapping/title_lookup.py` or `src/indexing/metadata/title_loader.py`
- `src/knowledge/hadith_grader.py` -> move to `src/verification/checks/hadith_grade.py`
- `src/knowledge/book_weighter.py` -> move to `src/retrieval/ranking/scorers.py`
- `src/retrieval/strategies.py` -> keep and make canonical
- `src/retrieval/retrievers/` -> keep and fill with migrated code
- `src/retrieval/ranking/` -> keep and fill with migrated code
- `src/retrieval/policies/` -> keep
- `src/retrieval/expanders/` -> keep and absorb `knowledge/query_expander.py`
- `src/retrieval/aggregation/` -> keep
- `src/retrieval/planning/` -> keep
- add `src/retrieval/schemas.py`
- add `src/retrieval/filters/builder.py`
- add `src/retrieval/filters/presets.py`
- add `src/retrieval/fusion/rrf.py`
- add `src/retrieval/mapping/payload_mapper.py`
- add `src/retrieval/mapping/citation_mapper.py`

### Verification
- `src/verifiers/base.py` -> rename/move to `src/verification/base.py`
- `src/verifiers/suite_builder.py` -> move to `src/verification/suite_builder.py`
- `src/verifiers/fiqh_checks.py` -> move to `src/verification/checks/fiqh_checks.py`
- `src/verifiers/exact_quote.py` -> move to `src/verification/checks/exact_quote.py`
- `src/verifiers/hadith_grade.py` -> move to `src/verification/checks/hadith_grade.py`
- `src/verifiers/source_attribution.py` -> move to `src/verification/checks/source_attribution.py`
- `src/verifiers/contradiction.py` -> move to `src/verification/checks/contradiction.py`
- `src/verifiers/evidence_sufficiency.py` -> move to `src/verification/checks/evidence_sufficiency.py`
- `src/verifiers/policies.py` -> move to `src/verification/policies.py`
- add `src/verification/schemas.py`
- add `src/verification/trace.py`

### Agents
- `src/agents/base.py` -> split: core typed models to `src/domain/`, abstract interfaces to `src/agents/collection/base.py` if needed
- `src/agents/base_rag_agent.py` -> move to `src/agents/legacy/base_rag_agent.py`
- `src/agents/chatbot_agent.py` -> move to `src/agents/chatbot/chatbot_agent.py`
- `src/agents/fiqh_agent.py` -> move to `src/agents/legacy/fiqh_agent.py`
- `src/agents/hadith_agent.py` -> move to `src/agents/legacy/hadith_agent.py`
- `src/agents/seerah_agent.py` -> move to `src/agents/legacy/seerah_agent.py`
- `src/agents/general_islamic_agent.py` -> move to `src/agents/legacy/general_islamic_agent.py`
- `src/agents/collection_agent.py` -> move to `src/agents/collection/base.py`
- `src/agents/fiqh_collection_agent.py` -> move/rename to `src/agents/collection/fiqh.py`
- `src/agents/hadith_collection_agent.py` -> move/rename to `src/agents/collection/hadith.py`
- `src/agents/tafsir_collection_agent.py` -> move/rename to `src/agents/collection/tafsir.py`
- `src/agents/aqeedah_collection_agent.py` -> move/rename to `src/agents/collection/aqeedah.py`
- `src/agents/seerah_collection_agent.py` -> move/rename to `src/agents/collection/seerah.py`
- `src/agents/usul_fiqh_collection_agent.py` -> move/rename to `src/agents/collection/usul_fiqh.py`
- `src/agents/history_collection_agent.py` -> move/rename to `src/agents/collection/history.py`
- `src/agents/language_collection_agent.py` -> move/rename to `src/agents/collection/language.py`
- add `src/agents/collection/tazkiyah.py`
- add `src/agents/collection/general.py`
- `src/agents/registry.py` -> keep in `src/agents/registry.py` but make it v2-aware

### Application / Routing
- `src/application/router/router_agent.py` -> split responsibilities across `intent_router.py`, `planner.py`, `executor.py`
- `src/application/router/orchestration.py` -> move to `src/application/orchestration/` or split by pattern
- `src/application/router/multi_agent.py` -> merge into planner/executor if overlapping
- `src/application/router/config_router.py` -> rename to `src/application/routing/keyword_router.py` or fold into `intent_router.py`
- `src/application/container.py` -> keep in place
- `src/application/interfaces.py` -> keep in place
- `src/application/classifier_factory.py` -> keep or move to `src/application/routing/classifier_factory.py`
- `src/application/hybrid_classifier.py` -> move to `src/application/routing/hybrid_classifier.py`
- `src/application/models.py` -> move to `src/application/routing/models.py`
- add `src/application/use_cases/answer_query.py`
- add `src/application/use_cases/classify_intent.py`

### Generation
- `src/generation/prompts/` -> keep in place or make it loader-only if root `prompts/` is canonical
- `src/generation/composers/` -> keep in place
- `src/generation/policies/` -> keep in place
- add `src/generation/schemas.py`
- add `src/generation/prompt_loader.py`

### Quran
- `src/quran/verse_retrieval.py` -> keep in place
- `src/quran/nl2sql.py` -> keep in place
- `src/quran/quotation_validator.py` -> keep in place or integrate with `verification/checks/exact_quote.py` via adapter
- `src/quran/tafsir_retrieval.py` -> keep in place
- `src/quran/quran_router.py` -> keep in place, but integrate with application routing contracts

### Tools
- `src/tools/base.py` -> keep in place
- `src/tools/zak_at_calculator.py` -> rename to `src/tools/zakat_calculator.py`
- `src/tools/inheritance_calculator.py` -> keep in place
- `src/tools/prayer_times_tool.py` -> keep in place
- `src/tools/hijri_calendar_tool.py` -> keep in place
- `src/tools/dua_retrieval_tool.py` -> keep in place

### Infrastructure
- `src/infrastructure/llm_client.py` -> move to `src/infrastructure/llm/client.py`
- `src/infrastructure/database.py` -> keep in place
- `src/infrastructure/redis.py` -> keep in place
- `src/infrastructure/llm/` -> keep and consolidate with `llm_client.py`
- add `src/infrastructure/qdrant/`

### Domain / Core / Utils
- `src/domain/intents.py` -> keep in place
- `src/domain/models.py` -> expand and make canonical for cross-layer data contracts
- `src/core/exceptions.py` -> move to `src/shared/exceptions.py`
- `src/core/router.py` -> migrate to `src/application/routing/`
- `src/core/registry.py` -> merge with `src/agents/registry.py` or `src/application/container.py`
- `src/core/citation.py` -> move to `src/domain/citations.py`
- `src/utils/language_detection.py` -> move to `src/shared/language_detection.py`
- `src/utils/era_classifier.py` -> move to `src/shared/era_classifier.py`
- `src/utils/lazy_singleton.py` -> move to `src/shared/lazy_singleton.py`

### Evaluation / Tests / Docs
- `src/evaluation/golden_set_schema.py` -> keep in place
- `src/evaluation/metrics.py` -> keep in place
- `src/evaluation/cli.py` -> keep in place
- add `src/evaluation/harness.py`
- `tests/test_comprehensive.py` -> split into `tests/unit/` and `tests/integration/`
- `tests/test_config_backed_agents.py` -> keep and expand
- `docs/` -> promote canonical docs: `ARCHITECTURE.md`, `REFACTOR_PLAN.md`, `RETRIEVAL.md`, `VERIFICATION.md`, `ROUTING.md`, `CONTRIBUTING.md`

---

## 3) Branch-by-Branch Execution Plan (safe migration)

### Branch 1: `refactor/isolate-legacy-agents`
Goal: isolate old path without changing behavior.
- Create `src/agents/legacy/`
- Move `base_rag_agent.py`, `fiqh_agent.py`, `hadith_agent.py`, `seerah_agent.py`, `general_islamic_agent.py`
- Add compatibility imports/shims if needed
- Update imports
- Run full tests

### Branch 2: `refactor/collection-agents-layout`
Goal: make v2 agent path explicit.
- Create `src/agents/collection/`
- Move `collection_agent.py` -> `collection/base.py`
- Rename collection agent files to short domain names
- Update registry to support both legacy and collection agents
- Add deprecation comments to legacy agent usage

### Branch 3: `refactor/runtime-config-split`
Goal: remove config ambiguity.
- Move runtime code from `src/config/` -> `src/config_runtime/`
- Keep root `config/` as YAML-only
- Update loaders/imports
- Add tests for YAML loading and runtime settings

### Branch 4: `refactor/retrieval-canonical-layer`
Goal: make `retrieval/` the official retrieval stack.
- Add missing retrieval modules: schemas, filters, fusion, mapping
- Move `knowledge/hybrid_search.py` -> `retrieval/retrievers/hybrid.py`
- Move `knowledge/bm25_retriever.py` -> `retrieval/retrievers/sparse.py`
- Move `knowledge/reranker.py` -> `retrieval/ranking/reranker.py`
- Move `knowledge/query_expander.py` -> `retrieval/expanders/`
- Keep temporary wrappers in `knowledge/`
- Add unit tests for retrieval pipeline

### Branch 5: `refactor/qdrant-infrastructure-split`
Goal: separate Qdrant infra from retrieval logic.
- Split `knowledge/vector_store.py`
- Add `src/infrastructure/qdrant/client.py`
- Add `src/infrastructure/qdrant/collections.py`
- Add `src/infrastructure/qdrant/payload_indexes.py`
- Make retrieval layer consume infra client via interfaces

### Branch 6: `refactor/verification-first-class-layer`
Goal: normalize verifiers into a strong layer.
- Rename/move `verifiers/` -> `verification/`
- Add schemas.py and trace.py
- Move checks under `verification/checks/`
- Build suite builder from config
- Add abstention + evidence sufficiency tests

### Branch 7: `refactor/application-routing-split`
Goal: clean routing/planning/execution boundaries.
- Split current router modules into `intent_router.py`, `planner.py`, `executor.py`, `abstention.py`
- Move hybrid classifier next to routing if needed
- Make API routes call application use cases only
- Add routing unit tests

### Branch 8: `refactor/generation-contracts`
Goal: enforce verified-evidence-only generation.
- Add generation schemas
- Add answer composer contracts
- Add prompt loader
- Ensure generation consumes verification output only

### Branch 9: `refactor/tests-and-observability`
Goal: make migration safe and measurable.
- Split tests into unit/integration/evaluation
- Add request_id middleware
- Add structured trace schema
- Log retrieval/rerank/verification timings

### Branch 10: `cleanup/deprecate-knowledge-and-legacy`
Goal: finalize v2 and reduce old surface area.
- Mark `knowledge/` wrappers deprecated
- Remove dead imports
- Remove unused legacy code after parity is confirmed
- Update docs to declare v2 canonical path

---

## 4) Recommended execution order (short)
1. Isolate legacy agents.
2. Make collection agent path explicit.
3. Split runtime config from file config.
4. Canonicalize retrieval.
5. Split Qdrant infra.
6. Canonicalize verification.
7. Split routing/planning/execution.
8. Lock generation contracts.
9. Improve tests and observability.
10. Deprecate old paths.
