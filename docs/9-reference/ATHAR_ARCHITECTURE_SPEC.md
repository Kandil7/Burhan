  **Architectural Specification for the Burhan Multi-Agent Islamic Knowledge RAG System**

- الأقسام الرئيسية:
  0. Scope and Audience  
  1. System Overview: Digital Isnad at Scale  
  2. CollectionAgent Base Architecture (بما فيها كود الـ `CollectionAgent` منظم ومصحّح)  
  3. Retrieval Strategy Matrix (جدول الـ agents مع الـ BM25/Dense weights والـ filters)  
  4. VerificationSuite Design (جدول checks + تفسير Digital Isnad)  
  5. Agent-Specific Prompt Templates (FiqhAgent / HadithAgent)  
  6. Metadata Enrichment and Qdrant Schema  
  7. RouterAgent and Multi-Label Routing  
  8. Qdrant Collection Configuration and Scaling  
  9. Cross-Agent Orchestration Patterns (Sequential / Parallel / Hierarchical)  
  10. Evaluation Framework  
  11. Production Deployment Considerations (BGE‑M3, E5, ONNX, quantization، chunking)  
  12. Non-Goals  

وبه استشهادات مختصرة مبنية على مصادر حديثة عن BGE‑M3، LangGraph، وQdrant (quantization + hybrid search + resource optimization)، بالإضافة إلى ملخص Burhan‑Datasets الموجود عندك كـ corpus ضخم من 15.7M+ passages و ~8.4k مصدر أولي. [huggingface](https://huggingface.co/BAAI/bge-m3)

ما أستطيع فعله الآن هو إعطاؤك **النص الكامل جاهز نسخ‑لصق**:

***

# Architectural Specification for the Burhan Multi-Agent Islamic Knowledge RAG System

## 0. Scope and Audience

This document specifies the core architecture of the Burhan Multi-Agent Retrieval-Augmented Generation (RAG) system. It targets backend/ML engineers, information retrieval researchers, and Islamic studies specialists involved in designing, maintaining, or auditing Burhan in production.

The goal is to provide a production-grade, Arabic-centric framework that unifies classical Islamic scholarship workflows (isnad, takhrij, tahqiq, ikhtilaf handling) with modern multi-agent RAG, vector search, and verification techniques. [arxiv](https://arxiv.org/abs/2402.03216)

***

## 1. System Overview: Digital Isnad at Scale

Burhan operates on top of Burhan-Datasets (15.7M+ passages from 8,400+ primary sources) to implement a "Digital Isnad" framework: every answer must be grounded in traceable, historically verified texts. The system is designed to: [ppl-ai-file-upload.s3.amazonaws](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/57452145/f33d27d0-36ae-4a87-b8b8-696472d31141/chat-Search-Burhan-Dataset.txt)

- Support Arabic-first queries and responses across classical and modern registers. [ppl-ai-file-upload.s3.amazonaws](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/57452145/f33d27d0-36ae-4a87-b8b8-696472d31141/chat-Search-Burhan-Dataset.txt)
- Enforce epistemic integrity for religious knowledge (fatawa, hadith, tafsir, aqeedah).
- Move from a single naive RAG pipeline to a multi-agent, verification-heavy orchestration layer.

Key architectural principles:

- **Collection-aware agents**: each domain (fiqh, hadith, tafsir, etc.) has a specialized agent built on a shared base class.
- **Hybrid retrieval**: BM25 + dense retrieval + metadata filters + cross-encoder reranking. [qdrant](https://qdrant.tech/articles/hybrid-search/)
- **Explicit verification**: modular VerificationSuite implementing quote integrity, grade checks, source attribution, and contradiction detection. [aclanthology](https://aclanthology.org/2025.findings-acl.354.pdf)
- **LangGraph-style orchestration**: sequential, parallel, and hierarchical agent workflows for complex questions. [inexture](https://www.inexture.ai/agentic-rag-with-langgraph-adaptive-retrieval-production/)
- **Resource-aware vector search**: Qdrant with scalar quantization and on-disk payloads for >40GB datasets. [qdrant](https://qdrant.tech/course/essentials/day-4/what-is-quantization/)

***

## 2. CollectionAgent Base Architecture

### 2.1 Abstract CollectionAgent Interface

All domain agents derive from a common `CollectionAgent` base which encodes the RAG lifecycle and guarantees:

- Consistent retrieval -> ranking -> verification -> generation flow.
- Standardized citation structures.
- Configurable fallback policies (`answer`, `clarify`, `abstain`).

```python
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Sequence
from pydantic import BaseModel, Field


class Citation(BaseModel):
    book_title: str
    author_name: str
    author_death_hijri: int
    page_number: int
    section_title: str
    hierarchy: List[str]
    collection: str


class RetrievedPassage(BaseModel):
    content: str
    score: float
    metadata: Dict[str, Any]


class VerifiedPassage(RetrievedPassage):
    verification_flags: Dict[str, Any] = Field(default_factory=dict)


class AgentResponse(BaseModel):
    answer_arabic: str
    citations: List[Citation]
    confidence_score: float
    is_ikhtilaf_detected: bool
    metadata: Dict[str, Any] = Field(default_factory=dict)


class CollectionAgent(ABC):
    """
    Base class for all domain-specific Islamic knowledge agents.
    Implements the core RAG lifecycle with hooks for specialized behavior.
    """

    def __init__(
        self,
        collection_name: str,
        retrieval_strategy: Dict[str, Any],
        verification_suite: List[Any],
        prompt_template: str,
        fallback_policy: str = "abstain",
    ) -> None:
        self.collection_name = collection_name
        self.retrieval_strategy = retrieval_strategy
        self.verification_suite = verification_suite
        self.prompt_template = prompt_template
        self.fallback_policy = fallback_policy

    @abstractmethod
    async def retrieve(
        self,
        query: str,
        filters: Dict[str, Any],
    ) -> List[RetrievedPassage]:
        """Domain-specific retrieval logic (hybrid BM25 + dense + filters)."""

    @abstractmethod
    async def verify(
        self,
        passages: Sequence[RetrievedPassage],
    ) -> List[VerifiedPassage]:
        """Execute the VerificationSuite on retrieved candidates."""

    async def classify_intent(self, query: str) -> Dict[str, Any]:
        """Optional local, domain-specific intent classification."""
        return {"intent": "generic"}

    async def rerank(
        self,
        query: str,
        candidates: Sequence[RetrievedPassage],
    ) -> List[RetrievedPassage]:
        """Cross-encoder based reranking (arabic reranker)."""
        # Implementation delegated to concrete agents or shared service
        return list(candidates)

    async def generate(
        self,
        query: str,
        passages: Sequence[VerifiedPassage],
    ) -> AgentResponse:
        """Domain-specific generation and citation assembly using LLM."""
        raise NotImplementedError

    def generate_abstention(self) -> AgentResponse:
        """Standardized abstention response when evidence is insufficient."""
        return AgentResponse(
            answer_arabic=(
                "لا تتوفر أدلة كافية أو واضحة في المصادر الموثوقة ضمن قاعدة بيانات أثر "
                "للإجابة عن هذا السؤال بدقة. يُنصح بالرجوع إلى عالم أو مفتٍ مختص."
            ),
            citations=[],
            confidence_score=0.0,
            is_ikhtilaf_detected=False,
            metadata={"reason": "insufficient_evidence"},
        )

    async def run(self, query: str, state: Dict[str, Any]) -> AgentResponse:
        """Standardized lifecycle: intake -> intent -> retrieval -> ranking ->
        verification -> generation/abstention.
        """
        intent = await self.classify_intent(query)
        filters = state.get("filters", {})

        candidates = await self.retrieve(query, filters)
        if not candidates and self.fallback_policy == "abstain":
            return self.generate_abstention()

        ranked = await self.rerank(query, candidates)
        verified = await self.verify(ranked)

        if not verified and self.fallback_policy == "abstain":
            return self.generate_abstention()

        response = await self.generate(query, verified)
        response.metadata["intent"] = intent
        response.metadata["collection_name"] = self.collection_name
        return response
```

This interface matches well with LangGraph’s node model where each agent is a pure function on state (input query + filters -> enriched state with `AgentResponse`). [docs.langchain](https://docs.langchain.com/oss/python/langgraph/agentic-rag)

### 2.2 Agent Lifecycle and Manhaj Mapping

The lifecycle of a `CollectionAgent` mirrors classical Islamic research methodology:

1. Query intake + local intent: internal classification into subcategories (e.g., differentiating between early Salaf creed vs. later kalam developments within `AqeedahAgent`).
2. Hybrid retrieval:
   - Sparse BM25 for lexical precision and exact wording.
   - Dense retrieval (e.g., BGE-M3 / multilingual E5) for semantic capture. [bge-model](https://bge-model.com/bge/bge_m3.html)
   - Metadata filters (madhhab, era, collection, category) to constrain the search space.
3. Cross-encoder reranking: an Arabic reranker processes the top N candidates (e.g., 100–250) and selects the best 3–7 passages for the final context, as recommended in modern hybrid search + reranking setups. [qdrant](https://qdrant.tech/documentation/tutorials-search-engineering/reranking-hybrid-search/)
4. VerificationSuite: domain-tailored checks (hadith grading, quote integrity, source attribution, contradiction detection, temporal consistency) prune noisy or unverifiable passages before LLM exposure. [aclanthology](https://aclanthology.org/2025.findings-acl.354.pdf)
5. Generation + citation assembly: the LLM generates a response in Arabic using domain-specific prompts, with structured citations tied back to book and author metadata.
6. Fallback / abstention: if verification fails or evidence is sparse, the agent returns an abstention response instead of hallucinating.

***

## 3. Retrieval Strategy Matrix

Burhan uses domain-specific retrieval configurations tuned for each agent. Different collections have different structure (hadith vs. seerah vs. history) and therefore different BM25/dense weighting and filter priorities. [qdrant](https://qdrant.tech/articles/hybrid-search/)

### 3.1 Domain-Specific Strategy Table

| Agent         | Primary Strategy | BM25 / Dense Weight | Filter Priority          | Reranking Priority   |
|--------------|------------------|---------------------|--------------------------|----------------------|
| FiqhAgent    | Hybrid           | 0.4 / 0.6           | madhhab, era, category   | Ikhtilaf-aware       |
| HadithAgent  | Lexical-Heavy    | 0.7 / 0.3           | book_id, author_death    | Grade-first          |
| TafsirAgent  | Dense-Heavy      | 0.3 / 0.7           | book_title, section      | Verse-thematic       |
| AqeedahAgent | Hybrid           | 0.5 / 0.5           | school, author_death     | Precision-heavy      |
| SeerahAgent  | Semantic         | 0.2 / 0.8           | temporal_stage           | Narrative-flow       |
| HistoryAgent | Hybrid           | 0.4 / 0.6           | era, region              | Chronological        |
| LanguageAgent| Lexical-Heavy    | 0.8 / 0.2           | category, author         | Root-based           |
| TazkiyahAgent| Semantic         | 0.3 / 0.7           | author, category         | Tone-sentiment       |
| GeneralAgent | Hybrid           | 0.5 / 0.5           | collection, category     | Diversity            |
| UsulFiqhAgent| Dense-Heavy      | 0.3 / 0.7           | madhhab, era             | Logical-step         |

**Hybrid scoring:**

```text
FinalScore = w1 * BM25_normalized + w2 * Dense_score
```

Hybrid weighting and reranking are aligned with Qdrant’s documented patterns for production-grade hybrid semantic search with rerankers. [qdrant](https://qdrant.tech/documentation/tutorials-search-engineering/reranking-hybrid-search/)

### 3.2 Hyperparameters and Thresholds

Typical retrieval settings (tuned per collection):

- Initial retrieval (`top_k_initial`): 100–250 passages depending on collection size.
- Final context (`top_k_final`): 3–7 passages to keep within LLM context limits while maintaining diversity.
- Minimum dense score: 0.65; minimum BM25-normalized score: 0.50.
- Scalar fusion parameters (`w1`, `w2`) vary by agent as in the table above.

These ranges match best practices for hybrid search and multi-stage ranking pipelines in large-scale vector search engines. [qdrant](https://qdrant.tech/articles/hybrid-search/)

***

## 4. VerificationSuite Design

### 4.1 Verification Check Interface

Each verification check shares a standard signature so agents can compose suites appropriate to their domain:

- Input: passages, metadata, or combined context.
- Output: flags, normalized grades, or filtered sets.
- Fail policy: `abstain`, `warn`, or `proceed`.

Example checks:

| Check name        | Input    | Output           | Fail policy | Summary                                                             |
|-------------------|----------|------------------|-------------|---------------------------------------------------------------------|
| `quote_validator` | content  | bool             | Abstain     | Fuzzy match against golden Quran/hadith indices to avoid hallucinated quotes. |
| `source_attributor` | metadata | `Citation`      | Warn        | Joins `book_id` with `master_catalog` to build normalized citations.|
| `contradiction_det` | passages| list[conflict]   | Proceed     | Uses LLM to flag contradictory fiqh rulings for ikhtilaf handling.  |
| `grade_checker`   | passages | structured grade | Abstain     | Extracts hadith grades (sahih, daif, etc.) for `HadithAgent`.       |
| `temporal_const`  | metadata | bool             | Warn        | Flags anachronisms based on `author_death` vs. event date.         |
| `tone_safety`     | content  | bool             | Proceed     | Ensures tasawwuf texts avoid deviant or misattributed content.     |
| `sufficiency_val` | res_count| bool             | Abstain     | Requires N distinct sources for high-complexity queries.           |

This structure is compatible with recent research on inter-passage verification for grounded multi-evidence QA. [aclanthology](https://aclanthology.org/2025.findings-acl.354.pdf)

### 4.2 Digital Isnad and Epistemic Justification

The VerificationSuite encodes principles from ulum al-hadith and usul al-fiqh:

- Passages that cannot be mapped to `author_catalog`/`master_catalog` with high confidence are rejected (no broken chains).
- Hadith without clear grading are either flagged or excluded depending on agent policy.
- Conflicting views are surfaced instead of collapsed, enabling ikhtilaf-aware answers.

This is analogous to classical jarh wa ta'dil and takhrij, but implemented within a modern RAG verification pipeline. [aclanthology](https://aclanthology.org/2025.findings-acl.354.pdf)

***

## 5. Agent-Specific Prompt Templates

Each agent uses a tailored Arabic system prompt encoding domain-specific constraints (no personal fatwa, handle ikhtilaf, strict quotation rules, etc.).

### 5.1 FiqhAgent Prompt (Jurisprudence)

The FiqhAgent acts as a muhaqqiq (researcher), not a mufti, and presents madhhab positions fairly:

- Attribute statements accurately ("ذكر الحنفية في كتاب X...").
- Surface ikhtilaf explicitly ("ذهب الجمهور إلى... وقيل...").
- Always attach citations `[اسم الكتاب، المؤلف، الصفحة]`.
- Abstain on contemporary fatwa questions not directly grounded in corpus texts.

### 5.2 HadithAgent Prompt (Prophetic Traditions)

The HadithAgent focuses on exact matn and authenticity:

- Do not paraphrase prophetic text.
- Provide takhrij: collector, book, chapter, number where possible.
- Include grade (sahih, hasan, daif) from retrieved passages or metadata.
- Abstain or warn if text is weak/mawdu or attribution is uncertain.

These prompt constraints align with the Digital Isnad and verification design above.

***

## 6. Metadata Enrichment and Qdrant Schema

### 6.1 Enrichment Pipeline and Era Bucketing

At indexing time, Burhan joins raw passages with bibliographic and biographical catalogs to produce rich payloads, including: [ppl-ai-file-upload.s3.amazonaws](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/57452145/f33d27d0-36ae-4a87-b8b8-696472d31141/chat-Search-Burhan-Dataset.txt)

- `book_id`, `book_title`, `author_id`, `author_name`, `author_death_year`.
- `madhhab`, `aqeedah_school`, `era`, `category_main`, `category_sub`.
- Hierarchical path within the book (`hierarchy`).

Era bucketing uses `author_death_year` (Hijri) to classify texts:

- 0–100 AH: Prophetic / Sahabah.
- 100–300 AH: Foundational / Tabiin (school formation and hadith codification).
- 300–600 AH: Classical / Golden Age (mature legal and theological synthesis).
- 600–900 AH: Medieval / Post-Mongol.
- 900–1300 AH: Ottoman / Early Modern.
- 1300+ AH: Modern / Contemporary.

### 6.2 Qdrant Payload Schema

Each vector in Qdrant stores enriched metadata for fast filtering. [qdrant](https://qdrant.tech/documentation/manage-data/collections/)

```json
{
  "id": "uuid-v4",
  "content": "نص الممر الفقهي أو الحديثي...",
  "metadata": {
    "book_id": 4567,
    "book_title": "التمهيد لما في الموطأ من المعاني والأسانيد",
    "author_id": 890,
    "author_name": "ابن عبد البر",
    "author_death_year": 463,
    "madhhab": "maliki",
    "aqeedah_school": "ashari",
    "era": "classical",
    "category_main": "hadith",
    "category_sub": "hadith_commentary",
    "collection": "hadith_passages",
    "page_number": 124,
    "section_title": "باب ما جاء في وقت المغرب",
    "hierarchy": [
      "التمهيد",
      "كتاب الصلاة",
      "باب المواقيت"
    ]
  }
}
```

This structure is compatible with Qdrant collections and supports indexing-time scalar quantization and on-disk payloads. [qdrant](https://qdrant.tech/articles/vector-search-resource-optimization/)

***

## 7. RouterAgent and Multi-Label Routing

The `RouterAgent` dispatches queries to one or more domain agents based on:

- Lexical markers ("حكم", "واجب", "عقيدة", "حديث", "قياس", ...).
- Semantic classification using an LLM.
- User-provided context (preferred madhhab, scope, etc.).

For cross-domain queries, the router emits a task list (e.g., `FiqhAgent` + `SeerahAgent`) and chooses a parallel or sequential orchestration pattern.

This design matches agentic routing and parallelization patterns described for LangGraph-based systems. [pub.towardsai](https://pub.towardsai.net/agentic-design-patterns-with-langgraph-5fe7289187e6)

***

## 8. Qdrant Collection Configuration and Scaling

### 8.1 HNSW and Quantization Parameters

Large collections (e.g., hadith, fiqh) use tuned HNSW and quantization settings: [github](https://github.com/qdrant/qdrant/issues/6125)

- `m` in  and `ef_construct` in  depending on collection size. [arxiv](https://arxiv.org/abs/2603.08501)
- Scalar quantization `type = int8` for 4x memory reduction with minimal recall loss. [pub.towardsai](https://pub.towardsai.net/pplx-embed-qdrant-building-production-grade-semantic-search-with-quantization-cea9626b8c7c)
- `on_disk_payload = true` so payloads live on disk while HNSW graph and vectors stay in RAM. [github](https://github.com/qdrant/qdrant/issues/3956)

### 8.2 Resource Optimization

These settings allow Burhan to:

- Run large collections on CPU-optimized servers.
- Fit vectors into RAM while leaving payloads on NVMe.
- Maintain high recall with hybrid search + reranking, even with quantization enabled. [qdrant](https://qdrant.tech/articles/scalar-quantization/)

***

## 9. Cross-Agent Orchestration Patterns

Burhan uses LangGraph to implement three primary orchestration patterns for multi-hop queries: [inexture](https://www.inexture.ai/agentic-rag-with-langgraph-adaptive-retrieval-production/)

- Sequential (Methodological Path): `UsulFiqhAgent -> FiqhAgent -> HadithAgent` for questions about how a ruling is derived.
- Parallel (Holistic Path): `FiqhAgent`, `HadithAgent`, and `TazkiyahAgent` run concurrently on questions like fasting to cover rulings, narrations, and spiritual meanings.
- Hierarchical (Scholar Council): a supervisor agent coordinates multiple madhhab-specific `FiqhAgent` instances for ikhtilaf presentation and tarjih.

Orchestration is implemented as a LangGraph `StateGraph` where nodes are agent calls and edges encode routing logic. [docs.langchain](https://docs.langchain.com/oss/python/langgraph/agentic-rag)

***

## 10. Evaluation Framework

Burhan uses a "Golden Test Set" (~10k Arabic QA pairs) and modern evaluation tools to benchmark: [dev](https://dev.to/dowhatmatters/a-complete-architecture-guide-for-rag-agent-systems-454i)

- Retrieval quality (Recall@k per agent/collection).
- Citation precision and groundedness.
- Ikhtilaf coverage and hallucination rate.
- Authenticity grade correctness for hadith.

Evaluation is performed with tools like Ragas (Arabic-ready) and LLM-based judges tuned to penalize unsupported religious claims. [dev](https://dev.to/dowhatmatters/a-complete-architecture-guide-for-rag-agent-systems-454i)

***

## 11. Production Deployment Considerations

### 11.1 Embedding and Inference Optimization

- Use BGE-M3 or multilingual E5 for retrieval, as they provide strong multi-lingual, multi-granularity performance for long Arabic documents. [raw.githubusercontent](https://raw.githubusercontent.com/upstash/FlagEmbedding/master/research/BGE_M3/BGE_M3.pdf)
- Convert embedding models to ONNX and run with ONNX Runtime or similar for CPU acceleration. [github](https://github.com/yuniko-software/bge-m3-onnx)
- Apply scalar quantization (`int8`) at the vector DB layer to shrink memory footprint by ~4x while retaining most accuracy. [pub.towardsai](https://pub.towardsai.net/pplx-embed-qdrant-building-production-grade-semantic-search-with-quantization-cea9626b8c7c)

### 11.2 Indexing Strategy

- Page-level chunking for fiqh and tafsir to preserve ruling context. [ppl-ai-file-upload.s3.amazonaws](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/57452145/f33d27d0-36ae-4a87-b8b8-696472d31141/chat-Search-Burhan-Dataset.txt)
- 256-token chunks for hadith to guarantee matn + isnad remain in a single vector.
- Prioritize indexing for hadith and fiqh collections, as they dominate query volume and require strongest guarantees. [ppl-ai-file-upload.s3.amazonaws](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/57452145/f33d27d0-36ae-4a87-b8b8-696472d31141/chat-Search-Burhan-Dataset.txt)

***

## 12. Non-Goals

The current specification does not cover:

- Frontend/UI design for Burhan consumer applications.
- Dataset ingestion/cleaning tools beyond enriched payload structure.
- Detailed DevOps pipelines (CI/CD, monitoring stack, etc.).

Those aspects are documented separately in deployment and operations guides.

***

