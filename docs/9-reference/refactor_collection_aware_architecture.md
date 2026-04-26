الهيكل ده **قوي جدًا بالفعل**، وفيه معظم اللبنات الصحيحة لبناء Burhan كنظام Islamic RAG إنتاجي: فصل طبقات، agents، hybrid search، tools، quran module، وتهيئة لـ DI والاختبارات. [dev](https://dev.to/markoulis/layered-architecture-dependency-injection-a-recipe-for-clean-and-testable-fastapi-code-3ioo)
لكن لو هدفك فعلًا “أفضل Islamic RAG”، فالمطلوب الآن ليس إعادة بناء كل شيء من الصفر، بل **تقليل التداخل، إغلاق الفجوات المعمارية، وتحويل الهيكل من good backend إلى trustworthy agentic Islamic QA system**. [qdrant](https://qdrant.tech/articles/hybrid-search/)

## تقييمي السريع

بصراحة: الهيكل الحالي أقرب إلى **8/10 backend architecture** لنظام RAG إسلامي. [blog.stackademic](https://blog.stackademic.com/building-a-production-grade-fastapi-backend-with-clean-layered-architecture-7e3ad6deb0bb)
نقاط القوة الواضحة:

- فصل جيد بين `api`, `application`, `agents`, `knowledge`, `tools`, `quran`, `infrastructure`, `config`. [zyneto](https://zyneto.com/blog/best-practices-in-fastapi-architecture)
- وجود `hybrid_search`, `bm25_retriever`, `query_expander`, `reranker`, و`book_weighter` يدل أنك تفكر بطريقة retrieval engineering صحيحة، خصوصًا أن hybrid + reranking هو الاتجاه الموصى به مع Qdrant اليوم. [qdrant](https://qdrant.tech/documentation/tutorials-search-engineering/reranking-hybrid-search/)
- إدخال `quotation_validator` وdeterministic tools مثل الزكاة والمواريث ممتاز جدًا، لأن الأنظمة الإسلامية المتقدمة تعتمد على exact validation والأدوات الحتمية في المسائل الحساسة. [arxiv](https://arxiv.org/abs/2603.08501)
- وجود `container.py`, `interfaces.py`, `registry.py` يوحي أنك تتحرك نحو dependency injection ونظام extensible، وده يتماشى مع أفضل ممارسات FastAPI النظيفة. [dev](https://dev.to/markoulis/layered-architecture-dependency-injection-a-recipe-for-clean-and-testable-fastapi-code-3ioo)

## أقوى ما في الهيكل

### التطبيق متعدد الطبقات

وجود `application/` منفصل عن `api/` ممتاز لأنه يمنع routes من التحول إلى business logic dump، وده من أهم مبادئ FastAPI القابلة للاختبار والصيانة. [blog.stackademic](https://blog.stackademic.com/building-a-production-grade-fastapi-backend-with-clean-layered-architecture-7e3ad6deb0bb)
هذا القرار جيد خصوصًا لو كنت ستضيف أكثر من transport لاحقًا مثل CLI workers أو background tasks أو حتى gRPC. [dev](https://dev.to/markoulis/layered-architecture-dependency-injection-a-recipe-for-clean-and-testable-fastapi-code-3ioo)

### محور retrieval واضح

الملفات داخل `knowledge/` تبين أن لديك فهمًا جيدًا لتحديات Arabic Islamic retrieval: embedding model، BM25، query expansion، reranking، caching، وbook weighting. [qdrant](https://qdrant.tech/articles/hybrid-search/)
هذا مهم لأن جودة Islamic RAG غالبًا تتحسن أكثر من retrieval + verification قبل أي تغيير في الـ LLM نفسه. [arxiv](https://arxiv.org/abs/2603.08501)

### وجود modules متخصصة للقرآن والأدوات

فصل `quran/` عن البقية قرار صحيح لأن القرآن يحتاج exact quotation validation أكثر من أي corpus آخر، وFanar-Sadiq يبرز هذه النقطة تحديدًا في grounded Islamic QA. [arxiv](https://arxiv.org/abs/2603.08501)
وكذلك فصل calculators ضمن `tools/` يجعل الأسئلة الحاسمة مثل الزكاة والمواريث لا تقع بالكامل تحت free-form generation. [arxiv](https://arxiv.org/abs/2603.08501)

## أين المشكلة الآن

### التداخل بين الطبقات

رغم أن الفصل موجود، ما زال في الهيكل بعض التداخل الدلالي بين:
- `application/router.py`
- `core/router.py`
- `api/routes/classification.py`
- `agents/registry.py`
- `core/registry.py` [query]

هذا يوحي بإمكانية وجود **ازدواجية مسؤوليات**: من الذي يقرر الـ routing؟ من يملك registry؟ من ينسق lifecycle؟  
لو استمر هذا، ستجد بعد فترة أن إضافة agent جديد تحتاج تعديلًا في 4–5 أماكن بدل مكان واحد. [zyneto](https://zyneto.com/blog/best-practices-in-fastapi-architecture)

### `knowledge/` أصبح “kitchen sink”

المجلد `knowledge/` حاليًا يضم embedding, vector store, hybrid search, cache, BM25, query expansion, reranking, hierarchical retriever, hadith grader, book weighter.[query]  
هذا عملي مؤقتًا، لكنه مع الوقت سيصبح طبقة ضخمة جدًا تمزج:
- indexing
- retrieval
- ranking
- domain heuristics
- caching  
في مكان واحد، بينما الأفضل فصلها إلى: `indexing/`, `retrieval/`, `ranking/`, `enrichment/` أو ما شابه. [blog.stackademic](https://blog.stackademic.com/building-a-production-grade-fastapi-backend-with-clean-layered-architecture-7e3ad6deb0bb)

### agents أقل من collections

Burhan-Datasets عنده collections أكثر تنوعًا من عدد الـ agents الحاليين؛ عندك حاليًا `fiqh`, `hadith`, `seerah`, `general_islamic`, وربما chatbot، لكن ما زال ينقصك تمثيل صريح لـ:
- `aqeedah`
- `tafsir`
- `usul_fiqh`
- `spirituality`
- `history`
- `language` [query] [huggingface](https://huggingface.co/datasets/Kandil7/Burhan-Datasets)

هذا ليس خطأ الآن لو أنت تعمل بمرحلة Fiqh-first، لكنه يجب أن يكون **قرارًا معلنًا** في المعمارية، لا فجوة غير مقصودة. [huggingface](https://huggingface.co/datasets/Kandil7/Burhan-Datasets)

## أهم التحسينات المقترحة

### 1) اجعل `application/` هو orchestration layer الوحيد

أنا أنصح بالقاعدة التالية:

- `api/` = HTTP فقط
- `application/` = use-cases + orchestration
- `agents/` = domain behavior
- `knowledge/` أو `retrieval/` = retrieval infra
- `infrastructure/` = external services
- `core/` = shared primitives فقط

بالتالي:
- انقل أي `router.py` حقيقي إلى `application/router.py`
- واجعل `core/router.py` إن وُجد مجرد abstract primitives أو احذفه
- اجعل `registry` واحد فقط، غالبًا في `agents/registry.py` أو `application/container.py`, لا الاثنين معًا. [zyneto](https://zyneto.com/blog/best-practices-in-fastapi-architecture)

### 2) افصل `knowledge/` إلى وحدات أدق

اقترح هذا التحويل:

```text
knowledge/  ->  retrieval/ + indexing/ + ranking/
```

مثال:

```text
src/
├── retrieval/
│   ├── hybrid_search.py
│   ├── bm25_retriever.py
│   ├── hierarchical_retriever.py
│   ├── query_expander.py
│   └── book_weighter.py
├── ranking/
│   ├── reranker.py
│   └── score_fusion.py
├── indexing/
│   ├── embedding_model.py
│   ├── vector_store.py
│   ├── embedding_cache.py
│   └── title_loader.py
```

هذا يسهّل الفهم، ويجعل اختباراتك أكثر وضوحًا، ويمنع المجلد من التحول إلى “misc bag”. [blog.stackademic](https://blog.stackademic.com/building-a-production-grade-fastapi-backend-with-clean-layered-architecture-7e3ad6deb0bb)

### 3) أضف طبقة `verifiers/` مستقلة

هذه عندي أهم إضافة ناقصة في الهيكل الحالي.  
أنت عندك `quotation_validator.py` داخل `quran/` و`hadith_grader.py` داخل `knowledge/`، لكن التحقق يجب أن يصبح **framework مستقل** لا util files متناثرة. [arxiv](https://arxiv.org/abs/2603.08501)

أقترح:

```text
src/
├── verifiers/
│   ├── base.py
│   ├── pipeline.py
│   ├── source_attribution.py
│   ├── quote_span.py
│   ├── contradiction.py
│   ├── evidence_sufficiency.py
│   ├── school_consistency.py
│   ├── temporal_consistency.py
│   └── exact_quote.py
```

هذا لأن Islamic QA عالي الحساسية يحتاج verification pipeline حسب نوع السؤال، لا مجرد validator خاص بالقرآن فقط. [arxiv](https://arxiv.org/abs/2603.08501)

### 4) اربط agents بالcollections صراحة

الهيكل الحالي ممتاز ككود، لكن README والمعمارية يجب أن يوضحا هذا mapping بوضوح:

- `FiqhAgent` → `fiqh_passages` + `hadith_passages` + `usul_fiqh`
- `HadithAgent` → `hadith_passages`
- `Quran/TafsirAgent` → `quran_tafsir` + verse retrieval
- `AqeedahAgent` → `aqeedah_passages`
- `SeerahAgent` → `seerah_passages`
- `GeneralIslamicAgent` → `general_islamic`
- `HistoryAgent` → `islamic_history_passages`
- `LanguageAgent` → `arabic_language_passages`
- `TazkiyahAgent` → `spirituality_passages` [huggingface](https://huggingface.co/datasets/Kandil7/Burhan-Datasets)

من غير هذا الربط، سيصبح النظام “agent-named” فقط لكن ليس collection-aware فعلًا. [huggingface](https://huggingface.co/datasets/Kandil7/Burhan-Datasets)

## تعديل هيكلي مقترح على مشروعك الحالي

أنا لو سأعدّل شجرتك الحالية بدون تكسير كبير، سأحوّلها إلى هذا:

```text
Burhan/
├── src/
│   ├── api/
│   ├── application/
│   │   ├── container.py
│   │   ├── interfaces.py
│   │   ├── use_cases/
│   │   │   ├── answer_query.py
│   │   │   ├── classify_query.py
│   │   │   ├── search_collection.py
│   │   │   └── run_tool.py
│   │   ├── router.py
│   │   └── models.py
│   │
│   ├── agents/
│   ├── retrieval/
│   │   ├── hybrid_search.py
│   │   ├── bm25_retriever.py
│   │   ├── hierarchical_retriever.py
│   │   ├── query_expander.py
│   │   ├── book_weighter.py
│   │   └── collection_policies.py
│   │
│   ├── ranking/
│   │   ├── reranker.py
│   │   └── score_fusion.py
│   │
│   ├── indexing/
│   │   ├── embedding_model.py
│   │   ├── vector_store.py
│   │   ├── embedding_cache.py
│   │   └── title_loader.py
│   │
│   ├── verifiers/
│   │   ├── base.py
│   │   ├── pipeline.py
│   │   ├── quotation.py
│   │   ├── attribution.py
│   │   ├── contradiction.py
│   │   ├── sufficiency.py
│   │   └── policy.py
│   │
│   ├── quran/
│   ├── tools/
│   ├── infrastructure/
│   ├── config/
│   ├── domain/
│   ├── core/
│   └── utils/
```

هذا التعديل يحافظ على 90% من شغلك الحالي، لكنه يرفع الوضوح كثيرًا.[query]

## أي أجزاء أعتبرها Phase 1 وPhase 2

### Phase 1
- `FiqhAgent`
- `HadithAgent`
- `GeneralIslamicAgent`
- `hybrid_search`
- `bm25_retriever`
- `reranker`
- `query_expander`
- `vector_store`
- `quotation/source verification`
- `zakat` و`inheritance` tools

### Phase 2
- `AqeedahAgent`
- `TafsirAgent`
- `UsulFiqhAgent`
- `HistoryAgent`
- `LanguageAgent`
- `TemporalConsistencyVerifier`
- `SchoolConsistencyVerifier`
- NL2SQL للقرآن لو عندك structured Quran DB
- prayer/hijri utilities

بهذا تمنع نفسك من التوسع المبكر وتحافظ على سرعة التنفيذ. [huggingface](https://huggingface.co/datasets/Kandil7/Burhan-Datasets)

## حكم نهائي على الهيكل

الهيكل الحالي **أقوى بكثير من MVP عادي**، وفيه أساس ممتاز لنظام Islamic RAG جاد.[query]  
لكي يصير architecture “ممتازة” فعلاً، ركّز على 4 تحسينات فقط:

- إزالة ازدواجية `router/registry`
- فصل retrieval/indexing/ranking
- إنشاء `verifiers/` مستقلة
- توثيق mapping واضح بين agents وBurhan collections. [dev](https://dev.to/markoulis/layered-architecture-dependency-injection-a-recipe-for-clean-and-testable-fastapi-code-3ioo)


## Refactored tree v2

هذه نسخة v2 مقترحة تحافظ على روح مشروعك الحالي، لكن تنظّف المسؤوليات وتجهّز Burhan للتوسع agentic بشكل أفضل.[query] [dev](https://dev.to/markoulis/layered-architecture-dependency-injection-a-recipe-for-clean-and-testable-fastapi-code-3ioo)

```text
Burhan/
├── src/
│   ├── api/                              # HTTP transport only
│   │   ├── main.py
│   │   ├── lifespan.py
│   │   ├── dependencies.py
│   │   ├── middleware/
│   │   │   ├── error_handler.py
│   │   │   ├── request_context.py
│   │   │   ├── rate_limit.py
│   │   │   └── metrics.py
│   │   ├── routes/
│   │   │   ├── ask.py                    # unified ask endpoint
│   │   │   ├── search.py                 # retrieval/debug search
│   │   │   ├── classify.py               # intent/domain classification
│   │   │   ├── tools.py                  # deterministic tools
│   │   │   ├── quran.py                  # exact Quran endpoints
│   │   │   ├── admin.py                  # internal admin ops
│   │   │   └── health.py
│   │   └── schemas/
│   │       ├── common.py
│   │       ├── ask.py
│   │       ├── search.py
│   │       ├── classify.py
│   │       ├── tools.py
│   │       └── traces.py
│   │
│   ├── application/                      # orchestration/use-cases
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
│   ├── domain/                           # pure domain definitions
│   │   ├── intents.py
│   │   ├── collections.py
│   │   ├── decisions.py
│   │   ├── citations.py
│   │   ├── evidence.py
│   │   ├── tools.py
│   │   └── models.py
│   │
│   ├── agents/                           # domain-specialized behavior
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
│   ├── retrieval/                        # query planning + retrieval
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
│   ├── indexing/                         # ingestion + index building
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
│   ├── verifiers/                        # explicit verification framework
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
│   ├── generation/                       # answer drafting/composition
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
│   ├── quran/                            # Quran-specialized logic
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
│   ├── infrastructure/                   # external adapters only
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
│   ├── core/                             # tiny shared primitives only
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
│   │   ├── agents/
│   │   ├── retrieval/
│   │   ├── verifiers/
│   │   ├── generation/
│   │   └── application/
│   ├── integration/
│   │   ├── api/
│   │   ├── qdrant/
│   │   └── pipelines/
│   ├── regression/
│   │   ├── fiqh_cases.jsonl
│   │   ├── hadith_cases.jsonl
│   │   └── quran_cases.jsonl
│   └── conftest.py
│
├── scripts/
│   ├── ingest_Burhan.py
│   ├── build_indexes.py
│   ├── backfill_metadata.py
│   ├── run_eval.py
│   └── smoke_test.py
│
├── docs/
│   ├── architecture.md
│   ├── collections.md
│   ├── routing.md
│   ├── retrieval.md
│   ├── verification.md
│   ├── tools.md
│   ├── deployment.md
│   └── decisions/
│       ├── adr-001-fiqh-first.md
│       ├── adr-002-verification-pipeline.md
│       └── adr-003-qdrant-over-chroma.md
│
├── docker/
├── .github/
├── Makefile
└── pyproject.toml
```

## لماذا هذه النسخة أنظف

- `api/` صار HTTP فقط، وهذا ينسجم مع فصل presentation عن service layer في FastAPI clean architecture. [blog.stackademic](https://blog.stackademic.com/building-a-production-grade-fastapi-backend-with-clean-layered-architecture-7e3ad6deb0bb)
- `application/` صار مكان الـ orchestration الفعلي، بما في ذلك use-cases وrouter agent، بدل تشتت منطق التدفق بين `api`, `core`, و`agents`. [dev](https://dev.to/markoulis/layered-architecture-dependency-injection-a-recipe-for-clean-and-testable-fastapi-code-3ioo)
- `retrieval/`, `indexing/`, و`verifiers/` انفصلت بوضوح، وهذا مهم لأن hybrid search وreranking والتحقق غالبًا تتطور بسرعات مختلفة وتحتاج اختبارات مستقلة. [qdrant](https://qdrant.tech/articles/hybrid-search/)
- `infrastructure/` صار adapters فقط، فلا تختلط clients الخارجية بمنطق التوليد أو التحقق. [dev](https://dev.to/markoulis/layered-architecture-dependency-injection-a-recipe-for-clean-and-testable-fastapi-code-3ioo)
- `core/` تقلص إلى primitives عامة فقط، وهذا يمنع تحوله إلى “misc” بمرور الوقت. [blog.stackademic](https://blog.stackademic.com/building-a-production-grade-fastapi-backend-with-clean-layered-architecture-7e3ad6deb0bb)

## خطة refactor بدون تكسير

الأفضل تنفيذ النقل على مراحل صغيرة مع compatibility shims مؤقتة، لأن إعادة هيكلة كبيرة دفعة واحدة سترفع المخاطر وتكسر الاستيرادات بسهولة. [dev](https://dev.to/markoulis/layered-architecture-dependency-injection-a-recipe-for-clean-and-testable-fastapi-code-3ioo)

## Phase 1: تثبيت الطبقات

### Commit 1
**chore: introduce target architecture folders**

- أنشئ المجلدات الجديدة الفارغة:
  - `retrieval/`
  - `indexing/`
  - `verifiers/`
  - `application/use_cases/`
  - `application/services/`
- لا تنقل أي كود بعد؛ فقط أنشئ البنية الجديدة. [dev](https://dev.to/markoulis/layered-architecture-dependency-injection-a-recipe-for-clean-and-testable-fastapi-code-3ioo)

### Commit 2
**docs: add architecture v2 ADR and migration map**

- أضف `docs/architecture.md`
- أضف `docs/decisions/adr-002-structure-v2.md`
- وثّق mapping من الملفات القديمة إلى الجديدة. [dev](https://dev.to/markoulis/layered-architecture-dependency-injection-a-recipe-for-clean-and-testable-fastapi-code-3ioo)

## Phase 2: فصل retrieval

### Commit 3
**refactor: move retrieval concerns out of knowledge package**

انقل بدون تغيير سلوكي:
- `knowledge/hybrid_search.py` → `retrieval/retrievers/hybrid_retriever.py`
- `knowledge/bm25_retriever.py` → `retrieval/retrievers/bm25_retriever.py`
- `knowledge/hierarchical_retriever.py` → `retrieval/retrievers/hierarchical_retriever.py`
- `knowledge/query_expander.py` → `retrieval/expanders/query_expander.py`
- `knowledge/book_weighter.py` → `retrieval/ranking/book_weighter.py`
- `knowledge/reranker.py` → `retrieval/ranking/reranker.py` [query]

واترك ملفات shim داخل `knowledge/` تستورد من المواقع الجديدة مؤقتًا حتى لا ينكسر المشروع.

### Commit 4
**refactor: extract indexing concerns from knowledge package**

انقل:
- `knowledge/embedding_model.py` → `indexing/embeddings/embedding_model.py`
- `knowledge/embedding_cache.py` → `indexing/embeddings/embedding_cache.py`
- `knowledge/vector_store.py` → `indexing/vectorstores/qdrant_store.py`
- `knowledge/title_loader.py` → `indexing/metadata/title_loader.py`

ثم أنشئ:
- `indexing/vectorstores/factory.py`
- `indexing/lexical/bm25_index.py`

## Phase 3: إنشاء verification framework

### Commit 5
**feat: introduce verifier pipeline abstraction**

أنشئ:
- `verifiers/base.py`
- `verifiers/pipeline.py`
- `verifiers/policies.py`

ثم حوّل:
- `quran/quotation_validator.py` → verifier أو adapter داخل `verifiers/exact_quote.py`
- `knowledge/hadith_grader.py` → `verifiers/hadith_grade.py` [query]

### Commit 6
**feat: add source attribution and evidence sufficiency verifiers**

- أضف `source_attribution.py`
- أضف `evidence_sufficiency.py`
- أضف `quote_span.py`
- اربطهم في pipeline واحدة قابلة للتركيب حسب نوع الـ agent. [ml-architects](https://ml-architects.ch/blog_posts/testing_qa_ai_eingineering.html)

## Phase 4: توحيد الـ orchestration

### Commit 7
**refactor: consolidate routing logic into application layer**

- اجعل `application/router/router_agent.py` هو مصدر الحقيقة الوحيد للـ routing.
- انقل أي منطق من:
  - `core/router.py`
  - `api/routes/classification.py`
  - `application/router.py` القديم  
  إلى `application/router/`.
- اترك wrappers قديمة مؤقتًا تستدعي المكان الجديد. [dev](https://dev.to/markoulis/layered-architecture-dependency-injection-a-recipe-for-clean-and-testable-fastapi-code-3ioo)

### Commit 8
**refactor: introduce use-case driven services**

- أنشئ:
  - `application/use_cases/answer_query.py`
  - `classify_query.py`
  - `run_retrieval.py`
  - `run_tool.py`
- اجعل routes في `api/` تستدعي use-cases فقط، وليس agents أو retrievers مباشرة. [blog.stackademic](https://blog.stackademic.com/building-a-production-grade-fastapi-backend-with-clean-layered-architecture-7e3ad6deb0bb)

## Phase 5: توضيح agents وربطها بالcollections

### Commit 9
**feat: add collection policy registry**

أنشئ ملف:
- `retrieval/policies/collection_policy.py`

وضع فيه mapping صريح:
- `fiqh_passages` ↔ `FiqhAgent`
- `hadith_passages` ↔ `HadithAgent`
- `quran_tafsir` ↔ `TafsirAgent`
- ... [huggingface](https://huggingface.co/datasets/Kandil7/Burhan-Datasets)

### Commit 10
**feat: add missing domain agents as stubs**

أنشئ stubs أولًا لـ:
- `tafsir_agent.py`
- `aqeedah_agent.py`
- `history_agent.py`
- `language_agent.py`
- `tazkiyah_agent.py`
- `usul_fiqh_agent.py` [huggingface](https://huggingface.co/datasets/Kandil7/Burhan-Datasets)

حتى لو كانت مجرد wrappers حول `BaseRAGAgent` في البداية، فهذا يجعل architecture collection-aware بشكل رسمي. [huggingface](https://huggingface.co/datasets/Kandil7/Burhan-Datasets)

## Phase 6: تنظيف الـ API

### Commit 11
**refactor: simplify api routes and schemas**

- دمج/تنظيف المسارات لتكون:
  - `POST /ask`
  - `POST /search`
  - `POST /classify`
  - `POST /tools/...`
  - `GET /health`
- أزل أي منطق business من الـ route handlers. [dev](https://dev.to/markoulis/layered-architecture-dependency-injection-a-recipe-for-clean-and-testable-fastapi-code-3ioo)

### Commit 12
**refactor: centralize request/response contracts**

- قسّم schemas إلى:
  - `ask.py`
  - `search.py`
  - `classify.py`
  - `tools.py`
  - `traces.py`
- اجعلها عقود I/O فقط، وليس models داخلية للنظام. [dev](https://dev.to/markoulis/layered-architecture-dependency-injection-a-recipe-for-clean-and-testable-fastapi-code-3ioo)

## Phase 7: اختبارات regression

### Commit 13
**test: add golden regression cases for fiqh and hadith**

- أضف `tests/regression/fiqh_cases.jsonl`
- أضف `tests/regression/hadith_cases.jsonl`
- أضف assertions على:
  - chosen agent
  - top collections
  - verification outcome
  - answer mode (`answer/clarify/abstain`) [ml-architects](https://ml-architects.ch/blog_posts/testing_qa_ai_eingineering.html)

### Commit 14
**test: add module-level tests after refactor**

- اختبارات لـ:
  - `retrieval/retrievers/*`
  - `verifiers/*`
  - `application/use_cases/*`
  - `agents/registry.py`

## Issues backlog جاهزة

### P0
- Create architecture v2 folders
- Extract retrieval from `knowledge/`
- Extract indexing from `knowledge/`
- Create verifier pipeline
- Consolidate router into `application/`
- Add collection policy registry

### P1
- Add missing agent stubs
- Simplify API routes
- Centralize schemas
- Add regression tests
- Add migration docs

### P2
- Remove compatibility shims
- Delete deprecated `core/router.py`
- Delete deprecated `knowledge/*` wrappers
- Add groundedness judge and retry policies. [kore](https://www.kore.ai/blog/what-is-agentic-rag)

## قواعد تمنع التكسير أثناء النقل

- لا تنقل وتعيد كتابة السلوك في نفس الـ commit؛ **انقل أولًا، ثم نظّف لاحقًا**. [dev](https://dev.to/markoulis/layered-architecture-dependency-injection-a-recipe-for-clean-and-testable-fastapi-code-3ioo)
- استخدم compatibility imports مؤقتًا لمدة 1–2 phases.
- بعد كل phase، شغّل:
  - unit tests
  - smoke tests
  - couple of golden fiqh queries
- لا تغيّر أسماء الـ API الخارجية في البداية؛ ابدأ بالداخل أولًا. [blog.stackademic](https://blog.stackademic.com/building-a-production-grade-fastapi-backend-with-clean-layered-architecture-7e3ad6deb0bb)

## أنصحك بأي خيار؟

لو ستبدأ غدًا عمليًا، افعل هذا:

1. اعتمد **شجرة v2** كـ target architecture. [dev](https://dev.to/markoulis/layered-architecture-dependency-injection-a-recipe-for-clean-and-testable-fastapi-code-3ioo)
2. نفّذ **خطة commits** من Commit 1 إلى Commit 6 أولًا فقط. [dev](https://dev.to/markoulis/layered-architecture-dependency-injection-a-recipe-for-clean-and-testable-fastapi-code-3ioo)
3. لا تلمس كل agents الآن؛ ابدأ بـ fiqh/hadith/quran path فقط. [arxiv](https://arxiv.org/abs/2603.08501)

هذا سيعطيك refactor نظيفًا من غير ما يوقف التطوير الفعلي.

أفضّل هنا أن أعطيك **الاثنين معًا**: checklist Issues جاهزة للنسخ في GitHub، ثم migration table واضح من الملف الحالي إلى الجديد، لأن هذا يحول refactor من “فكرة” إلى تنفيذ عملي قابل للإدارة. [smithery](https://smithery.ai/skills/rafaelkamimura/fastapi-clean-architecture)
هذا أيضًا متوافق مع أفضل ممارسات clean architecture في FastAPI، حيث تكون الهجرة موثّقة، تدريجية، وبها deprecation path بدل النقل العنيف دفعة واحدة. [launch](https://www.launch.ist/blog/clean-architecture-structure/)

## GitHub issues checklist

انسخ هذا كما هو في GitHub Project أو Issues:

```md
# Burhan v2 Refactor Checklist

## Epic 1: Establish target architecture
- [ ] Create new top-level modules under `src/`: `retrieval/`, `indexing/`, `verifiers/`
- [ ] Create `application/services/` and `application/use_cases/`
- [ ] Create `docs/architecture.md`
- [ ] Create `docs/decisions/adr-002-structure-v2.md`
- [ ] Document layer rules: `api -> application -> agents/retrieval/generation`
- [ ] Document deprecation policy for legacy module paths

## Epic 2: Extract retrieval from `knowledge/`
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

## Epic 3: Extract indexing from `knowledge/`
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

## Epic 4: Introduce verification framework
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

## Epic 5: Consolidate routing and orchestration
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

## Epic 6: Make agents collection-aware
- [ ] Add explicit collection-to-agent mapping
- [ ] Create `agents/tafsir_agent.py`
- [ ] Create `agents/aqeedah_agent.py`
- [ ] Create `agents/history_agent.py`
- [ ] Create `agents/language_agent.py`
- [ ] Create `agents/tazkiyah_agent.py`
- [ ] Create `agents/usul_fiqh_agent.py`
- [ ] Update `agents/registry.py` to register all collection-aware agents
- [ ] Add regression tests for agent selection by query type

## Epic 7: Simplify API layer
- [ ] Keep API routes thin and transport-only
- [ ] Merge/normalize endpoints into: `/ask`, `/search`, `/classify`, `/tools/*`, `/health`
- [ ] Split schemas into `ask.py`, `search.py`, `classify.py`, `tools.py`, `traces.py`
- [ ] Remove business logic from route handlers
- [ ] Add structured error responses across API
- [ ] Add request tracing metadata to responses

## Epic 8: Add regression safety net
- [ ] Add `tests/regression/fiqh_cases.jsonl`
- [ ] Add `tests/regression/hadith_cases.jsonl`
- [ ] Add `tests/regression/quran_cases.jsonl`
- [ ] Assert selected agent for each golden case
- [ ] Assert selected collections for each golden case
- [ ] Assert verification outcome for each golden case
- [ ] Assert final mode: `answer | clarify | abstain`
- [ ] Add CI job for regression suite

## Epic 9: Remove deprecated code
- [ ] Remove compatibility shims after migration stabilizes
- [ ] Delete deprecated `knowledge/*` wrappers
- [ ] Delete deprecated `core/router.py`
- [ ] Delete duplicate registry files
- [ ] Update imports across codebase
- [ ] Final architecture cleanup pass
```

## labels مقترحة للـ issues

استخدم labels ثابتة من البداية حتى لا يتحول الـ board إلى فوضى. [auth0](https://auth0.com/blog/fastapi-best-practices/)

```md
Labels:
- refactor
- architecture
- retrieval
- indexing
- verification
- api
- agents
- tests
- docs
- breaking-change
- good-first-issue
- priority:P0
- priority:P1
- priority:P2
```

## migration table

هذا الجدول يوضح: **الملف الحالي → الملف الجديد → السبب → الأولوية**. [smithery](https://smithery.ai/skills/rafaelkamimura/fastapi-clean-architecture)

| الملف الحالي | الملف الجديد | السبب | الأولوية |
|---|---|---|---|
| `src/knowledge/hybrid_search.py` | `src/retrieval/retrievers/hybrid_retriever.py` | فصل retrieval عن indexing وعن domain heuristics، وتحسين وضوح الطبقات  [qdrant](https://qdrant.tech/articles/hybrid-search/) | P0 |
| `src/knowledge/bm25_retriever.py` | `src/retrieval/retrievers/bm25_retriever.py` | إبقاء lexical retrieval داخل طبقة retrieval الموحدة  [qdrant](https://qdrant.tech/articles/hybrid-search/) | P0 |
| `src/knowledge/hierarchical_retriever.py` | `src/retrieval/retrievers/hierarchical_retriever.py` | توحيد جميع retrievers تحت namespace واحد | P1 |
| `src/knowledge/query_expander.py` | `src/retrieval/expanders/query_expander.py` | query expansion جزء من planning/retrieval وليس knowledge عام | P0 |
| `src/knowledge/reranker.py` | `src/retrieval/ranking/reranker.py` | reranking مرحلة ranking مستقلة عن الاسترجاع الخام  [qdrant](https://qdrant.tech/documentation/tutorials-search-engineering/reranking-hybrid-search/) | P0 |
| `src/knowledge/book_weighter.py` | `src/retrieval/ranking/book_weighter.py` | book authority weighting أقرب للranking policy | P1 |
| `src/knowledge/embedding_model.py` | `src/indexing/embeddings/embedding_model.py` | embedding concern يخص indexing/query encoding لا retrieval orchestration | P0 |
| `src/knowledge/embedding_cache.py` | `src/indexing/embeddings/embedding_cache.py` | cache مرتبط بعملية embedding نفسها | P1 |
| `src/knowledge/vector_store.py` | `src/indexing/vectorstores/qdrant_store.py` | vector store adapter يجب أن يكون في طبقة indexing/storage  [qdrant](https://qdrant.tech/documentation/tutorials-search-engineering/hybrid-search-fastembed/) | P0 |
| `src/knowledge/title_loader.py` | `src/indexing/metadata/title_loader.py` | metadata loading لا يجب أن يبقى داخل knowledge العام | P1 |
| `src/knowledge/hadith_grader.py` | `src/verifiers/hadith_grade.py` | grading هو verification concern لا retrieval concern | P0 |
| `src/quran/quotation_validator.py` | `src/verifiers/exact_quote.py` مع adapter في `src/quran/` | توحيد التحقق من الاقتباسات في framework واحد  [arxiv](https://arxiv.org/abs/2603.08501) | P0 |
| `src/application/router.py` | `src/application/router/router_agent.py` | جعل routing مركزًا واحدًا واضحًا | P0 |
| `src/application/classifier_factory.py` | `src/application/router/classifier_factory.py` | تجميع classifier-related files في submodule واحد | P1 |
| `src/application/hybrid_classifier.py` | `src/application/router/hybrid_classifier.py` | نفس السبب: توحيد ملفات التوجيه/التصنيف | P1 |
| `src/api/routes/classification.py` | يبقى في `src/api/routes/classify.py` لكن يستهلك `application/use_cases/classify_query.py` | route يجب أن يبقى transport-only  [zyneto](https://zyneto.com/blog/best-practices-in-fastapi-architecture) | P0 |
| `src/api/routes/query.py` | `src/api/routes/ask.py` | تسمية أوضح ومقابلة use-case أساسي | P1 |
| `src/api/routes/rag.py` | `src/api/routes/search.py` أو دمج جزئي مع `ask.py` | تقليل الغموض بين query/ask/rag | P1 |
| `src/core/router.py` | حذف بعد النقل إلى `application/router/router_agent.py` | إزالة ازدواجية routing | P0 |
| `src/core/registry.py` | حذف أو دمج في `src/agents/registry.py` | registry واحد فقط أفضل من اثنين | P0 |
| `src/core/citation.py` | `src/domain/citations.py` أو `src/generation/composers/citation_composer.py` | تحديد هل هو domain model أم formatting utility | P1 |
| `src/agents/registry.py` | يبقى كما هو مع توسيعه وربطه بالcollections | registry الطبيعي للـ agents | P0 |
| `src/agents/general_islamic_agent.py` | يبقى كما هو | agent موجود وصالح كبداية | P2 |
| `src/agents/seerah_agent.py` | يبقى كما هو | لا حاجة لنقله، فقط توثيق policy الخاصة به | P2 |
| `src/infrastructure/llm_client.py` | `src/generation/llm_client.py` أو `src/infrastructure/llm/openai_client.py` حسب الاستخدام | لو هو orchestration-aware فمكانه generation، لو adapter خام فمكانه infrastructure | P1 |
| `src/infrastructure/llm/` | `src/infrastructure/llm/` | مكان مناسب للadapters الخارجية، يُبقى كما هو | P2 |
| `src/tools/*.py` | تبقى كما هي مع إضافة `src/tools/registry.py` | tools layer جيدة، فقط تحتاج registry واضح | P1 |
| `src/domain/intents.py` | يبقى كما هو | domain enum واضح ومناسب | P2 |
| `src/domain/models.py` | يبقى كما هو أو يجزأ لاحقًا | ليس أولوية قبل تثبيت الطبقات | P2 |
| `src/utils/language_detection.py` | يبقى كما هو | util واضح | P2 |
| `src/utils/era_classifier.py` | يمكن نقله لاحقًا إلى `retrieval/expanders/era_expansion.py` أو يبقى مؤقتًا | يعتمد على استخدامه الفعلي | P2 |

## ترتيب التنفيذ العملي

نفّذ الجدول بهذا الترتيب حتى لا تتكسر المنظومة:

1. انقل `retrieval` files أولًا مع shims. [qdrant](https://qdrant.tech/articles/hybrid-search/)
2. انقل `indexing` files ثانيًا.
3. أنشئ `verifiers/` وابدأ بـ `exact_quote`, `source_attribution`, `evidence_sufficiency`. [aclanthology](https://aclanthology.org/2025.findings-acl.354.pdf)
4. وحّد routing وregistry.
5. بس بعد ذلك ابدأ حذف القديم. [auth0](https://auth0.com/blog/fastapi-best-practices/)

## قواعد مهمة أثناء الترحيل

- كل سطر في migration table من نوع P0 يجب أن يكون issue مستقل أو sub-issue واضح. [auth0](https://auth0.com/blog/fastapi-best-practices/)
- لا تحذف الملف القديم في نفس commit الذي تنقل فيه الكود؛ اترك shim مؤقتًا. [smithery](https://smithery.ai/skills/rafaelkamimura/fastapi-clean-architecture)
- بعد كل P0 migration، أضف smoke test بسيط على endpoint `/ask` و`/classify`. [zyneto](https://zyneto.com/blog/best-practices-in-fastapi-architecture)
- ضع تاريخ إزالة الـ deprecated paths في ADR أو docs حتى لا تبقى forever. [auth0](https://auth0.com/blog/fastapi-best-practices/)

