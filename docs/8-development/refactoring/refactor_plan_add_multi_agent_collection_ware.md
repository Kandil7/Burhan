# Burhan Refactor & Implementation Plan

هذا الملف يحوّل وثيقة  
**“Burhan CollectionAgent Architecture and Multi-Agent RAG Design”**  
إلى خطة تنفيذ عملية داخل مشروع Burhan، مع مراحل واضحة، ملفات مقترحة، و‑checklists.[file:138]

الهدف: الانتقال من RAG تقليدي إلى **Multi‑Agent RAG** مبني على:

- `CollectionAgent` abstractions مشتركة.
- Qdrant hybrid dense/BM25 retrieval مع strategies per‑agent.[file:138]
- VerificationSuite صارمة (Digital Isnad) قبل أي توليد.[file:138]
- RouterAgent + orchestration patterns للسيناريوهات المعقدة.[file:138]

---

## 0. High-Level Phases

1. **Core Abstractions**  
   - CollectionAgent base  
   - Retrieval layer + strategies  
   - Verification base

2. **Fiqh‑First MVP**  
   - FiqhAgent + prompts  
   - Minimal verification  
   - Minimal metadata + Qdrant collection

3. **Metadata & Qdrant Infrastructure**  
   - Enrichment pipeline (catalog joins, era, madhhab)  
   - Collections setup (HNSW, quantization, hybrid vectors)

4. **Router & Multi-Agent Skeleton**  
   - RouterAgent (rule‑based → LLM later)  
   - Basic multi-agent orchestration (Fiqh + Hadith skeleton)

5. **Evaluation & Benchmarks**  
   - Golden set schema  
   - Metrics (retrieval / citations / abstention / ikhtilaf)

6. **Scaling to Other Agents**  
   - HadithAgent, TafsirAgent, AqeedahAgent…  
   - Collection‑specific chunking & retrieval configs

---

## 1. Target Project Structure

> يمكن تكييف الأسماء مع الوضع الحالي للريبو، المهم الـ boundaries.

```text
Burhan/
  app/
    api/
      v1/
        routes/
          fiqh.py
          router.py
          health.py
    core/
      config.py
      logging.py
  agents/
    base.py
    fiqh_agent.py
    hadith_agent.py
    tafsir_agent.py
    router_agent.py
    verification/
      base.py
      fiqh_checks.py
      hadith_checks.py
  retrieval/
    qdrant_client.py
    strategies.py
    reranker.py
  metadata/
    catalogs.py
    enrichment.py
  qdrant_setup/
    collections.py
  evaluation/
    metrics.py
    golden_set_schema.py
  prompts/
    global_preamble.txt
    fiqh_prompt.txt
    hadith_prompt.txt
  scripts/
    ingest_Burhan_to_qdrant.py
    build_metadata.py
    rebuild_collections.py
  tests/
    test_agents_base.py
    test_fiqh_agent.py
    test_retrieval_fiqh.py
    test_verification_fiqh.py
```

---

## 2. Phase 1 – Core Abstractions

### 2.1 CollectionAgent Base

**Goal:** تثبيت الـ lifecycle القياسي كما في القسم 1 من الوثيقة.[file:138]

**Files**

- `agents/base.py`

**Tasks**

- [ ] تعريف `IntentLabel` (fiqh_hukm, hadith_takhrij, tafsir_ayah, ...).[file:138]
- [ ] تعريف Pydantic models:
  - `RetrievalStrategy`
  - `VerificationCheck`
  - `VerificationSuite`
  - `FallbackPolicy`
  - `CollectionAgentConfig`.[file:138]
- [ ] تعريف abstract class `CollectionAgent` مع abstract methods:
  - `query_intake`
  - `classify_intent`
  - `retrieve_candidates`
  - `rerank_candidates`
  - `run_verification`
  - `generate_answer`
  - `assemble_citations`.[file:138]
- [ ] إضافة method:
  ```python
  async def run(self, raw_question: str, meta: dict | None) -> FinalAnswer:
      ...
  ```
  لتنفيذ lifecycle end‑to‑end.

**Acceptance Criteria**

- يمكن إنشاء subclass dummy وتنفيذه في `tests/test_agents_base.py` بدون أخطاء.

---

### 2.2 Retrieval Layer & Strategies

**Goal:** عزل Qdrant + hybrid logic في طبقة واحدة، حسب **Retrieval Strategy Matrix**.[file:138]

**Files**

- `retrieval/qdrant_client.py`
- `retrieval/strategies.py`
- `retrieval/reranker.py`

**Tasks**

- [ ] `qdrant_client.py`:
  - تهيئة client واحد (singleton أو dependency).
  - دوال `search_hybrid(collection, dense_vec, sparse_vec, filters, top_k)` باستخدام Universal Query API (dense+BM25).[file:138]
- [ ] `strategies.py`:
  - استيراد `RetrievalStrategy` من `agents/base.py`.
  - تعريف `retrieval_matrix` من القسم 2.1/2.2 (FiqhAgent…).[file:138]
  - دالة:
    ```python
    def get_strategy_for_agent(agent_name: str) -> RetrievalStrategy:
        ...
    ```
- [ ] `reranker.py`:
  - interface لـ cross-encoder/ColBERT:
    - `rerank(query: str, candidates: list[RetrievedPassage]) -> list[RetrievedPassage]`.[file:138]
  - في البداية: identity implementation.

**Acceptance Criteria**

- استدعاء `get_strategy_for_agent("FiqhAgent")` يرجع config مطابق للـ YAML في الوثيقة.[file:138]

---

### 2.3 Verification Suite Base

**Goal:** تحويل section 3 (Verification Suite Design) إلى code.[file:138]

**Files**

- `agents/verification/base.py`
- `agents/verification/fiqh_checks.py`

**Tasks**

- [ ] `verification/base.py`:
  - model `VerificationCheck`, `VerificationSuite` (أو reuse).[file:138]
  - base class `VerificationCheckRunner`:
    ```python
    class VerificationCheckRunner(ABC):
        name: str
        fail_policy: Literal['abstain', 'warn', 'proceed']
        async def run(self, passages, normalized_query) -> VerificationResultPiece: ...
    ```
- [ ] `fiqh_checks.py`:
  - stubs للـ checks التالية:
    - `QuoteValidator`
    - `SourceAttributor`
    - `ContradictionDetector`
    - `EvidenceSufficiency`.[file:138]
  - config YAML‑like مطابق للمثال (FiqhAgent suite).[file:138]
- [ ] util:
  ```python
  def build_verification_suite_for(agent_name: str) -> VerificationSuite:
      ...
  ```

**Acceptance Criteria**

- `build_verification_suite_for("FiqhAgent")` يرجع suite بالـ checks الأربعة مع الـ fail_policy الصحيحة.[file:138]

---

## 3. Phase 2 – Fiqh‑First MVP

### 3.1 Prompts Wiring

**Goal:** استخراج prompts من القسم 4 إلى ملفات نصية.[file:138]

**Files**

- `prompts/global_preamble.txt`
- `prompts/fiqh_prompt.txt`

**Tasks**

- [ ] نسخ Global preamble العربي إلى `global_preamble.txt`.[file:138]
- [ ] نسخ FiqhAgent system prompt الكامل إلى `fiqh_prompt.txt`.[file:138]
- [ ] utility في `agents/fiqh_agent.py`:
  ```python
  def load_prompt(name: str) -> str:
      ...
  ```

---

### 3.2 Implement FiqhAgent

**Files**

- `agents/fiqh_agent.py`
- `app/api/v1/routes/fiqh.py`

**Tasks (FiqhAgent)**

- [ ] `FiqhAgent(CollectionAgent)`:
  - يمرر:
    - `collection_name="fiqh_passages"`
    - `retrieval_strategy=get_strategy_for_agent("FiqhAgent")`
    - `verification_suite=build_verification_suite_for("FiqhAgent")`
    - `prompt_template=global_preamble + fiqh_prompt`.[file:138]
- [ ] `query_intake`:
  - normalize نص السؤال (توحيد الألف/الياء، إزالة مسافات زائدة، tagging fatwa vs info).[file:138]
- [ ] `classify_intent`:
  - rules بسيطة على الكلمات: "حكم، زكاة، طلاق…" → `fiqh_hukm` إلخ.[file:138]
- [ ] `retrieve_candidates`:
  - call `qdrant_client.search_hybrid` بـ:
    - alpha، topK، filters حسب strategy (dense‑heavy hybrid, alpha=0.6, topk_initial=80…).[file:138]
- [ ] `rerank_candidates`:
  - استخدام `reranker.rerank` (identity في البداية).[file:138]
- [ ] `run_verification`:
  - تشغيل checks بالترتيب، واحترام `fail_policy`:
    - quote_validator (abstain on fail)
    - source_attributor (warn)
    - contradiction_detector (proceed)
    - evidence_sufficiency (abstain).[file:138]
- [ ] `generate_answer`:
  - إعداد system + user + context (passages + verification_result) واستدعاء LLM.[file:138]
- [ ] `assemble_citations`:
  - بناء citations موحدة: book_title, author_name, page_number, hierarchy….[file:138]

**Tasks (API)**

- [ ] `fiqh.py`:
  - endpoint: `POST /v1/fiqh/answer`
  - body: `{question: str, meta?: dict}`
  - ينادي FiqhAgent.run ويعيد:
    ```json
    {
      "answer": "...",
      "citations": [...],
      "confidence": 0.xx,
      "ikhtilaf_detected": true/false
    }
    ```

**Acceptance Criteria (MVP)**

- سؤال فقهي بسيط يمرّ عبر:
  - query_intake → retrieve (Qdrant) → verification (stubs) → generate → citations.[file:138]

---

## 4. Phase 3 – Metadata Pipeline & Qdrant

### 4.1 Metadata Enrichment

**Goal:** تنفيذ section 5 (Join logic, era bucketing, madhhab handling).[file:138]

**Files**

- `metadata/catalogs.py`
- `metadata/enrichment.py`
- `scripts/build_metadata.py`

**Tasks**

- [ ] `catalogs.py`:
  - loader لـ `master_catalog.json`, `author_catalog.json`, `category_mapping.json`.[file:138]
- [ ] `enrichment.py`:
  - `enrich_passage(row, master_cat, author_cat, cat_map)`:
    - يضيف: book_title, author_name, author_death_year, madhhab, aqeedah_school, era, category_main/sub, collection, hierarchy, surah/ayah/grade/hadith_number إذا وجدت.[file:138]
    - era buckets: sahabah, tabiin, classical, medieval, contemporary.[file:138]
    - سياسة missing madhhab (unknown + inferred flag).[file:138]
- [ ] `build_metadata.py`:
  - القراءة من Burhan‑Datasets
  - إنتاج JSONL/Parquet enriched جاهز لـ ingestion.

**Acceptance Criteria**

- عينة من enriched passages تحتوي الحقول كما في payload schema في الوثيقة.[file:138]

---

### 4.2 Qdrant Collections Setup

**Goal:** تنفيذ section 7 (vectors, sparse BM25, quantization, HNSW).[file:138]

**Files**

- `qdrant_setup/collections.py`
- `scripts/ingest_Burhan_to_qdrant.py`

**Tasks**

- [ ] `collections.py`:
  - تعريف:
    - `EMBED_DIM`
    - `base_vectors_config` (dense, cosine)
    - `sparse_config` (bm25, on_disk).[file:138]
    - `quantization` (INT8, always_ram=False).[file:138]
    - HNSW configs: large/medium/small + mapping لكل collection كما في الوثيقة.[file:138]
  - دالة:
    ```python
    def recreate_all_collections(client):
        ...
    ```
- [ ] `ingest_Burhan_to_qdrant.py`:
  - تحميل enriched data
  - call `recreate_all_collections`
  - upsert points (dense vector + bm25 sparse + payload).[file:138]

**Acceptance Criteria**

- Collection `fiqh_passages` موجودة في Qdrant، على hybrid config، ويمكن البحث فيها من FiqhAgent.[file:138]

---

## 5. Phase 4 – RouterAgent & Multi-Agent Skeleton

### 5.1 RouterAgent

**Goal:** تطبيق section 6 (decision tree + thresholds).[file:138]

**Files**

- `agents/router_agent.py`
- `app/api/v1/routes/router.py`

**Tasks**

- [ ] `RouterAgent`:
  - rule‑based routing حسب الكلمات المفتاحية (حديث، سورة، إسناد، عقيدة، غزوة، نحو…).[file:138]
  - config thresholds:
    - `primary_threshold`
    - `secondary_threshold`
    - `low_confidence_threshold`
    - `low_confidence_fallback = GeneralIslamicAgent`.[file:138]
  - لاحقًا: إضافة LLM classifier ليعطي p(domain|question) كما في الوثيقة.[file:138]
- [ ] API `/v1/router/answer`:
  - يأخذ السؤال
  - يحدد agents
  - الآن: إن كان Fiqh في القائمة → ينادي FiqhAgent فقط.

**Acceptance Criteria**

- أسئلة فقهية/حديثية/تفسيرية واضحة تُرَوت إلى agent الصحيح حسب decision tree المذكور.[file:138]

---

## 6. Phase 5 – Evaluation Framework

**Goal:** تنفيذ section 9 (metrics, golden test set).[file:138]

**Files**

- `evaluation/golden_set_schema.py`
- `evaluation/metrics.py`

**Tasks**

- [ ] تعريف schema لـ test item:
  - id, question, domains, ikhtilaf_required, abstention_expected, gold_evidence_ids, gold_answer_outline, metrics flags.[file:138]
- [ ] metrics:
  - Precision@k, Recall@k
  - Citation accuracy
  - Ikhtilaf coverage
  - Abstention rate
  - Hadith grade accuracy (لاحقًا للـ HadithAgent).[file:138]
- [ ] CLI صغيرة لتمرير golden set على FiqhAgent وكتابة report.

**Acceptance Criteria**

- يمكن تشغيل evaluation بسيطة على عدة أسئلة فقهية وقراءة نتائج retrieval وabstention.

---

## 7. Phase 6 –扩 / Other Agents (Later)

بعد ثبات FiqhAgent:

- [ ] Skeleton لـ HadithAgent، TafsirAgent, AqeedahAgent… مع:
  - retrieval_strategy من المصفوفة.[file:138]
  - verification_suite المناسب من YAML.[file:138]
  - prompts الخاصة بكل agent (القسم 4.3/4.4).[file:138]
- [ ] تطبيق chunking strategies per collection كما في section 10.3.[file:138]
- [ ] إضافة orchestration patterns:
  - Sequential (Fiqh → Usul → Hadith)
  - Parallel (Fiqh + Tazkiyah)
  - Hierarchical (General/Fiqh primary + others كـ tools).[file:138]

---

## 8. Milestones & Tracking

### Milestone A – FiqhAgent MVP (2–4 أسابيع)

- [ ] Phase 1 مكتملة (base + retrieval + verification base).
- [ ] Phase 2 مكتملة لـ FiqhAgent على عيّنة صغيرة من البيانات.
- [ ] Endpoint `/v1/fiqh/answer` يعمل.

### Milestone B – FiqhAgent Production‑Ready

- [ ] Metadata enrichment كاملة للـ fiqh_passages.
- [ ] Qdrant collection production settings (HNSW + quantization).[file:138]
- [ ] Verification checks فعّالة (quote_validator, source_attributor, evidence_sufficiency).
- [ ] Minimal evaluation set للفقه.

### Milestone C – Router + Second Agent (Hadith Skeleton)

- [ ] RouterAgent live.
- [ ] HadithAgent skeleton (تخريج + quote_validator + grade_checker stub).
- [ ] basic orchestration (Fiqh + Hadith) لسؤال مشترك.

---

## 9. Notes & Non‑Goals

- هذه الخطة لا تغطي:
  - Frontend/UI.
  - CI/CD وmonitoring.
  - LangGraph implementation الكامل (فقط مذكور كهدف لاحق).[file:138]
- التركيز الآن على:
  - Fiqh‑first correctness.
  - Digital Isnad (verification قبل generation).
  - Hybrid retrieval مضبوط فوق Burhan‑Datasets.[file:138]