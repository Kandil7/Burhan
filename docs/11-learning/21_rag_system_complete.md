# 🕌 Athar RAG System - Complete Step-by-Step Walkthrough

## Every Single Step Explained in Detail

This document provides an exhaustive explanation of how a query flows through the entire Athar RAG system - from the moment a user submits a question until they receive an answer with citations.

---

## 📊 High-Level Flow

```
User Query → Intent Classification → Agent Routing → Document Retrieval → Verification → LLM Generation → Response
```

Let's go through each step in detail.

---

## Step 1: User Query Received

### HTTP Entry Point
**File**: `src/api/main.py`

```python
app = FastAPI(
    title="Athar Islamic QA API",
    version="0.5.0",
)

app.include_router(ask_router, prefix="/api/v1")
```

### Endpoint Handler
**File**: `src/api/routes/ask.py`

```python
@ask_router.post("", response_model=AskResponse)
async def ask_question(request: AskRequest) -> AskResponse:
```

### Request Model
```python
class AskRequest(BaseModel):
    query: str = Field(..., description="User question")
    language: str = Field(default="ar", description="Query language")
    collection: str | None = Field(default=None, description="Target collection")
    madhhab: str | None = Field(default=None, description="Preferred madhhab")
```

### Example Request
```bash
POST /api/v1/ask
{
  "query": "ما حكم ترك صلاة الجمعة عمداً؟",
  "language": "ar"
}
```

### What Happens
1. FastAPI validates the request using Pydantic
2. If invalid, returns 422 error with details
3. If valid, creates `AskRequest` object
4. Passes to service layer

---

## Step 2: Intent Classification (Hybrid Classifier)

### Purpose
Determine what type of question the user is asking to route to the correct agent.

### Algorithm
The system uses a **Hybrid Intent Classifier** with multiple tiers:

```
Tier 1: Keyword Fast-Path (highest priority)
    ↓ (if keyword confidence < 0.85)
Tier 2: Embedding Fallback (semantic similarity)
    ↓
Tier 3: Default to keyword result
```

### Implementation
**File**: `src/application/router/hybrid_classifier.py`

```python
class MasterHybridClassifier(IntentClassifier):
    async def classify(self, query: str) -> ClassificationResult:
        # Tier 1: Keyword
        kw_result = await self._keyword_classifier.classify(query)
        
        if kw_result.confidence >= 0.85:
            return kw_result  # High confidence - return immediately
        
        # Tier 2: Embedding
        if self._embedding_classifier:
            emb_result = await self._embedding_classifier.classify(query)
            if emb_result.confidence > kw_result.confidence:
                return emb_result
        
        # Tier 3: Return keyword result
        return kw_result
```

### Keyword Detection
**File**: `src/application/router/classifier_factory.py`

```python
class KeywordBasedClassifier:
    KEYWORD_PATTERNS = {
        Intent.FIQH: [
            re.compile(r"حكم| halal| حرام| فقة", re.IGNORECASE),
            re.compile(r"ماذا يحكم|ما حكم", re.IGNORECASE),
        ],
        Intent.HADITH: [
            re.compile(r"حديث|صحيح|ضعيف", re.IGNORECASE),
            re.compile(r"حديث رقم|روا", re.IGNORECASE),
        ],
        Intent.TAFSIR: [
            re.compile(r"تفسير|معنى آية", re.IGNORECASE),
            re.compile(r"فسير سورة", re.IGNORECASE),
        ],
        # ... 16 intents total
    }
    
    async def classify(self, query: str) -> ClassificationResult:
        normalized = _normalize_arabic(query)
        for intent, patterns in KEYWORD_PATTERNS.items():
            matches = sum(1 for p in patterns if p.search(normalized))
            if matches >= 2:
                return ClassificationResult(
                    intent=intent,
                    confidence=min(0.85 + (matches * 0.05), 0.95),
                    requires_retrieval=True,
                )
        return ClassificationResult(..., confidence=0.3)
```

### Intent Types Supported
**File**: `src/domain/intents.py`

```python
class Intent(str, Enum):
    FIQH = "fiqh"                    # Islamic jurisprudence
    HADITH = "hadith"                # Hadith questions
    TAFSIR = "tafsir"               # Quran interpretation
    AQEEDAH = "aqeedah"              # Islamic theology
    SEERAH = "seerah"               # Prophet biography
    USUL_FIQH = "usul_fiqh"         # Principles of jurisprudence
    ISLAMIC_HISTORY = "islamic_history"  # Islamic history
    ARABIC_LANGUAGE = "arabic_language"  # Arabic language
    ZAKAT = "zakat"                  # Zakat calculation
    INHERITANCE = "inheritance"       # Inheritance calculation
    QURAN = "quran"                  # Quran verses
    DUA = "dua"                      # Supplications
    GREETING = "greeting"             # Greetings
    ISLAMIC_KNOWLEDGE = "islamic_knowledge"  # General
```

### Output
```python
ClassificationResult(
    intent=Intent.FIQH,
    confidence=0.90,
    language="ar",
    requires_retrieval=True,
)
```

---

## Step 3: Agent Routing

### Purpose
Route the query to the correct CollectionAgent based on intent.

### Implementation
**File**: `src/core/registry.py`

```python
class AgentRegistry:
    def __init__(self):
        self._agents: dict[str, CollectionAgent] = {}
    
    def register(self, name: str, agent: CollectionAgent):
        self._agents[name] = agent
    
    def get(self, route: str) -> CollectionAgent | None:
        return self._agents.get(route)
    
    def get_for_intent(self, intent: Intent) -> str:
        """Map intent to agent route."""
        INTENT_ROUTING = {
            Intent.FIQH: "fiqh:rag",
            Intent.HADITH: "hadith:rag",
            Intent.TAFSIR: "tafsir:rag",
            # ...
        }
        return INTENT_ROUTING.get(intent, "general:rag")
```

### Routing Decision
**File**: `src/application/router/router_agent.py`

```python
class RouterAgent:
    def __init__(self, classifier, conf_threshold=0.5):
        self._classifier = classifier
        self._conf_threshold = conf_threshold
    
    async def route(self, query: str) -> RoutingDecision:
        result = await self._classifier.classify(query)
        route = get_agent_for_intent(result.intent)
        
        return RoutingDecision(
            result=result,
            route=route,
            agent_metadata={}
        )
```

### Agent Selection
```python
route = "fiqh:rag"
agent = registry.get(route)  # FiQHCollectionAgent
```

---

## Step 4: Document Retrieval (Multi-Stage)

### Stage 4.1: Query Transformation

**File**: `src/agents/collection/fiqh.py`

```python
def _get_retrieval_query(self, user_query: str) -> str:
    """Transform user query for better retrieval."""
    # Example: "ما حكم الزكاة" → "حكم الزكاة فيIslam"
    # Add domain-specific terms
    return f"حكم {user_query} في الفقة الإسلامي"
```

### Stage 4.2: Strategy Selection

**File**: `src/retrieval/strategies.py`

```python
RETRIEVAL_MATRIX = {
    "fiqh:rag": RetrievalStrategy(
        collection="fiqh_passages",
        top_k=15,
        filters={"type": "fiqh"},
        rerank=True,
    ),
    "hadith:rag": RetrievalStrategy(
        collection="hadith_passages",
        top_k=10,
        filters={"grade": "sahih"},
        rerank=True,
    ),
    # ... per-agent configs
}

def get_strategy_for_agent(agent_name: str) -> RetrievalStrategy:
    return RETRIEVAL_MATRIX.get(agent_name, DEFAULT_STRATEGY)
```

### Stage 4.3: Hybrid Search

**File**: `src/retrieval/retrievers/hybrid_retriever.py`

```python
class HybridSearcher:
    def __init__(self, qdrant_client, embedding_model):
        self._semantic = DenseRetriever(qdrant_client, embedding_model)
        self._bm25 = BM25Retriever()
        self._rrf = ReciprocalRankFusion(k=60)
    
    async def search(
        self,
        query: str,
        collection: str,
        top_k: int = 10,
    ) -> list[RetrievalResult]:
        # 1. Semantic search (embeddings)
        semantic_results = await self._semantic.search(
            query, collection, top_k * 2
        )
        
        # 2. Keyword search (BM25)
        keyword_results = await self._bm25.search(
            query, collection, top_k * 2
        )
        
        # 3. Fuse results using RRF
        fused = self._rrf.fuse(
            semantic_results, 
            keyword_results,
            k=60  # RRF parameter
        )
        
        return fused[:top_k]
```

### Stage 4.3a: Semantic Search (Dense)

**File**: `src/retrieval/retrievers/dense_retriever.py`

```python
class DenseRetriever:
    async def search(self, query, collection, top_k):
        # 1. Embed the query
        query_embedding = await self._model.encode([query])
        
        # 2. Search Qdrant
        results = await self._qdrant.search(
            collection=collection,
            query_vector=query_embedding[0].tolist(),
            limit=top_k,
            score_threshold=0.5,
        )
        
        return [self._to_result(r) for r in results]
```

### Stage 4.3b: Keyword Search (BM25)

**File**: `src/retrieval/retrievers/bm25_retriever.py`

```python
class BM25Retriever:
    async def search(self, query, collection, top_k):
        # Uses rank_bm25 library
        # Classic information retrieval algorithm
        scores = self._index.score(query)
        
        # Get top results
        top_indices = sorted(
            range(len(scores)), 
            key=lambda i: scores[i],
            reverse=True
        )[:top_k]
        
        return [self._to_result(i, scores[i]) for i in top_indices]
```

### Stage 4.3c: Reciprocal Rank Fusion

**File**: `src/retrieval/fusion/rrf.py`

```python
class ReciprocalRankFusion:
    def fuse(self, list_a, list_b, k=60):
        """Combine rankings from two retrievers."""
        
        # Score each document
        scores = {}
        
        # Add scores from list_a (semantic)
        for rank, result in enumerate(list_a):
            doc_id = result.id
            scores[doc_id] = scores.get(doc_id, 0) + 1.0 / (k + rank + 1)
        
        # Add scores from list_b (BM25)
        for rank, result in enumerate(list_b):
            doc_id = result.id
            scores[doc_id] = scores.get(doc_id, 0) + 1.0 / (k + rank + 1)
        
        # Sort by combined score
        sorted_docs = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        
        return [self._to_result(doc_id, score) for doc_id, score in sorted_docs]
```

### Stage 4.4: Filtering

**File**: `src/retrieval/filters/builder.py`

```python
class FilterBuilder:
    def build(self, filters: dict) -> QdrantFilter:
        """Build Qdrant filter from dict."""
        must = []
        
        for key, value in filters.items():
            must.append({
                "key": key,
                "match": {"value": value}
            })
        
        return {"must": must} if must else None
```

### Stage 4.5: Reranking (Optional)

**File**: `src/retrieval/ranking/reranker.py`

```python
class CrossEncoderReranker:
    async def rerank(self, query, results, top_k=10):
        # Use cross-encoder for more accurate scoring
        pairs = [(query, r.text) for r in results]
        
        # Get scores
        scores = await self._model.predict(pairs)
        
        # Re-sort by cross-encoder scores
        reranked = sorted(
            zip(results, scores),
            key=lambda x: x[1],
            reverse=True
        )
        
        return [r for r, s in reranked[:top_k]]
```

### Output: List of RetrievalPassage

```python
class RetrievalPassage(BaseModel):
    id: str
    text: str
    score: float
    collection: str
    metadata: dict  # book_title, author, page, etc.
```

---

## Step 5: Verification

### Purpose
Validate that the retrieved passages actually support the answer before sending to LLM.

### Implementation
**File**: `src/verifiers/suite_builder.py`

```python
async def run_verification_suite(
    answer: str,
    passages: list[RetrievalPassage],
    suite: VerificationSuite,
) -> VerificationReport:
    
    results = []
    
    for check in suite.checks:
        if not check.enabled:
            continue
        
        result = await _run_check(check.name, answer, passages)
        results.append(result)
        
        if check.fail_policy == "abstain" and result.status == "failed":
            return VerificationReport(
                status="abstained",
                confidence=0.0,
                abstention_reason=f"Check {check.name} failed",
            )
    
    # Compute overall confidence
    passed = sum(1 for r in results if r.passed)
    confidence = passed / len(results) if results else 0.0
    
    return VerificationReport(
        status="passed" if confidence > 0.7 else "failed",
        confidence=confidence,
        verified_passages=[r for r in results if r.passed],
    )
```

### Verification Checks

| Check | Purpose | Fail Policy |
|-------|---------|------------|
| **Quote Validation** | Verify answer quotes match passages | abstain/warn |
| **Source Attribution** | Verify sources are correct | warn |
| **Hadith Grade** | Verify hadith grade is accurate | abstain |
| **Contradiction** | Check for self-contradictions | proceed |
| **Evidence Sufficiency** | Check enough evidence | abstain |

### Quote Validation Example
**File**: `src/verifiers/exact_quote.py`

```python
class ExactQuoteVerifier:
    async def verify(self, answer: str, passages: list) -> CheckResult:
        # Extract quotes from answer (e.g., [C1], [C2])
        quote_refs = re.findall(r"\[C(\d+)\]", answer)
        
        for ref in quote_refs:
            passage = get_passage_by_ref(ref)
            
            # Check if quote text exists in passage
            if quote_text not in passage.text:
                return CheckResult(
                    passed=False,
                    reason=f"Quote [C{ref}] not found in passage",
                )
        
        return CheckResult(passed=True)
```

### Output: VerificationReport

```python
class VerificationReport(BaseModel):
    status: str          # "passed", "failed", "abstained"
    confidence: float    # 0.0 - 1.0
    verified_passages: list[str]
    abstained: bool
    abstention_reason: str | None
```

---

## Step 6: Answer Generation (LLM)

### Purpose
Generate an answer using the retrieved and verified passages + LLM.

### Implementation
**File**: `src/agents/collection/fiqh.py`

```python
async def generate(self, query: str, passages: list[RetrievalPassage]) -> str:
    # 1. Build prompt
    prompt = self._build_prompt(query, passages)
    
    # 2. Call LLM
    response = await self._llm.chat.completions.create(
        model="mixtral-8x7b-32768",
        messages=[
            {"role": "system", "content": self._system_prompt},
            {"role": "user", "content": prompt},
        ],
        temperature=0.3,
        max_tokens=1024,
    )
    
    # 3. Return generated text
    return response.choices[0].message.content
```

### Prompt Building
**File**: `src/agents/collection/fiqh.py`

```python
def _build_prompt(self, query: str, passages: list[RetrievalPassage]) -> str:
    # Build context from passages
    contexts = "\n\n".join([
        f"[{i+1}] {p.text}\n— {p.metadata.get('book_title', 'Unknown')}"
        for i, p in enumerate(passages)
    ])
    
    # Build full prompt
    prompt = f"""\
    السؤال: {query}

    المصادر:
    {contexts}

    Instructions:
    - أجب بالعربية بناءً على المصادر المقدمة
    - استشهد بالم_sources باستخدام [C1], [C2], etc.
    - إذا لم تجد إجابة في المصادر، قل "لا أعرف"
    - Mention the view of major scholars (Abu Hanifa, Malik, Shafi'i, Ahmad)
    """
    
    return prompt
```

### System Prompt
**File**: `prompts/fiqh_agent.txt`

```
أنت عالم إسلامي متخصص في الفقه الإسلامي.
تجيب على أسئلة الفقه بناءً على المصادر الموثوقة.
تMention آراء المذاهب الأربعة عندما تختلف.
Always cite your sources using [C1], [C2], etc.
```

### Post-Processing: Remove CoT Leakage
**File**: `src/agents/base.py`

```python
def strip_cot_leakage(text: str) -> str:
    """Remove chain-of-thought markers from generated text."""
    patterns = [
        r"##?\s*(Analysis|Reasoning|Thought).*?\n\n",
        r"<\s*(analysis|reasoning)\s*>\s*",
        r"###\s*(?:Let me|I'll).*?\n\s*",
    ]
    
    for pattern in patterns:
        text = re.sub(pattern, "", text, flags=re.IGNORECASE)
    
    return text.strip()
```

---

## Step 7: Build Citations

### Purpose
Create citation objects from retrieved passages.

```python
def _build_citations(self, passages: list[RetrievalPassage]) -> list[Citation]:
    citations = []
    
    for i, passage in enumerate(passages, 1):
        citations.append(Citation(
            source_id=f"C{i}",
            text=passage.text[:200],  # First 200 chars
            book_title=passage.metadata.get("book_title"),
            page=passage.metadata.get("page_number"),
            grade=passage.metadata.get("grade"),  # For hadith
        ))
    
    return citations
```

---

## Step 8: Build Response

### Final Response Model
**File**: `src/api/schemas/ask.py`

```python
class AskResponse(BaseModel):
    answer: str                          # Generated answer
    citations: list[CitationResponse]    # Citations
    intent: str                         # Detected intent
    confidence: float                  # Confidence score
    processing_time_ms: int            # Time taken
```

### Example Response
```json
{
  "answer": "صلاة الجمعة فرض عين على كل رجل مسلم بالغ عاقل، في قوله تعالى: {البقرة 272}. وقد ذهب الجمهور إلى وجوبها، لكن لها قول آخر عند الحنفية. [C1], [C2]",
  "citations": [
    {
      "source_id": "C1",
      "text": "الجمعة فرض عين",
      "book_title": "الموسوعة الفقهية",
      "page": 123,
      "grade": null
    },
    {
      "source_id": "C2", 
      "text": "وله قول آخر",
      "book_title": "بدائع الصنائع",
      "page": 456,
      "grade": null
    }
  ],
  "intent": "fiqh",
  "confidence": 0.87,
  "processing_time_ms": 1250
}
```

---

## Complete Flow Diagram

```
User Query: "ما حكم ترك صلاة الجمعة عمداً؟"
           │
           ▼
┌─────────────────────────────────────┐
│  1. API Validation (FastAPI)        │
│     src/api/routes/ask.py          │
└─────────────────────────────────────┘
           │
           ▼
┌─────────────────────────────────────┐
│  2. Intent Classification          │
│     Hybrid Classifier (Phase 8)    │
│     - Keyword Fast-Path             │
│     - Embedding Fallback            │
│     → Intent.FIQH (0.90)           │
└─────────────────────────────────────┘
           │
           ▼
┌─────────────────────────────────────┐
│  3. Agent Routing                  │
│     AgentRegistry                  │
│     → FiQHCollectionAgent         │
└─────────────────────────────────────┘
           │
           ▼
┌─────────────────────────────────────┐
│  4. Document Retrieval              │
│     - Query Transform              │
│     - Strategy Selection           │
│     - Hybrid Search (RRF)          │
│       • Semantic (BGE-M3)           │
│       • Keyword (BM25)               │
│     → Top 15 passages              │
└─────────────────────────────────────┘
           │
           ▼
┌─────────────────────────────────────┐
│  5. Verification                   │
│     VerificationSuite              │
│     - Quote validation             │
│     - Source attribution            │
│     → Confidence: 0.85             │
└─────────────────────────────────────┘
           │
           ▼
┌─────────────────────────────────────┐
│  6. LLM Generation                  │
│     Mixtral-8x7b                   │
│     - Build prompt                 │
│     - Call LLM                      │
│     - Strip CoT leakage            │
└─────────────────────────────────────┘
           │
           ▼
┌─────────────────────────────────────┐
│  7. Build Citations                │
│     From retrieved passages         │
└─────────────────────────────────────┘
           │
           ▼
┌─────────────────────────────────────┐
│  8. Return Response                 │
│     AskResponse with citations      │
└─────────────────────────────────────┘
           │
           ▼
   User receives answer with sources
```

---

## Timing Breakdown (Typical)

| Step | Time (ms) | Percentage |
|------|----------|-----------|
| API Validation | 5 | 0.4% |
| Intent Classification | 15 | 1.2% |
| Agent Routing | 2 | 0.2% |
| Document Retrieval | 450 | 36% |
| Verification | 200 | 16% |
| LLM Generation | 550 | 44% |
| Build Response | 28 | 2% |
| **Total** | **1250** | **100%** |

---

## Key Files Reference

| Step | File |
|------|------|
| API Entry | `src/api/routes/ask.py` |
| Intent Classification | `src/application/router/hybrid_classifier.py` |
| Keywords | `src/application/router/classifier_factory.py` |
| Intents | `src/domain/intents.py` |
| Agent Routing | `src/core/registry.py` |
| Hybrid Search | `src/retrieval/retrievers/hybrid_retriever.py` |
| RRF | `src/retrieval/fusion/rrf.py` |
| Verification Suite | `src/verifiers/suite_builder.py` |
| Quote Validation | `src/verifiers/exact_quote.py` |
| Generation | `src/agents/collection/fiqh.py` |
| CoT Stripping | `src/agents/base.py` |

---

**Related Documentation**:
- [18_src_modules_complete_guide.md](18_src_modules_complete_guide.md)
- [19_complete_file_index.md](19_complete_file_index.md)

**Last Updated**: April 2026