# Athar CollectionAgent Architecture and Multi-Agent RAG Design

## Executive Summary

This document specifies a reusable `CollectionAgent` architecture for Athar, an Islamic multi-agent RAG system built on the Athar-Datasets. It defines a shared lifecycle, retrieval strategies, verification suites, prompts, metadata enrichment, routing, Qdrant configuration, orchestration patterns, evaluation framework, and deployment considerations, aligned with usul al-fiqh principles (الرجوع إلى الأدلة، بيان الخلاف، التوقف عند الجهل).[^1][^2][^3][^4][^5]

The design assumes Python + FastAPI backend, Qdrant hybrid dense/BM25 retrieval, and an Arabic-capable LLM such as Qwen2.5-72B, with domain-specific Arabic embeddings (AraBERT/CAMeLBERT or newer Arabic embedding models) for similarity search.[^6][^7][^8][^9]

***

## 1. CollectionAgent Base Architecture

### 1.1 Concept and Responsibilities

A `CollectionAgent` represents a domain-specialized retrieval-and-generation pipeline bound to a single Athar collection (e.g., fiqh_passages, hadith_passages). It encapsulates:

- Configuration: `collection_name`, `retrieval_strategy`, `verification_suite`, `prompt_template`, `fallback_policy`.
- Lifecycle: query intake → intent classification (intra-collection) → retrieval → reranking → verification → generation → citation assembly.
- Domain logic: ikhtilaf handling, grade and authenticity constraints, abstention behavior, and citation formats aligned with classical methodology.[^3][^4]

### 1.2 Lifecycle Overview

The shared lifecycle is:

1. **query_intake**: Normalize and validate user question, enforce Arabic and scholarly tone constraints, tag safety flags (fatwa vs. information-only).[^4]
2. **intent_classification**: Within a collection, classify question type (حكم فقهي، تخريج حديث، تفسير آية، تراجم، لغوي، تزكية، تاريخي...) to adjust retrieval filters and prompts.
3. **retrieval**: Hybrid dense + BM25 retrieval from the collection in Qdrant using the Universal Query API and per-agent configuration.[^10][^11][^6]
4. **reranking**: Cross-encoder or ColBERT-style reranking to refine Top-K, possibly with domain-aware lexical boosts (e.g., hadith terms).[^12]
5. **verification**: Run a composed `VerificationSuite` of checks (quote validation, source attribution, contradiction detection, grade checking, temporal consistency, tone safety, sufficiency) that can abstain, warn, or proceed.[^4]
6. **generation**: Call LLM with structured system + user + tool context, including retrieved passages and verification results, enforcing abstention and ikhtilaf policy.
7. **citation_assembly**: Ensure every factual claim is backed by normalized citations (book, volume, page, hadith number, grade) and surfaced in the final Arabic response.

### 1.3 TypeScript-like Interface

```ts
// Pseudo-TS interface for CollectionAgent

export type RetrievalStrategy = {
  name: string; // "hybrid_fiqh_alpha0.6" etc.
  primary: 'dense' | 'sparse' | 'hybrid';
  alpha: number; // weight for dense vs sparse (0..1)
  topK_initial: number;
  topK_reranked: number;
  min_relevance: number; // 0..1 normalized
  metadataFiltersPriority: string[]; // ["madhhab", "era", ...]
};

export type VerificationCheckPolicy = 'abstain' | 'warn' | 'proceed';

export interface VerificationCheck {
  name: string;
  inputSchema: string; // description / pydantic model name
  outputSchema: string;
  failPolicy: VerificationCheckPolicy;
}

export interface VerificationSuite {
  checks: VerificationCheck[];
}

export interface FallbackPolicy {
  // e.g., fallback to GeneralIslamicAgent, or to pure lexical, or abstain
  onLowRecall: 'fallback_dense' | 'fallback_sparse' | 'delegate' | 'abstain';
  onVerificationFailure: 'delegate' | 'abstain';
  delegateAgent?: string; // e.g., "GeneralIslamicAgent";
}

export interface CollectionAgentConfig {
  collectionName: string;
  domain: string; // "fiqh", "hadith", ...
  retrievalStrategy: RetrievalStrategy;
  verificationSuite: VerificationSuite;
  promptTemplate: string; // system prompt
  fallbackPolicy: FallbackPolicy;
}

export interface CollectionAgent {
  readonly config: CollectionAgentConfig;

  queryIntake(rawQuestion: string, meta?: Record<string, any>): Promise<NormalizedQuery>;
  classifyIntent(normalized: NormalizedQuery): Promise<IntentLabel>; // e.g., "fatwa_info", "tafsir_ayah";

  retrieveCandidates(
    intent: IntentLabel,
    normalized: NormalizedQuery
  ): Promise<RetrievedPassage[]>;

  rerankCandidates(candidates: RetrievedPassage[]): Promise<RetrievedPassage[]>;

  runVerification(
    reranked: RetrievedPassage[],
    normalized: NormalizedQuery
  ): Promise<VerificationResult>;

  generateAnswer(
    verified: VerifiedEvidence,
    normalized: NormalizedQuery,
    verificationResult: VerificationResult
  ): Promise<LLMAnswerDraft>;

  assembleCitations(
    draft: LLMAnswerDraft,
    verified: VerifiedEvidence
  ): Promise<FinalAnswer>;
}
```

### 1.4 Python Pydantic / ABC Sketch

```python
from abc import ABC, abstractmethod
from typing import List, Dict, Literal, Optional, Any
from pydantic import BaseModel

IntentLabel = Literal[
    'fiqh_hukm', 'fiqh_tarjih', 'hadith_takhrij', 'hadith_sharh',
    'tafsir_ayah', 'aqeedah_masalah', 'seerah_event', 'history_event',
    'lugha_explanation', 'tazkiyah_mauidha', 'general_info', 'usul_qawaid'
]


class RetrievalStrategy(BaseModel):
    name: str
    primary: Literal['dense', 'sparse', 'hybrid']
    alpha: float  # dense weight in [0,1]
    topk_initial: int
    topk_reranked: int
    min_relevance: float
    metadata_filters_priority: List[str]


class VerificationCheck(BaseModel):
    name: str
    input_schema: str
    output_schema: str
    fail_policy: Literal['abstain', 'warn', 'proceed']


class VerificationSuite(BaseModel):
    checks: List[VerificationCheck]


class FallbackPolicy(BaseModel):
    on_low_recall: Literal['fallback_dense', 'fallback_sparse', 'delegate', 'abstain']
    on_verification_failure: Literal['delegate', 'abstain']
    delegate_agent: Optional[str] = None


class CollectionAgentConfig(BaseModel):
    collection_name: str
    domain: str
    retrieval_strategy: RetrievalStrategy
    verification_suite: VerificationSuite
    prompt_template: str
    fallback_policy: FallbackPolicy


class CollectionAgent(ABC):
    def __init__(self, config: CollectionAgentConfig, qdrant_client, llm):
        self.config = config
        self.qdrant = qdrant_client
        self.llm = llm

    @abstractmethod
    def query_intake(self, raw_question: str, meta: Optional[Dict[str, Any]] = None) -> 'NormalizedQuery':
        ...

    @abstractmethod
    def classify_intent(self, normalized: 'NormalizedQuery') -> IntentLabel:
        ...

    @abstractmethod
    def retrieve_candidates(self, intent: IntentLabel, normalized: 'NormalizedQuery') -> List['RetrievedPassage']:
        ...

    @abstractmethod
    def rerank_candidates(self, candidates: List['RetrievedPassage']) -> List['RetrievedPassage']:
        ...

    @abstractmethod
    def run_verification(
        self,
        reranked: List['RetrievedPassage'],
        normalized: 'NormalizedQuery'
    ) -> 'VerificationResult':
        ...

    @abstractmethod
    def generate_answer(
        self,
        verified: 'VerifiedEvidence',
        normalized: 'NormalizedQuery',
        verification_result: 'VerificationResult',
    ) -> 'LLMAnswerDraft':
        ...

    @abstractmethod
    def assemble_citations(
        self,
        draft: 'LLMAnswerDraft',
        verified: 'VerifiedEvidence'
    ) -> 'FinalAnswer':
        ...
```


***

## 2. Retrieval Strategy Matrix

Hybrid search in Qdrant combines dense semantic vectors with BM25-like sparse vectors using the Universal Query API; results can be fused via RRF and then reranked by a cross-encoder. For Athar, each agent configures its own weights, filters, and thresholds.[^13][^7][^6][^12]

### 2.1 Strategy Table

| Agent | Primary Strategy | Secondary | Filters | Reranking |
|-------|------------------|-----------|---------|-----------|
| FiqhAgent | Hybrid (dense-heavy) | Metadata | madhhab, era, category_sub | Cross-encoder + ikhtilaf-aware lexical boosts |
| HadithAgent | Hybrid (lexical-heavy) | Dense fallback | book_id, grade, compiler | Hadith-term lexical boost + cross-encoder |
| TafsirAgent | Hybrid (balanced) | Sparse | surah, ayah_range, mufassir_era | Cross-encoder contextual around ayah |
| AqeedahAgent | Hybrid (dense-heavy) | Sparse | aqeedah_school, era | Cross-encoder + contradiction clustering |
| SeerahAgent | Hybrid (dense-heavy) | Sparse | event_period, location | Cross-encoder + temporal proximity |
| HistoryAgent | Hybrid (balanced) | Sparse | era_bucket, region | Cross-encoder + timeline scoring |
| LanguageAgent | Hybrid (dense-heavy) | Sparse | topic (صرف، نحو، بلاغة), author | Cross-encoder with term-definition bias |
| TazkiyahAgent | Hybrid (dense-heavy) | Sparse | genre (رقائق، مواعظ), era | Cross-encoder + tone safety scoring |
| GeneralIslamicAgent | Hybrid (balanced) | Sparse | category_main, category_sub | Cross-encoder generic |
| UsulFiqhAgent | Hybrid (dense-heavy) | Sparse | usul_topic, madhhab, era | Cross-encoder + qawaid / usuli term boost |

### 2.2 Quantitative Parameters per Agent

Suggested alpha denotes dense weight in score fusion: final_score = alpha * dense_score + (1-alpha) * sparse_score, consistent with standard hybrid search practice.[^14][^15]

```yaml
retrieval_matrix:
  FiqhAgent:
    primary_strategy: hybrid
    alpha: 0.6         # dense 60%, sparse 40%
    topk_initial: 80
    topk_reranked: 12
    min_relevance: 0.35
    metadata_filters_priority: ["madhhab", "category_sub", "era"]
    fallback:
      if_recall_below_k: 5
      mode: fallback_sparse  # increase BM25 weight to catch exact terms

  HadithAgent:
    primary_strategy: hybrid
    alpha: 0.3         # lexical-heavy: dense 30%, sparse 70%
    topk_initial: 120
    topk_reranked: 20
    min_relevance: 0.4
    metadata_filters_priority: ["book_id", "compiler", "grade"]
    fallback:
      if_recall_below_k: 8
      mode: fallback_dense  # broaden semantics when exact match missing

  TafsirAgent:
    primary_strategy: hybrid
    alpha: 0.5
    topk_initial: 60
    topk_reranked: 15
    min_relevance: 0.35
    metadata_filters_priority: ["surah", "ayah_range", "mufassir_era"]

  AqeedahAgent:
    primary_strategy: hybrid
    alpha: 0.65
    topk_initial: 70
    topk_reranked: 15
    min_relevance: 0.4
    metadata_filters_priority: ["aqeedah_school", "era"]

  SeerahAgent:
    primary_strategy: hybrid
    alpha: 0.6
    topk_initial: 80
    topk_reranked: 18
    min_relevance: 0.35
    metadata_filters_priority: ["event_period", "location"]

  HistoryAgent:
    primary_strategy: hybrid
    alpha: 0.5
    topk_initial: 80
    topk_reranked: 18
    min_relevance: 0.35
    metadata_filters_priority: ["era_bucket", "region"]

  LanguageAgent:
    primary_strategy: hybrid
    alpha: 0.7
    topk_initial: 60
    topk_reranked: 15
    min_relevance: 0.3
    metadata_filters_priority: ["topic", "author"]

  TazkiyahAgent:
    primary_strategy: hybrid
    alpha: 0.65
    topk_initial: 60
    topk_reranked: 15
    min_relevance: 0.3
    metadata_filters_priority: ["genre", "era"]

  GeneralIslamicAgent:
    primary_strategy: hybrid
    alpha: 0.5
    topk_initial: 80
    topk_reranked: 15
    min_relevance: 0.3
    metadata_filters_priority: ["category_main", "category_sub"]

  UsulFiqhAgent:
    primary_strategy: hybrid
    alpha: 0.65
    topk_initial: 70
    topk_reranked: 15
    min_relevance: 0.4
    metadata_filters_priority: ["usul_topic", "madhhab", "era"]
```

These values should be tuned empirically using a validation set; Qdrant’s hybrid and multi-stage retrieval infrastructure supports this experimentation.[^16][^6][^12]

***

## 3. Verification Suite Design

### 3.1 General Design

Each `VerificationSuite` is a list of checks, each defined as `{check_name, input, output, fail_policy}`. Checks are composable and applied after reranking but before generation, enabling abstention when evidence is weak or contradictory, consistent with usuli emphasis on tahqiq al-manat and avoidance of fatwa without clear daleel.[^4]

Generic schema:

```json
{
  "check_name": "quote_validator",
  "input": {
    "passages": "List[RetrievedPassage]",
    "question": "NormalizedQuery"
  },
  "output": {
    "validated_spans": "List[ExactQuoteSpan]",
    "errors": "List[str]"
  },
  "fail_policy": "abstain"
}
```

### 3.2 Core Checks

1. **quote_validator**
   - Input: retrieved passages + extracted candidate quotes (e.g., Quran ayat, hadith matn).
   - Logic: ensure that any quoted text in the answer is an exact substring of a canonical text in the corpus (for Qur’an/Hadith/athar).[^4]
   - Output: list of validated spans with references.
   - Fail policy: `abstain` (better to abstain than misquote revealed texts).

2. **source_attributor**
   - Input: passages with `book_id`, `page_number`, `hierarchy`, and catalogs.
   - Logic: join against `master_catalog` and `author_catalog` to normalize references: author full name, death year, work title, edition info when available.[^1]
   - Output: normalized citation objects.
   - Fail policy: `warn` (if attribution incomplete but text authentic, allow answer with caveat).

3. **contradiction_detector** (for fiqh, aqeedah)
   - Input: cluster of passages around same hukm/mas’alah.
   - Logic: label positions by madhhab/aqeedah_school and detect conflicting rulings; align with usul practice of bayān al-khilāf and tarjih.[^5][^3]
   - Output: grouped positions, markers of ikhtilaf.
   - Fail policy: `proceed` (but mark answer as khilāfī and avoid single definitive tarjih unless asked for tarjih explicitly).

4. **grade_checker** (HadithAgent only)
   - Input: hadith passages with `grade` metadata (sahih, hasan, da’if, mawdu‘, etc.).
   - Logic: ensure only acceptable grades are used for rulings or aqeedah; weaker grades may be used for fada’il al-a’mal with explicit mention, following usul rules.[^4]
   - Output: filtered list of acceptable evidences + warnings for weak reports.
   - Fail policy: `warn` (allow but tag weak evidence; or `abstain` if only extremely weak/mawdu‘).

5. **temporal_consistency** (Seerah, History)
   - Input: events with `era_bucket`, `date`, `sequence` where encoded.
   - Logic: check that narration chain of events is chronological; flag inconsistencies.
   - Output: sorted events, inconsistency flags.
   - Fail policy: `warn` (inform model to mention disagreement in chronology).

6. **tone_safety_filter** (Tazkiyah)
   - Input: passages and draft LLM outputs.
   - Logic: detect harsh, despair-inducing, or miscontextualized citations; prefer balanced admonitions, align with maqasid (rahma, targhib wa tarhib in balance).[^4]
   - Output: list of safe passages, flagged content.
   - Fail policy: `abstain` from quoting harmful misuses; or `warn` to soften tone.

7. **evidence_sufficiency**
   - Input: count and diversity of passages (different authors, eras, madhahib) for a given mas’alah.
   - Logic: compute diversity score and ensure min number of independent sources before answering.[^3]
   - Output: sufficiency boolean, statistics.
   - Fail policy: `abstain` if insufficient evidence.

### 3.3 VerificationSuite per Agent

Example YAML-like configuration:

```yaml
verification_suites:
  FiqhAgent:
    - {check_name: quote_validator, input: passages+question, output: validated_spans, fail_policy: abstain}
    - {check_name: source_attributor, input: passages+catalogs, output: normalized_citations, fail_policy: warn}
    - {check_name: contradiction_detector, input: passages, output: positions_by_madhhab, fail_policy: proceed}
    - {check_name: evidence_sufficiency, input: passages, output: sufficiency_stats, fail_policy: abstain}

  HadithAgent:
    - {check_name: quote_validator, input: hadith_matn+isnad, output: validated_spans, fail_policy: abstain}
    - {check_name: source_attributor, input: passages+catalogs, output: normalized_citations, fail_policy: warn}
    - {check_name: grade_checker, input: hadith_metadata, output: filtered_evidence, fail_policy: warn}
    - {check_name: evidence_sufficiency, input: passages, output: sufficiency_stats, fail_policy: abstain}

  TafsirAgent:
    - {check_name: quote_validator, input: ayat+tafsir, output: validated_spans, fail_policy: abstain}
    - {check_name: source_attributor, input: passages+catalogs, output: normalized_citations, fail_policy: warn}
    - {check_name: evidence_sufficiency, input: passages, output: sufficiency_stats, fail_policy: abstain}

  AqeedahAgent:
    - {check_name: quote_validator, input: dalil_texts, output: validated_spans, fail_policy: abstain}
    - {check_name: source_attributor, input: passages+catalogs, output: normalized_citations, fail_policy: warn}
    - {check_name: contradiction_detector, input: passages, output: positions_by_school, fail_policy: proceed}
    - {check_name: evidence_sufficiency, input: passages, output: sufficiency_stats, fail_policy: abstain}

  SeerahAgent:
    - {check_name: quote_validator, input: riwayat, output: validated_spans, fail_policy: abstain}
    - {check_name: source_attributor, input: passages+catalogs, output: normalized_citations, fail_policy: warn}
    - {check_name: temporal_consistency, input: events, output: ordered_events, fail_policy: warn}
    - {check_name: evidence_sufficiency, input: passages, output: sufficiency_stats, fail_policy: abstain}

  HistoryAgent:
    - {check_name: quote_validator, input: texts, output: validated_spans, fail_policy: warn}
    - {check_name: source_attributor, input: passages+catalogs, output: normalized_citations, fail_policy: warn}
    - {check_name: temporal_consistency, input: events, output: ordered_events, fail_policy: warn}
    - {check_name: evidence_sufficiency, input: passages, output: sufficiency_stats, fail_policy: abstain}

  LanguageAgent:
    - {check_name: quote_validator, input: shawahid+definitions, output: validated_spans, fail_policy: warn}
    - {check_name: source_attributor, input: passages+catalogs, output: normalized_citations, fail_policy: warn}

  TazkiyahAgent:
    - {check_name: quote_validator, input: texts, output: validated_spans, fail_policy: warn}
    - {check_name: source_attributor, input: passages+catalogs, output: normalized_citations, fail_policy: warn}
    - {check_name: tone_safety_filter, input: passages+draft, output: safe_passages, fail_policy: abstain}

  GeneralIslamicAgent:
    - {check_name: quote_validator, input: texts, output: validated_spans, fail_policy: warn}
    - {check_name: source_attributor, input: passages+catalogs, output: normalized_citations, fail_policy: warn}
    - {check_name: evidence_sufficiency, input: passages, output: sufficiency_stats, fail_policy: abstain}

  UsulFiqhAgent:
    - {check_name: quote_validator, input: usuli_texts, output: validated_spans, fail_policy: warn}
    - {check_name: source_attributor, input: passages+catalogs, output: normalized_citations, fail_policy: warn}
    - {check_name: contradiction_detector, input: passages, output: positions_by_madhhab, fail_policy: proceed}
    - {check_name: evidence_sufficiency, input: passages, output: sufficiency_stats, fail_policy: abstain}
```

***

## 4. Agent-Specific Prompt Templates

Prompts must encode classical methodology: no fatwa without evidence, clarity on level of confidence (qat‘i / zanni, rajih vs marjuh), explicit mention of ikhtilaf, and abstention when evidence is insufficient.[^3][^4]

### 4.1 Global Principles (Arabic)

All agents share a preamble appended or prepended to their domain-specific system prompt:

> أنت مساعد بحثي متخصص في العلوم الشرعية، تعمل وفق منهجية أهل العلم في أصول الفقه وعلوم الحديث والتفسير. لا تفتي، ولا تصدر أحكامًا شخصية، وإنما تقتصر وظيفتك على **عرض أقوال العلماء وأدلتهم** مع توثيق دقيق للمصادر. إذا لم يتوفر لديك دليل موثوق أو كان الكلام في المسألة موضع اجتهاد دقيق لا يتسع له ما بين يديك من النصوص، فالأصل عندك **التوقف والإحالة إلى أهل العلم**.

### 4.2 FiqhAgent System Prompt (Full Example)

```text
[ROLE]
أنت "وكيل مجموعة فقهية" (Fiqh CollectionAgent) في نظام أثَر للمعرفة الإسلامية. مجال عملك هو نصوص الفقه وأدلته، دون إصدار فتاوى شخصية.

[OBJECTIVE]
مهمتك هي:
1. فهم سؤال المستخدم بدقة، وتحديد موضوع المسألة الفقهية ونطاقها.
2. استرجاع النصوص الفقهية ذات الصلة من المراجع الموثوقة في قاعدة البيانات (كتب الفقه المعتمدة في المذاهب السنية المشهورة.
3. **عرض أقوال الفقهاء مع أدلتهم**، وبيان مواضع الاتفاق والخلاف (الإجماع / الخلاف)، دون الإلزام بقول معيّن للمستخدم.
4. الالتزام بمنهج أهل العلم في الألفاظ، مثل: "الراجح"، "قيل"، "ذهب فلان"، "عند الحنفية"، "عند الجمهور"، مع ذكر الدليل عند كل قول ما أمكن.
5. ذكر المصادر بدقة (اسم الكتاب، اسم المؤلف، الجزء/المجلد، الصفحة أو رقم المسألة)، كما يعرضها لك نظام الاسترجاع.

[CONSTRAINTS]
- لا تستخدم ضمير المتكلم، بل عبّر بصيَغ العلماء: "ذكر العلماء"، "جاء في"، "نصّ فلان".
- لا تجزم بالحكم الشرعي على أنه فتوى شخصية للمستخدم، بل قدّم **معلومة فقهية** مستندة إلى الكتب.
- عند وجود **خلاف معتبر** بين أهل العلم:
  - اذكر الأقوال الرئيسة مرتبة حسب انتشارها (مثلاً: مذهب الجمهور، ثم مذهب الحنفية إن خالفوا، وهكذا).
  - بيّن أدلّة كل قول باختصار.
  - استخدم ألفاظًا مثل: "الراجح عند كثير من المحققين" فقط إذا توفّر في النصوص ما يدل على ذلك.
- إذا كانت النصوص المسترجعة قليلة أو غير صريحة في محل النزاع، فبيّن ذلك بوضوح، وامتنع عن الترجيح.

[CITATIONS FORMAT]
- عند ذكر نص فقهي، اذكره بصيغة قريبة من الأصل، ثم عقّب بتوثيق مثل:
  - "قال النووي في المجموع (ج X، ص Y): ...".
  - "جاء في المغني لابن قدامة (ج X، ص Y): ...".
- التزم بأن يكون **كل حكم فقهي مذكور مقترنًا بمصدر واحد على الأقل**.

[ABSTENTION]
- امتنع عن الإجابة (مع بيان السبب) في الحالات الآتية:
  - إذا تعلّق السؤال بفتوى شخصية تحتاج إلى تنزيل الحكم على واقع معقّد (مثال: تفاصيل معاملات مالية معاصرة).
  - إذا لم تُسترجَع نصوص كافية أو واضحة في المسألة.
  - إذا كان السؤال خارج نطاق الفقه (حوّله إلى وكيل آخر عبر النظام).

[OUTPUT STYLE]
- اكتب بالعربية الفصحى، بأسلوب علمي رصين، مع تقسيم الجواب إلى فقرات وعناوين فرعية إن لزم.
- قدّم أولًا تعريفًا موجزًا بالمسألة (إن كان مناسبًا)، ثم اذكر أقوال العلماء وأدلتهم، ثم ملاحظات تتعلّق بواقع السؤال إن كانت ظاهرة من النصوص.

[DISCLAIMER]
- اختم دائمًا بتنبيه مثل: "هذا العرض لِما في كتب الفقهاء، ولا يُعدُّ فتوى شخصية، ويُرجع في النوازل المعاصرة وأعيان المسائل إلى أهل العلم الراسخين.".
```

### 4.3 HadithAgent System Prompt (Full Example)

```text
[ROLE]
أنت "وكيل مجموعة حديثية" (Hadith CollectionAgent) في نظام أثَر. وظيفتك تخريج الأحاديث، وبيان درجتها، وذكر شروح العلماء عليها، دون استنباط أحكام جديدة أو إصدار فتاوى.

[OBJECTIVE]
1. تحديد ما إذا كان سؤال المستخدم:
   - عن **درجة حديث** معيّن.
   - عن **شرح معنى حديث**.
   - عن **جمع طرق وروايات** لحديث واحد.
2. استرجاع الأحاديث من المصادر الحديثية المعتمدة (الكتب الستة، المسانيد، السنن، ونحوها) مع معلومات السند والحكم على الإسناد إن وجدت.
3. عرض نص الحديث بدقة كما في المصدر، مع ذكر التخريج الكامل والمعروف.
4. بيان درجة الحديث (صحيح، حسن، ضعيف، موضوع...)، مع نسبة الحكم إلى من نصّ عليه من الأئمة (البخاري، مسلم، الترمذي، ابن حجر، الألباني...).
5. عند طلب الشرح، تُلخّص أقوال الشُرّاح الموثوقين، وتُنسب إليهم.

[CITATIONS FORMAT]
- استخدم صيغة توثيق قياسية:
  - "رواه البخاري في صحيحه (كتاب كذا، باب كذا، رقم الحديث XXXX)."
  - "رواه مسلم..."، "رواه أبو داود...".
- عند بيان الدرجة:
  - قل: "صححه الألباني"، "حسّنه الترمذي"، "ضعّفه فلان"، مع الإحالة لكتاب الحكم (مثلاً: "في السلسلة الصحيحة"، "في ضعيف الجامع"...).
- لا تنسب التصحيح أو التضعيف إلى النظام نفسه، بل إلى الأئمة.

[USAGE OF WEAK HADITH]
- في **العقائد** والأحكام: لا تستدل بالأحاديث الضعيفة، وبيّن ضعفها إذا ذُكرت في النصوص المسترجعة.
- في **فضائل الأعمال**: يمكن ذكر الحديث الضعيف مع التنبيه الصريح: "هذا حديث ضعيف، يورده بعض أهل العلم في فضائل الأعمال بشروطهم".

[ABSTENTION]
- إذا لم تجد نص الحديث في المصادر، قل بوضوح: "لم يظهر لهذا اللفظ تخريج معتبر في المصادر المتاحة لدي"، ولا تُقدّم حكمًا على ما لا تعرف.
- إذا اختلطت عليك الألفاظ ولم يتحقق التطابق التام، فنبّه على ذلك وامتنع عن الجزم.

[IKHTILAF HANDLING]
- عند اختلاف المحدّثين في الحكم على الحديث:
  - اذكر الأقوال المختلفة مع نسبتها لأصحابها.
  - استخدم ألفاظًا مثل: "صححه فلان، وضعّفه فلان".
  - لا تحسم الخلاف من نفسك، بل يمكن أن تقول: "والأقرب -بحسب ما نُقل عن أهل العلم- هو ..." **فقط إذا نقلت ذلك عن إمام معتبر**.

[OUTPUT STYLE]
- ابدأ بنص الحديث مضبوطًا قدر الإمكان.
- ثم التخريج: الكتاب، الباب، رقم الحديث.
- ثم درجة الحديث مع ذكر قائلها.
- ثم –إن سُئلت عن المعنى– تلخيص كلام الشراح مع توثيق الأسماء (مثل: "قال النووي...").

[DISCLAIMER]
- اختم بتنبيه: "هذا عرض لِما ورد في كتب الحديث وأحكام الأئمة عليها، ولا يُعدُّ حكمًا اجتهاديًا جديدًا".
```

### 4.4 Other Agents (Patterns)

- **TafsirAgent**: emphasize linkage of tafsir to Qur’anic ayat, mention mufassir, work, and methodology (bi’l-ma’thur vs bi’l-ra’y), avoid independent tafsir; abstain when no tafsir text exists.[^4]
- **AqeedahAgent**: stress reliance on Qur’an, sahih sunnah, and statements of salaf; clearly separate Ahl al-Sunnah creed from other schools, and highlight areas of ijma vs ikhtilaf.[^4]
- **UsulFiqhAgent**: describe qawaid usuliyya, dalalat al-alfazh, tarjih rules, but do not perform fresh ijtihad; attribute principles to classical works on usul al-fiqh.[^3][^4]

***

## 5. Metadata Enrichment Pipeline

### 5.1 Join Logic

Each passage in Athar collections contains fields such as `book_id`, `content`, `author`, `page_number`, etc., while master catalogs provide richer metadata across books and authors. During indexing:[^2][^1]

1. Load `master_catalog.json` keyed by `book_id`, including `book_title`, `author_id`, categories, edition data.
2. Load `author_catalog.json` keyed by `author_id` with `author_name`, `death_year`, `madhhab`, `aqeedah_school`, region.
3. For each passage row:
   - Use its `book_id` to fetch `book_title`, `author_id`.
   - Use `author_id` to fetch `author_name`, `death_year`, `madhhab`, `aqeedah_school`.
   - Derive `era` bucket from `death_year`.
   - Derive `category_main` and `category_sub` from `category_mapping.json` using existing `category`.[^1]

### 5.2 Era Bucketing Strategy

Era buckets can follow common scholarly periodization:[^4]

- `sahabah`: companions of the Prophet (death_year ≤ 110 AH approx.).
- `tabiin`: early successors (≈ 110–200 AH).
- `classical`: 200–700 AH (formation and consolidation of madhahib, major fiqh and hadith compilations).
- `medieval`: 700–1200 AH.
- `contemporary`: >1200 AH.

These ranges are tunable but should be consistent across all agents to enable temporal filters and analyses.

### 5.3 Missing Madhhab Handling

When `madhhab` is missing in `author_catalog`:

- Try heuristic inference from book metadata (e.g., if the work is a standard Hanafi text); this heuristic should be conservative and flagged as inferred.
- If still unknown, set `madhhab: "unknown"` and avoid using it as a strict filter; instead, treat such authors as cross-madhhab references.
- In answers, avoid phrasing such authors as representative of a madhhab unless the source explicitly states this.

### 5.4 Qdrant Payload Schema

Qdrant supports rich JSON payloads with indexed fields used for filtering and faceting. For each passage:[^17][^6]

```python
from qdrant_client import models

payload_schema_example = {
    "id": "...",  # string or int, unique per passage
    "content": "...",  # Arabic text
    "content_type": "passage",  # or "ayah", "hadith", etc.
    "metadata": {
        "book_id": "...",
        "book_title": "...",
        "author_id": "...",
        "author_name": "...",
        "author_death_year": 1234,
        "madhhab": "hanbali",          # or "shafii", "hanafi", "maliki", "zahiri", "unknown"
        "aqeedah_school": "athari",     # or "ashari", "maturidi", etc.
        "era": "classical",             # sahabah / tabiin / classical / medieval / contemporary
        "category_main": "fiqh",        # from category_mapping
        "category_sub": "fiqh_ibadah",  # fine-grained
        "collection": "fiqh_passages",  # name of Athar collection
        "page_number": 45,
        "section_title": "...",
        "hierarchy": "كتاب الصلاة > باب شروط الصلاة",
        # collection-specific extras
        "surah": 2,
        "ayah_start": 183,
        "ayah_end": 185,
        "hadith_number": "1234",
        "grade": "sahih",
        "compiler": "al-Bukhari",
        "region": "sham",
    },
}

point = models.PointStruct(
    id=payload_schema_example["id"],
    vector={"dense": embedding_vector},
    sparse_vector={"bm25": bm25_sparse_vector},
    payload=payload_schema_example,
)
```

Index frequently filtered fields (madhhab, era, category_main, category_sub, surah, grade, compiler) to accelerate queries.[^17]

***

## 6. Router Agent Design

### 6.1 Intent Classification

RouterAgent classifies incoming questions into one or more domain labels corresponding to CollectionAgents. Multi-label routing is necessary for questions that bridge fiqh and hadith, or fiqh and seerah, etc. A light LLM classifier or rules over keywords (e.g., "حديث", "سند", "رواه", "آية", "سورة", "إسناد", "نهائي", "حكم") can be combined.[^18]

### 6.2 Routing Decision Tree (Simplified)

```mermaid
graph TD
  Q[User Question] --> C{Contains explicit hadith cues?}
  C -->|"حديث" / "رواه" / سند / إسناد| H(HadithAgent)
  C -->|No| Q2{Contains explicit Qur'an/ayah cues?}

  Q2 -->|"قال الله" / آية / سورة / رقم آية| T(TafsirAgent)
  Q2 -->|No| Q3{Primarily about حكم عملي؟}

  Q3 -->|Yes| F(FiqhAgent)
  Q3 -->|No| Q4{Aqeedah terms (إيمان، توحيد، صفات، قدر؟)}

  Q4 -->|Yes| A(AqeedahAgent)
  Q4 -->|No| Q5{Seerah events (غزوة، هجرة، بدر...)?}

  Q5 -->|Yes| S(SeerahAgent)
  Q5 -->|No| Q6{Historical (دولة، خلافة، dynasties)?}

  Q6 -->|Yes| Hst(HistoryAgent)
  Q6 -->|No| Q7{Language (إعراب، صرف، بلاغة، معنى لفظ)؟}

  Q7 -->|Yes| L(LanguageAgent)
  Q7 -->|No| Q8{Tazkiyah (تزكية، قلب، إخلاص، رقة، خوف، رجاء)؟}

  Q8 -->|Yes| Z(TazkiyahAgent)
  Q8 -->|No| Q9{Usul al-fiqh terms (عام، خاص، ناسخ، منسوخ، قياس، إجماع، قياس)?}

  Q9 -->|Yes| U(UsulFiqhAgent)
  Q9 -->|No| G(GeneralIslamicAgent)
```

### 6.3 Multi-Label Routing and Confidence

Use an LLM classifier (on top of embeddings) to output probability per domain. Define:

- `p(domain | question)` per agent.
- Primary routes: any domain with p ≥ 0.5.
- Secondary supporting routes: domains with 0.2 ≤ p < 0.5.
- If max p < 0.4 → route to `GeneralIslamicAgent` only and answer at high level.

Example cross-domain question: "ما حكم الصلاة في المسجد النبوي وما أهميته في السيرة؟" → FiqhAgent (hukm of prayer in a mosque) + SeerahAgent (importance of Masjid Nabawi in the Prophet’s life). Router would send question to both; FiqhAgent focuses on virtue and ahkam of prayer there, SeerahAgent summarizes historical significance.

Routing config:

```yaml
router:
  primary_threshold: 0.5
  secondary_threshold: 0.2
  low_confidence_threshold: 0.4
  low_confidence_fallback: GeneralIslamicAgent
```

***

## 7. Qdrant Collection Configuration

Qdrant supports hybrid dense/sparse vectors with named vector fields and BM25-based sparse vectors in each collection. Athar should create one Qdrant collection per dataset collection (fiqh_passages, hadith_passages, etc.).[^6][^17]

### 7.1 Base Template

```python
from qdrant_client import models

EMBED_DIM = 1024  # depends on chosen Arabic embedding model

base_vectors_config = models.VectorsConfig(
    vectors={
        "dense": models.VectorParams(
            size=EMBED_DIM,
            distance=models.Distance.COSINE,
        )
    }
)

sparse_config = {
    "bm25": models.SparseVectorParams(  # BM25-like sparse index
        index=models.SparseIndexParams(on_disk=True)
    )
}

quantization = models.ScalarQuantization(
    scalar=models.ScalarQuantizationConfig(
        type=models.ScalarType.INT8,
        always_ram=False,
    )
)
```

### 7.2 Collection-Specific HNSW Parameters

Large collections (e.g., hadith_passages ≈ 11 GB, general_islamic ≈ 6.5 GB) need more aggressive HNSW tuning for recall vs memory trade-offs.[^11][^16]

Example configurations:

```python
large_hnsw = models.HnswConfigDiff(
    m=32,            # higher connectivity for recall
    ef_construct=256,
    full_scan_threshold=10000,
)

medium_hnsw = models.HnswConfigDiff(
    m=24,
    ef_construct=200,
    full_scan_threshold=10000,
)

small_hnsw = models.HnswConfigDiff(
    m=16,
    ef_construct=128,
    full_scan_threshold=5000,
)

collections_config = {
    "fiqh_passages": medium_hnsw,
    "hadith_passages": large_hnsw,
    "quran_tafsir": medium_hnsw,
    "aqeedah_passages": medium_hnsw,
    "seerah_passages": small_hnsw,
    "islamic_history_passages": medium_hnsw,
    "arabic_language_passages": medium_hnsw,
    "spirituality_passages": small_hnsw,
    "general_islamic": large_hnsw,
    "usul_fiqh": small_hnsw,
}

for name, hnsw_conf in collections_config.items():
    client.recreate_collection(
        collection_name=name,
        vectors_config=base_vectors_config,
        sparse_vectors_config=sparse_config,
        hnsw_config=hnsw_conf,
        quantization_config=quantization,
        on_disk_payload=True,
    )
```

- `on_disk_payload=True` is recommended for large textual payloads to save RAM.[^6]
- For smaller collections (seerah, spirituality, usul_fiqh), `m=16` and lower `ef_construct` suffice, reducing build time and memory.

***

## 8. Cross-Agent Orchestration Patterns

Complex questions often require multiple agents cooperatively. Athar’s orchestration graph can be modeled in LangGraph or a similar framework, following standard multi-stage retrieval + reranking practices but specialized for Islamic domains.[^18][^12]

### 8.1 Pattern A: Sequential (Fiqh → Usul → Hadith)

**Use case:** questions that implicitly require explanation of usuli basis and textual evidence for a fiqh ruling, e.g., "ما العلة في تحريم الربا؟".

Flow:

1. Router sends to `FiqhAgent` as primary.
2. `FiqhAgent` retrieves and summarizes madhhab positions and their dalil.
3. `FiqhAgent` triggers `UsulFiqhAgent` to explain underlying usuli principles (qiyas, sadd al-dhara’i, maslaha, etc.).
4. Both agents optionally call `HadithAgent` to perform detailed takhrij of key narrations.
5. FiqhAgent composes final informational answer referencing all supporting agents, making explicit which content comes from which source, in line with usul practice of combining adillah.[^4]

### 8.2 Pattern B: Parallel (Simultaneous Retrieval)

**Use case:** questions that naturally span two or three domains without strict dependency, e.g., "ما حكم زيارة القبور وما الحكمة الروحية منها؟" → fiqh + tazkiyah; or "ما فضل سورة البقرة في الحديث والتفسير؟" → hadith + tafsir.

Flow:

1. Router sends question concurrently to relevant agents.
2. Each agent independently runs retrieval, verification, and produces a domain-specific draft.
3. A `ComposerNode` merges drafts, ensuring:
   - Clear separation of domains (فقهي / حديثي / تفسيري / تزكوي).
   - Alignment of citations and removal of duplicates.
   - When conflicts arise (e.g., different understandings of a hadith), highlight them rather than overriding.

### 8.3 Pattern C: Hierarchical (Router → Primary Agent → Supporting Tools)

**Use case:** broad educational questions like "بيّن أهمية الصلاة في الإسلام مع ذكر الأدلة من القرآن والسنة وأقوال العلماء".

Flow:

1. Router selects `GeneralIslamicAgent` or `FiqhAgent` as primary.
2. Primary agent calls other agents as tools using a tool-calling LLM:
   - `TafsirAgent` to provide ayat and brief tafsir.
   - `HadithAgent` to list relevant sahih ahadith.
   - `TazkiyahAgent` to add spiritual insights.
3. Primary agent synthesizes, structuring the answer by source type and including disclaimers.

### 8.4 Contradiction Handling and Citation Assembly

When multiple agents produce overlapping or conflicting evidence:

- Group content by domain and by madhhab/aqeedah_school.
- Use usuli notions of tarjih: consider source strength (Qur’an > sahih mutawatir hadith > ahad hadith > athar > qiyas), chain reliability, and scholar authority.[^4]
- Clearly mark disputed points and avoid claiming ijma unless sources explicitly state it.
- For citations, maintain per-agent citation lists and deduplicate; provide combined references in each paragraph but tag them with origin (e.g., "في الفقه" vs "في الحديث").

***

## 9. Evaluation Framework

Evaluation should cover retrieval quality, citation correctness, ikhtilaf coverage, abstention behavior, and, for HadithAgent, grade accuracy. Islamic QA tasks like QIAS and Tafsir RAG pipelines illustrate the importance of domain-specific evaluation.[^18]

### 9.1 Metrics per Agent

Sample metric table (to be implemented with a labeled test set):

| Metric | FiqhAgent | HadithAgent | TafsirAgent |
|--------|----------|-------------|-------------|
| Retrieval Precision@5 | Required (≥0.7 target) | Required (≥0.75, since exact matches matter) | Required (≥0.7) |
| Retrieval Recall@20 | Required | Required | Required |
| Citation Accuracy | Required (source, page) | Required (book, number, grade) | Required (surah, ayah, tafsir source) |
| Ikhtilaf Coverage | Required (detect and mention major views) | N/A | N/A |
| Abstention Rate | Monitored (prefer abstention over speculative) | Monitored | Monitored |
| Hadith Grade Accuracy | N/A | Required (correct grade vs reference) | N/A |

Similar tables can be defined for Aqeedah, Seerah, History, Language, Tazkiyah, General, UsulFiqh with appropriate metrics (e.g., timeline accuracy for Seerah/History, linguistic correctness for LanguageAgent).

### 9.2 Golden Test Set Structure

Design a curated test set with:

- **Queries**: user-like questions in Arabic, tagged by domain(s) and intent type.
- **Gold Evidence**: list of passages (IDs) that should be retrieved, including Quran ayat, ahadith, and classical texts.
- **Gold Answer Sketch**: short human-written answer summarizing correct content, but not for direct training (avoid full text regeneration).
- **Annotations**:
  - `ikhtilaf_required: bool`.
  - `abstention_expected: bool` when humans decided not to answer from texts alone.
  - `hadith_grades_expected`: reference grades per hadith.

Format example:

```json
{
  "id": "fiqh_001",
  "question": "ما حكم زكاة عروض التجارة؟",
  "domains": ["fiqh"],
  "ikhtilaf_required": true,
  "abstention_expected": false,
  "gold_evidence_ids": ["fiqh:12345", "fiqh:78901"],
  "gold_answer_outline": "ذكر الجمهور وجوب زكاة عروض التجارة...",
  "metrics": {
    "precision_at_5": true,
    "citation_accuracy": true
  }
}
```

Human scholars should review test items to ensure alignment with authentic methodology.[^4]

***

## 10. Production Deployment Considerations

### 10.1 Embedding Model Recommendation

Arabic-specific embedding models such as AraBERT, CAMeLBERT, or more recent Arabic general-purpose embeddings provide better semantic similarity in Arabic than generic multilingual models. For large-scale retrieval in Islamic text:[^8][^9][^19]

- Use an Arabic sentence or document embedding model fine-tuned on ISLAM/Qur’an/Hadith text if available (e.g., from recent Arabic embedding research).[^9][^20]
- If such a model is not yet available, start with AraBERT/CAMeLBERT-based sentence embeddings and refine using contrastive learning on Athar pairs (similar vs dissimilar passages).[^19][^8]

### 10.2 CPU-Optimized Inference

Given CPU-based servers:

- Use quantized LLM weights where possible and offload heavy embedding computations to batch jobs or a separate service with caching.
- Pre-compute and store all passage embeddings offline; only query embeddings are computed online.[^6]
- Use small, efficient embedding models (e.g., Arabic-small or medium sizes) that still maintain quality.
- Optimize Qdrant search parameters (ef_search, m) for latency vs recall.[^16]

### 10.3 Chunking Strategy per Collection

Different Athar collections benefit from specialized chunking:

- **fiqh_passages, usul_fiqh**: semantic chunks by mas’alah or section (approx. 200–400 tokens) to align with issue-based reasoning.
- **hadith_passages**: per hadith (matn + core sharh excerpt) as one chunk; avoid splitting matn across chunks.
- **quran_tafsir**: group tafsir by ayah or small ayah ranges (2–3 ayat) to keep context localized.
- **aqeedah_passages**: by mas’alah (e.g., باب الإيمان بالقدر) with moderate size.
- **seerah_passages, islamic_history_passages**: by event or historical episode.
- **arabic_language_passages**: by concept (e.g., باب المبتدأ والخبر).  
- **spirituality_passages, general_islamic**: semantic chunks at 250–400 tokens, preserving rhetorical coherence.

Chunk sizes should be tuned to keep embeddings meaningful without exceeding model limits.

### 10.4 Index Build Order (MVP)

For an MVP:

1. `hadith_passages` – central for many queries; requires careful verification but high impact.
2. `quran_tafsir` – ensures any Qur’an-related questions are grounded.
3. `fiqh_passages` – core rulings.
4. `general_islamic` – covers many generic queries.
5. `seerah_passages` and `spirituality_passages` – essential for educational questions.
6. `aqeedah_passages`, `usul_fiqh`, `arabic_language_passages`, `islamic_history_passages` – more specialized, added as demand grows.

This ordering balances user demand with complexity: hadith and tafsir require strict verification but are foundational for fiqh and aqeedah.[^4]

### 10.5 Memory Management for Large Collections

Athar’s largest collections (hadith ≈ 11 GB, general_islamic ≈ 6.5 GB) require attention to storage, indexing, and query-time RAM usage:

- Enable `on_disk_payload=True` and quantization to reduce memory.[^16][^6]
- Consider sharding large collections by era or compiler (e.g., sahih, sunan, musnad) if Qdrant cluster mode is available.
- Tune HNSW `m` and `ef_search` to maintain acceptable latency on CPU; use benchmarking as recommended in Qdrant performance guides.[^11]
- Use aggressive compression for sparse vectors if disk space becomes critical, while leveraging Qdrant’s IDF-based BM25 implementation.[^17]

***

## 11. Mermaid Architecture Diagram

```mermaid
graph LR
  U[User Question] --> R[RouterAgent]
  R -->|domains| A1[CollectionAgent: Fiqh]
  R -->|domains| A2[CollectionAgent: Hadith]
  R -->|domains| A3[CollectionAgent: Tafsir]
  
  subgraph CollectionAgent Lifecycle
    QI[Query Intake] --> IC[Intent Classification]
    IC --> RET[Hybrid Retrieval (Qdrant)]
    RET --> RR[Reranking]
    RR --> VS[Verification Suite]
    VS --> GEN[LLM Generation]
    GEN --> CIT[Citation Assembly]
  end

  A1 --> QD[(Qdrant Collections)]
  A2 --> QD
  A3 --> QD

  CIT --> ORCH[Orchestrator / Composer]
  ORCH --> RESP[Final Arabic Scholarly Answer]
```

---

## References

1. [Kandil7/Athar-Datasets - Hugging Face](https://huggingface.co/datasets/Kandil7/Athar-Datasets) - We're on a journey to advance and democratize artificial intelligence through open source and open s...

2. [Kandil7/Athar-Datasets at main - Hugging Face](https://huggingface.co/datasets/Kandil7/Athar-Datasets/tree/main) - Datasets: · Kandil7. /. Athar-Datasets. like 4. Tasks: Question Answering · Text Generation · Text R...

3. [منهجية البحث في أصول الفقه Methodology of Research in Usul al-Fiqh](https://asjp.cerist.dz/en/article/244278) - This is elucidated within the general framework of "Research Methodology in Usul al-Fiqh," presented...

4. [[PDF] USUL AL FIQH AL ISLAMI SOURCE METHODOLOGY IN ISLAMIC ...](https://data.quranacademy.com/Audios/01_-_Dars-e-Quran/Usul_al-Fiqh_al-Islami.pdf) - Allah has provided articulate proofs and clear source-evidence in order that the believers should ha...

5. [RGS 411 Methodology of Islamic Law (Usul al-Fiqh)](https://www.respectgs.us/course/rgs-411-methodology-of-islamic-law-usul-al-fiqh/) - This course addresses the methodology related to the principles of Islamic jurisprudence (Usul al-fi...

6. [Hybrid Search and the Universal Query API - Qdrant](https://qdrant.tech/course/essentials/day-3/hybrid-search/) - Learn how to combine dense and sparse vector search methods to build powerful hybrid search pipeline...

7. [Project: Building a Hybrid Search Engine - Qdrant](https://qdrant.tech/course/essentials/day-3/pitstop-project/) - Build a hybrid search engine in Qdrant combining dense and sparse vectors with Reciprocal Rank Fusio...

8. [Embedding Extraction for Arabic Text Using the AraBERT Model](https://www.techscience.com/cmc/v72n1/46934/html) - We propose an algorithm for estimating textual similarity scores and then use these scores in multip...

9. [[PDF] General Arabic Text Embedding for Enhanced Semantic Textual ...](https://arxiv.org/pdf/2505.24581.pdf) - While AraBERT focuses on for- mal Arabic (Antoun et al., 2020), MARBERT ex- tends coverage to dialec...

10. [Hybrid Queries - Qdrant](https://qdrant.tech/documentation/search/hybrid-queries/) - Here is an example of RRF for a query containing two prefetches against different named vectors conf...

11. [Project: HNSW Performance Benchmarking - Qdrant](https://qdrant.tech/course/essentials/day-2/pitstop-project/) - Which HNSW configuration ( m , ef_construct ) worked best for your domain? How did the balance betwe...

12. [Multi-Stage Retrieval with Universal Query API - Qdrant](https://qdrant.tech/course/multi-vector-search/module-3/multi-stage-retrieval/) - For example, you might combine both dense and sparse vectors using query fusion to create a stronger...

13. [Qdrant Hybrid Search with Reranking](https://qdrant.tech/documentation/tutorials-search-engineering/reranking-hybrid-search/) - Hybrid search combines dense and sparse retrieval to deliver precise and comprehensive results. ... ...

14. [Hybrid Search with HNSW and BM25: Pinecone, Weaviate, Qdrant ...](https://www.linkedin.com/posts/hariharan2305_generativeai-rag-ai-activity-7440773101564571648-x-8j) - We combine dense retrieval from a vector DB (like FAISS or Weaviate) with sparse retrieval using a c...

15. [What is Hybrid Search? - DEV Community](https://dev.to/qdrant/what-is-hybrid-search-383g) - A distribution of both Qdrant and BM25 scores mapped into 2D space. It clearly shows relevant and no...

16. [Demo: HNSW Performance Tuning - Qdrant](https://qdrant.tech/course/essentials/day-2/collection-tuning-demo/) - You'll learn to: Optimize bulk upload speed with strategic HNSW configuration; Measure the performan...

17. [Demo: Keyword Search with Sparse Vectors - Qdrant](https://qdrant.tech/course/essentials/day-3/sparse-retrieval-demo/) - Hands-on sparse retrieval in Qdrant—create BM25 collections, enable IDF, index with FastEmbed, try S...

18. [[PDF] QIAS 2025: Overview of the Shared Task on Islamic Inheritance ...](https://aclanthology.org/2025.arabicnlp-sharedtasks.117.pdf) - The Transformer Tafsir team (AbuAhmad et al.,. 2025) developed a hybrid RAG pipeline combin ing spar...

19. [CAMeLBERT: A collection of pre-trained models for Arabic NLP tasks](https://github.com/CAMeL-Lab/CAMeLBERT) - This repo contains code for the experiments presented in our paper: The Interplay of Variant, Size, ...

20. [[PDF] Combining FastText with AraBERT for Arabic Text Representation](https://f1000research.com/articles/15-206/pdf) - This study aims to develop a novel sentence-embedding framework tailored for Arabic that addresses t...

