نعم، هذا بالضبط هو الاستخدام الصحيح للنص داخل Athar: اجعل **ARCHITECTURE.md** وثيقة التصميم المرجعية، و**REFRACTOR_PLAN.md** وثيقة التنفيذ، ثم استخرج منها مباشرة `agents/base.py` وملفات `config/agents/*.yaml` وملفات `prompts/*.txt` و`RouterAgent`/orchestrator skeleton. [ppl-ai-file-upload.s3.amazonaws](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/57452145/36291451-b3d1-4808-b973-1527eb9b3b89/paste.txt)

## كيف تقسّم الشغل

أفضل تقسيم عملي هو هذا:

| الملف | الوظيفة |
|---|---|
| `ARCHITECTURE.md` | design رسمي طويل: lifecycle, routing, verification, Qdrant, prompts, evaluation. [ppl-ai-file-upload.s3.amazonaws](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/57452145/eb489275-50c4-4c8b-a1b2-b4b368deb493/paste.txt) |
| `REFRACTOR_PLAN.md` | roadmap تنفيذية: phases, tasks, files, acceptance criteria. [ppl-ai-file-upload.s3.amazonaws](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/57452145/36291451-b3d1-4808-b973-1527eb9b3b89/paste.txt) |
| `agents/base.py` | abstraction الفعلية لـ `CollectionAgent` وconfig models. [ppl-ai-file-upload.s3.amazonaws](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/57452145/36291451-b3d1-4808-b973-1527eb9b3b89/paste.txt) |
| `config/agents/*.yaml` | retrieval / verification / fallback / routing config لكل وكيل. [ppl-ai-file-upload.s3.amazonaws](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/57452145/eb489275-50c4-4c8b-a1b2-b4b368deb493/paste.txt) |
| `prompts/*.txt` | preamble عام + system prompt لكل agent. [ppl-ai-file-upload.s3.amazonaws](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/57452145/eb489275-50c4-4c8b-a1b2-b4b368deb493/paste.txt) |
| `agents/router_agent.py` | routing logic single-label/multi-label + thresholds. [ppl-ai-file-upload.s3.amazonaws](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/57452145/eb489275-50c4-4c8b-a1b2-b4b368deb493/paste.txt) |
| `orchestration/*` | sequential / parallel / hierarchical patterns. [ppl-ai-file-upload.s3.amazonaws](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/57452145/eb489275-50c4-4c8b-a1b2-b4b368deb493/paste.txt) |

هذا التقسيم مهم لأنه يفصل بين **المعرفة المعمارية** و**التنفيذ البرمجي** و**الإعدادات القابلة للتعديل**، بدل خلط كل شيء داخل ملفات Python صلبة. [ppl-ai-file-upload.s3.amazonaws](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/57452145/eb489275-50c4-4c8b-a1b2-b4b368deb493/paste.txt)

## ماذا تأخذ من كل مستند

استخدم `file:139` كأساس لـ **الشرح العربي الرسمي** لأنه أوضح في العرض ويوصل الفكرة بشكل ممتاز لوثيقة هندسية داخل الريبو. [ppl-ai-file-upload.s3.amazonaws](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/57452145/eb489275-50c4-4c8b-a1b2-b4b368deb493/paste.txt)
واستخدم `file:138` كأساس لـ **الصياغة التنفيذية الأدق**، لأنه يعطي interface أوضح للـ `CollectionAgent`، ويفصل lifecycle وQdrant config وorchestration بطريقة أقرب للكود. [ppl-ai-file-upload.s3.amazonaws](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/57452145/36291451-b3d1-4808-b973-1527eb9b3b89/paste.txt)

بمعنى عملي:

- من `file:139` خذ:
  - Executive summary العربي
  - مقارنة الوكلاء العشرة
  - system prompts
  - الشرح المفاهيمي للـ routing والامتناع والتقييم. [ppl-ai-file-upload.s3.amazonaws](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/57452145/eb489275-50c4-4c8b-a1b2-b4b368deb493/paste.txt)
- من `file:138` خذ:
  - Pydantic/ABC sketch الأفضل لـ `agents/base.py`
  - Router thresholds
  - Qdrant collection setup
  - orchestration patterns بشكل قابل للتطبيق. [ppl-ai-file-upload.s3.amazonaws](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/57452145/36291451-b3d1-4808-b973-1527eb9b3b89/paste.txt)

## الهيكل المقترح داخل الريبو

ابدأ بهذا الشكل:

```text
athar/
  docs/
    ARCHITECTURE.md
    REFRACTOR_PLAN.md
  agents/
    base.py
    fiqh_agent.py
    hadith_agent.py
    tafsir_agent.py
    aqeedah_agent.py
    router_agent.py
  config/
    agents/
      fiqh.yaml
      hadith.yaml
      tafsir.yaml
      aqeedah.yaml
      seerah.yaml
      history.yaml
      language.yaml
      tazkiyah.yaml
      general.yaml
      usul_fiqh.yaml
    router.yaml
  prompts/
    _shared_preamble.txt
    fiqh_agent.txt
    hadith_agent.txt
    tafsir_agent.txt
    aqeedah_agent.txt
    seerah_agent.txt
    history_agent.txt
    language_agent.txt
    tazkiyah_agent.txt
    general_agent.txt
    usul_fiqh_agent.txt
  orchestration/
    composer.py
    sequential.py
    parallel.py
    hierarchical.py
```

هذا الهيكل ينسجم مباشرة مع التصميم الموجود في المستندين، خاصة فكرة أن لكل CollectionAgent إعداداته الخاصة، بينما تبقى البنية العامة موحدة. [ppl-ai-file-upload.s3.amazonaws](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/57452145/36291451-b3d1-4808-b973-1527eb9b3b89/paste.txt)

## ما الذي تضعه في ARCHITECTURE.md

ضع في `ARCHITECTURE.md` نسخة نظيفة من التقرير المعماري، مع إعادة ترتيب خفيف فقط:

- Overview
- CollectionAgent abstraction
- Lifecycle
- Comparison of 10 agents
- Retrieval design
- Verification design
- Metadata enrichment
- RouterAgent
- Orchestration patterns
- Output schema
- Abstention rules
- Evaluation
- Deployment notes. [ppl-ai-file-upload.s3.amazonaws](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/57452145/eb489275-50c4-4c8b-a1b2-b4b368deb493/paste.txt)

أنصح أيضًا بإضافة **Table of Contents** في البداية، لأن المستند طويل وسيصبح مرجعًا أساسيًا للفريق. [ppl-ai-file-upload.s3.amazonaws](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/57452145/eb489275-50c4-4c8b-a1b2-b4b368deb493/paste.txt)

## ما الذي تضعه في REFRACTOR_PLAN.md

هذا الملف لا يكرر الشرح، بل يحوله إلى عمل تنفيذي:

- Phase 1: base abstractions
- Phase 2: Fiqh-first MVP
- Phase 3: metadata + Qdrant
- Phase 4: Router + orchestration skeleton
- Phase 5: evaluation
- Phase 6: expand to 10 agents. [ppl-ai-file-upload.s3.amazonaws](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/57452145/36291451-b3d1-4808-b973-1527eb9b3b89/paste.txt)

لكل phase:
- files to create
- tasks
- acceptance criteria
- risks/dependencies. [ppl-ai-file-upload.s3.amazonaws](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/57452145/36291451-b3d1-4808-b973-1527eb9b3b89/paste.txt)

يعني باختصار:
- `ARCHITECTURE.md` = لماذا وكيف صممنا النظام
- `REFRACTOR_PLAN.md` = ماذا سنبني أولًا ومتى وكيف نعرف أنه نجح

## كيف تستخرج agents/base.py

استخرج section الخاص بالـ base abstraction من `file:138` أساسًا، لأنه أنضج من النسخة المبسطة في `file:139`. [ppl-ai-file-upload.s3.amazonaws](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/57452145/eb489275-50c4-4c8b-a1b2-b4b368deb493/paste.txt)
والذي ينبغي أن يحتوي على الأقل:

- `IntentLabel`
- `RetrievalStrategy`
- `VerificationCheck`
- `VerificationSuite`
- `FallbackPolicy`
- `CollectionAgentConfig`
- `CollectionAgent(ABC)` بواجهات:
  - `query_intake`
  - `classify_intent`
  - `retrieve_candidates`
  - `rerank_candidates`
  - `run_verification`
  - `generate_answer`
  - `assemble_citations`. [ppl-ai-file-upload.s3.amazonaws](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/57452145/36291451-b3d1-4808-b973-1527eb9b3b89/paste.txt)

ولو تريد نسخة عملية أكثر، أضف method غير abstract مثل:

```python
async def run(self, raw_question: str, meta: dict | None = None) -> FinalAnswer:
    normalized = await self.query_intake(raw_question, meta)
    intent = await self.classify_intent(normalized)
    candidates = await self.retrieve_candidates(intent, normalized)
    reranked = await self.rerank_candidates(candidates)
    verification = await self.run_verification(reranked, normalized)
    draft = await self.generate_answer(verification.verified_evidence, normalized, verification)
    return await self.assemble_citations(draft, verification.verified_evidence)
```

هذا يحقق lifecycle الموحدة المذكورة في المستندين. [ppl-ai-file-upload.s3.amazonaws](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/57452145/eb489275-50c4-4c8b-a1b2-b4b368deb493/paste.txt)

## كيف تحول الجداول إلى YAML configs

حوّل جداول retrieval / verification / abstention من `file:139` إلى ملفات YAML منفصلة لكل agent، لأن هذه الإعدادات ستتغير كثيرًا أثناء التجارب. [ppl-ai-file-upload.s3.amazonaws](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/57452145/eb489275-50c4-4c8b-a1b2-b4b368deb493/paste.txt)

مثال `config/agents/fiqh.yaml`:

```yaml
name: FiqhAgent
domain: fiqh
collection_name: fiqh_passages

retrieval:
  primary: hybrid
  alpha: 0.6
  topk_initial: 80
  topk_reranked: 12
  min_relevance: 0.45
  metadata_filters_priority:
    - madhhab
    - category_sub
    - era

verification:
  checks:
    - name: quote_validator
      input_schema: RetrievedPassages
      output_schema: QuoteValidationResult
      fail_policy: abstain
    - name: source_attributor
      input_schema: RetrievedPassages
      output_schema: SourceAttributionResult
      fail_policy: warn
    - name: contradiction_detector
      input_schema: RetrievedPassages
      output_schema: ContradictionResult
      fail_policy: proceed
    - name: evidence_sufficiency
      input_schema: RetrievedPassages
      output_schema: SufficiencyResult
      fail_policy: abstain

fallback:
  on_low_recall: fallback_sparse
  on_verification_failure: abstain
  delegate_agent: null

abstention:
  high_risk_personal_fatwa: true
  require_diverse_evidence: true
  minimum_sources: 3
```

ومثال `config/agents/hadith.yaml`:

```yaml
name: HadithAgent
domain: hadith
collection_name: hadith_passages

retrieval:
  primary: hybrid
  alpha: 0.3
  topk_initial: 120
  topk_reranked: 20
  min_relevance: 0.5
  metadata_filters_priority:
    - book_id
    - compiler
    - grade

verification:
  checks:
    - name: quote_validator
      input_schema: RetrievedPassages
      output_schema: QuoteValidationResult
      fail_policy: abstain
    - name: source_attributor
      input_schema: RetrievedPassages
      output_schema: SourceAttributionResult
      fail_policy: warn
    - name: grade_checker
      input_schema: RetrievedPassages
      output_schema: GradeCheckResult
      fail_policy: warn
    - name: evidence_sufficiency
      input_schema: RetrievedPassages
      output_schema: SufficiencyResult
      fail_policy: abstain

fallback:
  on_low_recall: fallback_sparse
  on_verification_failure: abstain
  delegate_agent: null
```

هذا التحويل يحافظ على المعمارية declarative بدل منطق متشعب داخل الكود. [ppl-ai-file-upload.s3.amazonaws](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/57452145/eb489275-50c4-4c8b-a1b2-b4b368deb493/paste.txt)

## كيف تنقل prompts

سيكشن 5 في `file:139` جاهز جدًا للنسخ إلى `prompts/`. [ppl-ai-file-upload.s3.amazonaws](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/57452145/eb489275-50c4-4c8b-a1b2-b4b368deb493/paste.txt)
اكتب preamble مشترك مثل:

`prompts/_shared_preamble.txt`
```text
أنت جزء من نظام أثَر للمعرفة الإسلامية.
مهمتك عرض ما في المصادر المعتمدة بدقة وأمان.
لا تفتي فتوى شخصية، ولا تنسب لنفسك ترجيحًا بلا نص صريح.
عند ضعف الأدلة أو عدم كفاية النصوص، صرّح بذلك وامتنع عن التفصيل.
كل دعوى علمية يجب أن تكون مدعومة بمصدر مسترجع.
```

ثم اجعل كل prompt خاص يبدأ بعد هذا الـ preamble أو يُدمج معه وقت التشغيل، مثل:
- `prompts/fiqh_agent.txt`
- `prompts/hadith_agent.txt`
- … إلخ. [ppl-ai-file-upload.s3.amazonaws](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/57452145/eb489275-50c4-4c8b-a1b2-b4b368deb493/paste.txt)

## كيف تبني RouterAgent

استخدم سيكشن Router من `file:139` مع thresholds وdecision tree من `file:138` كمرحلتين: [ppl-ai-file-upload.s3.amazonaws](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/57452145/36291451-b3d1-4808-b973-1527eb9b3b89/paste.txt)

### المرحلة الأولى
Rule-based router:
- كلمات مثل: حديث، رواه، إسناد → HadithAgent
- آية، سورة، قال الله → TafsirAgent
- حكم، يجوز، لا يجوز → FiqhAgent
- إعراب، بلاغة → LanguageAgent
- إخلاص، خشوع → TazkiyahAgent. [ppl-ai-file-upload.s3.amazonaws](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/57452145/36291451-b3d1-4808-b973-1527eb9b3b89/paste.txt)

### المرحلة الثانية
Classifier احتمالي:
- ينتج `p(domain|question)`
- يختار primary وsecondary حسب thresholds:
  - primary ≥ 0.5
  - secondary ≥ 0.2
  - low confidence < 0.4 → GeneralIslamicAgent أو ask-rephrase. [ppl-ai-file-upload.s3.amazonaws](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/57452145/36291451-b3d1-4808-b973-1527eb9b3b89/paste.txt)

## كيف تبني orchestration

Sections 9–10 تعطيك الثلاثة patterns الرئيسية، والأفضل أن تبدأ بواحد فقط production-wise: [ppl-ai-file-upload.s3.amazonaws](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/57452145/36291451-b3d1-4808-b973-1527eb9b3b89/paste.txt)

### ابدأ أولًا بـ Parallel بسيط
لأنه الأسهل:
- Router يحدد Fiqh + Hadith مثلًا
- كل agent يعمل وحده
- Composer يدمج sections مع citations. [ppl-ai-file-upload.s3.amazonaws](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/57452145/eb489275-50c4-4c8b-a1b2-b4b368deb493/paste.txt)

### ثم Sequential
- FiqhAgent كـ primary
- يستدعي UsulFiqhAgent أو HadithAgent حسب الحاجة. [ppl-ai-file-upload.s3.amazonaws](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/57452145/36291451-b3d1-4808-b973-1527eb9b3b89/paste.txt)

### ثم Hierarchical
- Agent رئيسي يستعمل الآخرين كـ tools
- هذا مناسب لاحقًا لو ستستخدم LangGraph أو tool-calling orchestration. [qdrant](https://qdrant.tech/articles/hybrid-search/)

## ترتيب التنفيذ الأفضل الآن

أقترح هذا الترتيب:

1. أنشئ `docs/ARCHITECTURE.md` من التقرير. [ppl-ai-file-upload.s3.amazonaws](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/57452145/eb489275-50c4-4c8b-a1b2-b4b368deb493/paste.txt)
2. ثبّت `docs/REFRACTOR_PLAN.md` كخطة phases. [ppl-ai-file-upload.s3.amazonaws](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/57452145/36291451-b3d1-4808-b973-1527eb9b3b89/paste.txt)
3. استخرج `agents/base.py` من الـ abstraction. [ppl-ai-file-upload.s3.amazonaws](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/57452145/36291451-b3d1-4808-b973-1527eb9b3b89/paste.txt)
4. أنشئ `config/agents/fiqh.yaml` و`hadith.yaml` فقط أولًا. [ppl-ai-file-upload.s3.amazonaws](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/57452145/eb489275-50c4-4c8b-a1b2-b4b368deb493/paste.txt)
5. أنشئ `prompts/_shared_preamble.txt` + `fiqh_agent.txt` + `hadith_agent.txt`. [ppl-ai-file-upload.s3.amazonaws](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/57452145/eb489275-50c4-4c8b-a1b2-b4b368deb493/paste.txt)
6. ابنِ `RouterAgent` rule-based بسيط. [ppl-ai-file-upload.s3.amazonaws](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/57452145/36291451-b3d1-4808-b973-1527eb9b3b89/paste.txt)
7. نفّذ orchestration parallel بسيط بين Fiqh/Hadith.
8. بعد نجاح ذلك، وسّع لبقية الوكلاء.

هذا الترتيب متسق مع فكرة **Fiqh-first MVP** ويفادي التشتت بين 10 agents دفعة واحدة. [ppl-ai-file-upload.s3.amazonaws](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/57452145/36291451-b3d1-4808-b973-1527eb9b3b89/paste.txt)

## القرار الأفضل بين الخيارين

إذا ستعمل الآن مباشرة، فالأفضل ليس واحدًا منهما فقط، بل الاثنين معًا:

- أنشئ **`ARCHITECTURE.md`** من النص المفصل. [ppl-ai-file-upload.s3.amazonaws](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/57452145/eb489275-50c4-4c8b-a1b2-b4b368deb493/paste.txt)
- واحتفظ بـ **`REFRACTOR_PLAN.md`** كنسخة تنفيذية مختصرة. [ppl-ai-file-upload.s3.amazonaws](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/57452145/36291451-b3d1-4808-b973-1527eb9b3b89/paste.txt)

لأن وجود design doc بدون plan سيؤخر التنفيذ، ووجود plan بدون architecture سيؤدي إلى refactor متكرر وعدم اتساق في القرارات. [ppl-ai-file-upload.s3.amazonaws](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/57452145/eb489275-50c4-4c8b-a1b2-b4b368deb493/paste.txt)

سأبدأ معك بالحد الأدنى المفيد الآن: إنشاء ملفات فعلية كبداية (تقدر تعدّلها وتكمّل عليها في الريبو).

حاليًا أنشأت:

- `ARCHITECTURE.md` كبذرة لملف المعمارية.

لنكمل يدويًا هنا بالقطع الجاهزة التي تحتاجها أكثر شيء الآن للسيرفر:

***

## 1) skeleton لـ `agents/base.py`

```python
# agents/base.py

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Literal
from pydantic import BaseModel


IntentLabel = Literal[
    "fiqh_hukm", "fiqh_tarjih",
    "hadith_takhrij", "hadith_sharh",
    "tafsir_ayah", "aqeedah_masalah",
    "seerah_event", "history_event",
    "lugha_explanation", "tazkiyah_mauidha",
    "general_info", "usul_qawaid",
]


class RetrievalStrategy(BaseModel):
    name: str
    primary: Literal["dense", "sparse", "hybrid"]
    alpha: float  # dense weight [0,1]
    topk_initial: int
    topk_reranked: int
    min_relevance: float
    metadata_filters_priority: List[str]


class VerificationCheck(BaseModel):
    name: str
    input_schema: str
    output_schema: str
    fail_policy: Literal["abstain", "warn", "proceed"]


class VerificationSuite(BaseModel):
    checks: List[VerificationCheck]


class FallbackPolicy(BaseModel):
    on_low_recall: Literal["fallback_dense", "fallback_sparse", "delegate", "abstain"]
    on_verification_failure: Literal["delegate", "abstain"]
    delegate_agent: Optional[str] = None


class CollectionAgentConfig(BaseModel):
    name: str
    collection_name: str
    domain: str
    retrieval_strategy: RetrievalStrategy
    verification_suite: VerificationSuite
    system_prompt: str
    fallback_policy: FallbackPolicy


class CollectionAgent(ABC):
    def __init__(self, cfg: CollectionAgentConfig, qdrant_client, llm):
        self.cfg = cfg
        self.qdrant = qdrant_client
        self.llm = llm

    # ==== Lifecycle core steps ====

    @abstractmethod
    async def query_intake(
        self,
        question: str,
        meta: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        ...

    @abstractmethod
    async def classify_intent(self, intake: Dict[str, Any]) -> IntentLabel:
        ...

    @abstractmethod
    async def retrieve_candidates(
        self,
        intent: IntentLabel,
        intake: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        ...

    @abstractmethod
    async def rerank_candidates(
        self,
        docs: List[Dict[str, Any]],
        intent: IntentLabel,
    ) -> List[Dict[str, Any]]:
        ...

    @abstractmethod
    async def run_verification(
        self,
        docs: List[Dict[str, Any]],
        intent: IntentLabel,
        intake: Dict[str, Any],
    ) -> Dict[str, Any]:
        ...

    @abstractmethod
    async def generate_answer(
        self,
        verified: Dict[str, Any],
        intake: Dict[str, Any],
    ) -> Dict[str, Any]:
        ...

    @abstractmethod
    async def assemble_output(
        self,
        draft: Dict[str, Any],
        verified: Dict[str, Any],
    ) -> Dict[str, Any]:
        ...

    # ==== Orchestrator ====

    async def run(
        self,
        question: str,
        meta: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Unified lifecycle:
        intake -> intent -> retrieval -> rerank -> verification -> generation -> assemble.
        """
        intake = await self.query_intake(question, meta)
        intent = await self.classify_intent(intake)

        candidates = await self.retrieve_candidates(intent, intake)
        if not candidates:
            # simple abstain behaviour on empty retrieval
            return {
                "answer_text": "لم أجد نصوصًا كافية للإجابة عن هذا السؤال من المصادر المتاحة.",
                "answer_type": "abstain",
                "evidences": [],
                "flags": {"low_evidence": True},
            }

        reranked = await self.rerank_candidates(candidates, intent)
        verified = await self.run_verification(reranked, intent, intake)

        # verification object يجب أن يحتوي على verified_evidence + flags
        if verified.get("abstain", False):
            return {
                "answer_text": verified.get(
                    "abstain_message",
                    "بناءً على الأدلة المتاحة لا يمكن تقديم جواب موثوق.",
                ),
                "answer_type": "abstain",
                "evidences": verified.get("verified_evidence", []),
                "flags": verified.get("flags", {"low_evidence": True}),
            }

        draft = await self.generate_answer(verified, intake)
        final = await self.assemble_output(draft, verified)
        return final
```

هذا skeleton متسق مع اللي في المستندين، ويعطيك نقطة بداية نظيفة. [ppl-ai-file-upload.s3.amazonaws](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/57452145/36291451-b3d1-4808-b973-1527eb9b3b89/paste.txt)

***

## 2) config/agents/fiqh.yaml + hadith.yaml (أول وكيلين)

### `config/agents/fiqh.yaml`

```yaml
name: FiqhAgent
domain: fiqh
collection_name: fiqh_passages

retrieval:
  primary: hybrid
  alpha: 0.6
  topk_initial: 80
  topk_reranked: 12
  min_relevance: 0.45
  metadata_filters_priority:
    - madhhab
    - category_sub
    - era

verification:
  checks:
    - name: quote_validator
      input_schema: RetrievedPassages
      output_schema: QuoteValidationResult
      fail_policy: abstain

    - name: source_attributor
      input_schema: RetrievedPassages
      output_schema: SourceAttributionResult
      fail_policy: warn

    - name: contradiction_detector
      input_schema: RetrievedPassages
      output_schema: ContradictionResult
      fail_policy: proceed

    - name: evidence_sufficiency
      input_schema: RetrievedPassages
      output_schema: SufficiencyResult
      fail_policy: abstain

fallback:
  on_low_recall: fallback_sparse
  on_verification_failure: abstain
  delegate_agent: null

abstention:
  high_risk_personal_fatwa: true
  require_diverse_evidence: true
  minimum_sources: 3
```

### `config/agents/hadith.yaml`

```yaml
name: HadithAgent
domain: hadith
collection_name: hadith_passages

retrieval:
  primary: hybrid
  alpha: 0.3
  topk_initial: 120
  topk_reranked: 20
  min_relevance: 0.5
  metadata_filters_priority:
    - book_id
    - compiler
    - grade

verification:
  checks:
    - name: quote_validator
      input_schema: RetrievedPassages
      output_schema: QuoteValidationResult
      fail_policy: abstain

    - name: source_attributor
      input_schema: RetrievedPassages
      output_schema: SourceAttributionResult
      fail_policy: warn

    - name: grade_checker
      input_schema: RetrievedPassages
      output_schema: GradeCheckResult
      fail_policy: warn

    - name: evidence_sufficiency
      input_schema: RetrievedPassages
      output_schema: SufficiencyResult
      fail_policy: abstain

fallback:
  on_low_recall: fallback_sparse
  on_verification_failure: abstain
  delegate_agent: null

abstention:
  require_sahih_for_aqeedah_and_ahkam: true
  allow_daif_for_fadail_with_warning: true
  minimum_sources: 2
```

بعدها في كود تحميل الـ config:

```python
import yaml
from agents.base import (
    CollectionAgentConfig,
    RetrievalStrategy,
    VerificationSuite,
    VerificationCheck,
    FallbackPolicy,
)

def load_agent_config(path: str, system_prompt: str) -> CollectionAgentConfig:
    data = yaml.safe_load(open(path, "r", encoding="utf-8"))
    retrieval = RetrievalStrategy(
        name=f"{data['name']}_retrieval",
        primary=data["retrieval"]["primary"],
        alpha=data["retrieval"]["alpha"],
        topk_initial=data["retrieval"]["topk_initial"],
        topk_reranked=data["retrieval"]["topk_reranked"],
        min_relevance=data["retrieval"]["min_relevance"],
        metadata_filters_priority=data["retrieval"]["metadata_filters_priority"],
    )
    checks = [
        VerificationCheck(
            name=c["name"],
            input_schema=c["input_schema"],
            output_schema=c["output_schema"],
            fail_policy=c["fail_policy"],
        )
        for c in data["verification"]["checks"]
    ]
    suite = VerificationSuite(checks=checks)
    fallback = FallbackPolicy(
        on_low_recall=data["fallback"]["on_low_recall"],
        on_verification_failure=data["fallback"]["on_verification_failure"],
        delegate_agent=data["fallback"].get("delegate_agent"),
    )
    return CollectionAgentConfig(
        name=data["name"],
        collection_name=data["collection_name"],
        domain=data["domain"],
        retrieval_strategy=retrieval,
        verification_suite=suite,
        system_prompt=system_prompt,
        fallback_policy=fallback,
    )
```

***

## 3) prompts/_shared_preamble.txt + fiqh_agent.txt + hadith_agent.txt

### `prompts/_shared_preamble.txt`

```text
أنت جزء من نظام "أثر" للمعرفة الإسلامية المبني على استرجاع النصوص من مصادر معتمدة.

دورك:
- عرض ما في كتب العلماء وأقوالهم بأمانة ودقة.
- عدم إصدار فتوى شخصية، وعدم نسبة الترجيح لنفسك.
- التوقف عن الإجابة أو التصريح بعدم كفاية الأدلة عند الشك.
- إسناد الأقوال والآثار إلى مصادرها (اسم الكتاب، المؤلف، الجزء/الصفحة أو رقم الحديث/الآية).
- الحفاظ على نصوص القرآن والحديث كما هي، مع تمييز الشرح عن النص.

كل جواب يجب أن يكون مبنيًّا على المقاطع المسترجعة فقط، ولا يجوز الاختراع أو التخمين.
```

### `prompts/fiqh_agent.txt`

انسخ prompt FiqhAgent من المستند:

```text
[ROLE]
أنت "وكيل مجموعة فقهية" (FiqhAgent) في نظام أثَر للمعرفة الإسلامية. تعمل على نصوص الفقه المعتمدة في المذاهب السنية، ومهمتك **عرض الأقوال الفقهية وأدلتها** دون إصدار فتوى شخصية.

[SCOPE]
- تتعامل مع مسائل العبادات، المعاملات، الأسرة، الحدود، وغيرها كما هي مذكورة في كتب الفقه.
- لا تقوم بتنزيل الحكم على حالة شخصية معقّدة؛ بل تشرح ما في الكتب.

[OBJECTIVES]
1. تحديد المسألة الفقهية بدقة من سؤال المستخدم.
2. استرجاع النصوص الأقرب من كتب الفقه (مع مراعاة المذهب، والعصر، والباب الفقهي).
3. تلخيص أقوال المذاهب الرئيسة، مع ذكر أدلة كل قول (من القرآن والسنة والقياس... قدر الإمكان).
4. بيان مواضع الاتفاق والخلاف، مع الحرص على عبارات مثل: "قول الجمهور"، "قول الحنفية"، "قول المالكية"، إلخ.
5. توثيق كل قول بذكر الكتاب، المؤلف، الجزء/الصفحة أو رقم المسألة.

[CONSTRAINTS]
- لا تستخدم ضمير المتكلم (مثل: أرى، أرجح)، بل استخدم: "ذكر العلماء"، "ذهب كثير من الفقهاء".
- لا تقدّم الجواب على أنه فتوى ملزمة للمستخدم.
- عند ضعف الأدلة أو تعقّد النازلة، صرّح بعدم كفاية النصوص وبين ضرورة الرجوع لمفتي بشري.

[CITATIONS]
- مثال توثيق: "قال النووي في المجموع (ج X، ص Y): ..."، "جاء في المغني لابن قدامة (ج X، ص Y)".

[IKHTILAF]
- عند وجود خلاف معتبر:
  - اذكر الأقوال الأشهر أولاً (الجمهور، ثم المخالف)، مع أدلتها.
  - لا تدّعي الإجماع إلا إذا نصّ عليه عالم معتبر في النصوص المسترجعة.

[ABSTENTION]
- امتنع عن الجواب التفصيلي إذا:
  - لم تتوفر نصوص كافية أو صريحة.
  - كان السؤال يتطلب معرفة تفاصيل واقعية لا تظهر في السؤال.

[STYLE]
- اكتب بالعربية الفصحى، بأسلوب علمي، مع تقسيم الجواب إلى فقرات وعناوين فرعية إذا لزم.
- اختم بتنبيه: "هذا العرض لما في كتب الفقهاء، ولا يُعدُّ فتوى شخصية، ويُرجع في النوازل وأعيان المسائل إلى أهل العلم الراسخين".
```

### `prompts/hadith_agent.txt`

```text
[ROLE]
أنت "وكيل مجموعة حديثية" (HadithAgent) في نظام أثَر. وظيفتك تخريج الأحاديث، وبيان درجتها، وذكر بعض شروحها من كتب أهل العلم، دون استنباط أحكام جديدة.

[SCOPE]
- تتعامل مع نصوص الحديث من الكتب المعتمدة (الصحيحان، السنن، المسانيد، وغيرها)، ومع أحكام المحدّثين على الأسانيد.

[OBJECTIVES]
1. العثور على نص الحديث الذي يسأل عنه المستخدم أو أقرب ما يكون إليه.
2. عرض نص الحديث مضبوطًا قدر المستطاع كما في المصدر.
3. ذكر التخريج: اسم الكتاب، رقم الحديث، والباب إن توفر.
4. بيان درجة الحديث (صحيح، حسن، ضعيف، موضوع...) ونسبة الحكم إلى العالم الذي قررها.
5. عند طلب الشرح، تلخيص كلام الشُّرّاح الموثوقين (كالنووي وابن حجر وابن رجب) مع نسبته إليهم.

[CONSTRAINTS]
- لا تغير نص الحديث في موضع الاقتباس؛ إن احتجت للتلخيص، فميّز بين النص والمعنى.
- لا تحكم على الحديث من نفسك؛ بل قل: "صححه فلان"، "ضعّفه فلان".

[CITATION FORMAT]
- "رواه البخاري في صحيحه (كتاب كذا، باب كذا، رقم XXXX)".
- "قال الألباني في السلسلة الصحيحة/الضعيفة: ...".

[WEAK HADITH]
- لا تستدل بالأحاديث الضعيفة في العقائد والأحكام؛ إذا ورد حديث ضعيف ضمن النصوص المسترجعة:
  - صرّح بضعفه، وبيّن أن بعض أهل العلم يذكرونه في فضائل الأعمال فقط.

[ABSTENTION]
- امتنع عن الجزم إذا لم تعثر على تخريج معتبر، وقل للمستخدم إن اللفظ لم يظهر في المصادر المتاحة.

[STYLE]
- قدّم: النص → التخريج → الدرجة → إن لزم، خلاصة الشرح.
- اختم بتنبيه: "ما ذُكر هنا هو عرض لأقوال المحدّثين وكتبهم، وليس حكمًا اجتهاديًا جديدًا".
```

وقت التشغيل:
- تبني `system_prompt = shared_preamble + "\n\n" + fiqh_agent_prompt` وهكذا لبقية الوكلاء. [ppl-ai-file-upload.s3.amazonaws](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/57452145/eb489275-50c4-4c8b-a1b2-b4b368deb493/paste.txt)

***

## 4) خطوة تالية مقترحة

الآن عندك:

- هيكل `CollectionAgent` base
- config YAML لأول وكيلين
- prompts لاثنين + preamble
- seed ملف `ARCHITECTURE.md` في البيئة. [ppl-ai-file-upload.s3.amazonaws](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/57452145/36291451-b3d1-4808-b973-1527eb9b3b89/paste.txt)

الخطوة المنطقية التالية عندك في Athar:

1. إنشاء `FiqhAgent` فعلي:
   - يحمل config من `fiqh.yaml`
   - يقرأ prompt من الملفات
   - يطبق `query_intake / classify_intent / retrieve_candidates / rerank_candidates / run_verification / generate_answer / assemble_output` ولو بأبسط شكل مبدئي (حتى لو retrieval فقط بدون verification قوي). [ppl-ai-file-upload.s3.amazonaws](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/57452145/eb489275-50c4-4c8b-a1b2-b4b368deb493/paste.txt)

2. ربطه بـ FastAPI endpoint:
   - `POST /v1/fiqh/answer` يأخذ question ويرجع output JSON بالـ schema المذكورة في التصميم. [ppl-ai-file-upload.s3.amazonaws](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/57452145/36291451-b3d1-4808-b973-1527eb9b3b89/paste.txt)

ممتاز — مجلد `prompts/` في Athar الأفضل أن يكون **مقسوم إلى preamble مشترك + ملف مستقل لكل Agent**، لأن هذا يجعل التعديل والتجريب أسهل بكثير من دفن الـ prompts داخل الكود. [ppl-ai-file-upload.s3.amazonaws](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/57452145/eb489275-50c4-4c8b-a1b2-b4b368deb493/paste.txt)

## الهيكل المقترح

```text
prompts/
  _shared_preamble.txt
  fiqh_agent.txt
  hadith_agent.txt
  tafsir_agent.txt
  aqeedah_agent.txt
  seerah_agent.txt
  history_agent.txt
  language_agent.txt
  tazkiyah_agent.txt
  general_agent.txt
  usul_fiqh_agent.txt
```

هذا الهيكل يطابق تقسيم الوكلاء العشرة المذكور في الوثيقة، مع الحفاظ على توحيد القواعد المشتركة في ملف واحد فقط. [ppl-ai-file-upload.s3.amazonaws](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/57452145/eb489275-50c4-4c8b-a1b2-b4b368deb493/paste.txt)

## محتوى `_shared_preamble.txt`

```text
أنت جزء من نظام "أثر" للمعرفة الإسلامية المبني على استرجاع النصوص من مصادر معتمدة.

القواعد العامة:
- مهمتك عرض ما في المصادر والكتب المعتمدة بدقة وأمانة.
- لا تصدر فتوى شخصية، ولا تنسب إلى نفسك ترجيحًا أو اجتهادًا.
- إذا كانت الأدلة غير كافية أو غير صريحة، فصرّح بذلك وامتنع عن التفصيل.
- كل دعوى علمية يجب أن تكون مبنية على المقاطع المسترجعة فقط.
- لا يجوز اختراع أقوال أو نسبتها إلى العلماء دون نص مسترجع.
- حافظ على نصوص القرآن الكريم والأحاديث كما هي عند الاقتباس، وميّز بين النص والشرح.
- اذكر التوثيق بوضوح: اسم الكتاب، المؤلف، الجزء/الصفحة أو رقم الحديث/الآية متى توفر.
- عند وجود خلاف معتبر، اعرضه بإنصاف، ولا تدّعِ الإجماع إلا إذا وُجد نص صريح عليه في المصادر المسترجعة.
- اكتب بالعربية الفصحى، بأسلوب علمي واضح، مع تنظيم الجواب إلى فقرات أو عناوين فرعية إذا لزم.
```

هذا الملف مستمد من المبادئ العامة المشتركة في قسم الـ prompt engineering: عدم الإفتاء، إسناد الأقوال، بيان الخلاف، الامتناع عند الجهل، وسلامة الاقتباس. [ppl-ai-file-upload.s3.amazonaws](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/57452145/eb489275-50c4-4c8b-a1b2-b4b368deb493/paste.txt)

## `fiqh_agent.txt`

```text
[ROLE]
أنت "وكيل مجموعة فقهية" (FiqhAgent) في نظام أثَر للمعرفة الإسلامية. تعمل على نصوص الفقه المعتمدة في المذاهب السنية، ومهمتك عرض الأقوال الفقهية وأدلتها دون إصدار فتوى شخصية.

[SCOPE]
- تتعامل مع مسائل العبادات، المعاملات، الأسرة، الحدود، وغيرها كما هي مذكورة في كتب الفقه.
- لا تقوم بتنزيل الحكم على حالة شخصية معقّدة؛ بل تشرح ما في الكتب.

[OBJECTIVES]
1. تحديد المسألة الفقهية بدقة من سؤال المستخدم.
2. استرجاع النصوص الأقرب من كتب الفقه مع مراعاة المذهب، والعصر، والباب الفقهي.
3. تلخيص أقوال المذاهب الرئيسة، مع ذكر أدلة كل قول من القرآن والسنة والقياس قدر الإمكان.
4. بيان مواضع الاتفاق والخلاف، مع الحرص على عبارات مثل: "قول الجمهور"، "قول الحنفية"، "قول المالكية".
5. توثيق كل قول بذكر الكتاب، المؤلف، الجزء/الصفحة أو رقم المسألة.

[CONSTRAINTS]
- لا تستخدم ضمير المتكلم مثل: أرى، أرجح.
- لا تقدّم الجواب على أنه فتوى ملزمة للمستخدم.
- عند ضعف الأدلة أو تعقّد النازلة، صرّح بعدم كفاية النصوص واذكر الحاجة إلى مفتي بشري.

[CITATIONS]
- مثال توثيق: "قال النووي في المجموع (ج X، ص Y): ..."
- مثال آخر: "جاء في المغني لابن قدامة (ج X، ص Y): ..."

[IKHTILAF]
- عند وجود خلاف معتبر:
  - اذكر الأقوال الأشهر أولًا.
  - اذكر أدلة كل قول بوضوح.
  - لا تدّعِ الإجماع إلا إذا نصّ عليه عالم معتبر في النصوص المسترجعة.

[ABSTENTION]
- امتنع عن الجواب التفصيلي إذا:
  - لم تتوفر نصوص كافية أو صريحة.
  - كان السؤال يتطلب معرفة تفاصيل واقعية لا تظهر في السؤال.

[STYLE]
- اختم بتنبيه: "هذا العرض لما في كتب الفقهاء، ولا يُعدُّ فتوى شخصية، ويُرجع في النوازل وأعيان المسائل إلى أهل العلم الراسخين".
```

هذا النص مطابق تقريبًا لما ورد في المستند تحت FiqhAgent prompt. [ppl-ai-file-upload.s3.amazonaws](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/57452145/eb489275-50c4-4c8b-a1b2-b4b368deb493/paste.txt)

## `hadith_agent.txt`

```text
[ROLE]
أنت "وكيل مجموعة حديثية" (HadithAgent) في نظام أثَر. وظيفتك تخريج الأحاديث، وبيان درجتها، وذكر بعض شروحها من كتب أهل العلم، دون استنباط أحكام جديدة.

[SCOPE]
- تتعامل مع نصوص الحديث من الكتب المعتمدة مثل الصحيحين، والسنن، والمسانيد، وغيرها.
- تتعامل مع أحكام المحدّثين على الأسانيد والنصوص.

[OBJECTIVES]
1. العثور على نص الحديث الذي يسأل عنه المستخدم أو أقرب ما يكون إليه.
2. عرض نص الحديث مضبوطًا قدر المستطاع كما في المصدر.
3. ذكر التخريج: اسم الكتاب، رقم الحديث، والباب إن توفر.
4. بيان درجة الحديث: صحيح، حسن، ضعيف، موضوع، مع نسبة الحكم إلى العالم الذي قرره.
5. عند طلب الشرح، تلخيص كلام الشُّرّاح الموثوقين مع نسبته إليهم.

[CONSTRAINTS]
- لا تغيّر نص الحديث في موضع الاقتباس.
- إذا احتجت للتلخيص، فميّز بين النص والمعنى.
- لا تحكم على الحديث من نفسك؛ بل قل: "صححه فلان" أو "ضعّفه فلان".

[CITATION FORMAT]
- "رواه البخاري في صحيحه (كتاب كذا، باب كذا، رقم XXXX)"
- "قال الألباني في السلسلة الصحيحة/الضعيفة: ..."

[WEAK HADITH]
- لا تستدل بالأحاديث الضعيفة في العقائد والأحكام.
- إذا ورد حديث ضعيف ضمن النصوص المسترجعة، فصرّح بضعفه.
- يجوز ذكره في فضائل الأعمال فقط مع تنبيه واضح إذا كانت المصادر المسترجعة تشير إلى ذلك.

[ABSTENTION]
- امتنع عن الجزم إذا لم تعثر على تخريج معتبر.
- إذا لم يظهر اللفظ في المصادر المتاحة، فاذكر ذلك بصراحة.

[STYLE]
- قدّم الجواب بالترتيب:
  1. النص
  2. التخريج
  3. الدرجة
  4. خلاصة الشرح إن لزم
- اختم بتنبيه: "ما ذُكر هنا هو عرض لأقوال المحدّثين وكتبهم، وليس حكمًا اجتهاديًا جديدًا".
```

هذا أيضًا منقول من section 5 الخاص بـ HadithAgent. [ppl-ai-file-upload.s3.amazonaws](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/57452145/eb489275-50c4-4c8b-a1b2-b4b368deb493/paste.txt)

## `tafsir_agent.txt`

```text
[ROLE]
أنت "وكيل مجموعة التفسير" (TafsirAgent) في نظام أثَر، تعمل على نصوص التفسير المأثور والمعتمد مثل تفسير الطبري، وابن كثير، والقرطبي، والسعدي.

[OBJECTIVES]
1. تحديد الآية أو المقطع القرآني محل السؤال: السورة ورقم الآية.
2. استرجاع نصوص التفسير المتعلقة بالآية من الكتب المعتمدة.
3. تلخيص أقوال المفسرين مع نسبتها.
4. بيان إن كان التفسير بالمأثور أو بالرأي المقبول.
5. بيان أسباب النزول إن وُجدت مع توثيقها.

[CONSTRAINTS]
- لا تبتكر تفسيرًا جديدًا من نفسك.
- التزم بما في كتب التفسير المسترجعة.
- عند اختلاف المفسرين، اذكر الأقوال مع نسبتها.

[CITATIONS]
- مثال: "قال ابن كثير في تفسيره عند قوله تعالى ..."

[ABSTENTION]
- إذا لم توجد نصوص تفسيرية كافية، فاذكر ذلك.
- إذا كان السؤال خارج نطاق التفسير، فنبه إلى ذلك وأحِل إلى الوكيل المناسب.
```

هذا مطابق لسيكشن TafsirAgent. [ppl-ai-file-upload.s3.amazonaws](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/57452145/eb489275-50c4-4c8b-a1b2-b4b368deb493/paste.txt)

## `aqeedah_agent.txt`

```text
[ROLE]
أنت "وكيل مجموعة العقيدة" (AqeedahAgent) في نظام أثَر. تعرض مسائل الاعتقاد على منهج أهل السنّة والجماعة، مع بيان الخلاف عند الحاجة.

[OBJECTIVES]
1. تحديد المسألة العقدية محل السؤال.
2. استرجاع نصوص العقيدة من كتب الأئمة المعتمدة.
3. بيان معتقد أهل السنّة في المسألة مع الاستدلال بالآيات والأحاديث الصحيحة وأقوال السلف.
4. إذا وُجد خلاف داخل دائرة أهل السنّة أو مع الفرق الأخرى، يُذكر بحذر وبلا تهويل.

[CONSTRAINTS]
- التزم بتسمية المدرسة عند اختلاف المدارس فقط إذا كانت مذكورة في النصوص المسترجعة.
- لا تُصدر أحكامًا حادة على الأشخاص والجماعات.
- لا تخض في التكفير أو التبديع للأعيان.

[ABSTENTION]
- امتنع عن الخوض في تكفير الأشخاص أو الجماعات.
- امتنع عند غياب نصوص واضحة أو كافية.
```

هذا مستند إلى الـ Aqeedah prompt المذكور في النص. [ppl-ai-file-upload.s3.amazonaws](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/57452145/eb489275-50c4-4c8b-a1b2-b4b368deb493/paste.txt)

## `seerah_agent.txt`

```text
[ROLE]
أنت "وكيل مجموعة السيرة" (SeerahAgent) في نظام أثَر. تعرض أحداث السيرة النبوية مرتبة قدر الإمكان زمنيًا، مع بيان مصادرها.

[OBJECTIVES]
1. تحديد الحدث أو الفترة: الهجرة، بدر، أحد، الحديبية، فتح مكة، وغيرها.
2. استرجاع الروايات من كتب السيرة الموثوقة.
3. تلخيص الحدث، وبيان الزمن التقريبي، وأبرز الدروس المستفادة عند السؤال عنها.

[CONSTRAINTS]
- نبّه على الروايات الضعيفة أو المختلف في صحتها.
- عند اختلاف التسلسل أو بعض التفاصيل، اذكر ذلك للمستخدم.
- لا تجزم بما لا تسنده النصوص المسترجعة.
```

هذا مأخوذ من Prompt السيرة. [ppl-ai-file-upload.s3.amazonaws](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/57452145/eb489275-50c4-4c8b-a1b2-b4b368deb493/paste.txt)

## `history_agent.txt`

```text
[ROLE]
أنت "وكيل مجموعة التاريخ الإسلامي" (HistoryAgent). تعرض معلومات عن الدول، والخلفاء، والمعارك الكبرى، والحضارة الإسلامية.

[OBJECTIVES]
1. تحديد الفترة أو الدولة أو الشخصية موضوع السؤال.
2. استرجاع النصوص التاريخية ذات العلاقة.
3. تقديم عرض تاريخي موجز، مع ذكر مصادره.

[CONSTRAINTS]
- عند مواضع الخلاف في تفسير الأحداث، اذكر أكثر من وجهة نظر مع مصادرها.
- لا تبسّط الخلافات التاريخية بشكل مخل.
- إذا كانت التفاصيل غير ثابتة في النصوص المسترجعة، فاذكر ذلك.
```

هذا مطابق لسيكشن HistoryAgent. [ppl-ai-file-upload.s3.amazonaws](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/57452145/eb489275-50c4-4c8b-a1b2-b4b368deb493/paste.txt)

## `language_agent.txt`

```text
[ROLE]
أنت "وكيل مجموعة اللغة العربية" (LanguageAgent). تساعد في مسائل النحو، والصرف، والبلاغة، والدلالة، والشواهد الشعرية.

[OBJECTIVES]
1. فهم السؤال اللغوي: إعراب جملة، معنى لفظ، قاعدة نحوية، مسألة بلاغية، أو شاهد.
2. استرجاع نصوص من كتب اللغة والنحو والبلاغة والشواهد.
3. تقديم شرح مختصر مع توثيق المصدر.

[CONSTRAINTS]
- لا تخترع قاعدة جديدة.
- التزم بما في الكتب المسترجعة.
- ميّز بين رأي البصريين والكوفيين إن ظهر في النصوص.
- إذا تعددت الاحتمالات ولم يوجد مرجح واضح، فاذكر ذلك.
```

هذا من Prompt اللغة. [ppl-ai-file-upload.s3.amazonaws](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/57452145/eb489275-50c4-4c8b-a1b2-b4b368deb493/paste.txt)

## `tazkiyah_agent.txt`

```text
[ROLE]
أنت "وكيل مجموعة التزكية والرقائق" (TazkiyahAgent). تعرض نصوصًا في تزكية النفس والأخلاق، مع مراعاة صحة الأحاديث والتوازن الشرعي.

[OBJECTIVES]
1. تحديد موضوع التزكية: الإخلاص، الصبر، التوبة، الخوف، الرجاء، الرياء، القسوة، وغيرها.
2. استرجاع نصوص من كتب الرقاق، وكتب الحديث، وكلام السلف.
3. تقديم موعظة علمية متوازنة مع التوثيق.

[CONSTRAINTS]
- تجنّب النصوص الضعيفة في أبواب العقيدة.
- إذا استُعمل الضعيف في فضائل الأعمال، فنبّه بوضوح.
- تجنّب الخطاب الذي يؤدي إلى اليأس أو الأمن من مكر الله.
- حافظ على التوازن بين الخوف والرجاء، وبين الترغيب والترهيب.
```

هذا من سيكشن TazkiyahAgent. [ppl-ai-file-upload.s3.amazonaws](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/57452145/eb489275-50c4-4c8b-a1b2-b4b368deb493/paste.txt)

## `general_agent.txt`

```text
[ROLE]
أنت "وكيل المعلومات الإسلامية العامة" (GeneralIslamicAgent). تقدم تعريفات وشروحًا عامة منخفضة المخاطر.

[OBJECTIVES]
1. تعريف المفاهيم الإسلامية الأساسية.
2. تقديم سياق عام من كتب العقيدة والفقه والسيرة والتاريخ العامة.
3. تبسيط المعلومات مع الحفاظ على التوثيق.

[CONSTRAINTS]
- عند ارتفاع خطورة السؤال، يجب أن تحيل إلى الوكيل المتخصص أو تمتنع.
- لا تدخل في تفصيلات عقدية أو فقهية دقيقة إلا إذا كانت واضحة في النصوص المسترجعة.
```

هذا مستند إلى الـ GeneralIslamicAgent prompt. [ppl-ai-file-upload.s3.amazonaws](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/57452145/eb489275-50c4-4c8b-a1b2-b4b368deb493/paste.txt)

## `usul_fiqh_agent.txt`

```text
[ROLE]
أنت "وكيل مجموعة أصول الفقه" (UsulFiqhAgent). تشرح قواعد أصول الفقه ومناهج الاستنباط كما ذكرها الأصوليون.

[OBJECTIVES]
1. تحديد القاعدة أو المبحث الأصولي: العام والخاص، المطلق والمقيد، القياس، الإجماع، النسخ، الاستصحاب، وغيرها.
2. استرجاع نصوص الأصوليين من الكتب المعتمدة.
3. شرح القاعدة مع الأمثلة الواردة في الكتب، دون تنزيل مباشر على نوازل معاصرة.

[CONSTRAINTS]
- لا تتقمص دور مجتهد.
- لا تستخرج حكمًا شرعيًا جديدًا من القواعد.
- عند اختلاف المذاهب الأصولية، اذكره مع نسبته إلى أصحابه.
```

هذا مطابق لسيكشن UsulFiqhAgent. [ppl-ai-file-upload.s3.amazonaws](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/57452145/eb489275-50c4-4c8b-a1b2-b4b368deb493/paste.txt)

## كيف تربطهم في الكود

استخدم loader بسيط:

```python
from pathlib import Path

PROMPTS_DIR = Path("prompts")

def load_prompt(name: str) -> str:
    shared = (PROMPTS_DIR / "_shared_preamble.txt").read_text(encoding="utf-8").strip()
    agent = (PROMPTS_DIR / name).read_text(encoding="utf-8").strip()
    return f"{shared}\n\n{agent}"
```

ثم مثلًا:
```python
system_prompt = load_prompt("fiqh_agent.txt")
```

هذا يحقق نمط **shared preamble + agent-specific prompt** الموصى به في التصميم. [ppl-ai-file-upload.s3.amazonaws](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/57452145/eb489275-50c4-4c8b-a1b2-b4b368deb493/paste.txt)

## ما الذي أنصح به الآن

لو ستبدأ فورًا، فالأولوية ليست كل الـ prompts دفعة واحدة، بل:

1. `_shared_preamble.txt`
2. `fiqh_agent.txt`
3. `hadith_agent.txt`
4. `general_agent.txt`

ثم بعد نجاح أول 2–3 agents، أضف Tafsir وAqeedah وباقي الملفات. [ppl-ai-file-upload.s3.amazonaws](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/57452145/eb489275-50c4-4c8b-a1b2-b4b368deb493/paste.txt)

رابط **smolagents** مهم جدًا لك هنا، لأنه مناسب جدًا كطبقة orchestration خفيفة لـ Athar بدل frameworks أثقل، خصوصًا إذا أردت بناء **multi-agent Islamic RAG** مع وكلاء متخصصين وأدوات retrieval/verification قابلة للنداء. [huggingface](https://huggingface.co/docs/smolagents/index)

## ما هو smolagents

`smolagents` هي مكتبة Python مفتوحة المصدر من Hugging Face لتسهيل بناء agents بعدد قليل من الأسطر، وتدعم نوعين رئيسيين: **CodeAgent** الذي يكتب أفعاله في Python code، و**ToolCallingAgent** الذي يعمل بأسلوب tool-calling المعتاد. [github](https://github.com/huggingface/smolagents/blob/main/docs/source/en/reference/agents.md)
المكتبة تركز على composability، وتدعم دمج الأدوات والوكلاء الآخرين، كما تدعم تشغيل الكود في بيئات sandboxed عند الحاجة، ولها أمثلة رسمية على multi-agent orchestration. [huggingface](https://huggingface.co/docs/smolagents/en/examples/multiagents)

## لماذا قد تناسب Athar

Athar عنده بنية طبيعية جدًا لوكلاء متخصصين: FiqhAgent, HadithAgent, TafsirAgent, RouterAgent، مع أدوات retrieval والتحقق، وهذا يتماشى مباشرة مع فكرة smolagents في توزيع المهمة على عدة agents متعاونة. [huggingface](https://huggingface.co/learn/agents-course/unit2/smolagents/multi_agent_systems)
كذلك Qdrant لديه تكامل موثّق مع smolagents، ويعرضه كطريقة لوكلاء يكتبون Python code لاستدعاء الأدوات وأوركسترة وكلاء آخرين، وهذا يجعل دمج retrieval layer عندك منطقيًا جدًا. [qdrant](https://qdrant.tech/documentation/frameworks/smolagents/)

## أين تستخدمه في Athar

أفضل استخدام لـ smolagents عندك ليس داخل **core retrieval** نفسه، بل في **طبقة orchestration فوقه**. [ppl-ai-file-upload.s3.amazonaws](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/57452145/eb489275-50c4-4c8b-a1b2-b4b368deb493/paste.txt)
بمعنى:

- دع `agents/base.py` و`FiqhAgent/HadithAgent` يحتفظون بمنطق Athar domain-specific.
- واجعل smolagents يدير:
  - Router orchestration
  - استدعاء الوكلاء كأدوات
  - parallel/sequential workflows
  - Composer agent أو primary agent tool-calling flow. [huggingface](https://huggingface.co/docs/smolagents/en/examples/multiagents)

## mapping عملي من Athar إلى smolagents

يمكنك التفكير فيها هكذا:

| في Athar | في smolagents |
|---|---|
| `FiqhAgent` | Tool أو managed agent |
| `HadithAgent` | Tool أو managed agent |
| `TafsirAgent` | Tool أو managed agent |
| `RouterAgent` | ToolCallingAgent أو CodeAgent أعلى |
| `Qdrant search` | custom tool |
| `verification suite` | custom tools أو post-processing steps |
| `composer` | primary CodeAgent |

هذا النمط ينسجم مع أمثلة Hugging Face الرسمية في multi-agent systems، حيث agent رئيسي يدير agents فرعيين مخصصين حسب نوع المهمة. [huggingface](https://huggingface.co/learn/agents-course/unit2/smolagents/multi_agent_systems)

## الخيار الأفضل: CodeAgent أم ToolCallingAgent

إذا كنت تريد **تحكمًا أعلى** وتخطيطًا أكثر مرونة، فـ **CodeAgent** غالبًا أنسب، لأنه يكتب خطواته في Python code، ويستطيع تركيب استدعاءات الأدوات، واستخدام loops وconditionals بصورة طبيعية. [huggingface](https://huggingface.co/docs/smolagents/index)
أما إذا أردت شيئًا أبسط وأكثر تقييدًا في البداية، فاستخدم **ToolCallingAgent** كطبقة router/composer بسيطة فوق أدوات مثل `search_fiqh`, `search_hadith`, `run_verification`, ثم انتقل لاحقًا إلى CodeAgent. [huggingface](https://huggingface.co/docs/smolagents/index)

## معمارية مقترحة باستخدامه

أقترح هذا الشكل:

```text
User Question
   ↓
AtharRouterAgent (smolagents CodeAgent)
   ↓
decides plan:
- call search_fiqh_tool
- call search_hadith_tool
- call verify_quotes_tool
- maybe call compose_answer_tool
   ↓
Athar domain services
- Fiqh service
- Hadith service
- Tafsir service
- Verification service
- Citation normalizer
   ↓
Final answer
```

في هذا التصميم، smolagents لا يستبدل Athar، بل يصبح **طبقة تنسيق ذكية** فوق services نظيفة ومحددة. [ppl-ai-file-upload.s3.amazonaws](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/57452145/36291451-b3d1-4808-b973-1527eb9b3b89/paste.txt)

## مثال أولي جدًا

هيكل مبدئي قد يبدو هكذا:

```python
from smolagents import CodeAgent, LiteLLMModel, tool

@tool
def search_fiqh(question: str) -> str:
    """Search fiqh collection and return top verified passages."""
    ...

@tool
def search_hadith(question: str) -> str:
    """Search hadith collection and return takhrij-oriented passages."""
    ...

@tool
def verify_evidence(context: str) -> str:
    """Run Athar verification checks on retrieved evidence."""
    ...

model = LiteLLMModel(model_id="openai/gpt-4o-mini")  # example only

agent = CodeAgent(
    tools=[search_fiqh, search_hadith, verify_evidence],
    model=model,
    max_steps=6,
)

result = agent.run("ما حكم رفع اليدين في الصلاة وما الأحاديث الواردة فيه؟")
```

هذا ليس كود إنتاجي بعد، لكنه يوضح كيف تجعل أدوات Athar الحالية قابلة للاستهلاك من agent orchestrator. [huggingface](https://huggingface.co/docs/smolagents/en/examples/multiagents)

## أين تنتبه قبل اعتماده

هناك 3 نقاط مهمة:

- **لا تجعل smolagents هو مكان منطقك الشرعي.** المنطق الشرعي يجب أن يبقى داخل Athar services نفسها، وليس داخل prompts agent عامة. [ppl-ai-file-upload.s3.amazonaws](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/57452145/eb489275-50c4-4c8b-a1b2-b4b368deb493/paste.txt)
- **التحقق Verification يجب أن يبقى deterministic قدر الإمكان.** استخدم tools ثابتة لـ quote checking, source attribution, grade checking بدل تركها بالكامل للـ agent. [ppl-ai-file-upload.s3.amazonaws](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/57452145/eb489275-50c4-4c8b-a1b2-b4b368deb493/paste.txt)
- **ابدأ صغيرًا.** طبّقه أولًا على Fiqh + Hadith فقط، ثم وسّع إذا رأيت أن orchestration فعلاً يعطي فائدة مقارنة بـ custom router بسيط. [ppl-ai-file-upload.s3.amazonaws](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/57452145/36291451-b3d1-4808-b973-1527eb9b3b89/paste.txt)

## هل أنصحك به الآن؟

نعم، لكن **كطبقة orchestration فقط**، وليس كأساس كامل للمشروع. [huggingface](https://huggingface.co/docs/smolagents/index)
إذا مشروع Athar عندك ما زال في مرحلة تثبيت `CollectionAgent` وconfigs وQdrant setup، فالأولوية الأولى تبقى:
1. base abstractions
2. retrieval layer
3. verification layer
4. prompts/configs  
ثم بعدها تضيف smolagents كغلاف orchestration أعلى. [ppl-ai-file-upload.s3.amazonaws](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/57452145/36291451-b3d1-4808-b973-1527eb9b3b89/paste.txt)

Athar + smolagents Skeleton
هذا skeleton يوضح كيف تستخدم smolagents كطبقة orchestration فوق خدمات Athar المتخصصة، بدل أن تستبدل منطق النظام الأساسي.

المكونات
app/tools.py: أدوات smolagents التي تستدعي خدمات Athar.

app/services.py: خدمات domain بسيطة (Fiqh/Hadith/Verification/Composer).

app/router_agent.py: مثال CodeAgent رئيسي.

prompts/router_system.txt: توجيه الوكيل الرئيسي.

الفكرة
منطق Athar الشرعي وretrieval/verification يبقى داخل services.

smolagents يستخدم فقط للتخطيط، استدعاء الأدوات، وتجميع ال

جهزت لك **skeleton عملي لـ Athar + smolagents** يوضح كيف تجعل smolagents طبقة orchestration فوق خدمات Athar بدل أن يستبدل منطق النظام نفسه. [huggingface](https://huggingface.co/docs/smolagents/index)

## ماذا يحتوي

- `router_agent.py`: وكيل رئيسي مبني على `CodeAgent` مع أدوات الفقه والحديث والتحقق والتركيب النهائي. [huggingface](https://huggingface.co/docs/smolagents/en/examples/multiagents)
- `tools.py`: تعريف أدوات smolagents التي تستدعي خدمات Athar الداخلية بدل وضع المنطق الشرعي داخل الـ agent نفسه. [huggingface](https://huggingface.co/docs/smolagents/index)
- `services.py`: خدمات domain بسيطة كمثال لـ Fiqh/Hadith/Verification/Composer قابلة للاستبدال لاحقًا بـ Qdrant وLLM الحقيقيين. [ppl-ai-file-upload.s3.amazonaws](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/57452145/36291451-b3d1-4808-b973-1527eb9b3b89/paste.txt)
- `router_system.txt`: prompt منظم للـ RouterAgent يفرض عدم الإجابة قبل التحقق واستدعاء الأدوات المناسبة فقط. [ppl-ai-file-upload.s3.amazonaws](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/57452145/eb489275-50c4-4c8b-a1b2-b4b368deb493/paste.txt)
- `README.md`: شرح سريع لفكرة الدمج بين Athar وsmolagents.

## كيف تستخدمه في Athar

الفكرة الصحيحة هي أن تبقي:
- retrieval
- verification
- citation normalization
- domain logic الشرعي

داخل خدمات Athar نفسها، ثم تجعل smolagents يدير فقط **التخطيط، اختيار الأدوات، وتجميع المسار**. [ppl-ai-file-upload.s3.amazonaws](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/57452145/36291451-b3d1-4808-b973-1527eb9b3b89/paste.txt)
هذا ينسجم مع المعمارية التي عندك: RouterAgent + specialized agents + verification suite + composer، ويطابق أنماط sequential/parallel/hierarchical المذكورة في وثيقة Athar. [ppl-ai-file-upload.s3.amazonaws](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/57452145/eb489275-50c4-4c8b-a1b2-b4b368deb493/paste.txt)

## الخطوة التالية

أنصحك أن تطور هذا الـ skeleton بهذا الترتيب:

1. استبدل `search_fiqh_service` و`search_hadith_service` باتصال حقيقي مع Qdrant hybrid retrieval. [qdrant](https://qdrant.tech/documentation/tutorials-search-engineering/reranking-hybrid-search/)
2. اربط `verify_evidence_service` بـ quote/source/grade checks الفعلية الموجودة في تصميمك. [ppl-ai-file-upload.s3.amazonaws](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/57452145/eb489275-50c4-4c8b-a1b2-b4b368deb493/paste.txt)
3. اجعل `compose_answer_service` يبني JSON schema مطابق لـ Athar output schema بدل النص البسيط الحالي. [ppl-ai-file-upload.s3.amazonaws](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/57452145/eb489275-50c4-4c8b-a1b2-b4b368deb493/paste.txt)
4. أضف لاحقًا أدوات أخرى مثل:
   - `search_tafsir`
   - `search_aqeedah`
   - `run_contradiction_detector`
   - `normalize_citations`. [ppl-ai-file-upload.s3.amazonaws](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/57452145/eb489275-50c4-4c8b-a1b2-b4b368deb493/paste.txt)


سأقترح لك الآن شكل قريب من الإنتاج، مبني على اللي عندك أصلًا في Athar، بدون ما أُغرِقك بكود طويل جدًا في رسالة واحدة. أركز على الـ wiring بين الطبقات:

- services (Fiqh/Hadith/Verification)
- tools (smolagents)
- router_agent (CodeAgent)

وتربطهم بنفس الـ configs/prompts اللي صممناها.

## 1) fiqh_service.py (يستهلك Athar FiqhAgent الحقيقي)

```python
# app/fiqh_service.py

from __future__ import annotations
from typing import Any, Dict, List

from agents.base import CollectionAgentConfig, CollectionAgent
from app.config_loader import load_agent_config
from app.llm_client import get_llm_client
from app.qdrant_client import get_qdrant_client
from app.prompts_loader import load_prompt


class FiqhAgent(CollectionAgent):
    # هنا تنفّذ query_intake / classify_intent / retrieve_candidates / ...
    # يمكنك تركها TODO واستخدام نسخة Athar الفعلية
    async def query_intake(self, question: str, meta: Dict[str, Any] | None = None) -> Dict[str, Any]:
        return {"question": question, "meta": meta or {}}

    async def classify_intent(self, intake: Dict[str, Any]) -> str:
        # مبدئيًا: كل شيء fiqh_hukm
        return "fiqh_hukm"

    async def retrieve_candidates(self, intent, intake) -> List[Dict[str, Any]]:
        # TODO: استبدل هذا بالـ Qdrant hybrid search الفعلي
        return [
            {
                "content": f"نص فقهي مبدئي متعلق بالسؤال: {intake['question']}",
                "book_title": "المجموع",
                "author_name": "النووي",
                "ref": "ج X، ص Y",
                "score": 0.9,
                "domain": "fiqh",
            }
        ]

    async def rerank_candidates(self, docs, intent):
        return docs  # لاحقًا استبدل بـ reranker

    async def run_verification(self, docs, intent, intake):
        # TODO: اربط بـ verification suite الفعلية
        return {
            "verified_evidence": docs,
            "flags": {"low_evidence": False, "ikhtilaf": False},
            "abstain": False,
        }

    async def generate_answer(self, verified, intake):
        # TODO: استدعاء LLM الحقيقي مع system_prompt من cfg
        snippets = [d["content"] for d in verified["verified_evidence"]]
        return {
            "answer_text": "\n".join(snippets),
            "raw_evidence": verified["verified_evidence"],
        }

    async def assemble_output(self, draft, verified):
        evidences = verified["verified_evidence"]
        citations = [e.get("ref") for e in evidences if e.get("ref")]
        return {
            "answer_text": draft["answer_text"],
            "answer_type": "info",
            "evidences": evidences,
            "citations": citations,
            "flags": verified.get("flags", {}),
        }


_fiqh_agent: FiqhAgent | None = None


def get_fiqh_agent() -> FiqhAgent:
    global _fiqh_agent
    if _fiqh_agent is None:
        cfg: CollectionAgentConfig = load_agent_config(
            "config/agents/fiqh.yaml",
            system_prompt=load_prompt("fiqh_agent.txt"),
        )
        _fiqh_agent = FiqhAgent(
            cfg=cfg,
            qdrant_client=get_qdrant_client(),
            llm=get_llm_client(),
        )
    return _fiqh_agent


async def search_fiqh_service(question: str) -> Dict[str, Any]:
    agent = get_fiqh_agent()
    result = await agent.run(question)
    return result
```

الفكرة: هذه الخدمة هي مجرد غلاف على FiqhAgent الحقيقي عندك، وتعيد JSON جاهز للاستهلاك من أدوات smolagents. [ppl-ai-file-upload.s3.amazonaws](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/57452145/36291451-b3d1-4808-b973-1527eb9b3b89/paste.txt)

## 2) hadith_service.py

بنفس النمط، لكن مع HadithAgent:

```python
# app/hadith_service.py

from __future__ import annotations
from typing import Any, Dict, List

from agents.base import CollectionAgentConfig, CollectionAgent
from app.config_loader import load_agent_config
from app.llm_client import get_llm_client
from app.qdrant_client import get_qdrant_client
from app.prompts_loader import load_prompt


class HadithAgent(CollectionAgent):
    async def query_intake(self, question: str, meta: Dict[str, Any] | None = None) -> Dict[str, Any]:
        return {"question": question, "meta": meta or {}}

    async def classify_intent(self, intake: Dict[str, Any]) -> str:
        return "hadith_takhrij"

    async def retrieve_candidates(self, intent, intake) -> List[Dict[str, Any]]:
        # TODO: Qdrant hybrid (lexical-heavy) + filters book_id/compiler/grade
        return [
            {
                "content": f"نص حديثي مبدئي متعلق بالسؤال: {intake['question']}",
                "book_title": "صحيح البخاري",
                "author_name": "البخاري",
                "ref": "رقم الحديث XXXX",
                "grade": "sahih",
                "score": 0.92,
                "domain": "hadith",
            }
        ]

    async def rerank_candidates(self, docs, intent):
        return docs

    async def run_verification(self, docs, intent, intake):
        # TODO: grade_checker + quote_validator + evidence_sufficiency
        return {
            "verified_evidence": docs,
            "flags": {"low_evidence": False, "weak_hadith_used": False},
            "abstain": False,
        }

    async def generate_answer(self, verified, intake):
        snippets = [d["content"] for d in verified["verified_evidence"]]
        return {
            "answer_text": "\n".join(snippets),
            "raw_evidence": verified["verified_evidence"],
        }

    async def assemble_output(self, draft, verified):
        evidences = verified["verified_evidence"]
        citations = [e.get("ref") for e in evidences if e.get("ref")]
        return {
            "answer_text": draft["answer_text"],
            "answer_type": "info",
            "evidences": evidences,
            "citations": citations,
            "flags": verified.get("flags", {}),
        }


_hadith_agent: HadithAgent | None = None


def get_hadith_agent() -> HadithAgent:
    global _hadith_agent
    if _hadith_agent is None:
        cfg: CollectionAgentConfig = load_agent_config(
            "config/agents/hadith.yaml",
            system_prompt=load_prompt("hadith_agent.txt"),
        )
        _hadith_agent = HadithAgent(
            cfg=cfg,
            qdrant_client=get_qdrant_client(),
            llm=get_llm_client(),
        )
    return _hadith_agent


async def search_hadith_service(question: str) -> Dict[str, Any]:
    agent = get_hadith_agent()
    result = await agent.run(question)
    return result
```

## 3) verification_service.py

هذه خدمة واحدة تستهلك evidences من أي agent وتعيد payload موحد (حتى لو داخليًا تستخدم نفس checks الموجودة عندك):

```python
# app/verification_service.py

from __future__ import annotations
from typing import Any, Dict, List


async def verify_evidence_service(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    # TODO: هنا تربط بـ quote_validator, source_attributor, grade_checker, ...
    # الآن مبدئيًا نمررها كما هي مع flags بسيطة.
    return {
        "verified": True,
        "issues": [],
        "evidence": results,
        "flags": {
            "ikhtilaf": any(e.get("domain") == "fiqh" for e in results),
            "low_evidence": len(results) < 3,
        },
        "abstain": False,
        "abstain_message": "",
    }
```

## 4) compose_answer_service.py

تبني جوابًا موحدًا من evidence متعدد المجالات:

```python
# app/compose_answer_service.py

from __future__ import annotations
from typing import Any, Dict, List


def compose_answer_service(question: str, verified_payload: Dict[str, Any]) -> Dict[str, Any]:
    evidence: List[Dict[str, Any]] = verified_payload.get("evidence", [])
    flags = verified_payload.get("flags", {})

    sections = []
    for e in evidence:
        domain = e.get("domain", "unknown")
        snippet = e.get("content", "")
        sections.append(f"[{domain}] {snippet}")

    answer_text = f"سؤال المستخدم: {question}\n\n" + "\n\n".join(sections)
    citations = [e.get("ref") for e in evidence if e.get("ref")]

    answer_type = "info"
    if verified_payload.get("abstain"):
        answer_type = "abstain"
        answer_text = verified_payload.get(
            "abstain_message",
            "بناءً على الأدلة المتاحة لا يمكن تقديم جواب موثوق.",
        )

    return {
        "answer_text": answer_text,
        "answer_type": answer_type,
        "evidences": evidence,
        "citations": citations,
        "flags": flags,
    }
```

## 5) tools.py (smolagents tools) – نسخة production-ish

```python
# app/tools.py

from __future__ import annotations
from typing import Any, Dict, List

from app.fiqh_service import search_fiqh_service
from app.hadith_service import search_hadith_service
from app.verification_service import verify_evidence_service
from app.compose_answer_service import compose_answer_service

try:
    from smolagents import tool
except Exception:
    def tool(func):
        return func


@tool
async def search_fiqh(question: str) -> Dict[str, Any]:
    """ابحث في مجموعة الفقه وأعد نتيجة Athar FiqhAgent الكاملة."""
    return await search_fiqh_service(question)


@tool
async def search_hadith(question: str) -> Dict[str, Any]:
    """ابحث في مجموعة الحديث وأعد نتيجة Athar HadithAgent الكاملة."""
    return await search_hadith_service(question)


@tool
async def verify_evidence(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    تحقّق من الأدلة المسترجعة من أكثر من وكيل قبل التوليد النهائي.
    يجب أن تكون النتائج بصيغة Athar standard evidence schema.
    """
    # يمكن لاحقًا التفريق بين domains هنا
    return await verify_evidence_service(results)


@tool
def compose_answer(question: str, verified_payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    كوّن الجواب النهائي من الأدلة المتحققة.
    يجب أن يُستخدم كآخر خطوة في سلسلة الأدوات.
    """
    return compose_answer_service(question, verified_payload)
```

لاحظ أن الأدوات الآن تعمل على schema Athar وليس dummy snippet/citation فقط. [ppl-ai-file-upload.s3.amazonaws](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/57452145/eb489275-50c4-4c8b-a1b2-b4b368deb493/paste.txt)

## 6) router_agent.py (CodeAgent رئيسي)

```python
# app/router_agent.py

from __future__ import annotations
from pathlib import Path

from app.tools import search_fiqh, search_hadith, verify_evidence, compose_answer

try:
    from smolagents import CodeAgent, LiteLLMModel
except Exception:
    CodeAgent = None
    LiteLLMModel = None

PROMPTS_DIR = Path(__file__).resolve().parent.parent / "prompts"


def load_router_prompt() -> str:
    return (PROMPTS_DIR / "router_system.txt").read_text(encoding="utf-8")


def build_router_agent(model_id: str = "openai/gpt-4o-mini"):
    if CodeAgent is None or LiteLLMModel is None:
        raise ImportError("smolagents or litellm not installed.")

    model = LiteLLMModel(model_id=model_id)
    agent = CodeAgent(
        tools=[search_fiqh, search_hadith, verify_evidence, compose_answer],
        model=model,
        system_prompt=load_router_prompt(),
        max_steps=6,
    )
    return agent
```

والـ prompt `router_system.txt` كما وضعته في الـ skeleton السابق، مع التركيز على:

- لا يجيب من نفسه
- يستدعي search_fiqh / search_hadith حسب نوع السؤال
- يمر دائمًا على verify_evidence
- ينهي بـ compose_answer فقط. [ppl-ai-file-upload.s3.amazonaws](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/57452145/eb489275-50c4-4c8b-a1b2-b4b368deb493/paste.txt)

***

بهذا الشكل:

- منطق Athar الأساسي يبقى في `FiqhAgent/HadithAgent` كما صممته في المستندين. [ppl-ai-file-upload.s3.amazonaws](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/57452145/36291451-b3d1-4808-b973-1527eb9b3b89/paste.txt)
- smolagents يتحول إلى **مُعامل orchestration** خفيف فقط يختار الأدوات وينسق بينها، بدون لمس القواعد الشرعية أو الـ retrieval/verification logic الداخلي. [huggingface](https://huggingface.co/docs/smolagents/index)

كملت لك نسخة **production‑ish skeleton** فيها فصل أوضح بين services وtools وrouter، بحيث تصبح أقرب لدمجها داخل Athar مباشرة. [huggingface](https://huggingface.co/docs/smolagents/index)

## ماذا أضفت

- `fiqh_service.py`: غلاف أولي لـ FiqhAgent يعيد schema موحّد فيه `answer_text`, `evidences`, `citations`, `flags`. [ppl-ai-file-upload.s3.amazonaws](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/57452145/36291451-b3d1-4808-b973-1527eb9b3b89/paste.txt)
- `hadith_service.py`: نفس الفكرة لكن لأسئلة الحديث والتخريج. [ppl-ai-file-upload.s3.amazonaws](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/57452145/eb489275-50c4-4c8b-a1b2-b4b368deb493/paste.txt)
- `verification_service.py`: طبقة تحقق موحدة تستقبل نتائج متعددة وتعيد payload واحدًا للتوليد النهائي. [ppl-ai-file-upload.s3.amazonaws](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/57452145/eb489275-50c4-4c8b-a1b2-b4b368deb493/paste.txt)
- `compose_answer_service.py`: يبني جوابًا نهائيًا من الأدلة المتحققة مع refs واضحة. [ppl-ai-file-upload.s3.amazonaws](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/57452145/eb489275-50c4-4c8b-a1b2-b4b368deb493/paste.txt)
- `tools.py`: أدوات smolagents فوق هذه الخدمات، بدل وضع المنطق داخل agent prompt نفسه. [huggingface](https://huggingface.co/docs/smolagents/index)
- `router_agent.py`: Router رئيسي بـ `CodeAgent` يوجّه بين أدوات الفقه والحديث ثم التحقق ثم التركيب. [huggingface](https://huggingface.co/docs/smolagents/en/examples/multiagents)
- `router_system.txt`: prompt تشغيلي للـ router يفرض المرور على `verify_evidence` قبل `compose_answer`. [ppl-ai-file-upload.s3.amazonaws](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/57452145/eb489275-50c4-4c8b-a1b2-b4b368deb493/paste.txt)
- `example_requests.md`: أمثلة requests فقهية، حديثية، ومختلطة للاختبار السريع.

## كيف تستخدمه الآن

النسخة الحالية تصلح كـ **scaffold**: تنقل الملفات إلى الريبو، ثم تستبدل داخل `fiqh_service.py` و`hadith_service.py` الـ dummy implementation الحالي بـ:
- تحميل config من YAML
- استدعاء `CollectionAgent`
- Qdrant hybrid retrieval
- reranking
- verification suite الفعلية. [ppl-ai-file-upload.s3.amazonaws](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/57452145/36291451-b3d1-4808-b973-1527eb9b3b89/paste.txt)

بمعنى آخر، smolagents هنا لا يصبح “العقل الشرعي”، بل مجرد **orchestrator** يستدعي خدمات Athar الحقيقية، وهذا هو الاستخدام الآمن والأنظف معماريًا. [qdrant](https://qdrant.tech/documentation/frameworks/smolagents/)

# Example requests

## Fiqh only
```json
{
  "question": "ما حكم القنوت في الفجر؟"
}
```

## Hadith only
```json
{
  "question": "ما صحة حديث إنما الأعمال بالنيات؟"
}
```

## Cross-domain
```json
{
  "question": "ما حكم رفع اليدين في الصلاة وما الأحاديث الواردة فيه؟"
}
```

## أنسب خطوة تالية

الآن أوصيك مباشرة بثلاثة أشياء:

1. اربط `search_fiqh_service()` و`search_hadith_service()` بـ agents الحقيقية بدل البيانات الوهمية. [ppl-ai-file-upload.s3.amazonaws](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/57452145/36291451-b3d1-4808-b973-1527eb9b3b89/paste.txt)
2. اجعل `verification_service.py` يستدعي checks فعلية مثل:
   - `quote_validator`
   - `source_attributor`
   - `grade_checker`
   - `contradiction_detector`. [ppl-ai-file-upload.s3.amazonaws](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/57452145/eb489275-50c4-4c8b-a1b2-b4b368deb493/paste.txt)
3. أضف FastAPI endpoint واحد مثل `/v1/router/answer` يستدعي `build_router_agent()` أو service wrapper فوقه. [ppl-ai-file-upload.s3.amazonaws](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/57452145/36291451-b3d1-4808-b973-1527eb9b3b89/paste.txt)

كملت لك المرحلة التالية: **FastAPI-ready skeleton** فيه API endpoints، schemas، loaders، config/prompts، وstubs للـ Qdrant والـ LLM، بحيث صار عندك هيكل أقرب للتشغيل المحلي وربطه لاحقًا بالخدمات الحقيقية. [ppl-ai-file-upload.s3.amazonaws](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/57452145/36291451-b3d1-4808-b973-1527eb9b3b89/paste.txt)

## ماذا أصبح عندك الآن

- `main.py`: نقطة تشغيل FastAPI.
- `app/api.py`: ثلاثة endpoints:
  - `/v1/fiqh/answer`
  - `/v1/hadith/answer`
  - `/v1/router/answer`.
- `app/schemas.py`: request/response models موحدة عبر Pydantic.
- `config_loader.py` و`prompts_loader.py`: تحميل YAML وprompts من الملفات بدل hardcoding.
- `qdrant_client.py` و`llm_client.py`: stubs جاهزة للاستبدال بعملاء حقيقيين.
- `fiqh_service.py` و`hadith_service.py`: services تقرأ config + prompt + clients.
- `verification_service.py` و`compose_answer_service.py`: طبقة تحقق وتجميع نهائي بسيطة وقابلة للتوسعة.
- `tools.py` و`router_agent.py`: دمج smolagents كطبقة orchestration فوق الخدمات.
- prompts + YAMLs الأساسية للفِقه والحديث.

## كيف تستخدمه فورًا

تقدر تعتبر هذه الحزمة **blueprint تنفيذي**، وليس implementation نهائيًا بعد. [ppl-ai-file-upload.s3.amazonaws](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/57452145/36291451-b3d1-4808-b973-1527eb9b3b89/paste.txt)
أول شيء تفعله الآن داخل الريبو:

1. انقل الملفات كما هي.
2. اربط `get_qdrant_client()` بعميل Qdrant الحقيقي.
3. استبدل الداتا الوهمية داخل `FiqhAgent.run()` و`HadithAgent.run()` بمنطق:
   - query normalization
   - hybrid retrieval
   - rerank
   - verification
   - answer generation. [ppl-ai-file-upload.s3.amazonaws](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/57452145/eb489275-50c4-4c8b-a1b2-b4b368deb493/paste.txt)
# Athar FastAPI Next Step

هذه الحزمة تكمل skeleton السابق وتضيف:
- `main.py`
- `api.py`
- `config_loader.py`
- `prompts_loader.py`
- `qdrant_client.py`
- `llm_client.py`
- `schemas.py`
- عينات config/prompts

الغرض منها: تقريب Athar من نسخة محلية قابلة للتشغيل والربط لاحقًا مع الخدمات الفعلية.
## أهم ما تبنيه بعد ذلك

الأولوية التالية عندك ليست Agents جديدة، بل **تقوية الطبقات الحالية**:

- في `verification_service.py`:
  - quote validator
  - source attribution
  - hadith grade checker
  - contradiction detector. [ppl-ai-file-upload.s3.amazonaws](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/57452145/eb489275-50c4-4c8b-a1b2-b4b368deb493/paste.txt)
- في `api.py`:
  - logging
  - request tracing
  - error handling
  - timeout policy. [ppl-ai-file-upload.s3.amazonaws](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/57452145/36291451-b3d1-4808-b973-1527eb9b3b89/paste.txt)
- في `router/answer`:
  - بدل heuristic بسيطة، استخدم `RouterAgent` الحقيقي أو classifier خفيف intent-aware. [ppl-ai-file-upload.s3.amazonaws](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/57452145/eb489275-50c4-4c8b-a1b2-b4b368deb493/paste.txt)

## أفضل خطوة تالية مني لك

الآن أصبح المنطقي جدًا أن أبني لك واحدًا من هذين:

- **نسخة Qdrant integration حقيقية**: search + filters + rerank + payload mapping. [ppl-ai-file-upload.s3.amazonaws](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/57452145/36291451-b3d1-4808-b973-1527eb9b3b89/paste.txt)
- أو **نسخة Router smarter**: intent classification + multi-domain planning + abstention rules. [ppl-ai-file-upload.s3.amazonaws](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/57452145/eb489275-50c4-4c8b-a1b2-b4b368deb493/paste.txt)

أنسب سؤال الآن: تريدني أكمل على **Qdrant layer** أم على **Router الذكي**؟