# Burhan Islamic QA System — Detailed Architecture

> **Version:** 0.5.0 | **Phase:** 6 — Multi-Agent & Mini-Dataset | **Date:** April 13, 2026  
> **Based on:** Fanar-Sadiq Multi-Agent Architecture for Grounded Islamic QA  
> **Repository:** https://github.com/Kandil7/Burhan

---

## Table of Contents

1. [System Overview](#1-system-overview)
2. [4-Layer Architecture](#2-4-layer-architecture)
3. [Query Flow (Detailed)](#3-query-flow-detailed)
4. [Intent Classification System](#4-intent-classification-system)
5. [Active Agents (6)](#5-active-agents-6)
6. [Deterministic Tools (5)](#6-deterministic-tools-5)
7. [RAG Infrastructure](#7-rag-infrastructure)
8. [Citation System](#8-citation-system)
9. [Data Pipeline](#9-data-pipeline)
10. [Configuration System](#10-configuration-system)
11. [API Endpoints (18 Total)](#11-api-endpoints-18-total)
12. [Security Architecture](#12-security-architecture)
13. [Deployment Architecture](#13-deployment-architecture)
14. [Current State & Future Work](#14-current-state--future-work)

---

## 1. System Overview

### What is Burhan?

**Burhan** (أثر) is a production-ready, multi-agent Islamic Question & Answer system built on the **Fanar-Sadiq** research architecture. It provides grounded, citation-backed answers to religious questions across 16 intent types, combining probabilistic LLM reasoning with deterministic calculators and verified source retrieval.

The system answers questions like:
- *"ما حكم زكاة الأسهم؟"* → RAG pipeline retrieves fiqh passages, generates answer with citations
- *"Calculate my inheritance"* → Deterministic calculator applies fara'id rules
- *"What are prayer times in Mecca?"* → Astronomical calculation with 6 methods
- *"Is this text from the Quran?"* → Quotation validator checks against 6,236 verses

### Key Metrics

| Metric | Value | Notes |
|--------|-------|-------|
| **Lines of Code** | 14,200+ | Python (FastAPI backend) |
| **Total Files** | 120+ | Backend, scripts, tests, docs |
| **Active Agents** | 6 | Fiqh, Hadith, Seerah, General, Chatbot, BaseRAG |
| **Deterministic Tools** | 5 | Zakat, Inheritance, Prayer, Hijri, Dua |
| **Intent Types** | 16 | fiqh, quran, hadith, zakat, inheritance, etc. |
| **Vector Collections** | 10 | Qdrant with 11,147+ vectors |
| **API Endpoints** | 18 | Query, tools, Quran, RAG, health |
| **Test Coverage** | ~91% | 121 passing tests |
| **Production Score** | 8.1/10 | Improved from 6.6/10 |

### Technology Stack

| Layer | Technology | Version | Purpose |
|-------|-----------|---------|---------|
| **Language** | Python | 3.12+ | Backend runtime |
| **Framework** | FastAPI | 0.115+ | HTTP API with async support |
| **Database** | PostgreSQL | 16 | Quran text, translations, tafsir |
| **Vector DB** | Qdrant | Latest | 10 collections, semantic search |
| **Cache** | Redis | 7 | Embedding cache, session storage |
| **LLM** | Groq / OpenAI | Qwen3-32B / GPT-4o-mini | Intent classification, answer generation |
| **Embeddings** | BAAI/bge-m3 | 1024 dims, 8192 tokens | Text vectorization |
| **Package Mgmt** | Poetry | 1.8+ | Dependency management |
| **Containerization** | Docker Compose | 3.9 | Development services |
| **Logging** | structlog | 24.x | Structured JSON logging |
| **Type Checking** | MyPy | Strict mode | Static type analysis |
| **Linting** | Ruff | Latest | Code quality & formatting |

### Why This Stack?

- **BAAI/bge-m3 over Qwen3-Embedding**: Superior multilingual support (100+ languages), 8192-token context window (vs 512), and optimized for retrieval tasks — critical for Arabic/Islamic text
- **Qdrant over Pinecone**: Open-source, self-hostable, supports payload filtering (needed for faceted search by author/era/book), and runs on CPU
- **Groq over OpenAI**: 10x faster inference for Qwen3-32B, lower cost, deterministic outputs at temperature 0.1
- **PostgreSQL over MongoDB**: ACID compliance for Quran text, native full-text search, mature ORM support

---

## 2. 4-Layer Architecture

Burhan follows a clean 4-layer architecture with strict separation of concerns. Each layer has a single responsibility and communicates with adjacent layers through well-defined interfaces.

```
┌─────────────────────────────────────────────────────────────────────┐
│                        API Layer (FastAPI)                           │
│                                                                      │
│  POST /api/v1/query    POST /api/v1/tools/zakat                     │
│  GET  /api/v1/quran/surahs   POST /api/v1/tools/inheritance         │
│  POST /api/v1/rag/fiqh   POST /api/v1/tools/prayer-times             │
│  GET  /health   GET /ready   POST /api/v1/tools/hijri                │
│                              POST /api/v1/tools/duas                 │
│  18 endpoints total • OpenAPI docs at /docs                         │
│  Middleware: CORS → Rate Limit → Security Headers → Error Handler   │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│                     Orchestration Layer                              │
│                                                                      │
│  ┌────────────────────────┐  ┌─────────────────────────────┐        │
│  │  HybridQueryClassifier │  │  Response Orchestrator       │        │
│  │  (src/core/router.py)  │  │  (src/api/routes/query.py)   │        │
│  │                        │  │                              │        │
│  │  Tier 1: Keywords      │  │  Routes intent → agent/tool  │        │
│  │  Tier 2: LLM           │  │  Builds AgentInput           │        │
│  │  Tier 3: Embedding     │  │  Constructs QueryResponse    │        │
│  └────────────────────────┘  └─────────────────────────────┘        │
│  ┌──────────────────────────────────────────────────────────┐       │
│  │  CitationNormalizer (src/core/citation.py)               │       │
│  │  Regex patterns → [C1],[C2] → Enriched metadata          │       │
│  └──────────────────────────────────────────────────────────┘       │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    Agents & Tools Layer                              │
│                                                                      │
│  ┌────────────┬────────────┬────────────┬──────────────┐            │
│  │ FiqhAgent  │ HadithAgent│ SeerahAgent│GeneralAgent  │            │
│  │ (RAG)      │ (RAG)      │ (RAG)      │ (RAG)        │            │
│  └────────────┴────────────┴────────────┴──────────────┘            │
│  ┌────────────┬────────────┬────────────┬──────────────┐            │
│  │ Chatbot    │ ZakatCalc  │Inheritance │ PrayerTimes   │            │
│  │ Agent      │            │ Calculator │ Tool          │            │
│  └────────────┴────────────┴────────────┴──────────────┘            │
│  ┌────────────┬────────────┐                                        │
│  │ HijriCal   │ DuaRetrieval│                                       │
│  │ Tool       │ Tool       │                                        │
│  └────────────┴────────────┘                                        │
│                                                                      │
│  6 Active Agents + 5 Deterministic Tools                            │
│  Base classes: BaseAgent, BaseRAGAgent, BaseTool                    │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│                       Knowledge Layer                                │
│                                                                      │
│  ┌──────────────────────┐  ┌──────────────────────────────────┐     │
│  │ PostgreSQL 16        │  │ Qdrant (10 collections)          │     │
│  │ - Quran text (6,236) │  │ - fiqh_passages (10,132 vectors) │     │
│  │ - Translations       │  │ - hadith_passages (160+ vectors) │     │
│  │ - Tafsir             │  │ - general_islamic, + 7 more      │     │
│  └──────────────────────┘  └──────────────────────────────────┘     │
│  ┌──────────────────────┐  ┌──────────────────────────────────┐     │
│  │ Redis 7              │  │ LLM Provider (Groq/OpenAI)       │     │
│  │ - Embedding cache    │  │ - Qwen3-32B (Groq)               │     │
│  │ - 7-day TTL          │  │ - GPT-4o-mini (OpenAI)           │     │
│  └──────────────────────┘  └──────────────────────────────────┘     │
│  ┌──────────────────────────────────────────────────────────┐       │
│  │ BAAI/bge-m3 Embedding Model (CPU/GPU, 1024 dims)         │       │
│  └──────────────────────────────────────────────────────────┘       │
└─────────────────────────────────────────────────────────────────────┘
```

### Layer Responsibilities

| Layer | Responsibility | Key Files | Design Pattern |
|-------|---------------|-----------|----------------|
| **API** | HTTP handling, validation, serialization, middleware | `src/api/routes/*.py`, `src/api/schemas/*.py` | Factory pattern (`create_app()`) |
| **Orchestration** | Intent classification, agent routing, citation normalization | `src/core/router.py`, `src/core/citation.py` | Strategy pattern (3-tier classification) |
| **Agents/Tools** | Domain-specific logic, retrieval, generation, calculation | `src/agents/*.py`, `src/tools/*.py` | Command pattern (`execute()` method) |
| **Knowledge** | Data storage, embedding, search, caching | `src/knowledge/*.py`, `src/quran/*.py`, `src/infrastructure/db.py` | Repository pattern |

### Why 4 Layers?

The 4-layer design enables:
1. **Testability**: Each layer can be unit-tested in isolation (e.g., test classifier without LLM)
2. **Replaceability**: Swap Qdrant for Weaviate without changing agent logic
3. **Scalability**: Deploy API layer separately from knowledge layer (different resource needs)
4. **Maintainability**: Clear boundaries prevent spaghetti code; new agents inherit from `BaseRAGAgent`

---

## 3. Query Flow (Detailed)

This section traces a complete query from user input to final response, showing every decision point and data transformation.

### ASCII Flow Diagram

```
User Query: "ما حكم صلاة الجمعة؟"
         │
         ▼
┌─────────────────────────────────┐
│  POST /api/v1/query              │
│  src/api/routes/query.py:128     │
│                                  │
│  1. Validate request (Pydantic)  │
│  2. Generate query_id (UUID)     │
│  3. Start timer                  │
└────────────┬────────────────────┘
             │
             ▼
┌─────────────────────────────────┐
│  HybridQueryClassifier.classify()│
│  src/core/router.py:116          │
│                                  │
│  ┌───────────────────────────┐  │
│  │ TIER 1: Keyword Match     │  │
│  │ "حكم" → FIQH (0.92)      │  │
│  │ ✅ Match >= 0.90? YES     │  │
│  │ → Return immediately      │  │
│  └───────────────────────────┘  │
│                                  │
│  Result: intent=fiqh,           │
│          confidence=0.92,        │
│          method="keyword"        │
└────────────┬────────────────────┘
             │
             ▼
┌─────────────────────────────────┐
│  Response Orchestrator           │
│  query.py:156-180                │
│                                  │
│  Intent = FIQH → FiqhAgent       │
│  Build AgentInput:               │
│  - query: "ما حكم صلاة الجمعة؟" │
│  - language: "ar"               │
│  - metadata: {madhhab, filters}  │
└────────────┬────────────────────┘
             │
             ▼
┌─────────────────────────────────┐
│  FiqhAgent.execute()             │
│  src/agents/fiqh_agent.py:130    │
│                                  │
│  Step 1: Initialize deps         │
│  Step 2: Embed query (bge-m3)    │
│  Step 3: Hybrid search           │
│    - Semantic: 15 passages       │
│    - Keyword: BM25 fusion        │
│  Step 4: Filter by score >= 0.65 │
│  Step 5: Format passages [C1]..  │
│  Step 6: LLM generation          │
│    - System: Fiqh prompt         │
│    - User: query + passages      │
│    - Model: qwen/qwen3-32B       │
│    - Temp: 0.1                   │
│  Step 7: Normalize citations     │
│  Step 8: Add disclaimer          │
│                                  │
│  Output: AgentOutput             │
│  - answer: "بناءً على النصوص..."│
│  - citations: [C1, C2, C3]       │
│  - confidence: 0.78              │
└────────────┬────────────────────┘
             │
             ▼
┌─────────────────────────────────┐
│  QueryResponse construction      │
│  src/api/schemas/response.py     │
│                                  │
│  {                               │
│    "query_id": "uuid-...",       │
│    "intent": "fiqh",             │
│    "intent_confidence": 0.92,    │
│    "answer": "بناءً على...",     │
│    "citations": [...],           │
│    "metadata": {                 │
│      "agent": "fiqh_agent",      │
│      "processing_time_ms": 257,  │
│      "classification_method":    │
│        "keyword",                │
│      "retrieved_count": 15,      │
│      "used_count": 5             │
│    }                             │
│  }                               │
└────────────┬────────────────────┘
             │
             ▼
    HTTP 200 OK → User receives JSON
```

### 3-Tier Intent Classification

The classifier uses a cascading approach to balance speed and accuracy:

```
┌──────────────────────────────────────────────────────────────┐
│                    Classification Pipeline                    │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  Tier 1: KEYWORD MATCHING (Fast Path)                        │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ Check query against 80+ keyword patterns             │   │
│  │ If match confidence >= 0.90 → Return immediately     │   │
│  │ Speed: <1ms, No LLM call, No network                 │   │
│  │ Coverage: ~60% of queries                            │   │
│  └──────────────────────────────────────────────────────┘   │
│                          │ No match                          │
│                          ▼                                   │
│  Tier 2: LLM CLASSIFICATION (Primary Path)                   │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ Send structured prompt to Groq/OpenAI                │   │
│  │ Parse JSON response {intent, confidence, reason}     │   │
│  │ If confidence >= 0.75 → Return                       │   │
│  │ Speed: ~200ms, LLM call required                     │   │
│  │ Coverage: ~30% of queries                            │   │
│  └──────────────────────────────────────────────────────┘   │
│                          │ Low confidence                    │
│                          ▼                                   │
│  Tier 3: EMBEDDING FALLBACK (Backup)                         │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ Compare query embedding to labeled examples          │   │
│  │ Cosine similarity → closest intent                   │   │
│  │ Speed: ~50ms, embedding model required               │   │
│  │ Coverage: ~10% of queries                            │   │
│  │ Status: Placeholder (Phase 5 pending)                │   │
│  └──────────────────────────────────────────────────────┘   │
│                          │ Fallback                          │
│                          ▼                                   │
│  DEFAULT: islamic_knowledge (confidence=0.5)                 │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

### Agent Routing Logic

After classification, the orchestrator routes to the appropriate component:

```python
# From src/config/intents.py: INTENT_ROUTING
INTENT_ROUTING = {
    Intent.FIQH: "fiqh_agent",              # RAG-based
    Intent.QURAN: "quran_agent",            # Pipeline (NL2SQL, verse retrieval)
    Intent.ISLAMIC_KNOWLEDGE: "general_islamic_agent",  # RAG-based
    Intent.GREETING: "chatbot_agent",       # Template-based
    Intent.ZAKAT: "zakat_tool",             # Deterministic
    Intent.INHERITANCE: "inheritance_tool", # Deterministic
    Intent.DUA: "dua_tool",                 # Retrieval
    Intent.HIJRI_CALENDAR: "hijri_tool",    # Deterministic
    Intent.PRAYER_TIMES: "prayer_tool",     # Deterministic
    Intent.HADITH: "hadith_agent",          # RAG-based
    Intent.SEERAH: "seerah_agent",          # RAG-based
    # Fallthrough intents (use general_islamic_agent):
    Intent.TAFSIR: "general_islamic_agent",
    Intent.AQEEDAH: "general_islamic_agent",
    Intent.USUL_FIQH: "general_islamic_agent",
    Intent.ISLAMIC_HISTORY: "general_islamic_agent",
    Intent.ARABIC_LANGUAGE: "general_islamic_agent",
}
```

### RAG Retrieval Pipeline

For RAG-based agents (Fiqh, Hadith, Seerah, General), the retrieval pipeline follows this flow:

```
Query → EmbeddingModel.encode() → 1024-dim vector
                                    │
                                    ▼
                          HybridSearcher.search()
                                    │
                    ┌───────────────┼───────────────┐
                    ▼               ▼               ▼
              Semantic Search  Keyword Search  Facet Filters
              (cosine sim)     (BM25-like)     (author, era)
                    │               │               │
                    └───────┬───────┘               │
                            ▼                       │
                  Reciprocal Rank Fusion            │
                  (k=60, combine scores)            │
                            │                       │
                            ▼                       ▼
                    Merged & Ranked Results (top-12)
                                    │
                                    ▼
                    Score Threshold Filter (>= 0.65)
                                    │
                                    ▼
                    TitleLoader.enrich_passages()
                    (add chapter/section context)
                                    │
                                    ▼
                    HadithGrader.enrich_passages()
                    (authenticity grading for hadith)
                                    │
                                    ▼
                    BookWeighter.weight_passages()
                    (importance scoring by book)
                                    │
                                    ▼
                    Top-5 passages formatted as [C1]..[C5]
                                    │
                                    ▼
                    LLM.generate(system_prompt + user_prompt)
                                    │
                                    ▼
                    CitationNormalizer.normalize()
                    → "بناءً على النصوص [C1] و [C2]..."
```

### Citation Normalization

The citation engine converts various reference formats to standardized `[C1]`, `[C2]` tags:

```
Input text: "As stated in Quran 2:255 and صحيح البخاري حديث 1234"
              │                              │
              ▼                              ▼
         Pattern match:              Pattern match:
         quran_reference             hadith_reference
              │                              │
              ▼                              ▼
         Citation(type="quran",       Citation(type="hadith",
                  source="Quran 2:255",       source="Sahih البخاري",
                  url="quran.com/2/255")      url="sunnah.com/bukhari/1234")
              │                              │
              └──────────┬───────────────────┘
                         ▼
              Enriched with passage metadata:
              - book_title, author, author_death
              - scholarly_era (classical, medieval, etc.)
              - page, chapter, section
                         │
                         ▼
              Output: "As stated in [C1] and [C2]..."
              Citations: [
                {id: "C1", type: "quran", source: "Quran 2:255", ...},
                {id: "C2", type: "hadith", source: "Sahih البخاري", ...}
              ]
```

---

## 4. Intent Classification System

### 16 Intent Types

| Intent | Description | Example Query | Handler | Retrieval? |
|--------|-------------|---------------|---------|------------|
| `fiqh` | Islamic jurisprudence rulings | "ما حكم ترك صلاة الجمعة؟" | FiqhAgent | ✅ RAG |
| `quran` | Quranic verses, surahs, tafsir | "كم عدد آيات سورة البقرة؟" | QuranAgent | ✅ NL2SQL |
| `islamic_knowledge` | General Islamic knowledge | "من هو ابن تيمية؟" | GeneralIslamicAgent | ✅ RAG |
| `greeting` | Greetings, salutations | "السلام عليكم" | ChatbotAgent | ❌ Template |
| `zakat` | Zakat calculation | "احسب زكاة مالي" | ZakatCalculator | ❌ Deterministic |
| `inheritance` | Inheritance distribution | "توزيع الميراث" | InheritanceCalculator | ❌ Deterministic |
| `dua` | Supplications and adhkar | "دعاء الصباح" | DuaRetrievalTool | ✅ Lookup |
| `hijri_calendar` | Hijri dates, conversions | "متى رمضان 2026؟" | HijriCalendarTool | ❌ Deterministic |
| `prayer_times` | Prayer times, Qibla | "مواقيت الصلاة في مكة" | PrayerTimesTool | ❌ Deterministic |
| `hadith` | Prophetic traditions | "حديث إنما الأعمال بالنيات" | HadithAgent | ✅ RAG |
| `tafsir` | Quran interpretation | "تفسير آية الكرسي" | GeneralIslamicAgent | ✅ RAG |
| `aqeedah` | Islamic creed and theology | "ما هو التوحيد؟" | GeneralIslamicAgent | ✅ RAG |
| `seerah` | Prophet's biography | "غزوة بدر الكبرى" | SeerahAgent | ✅ RAG |
| `usul_fiqh` | Jurisprudence principles | "ما هو القياس في الفقه؟" | GeneralIslamicAgent | ✅ RAG |
| `islamic_history` | Islamic civilization | "الدولة العباسية" | GeneralIslamicAgent | ✅ RAG |
| `arabic_language` | Arabic grammar, rhetoric | "ما هو الإعراب؟" | GeneralIslamicAgent | ✅ RAG |

### 3-Tier Classification Approach

#### Tier 1: Keyword Matching (`src/core/router.py:195`)

**How it works:** The query is lowercased and checked against 80+ predefined patterns across 16 intents. If a pattern matches with confidence >= 0.90, classification returns immediately without LLM call.

**Why this tier exists:** ~60% of queries contain clear intent signals (e.g., "زكاة" → zakat, "حكم" → fiqh). Keyword matching is 1000x faster than LLM classification (<1ms vs ~200ms).

**Keyword patterns by intent:**

| Intent | Key Patterns (Arabic) | Key Patterns (English) |
|--------|----------------------|----------------------|
| **fiqh** | حكم، ما حكم، هل يجوز، هل هو حلال | fiqh, halal, haram, Islamic law |
| **zakat** | زكاة، زكاة المال، نصاب، زكاة الذهب | zakat, zakat calculator |
| **inheritance** | ميراث، تركة، فرائض، عصبة | inheritance, inheritance calculator |
| **quran** | آية، سورة، قرآن، تفسير | ayah, surah, quran, tafsir |
| **hadith** | حديث، سند، متن، رواه، صحيح | hadith, sanad, matn |
| **greeting** | سلام، السلام عليكم، مرحبا | hello, hi, assalamu alaikum |
| **dua** | دعاء، ذكر، أذكار، استغفار | dua, adhkar, hisn al-muslim |
| **prayer_times** | مواقيت الصلاة، وقت الصلاة، قبلة | prayer times, qibla direction |
| **hijri_calendar** | هجري، رمضان، عيد، تاريخ | hijri, eid, hijri date |
| **seerah** | سيرة، النبي، السيرة النبوية | seerah, prophet biography |
| **islamic_knowledge** | من هو، ما هو، ما هي، شرح | who is, what is, explain |

#### Tier 2: LLM Classification (`src/core/router.py:218`)

**How it works:** When keyword matching fails or confidence < 0.90, a structured prompt is sent to the LLM (Groq/OpenAI). The prompt includes all 16 intent descriptions and asks for JSON output.

**Prompt structure:**
```
You are an expert intent classifier for an Islamic QA system called Burhan.

Available Intents:
- fiqh: Islamic jurisprudence (halal/haram, worship, transactions, rulings)
- quran: Quranic verses, surahs, tafsir, or Quran statistics
- islamic_knowledge: General Islamic knowledge (history, biography, theology)
... [all 16 intents]

Rules:
- Return ONLY valid JSON with fields: intent, confidence, language,
  requires_retrieval, sub_intent, reason, sub_questions

Examples:
Query: "ما حكم ترك صلاة الجمعة عمداً؟"
Output: {"intent":"fiqh","confidence":0.95,"language":"ar",...}

Query: "How do I calculate zakat on my savings?"
Output: {"intent":"zakat","confidence":0.93,"language":"en",...}

Now classify this query. Return ONLY valid JSON:
Query: {user_query}
```

**Configuration:**
- Temperature: 0.0 (fully deterministic)
- Max tokens: 300
- Response format: JSON object
- Confidence threshold: 0.75

**Why this tier exists:** Handles ambiguous queries, compound questions, and queries without clear keyword signals. Achieves ~90% classification accuracy.

#### Tier 3: Embedding Fallback (`src/core/router.py:272`)

**Status:** Placeholder implementation (Phase 5 pending). Will compare query embedding to a database of labeled examples using cosine similarity.

**Planned approach:**
1. Maintain a set of ~500 labeled queries (intent, embedding)
2. Encode new query with BAAI/bge-m3
3. Find closest labeled example via cosine similarity
4. Return intent of closest match if similarity > 0.70

**Why this tier exists:** Safety net when LLM is unavailable or returns low confidence. Provides graceful degradation.

### Confidence Thresholds

| Threshold | Value | Purpose |
|-----------|-------|---------|
| Keyword match | >= 0.90 | Fast-path return, skip LLM |
| LLM confidence | >= 0.75 | Accept LLM classification |
| Embedding similarity | >= 0.70 | Accept embedding fallback |
| Default fallback | 0.50 | When all tiers fail |

**Configurable via:** `src/config/settings.py`
```python
router_confidence_threshold: float = 0.75
router_fallback_enabled: bool = True
```

---

## 5. Active Agents (6)

Burhan has 6 active agents implementing the `BaseAgent` interface. All RAG-based agents inherit from `BaseRAGAgent` to share retrieval, citation, and generation logic.

### Agent Hierarchy

```
BaseAgent (src/agents/base.py)
├── execute() → AgentOutput
├── AgentInput, AgentOutput, Citation dataclasses
│
├── BaseRAGAgent (src/agents/base_rag_agent.py)
│   ├── _initialize() → embedding, vector store, LLM
│   ├── execute() → full RAG pipeline
│   ├── _format_passages() → [C1], [C2] markers
│   ├── _generate() → LLM answer generation
│   ├── _calculate_confidence() → avg passage scores
│   │
│   ├── FiqhAgent (src/agents/fiqh_agent.py)
│   ├── HadithAgent (src/agents/hadith_agent.py)
│   ├── SeerahAgent (src/agents/seerah_agent.py)
│   └── GeneralIslamicAgent (src/agents/general_islamic_agent.py)
│
└── ChatbotAgent (src/agents/chatbot_agent.py)
    └── Template-based responses (no RAG)
```

### 5.1 FiqhAgent

**File:** `src/agents/fiqh_agent.py`  
**Purpose:** Answer Islamic jurisprudence questions using verified fiqh texts  
**Collection:** `fiqh_passages` (10,132+ vectors)

| Parameter | Value | Reason |
|-----------|-------|--------|
| TOP_K_RETRIEVAL | 15 | Comprehensive coverage of fiqh opinions |
| TOP_K_RERANK | 5 | Focus on most relevant passages |
| SCORE_THRESHOLD | 0.65 | Balance precision and recall |
| TEMPERATURE | 0.1 | Very deterministic for legal rulings |
| MAX_TOKENS | 2048 | Sufficient for detailed fiqh answers |

**System Prompt (Arabic):**
```
أنت مساعد إسلامي متخصص في الفقه الإسلامي.
المهم:
- أجب بناءً ONLY على النصوص المسترجاعة المقدمة
- لا تختلق أي معلومات غير موجودة في النصوص
- استخدم المراجع [C1]، [C2]، إلخ لكل مصدر تستشهد به
- إذا لم تكن هناك نص sufficiently يجيب على السؤال، قل ذلك صراحة
- أضف تنبيه باستشارة عالم متخصص للحالات الخاصة
- اذكر المذهب الإسلامي إن وُجد في النصوص
```

**Key Features:**
- Faceted search support (author, era, book, category, death year range)
- Hierarchical retrieval (book → chapter → passage)
- Madhhab-aware responses (Hanafi, Maliki, Shafi'i, Hanbali)
- Fiqh disclaimer appended to all answers
- Fallback to top-3 passages if threshold not met

### 5.2 HadithAgent

**File:** `src/agents/hadith_agent.py`  
**Purpose:** Retrieve and authenticate Prophetic traditions  
**Collection:** `hadith_passages` (160+ vectors)

**Key Features:**
- Hadith authenticity grading (Sahih, Hasan, Da'if)
- Sanad (chain of narration) analysis
- Matn (text) verification
- Source attribution to 6 major collections

### 5.3 SeerahAgent

**File:** `src/agents/seerah_agent.py`  
**Purpose:** Answer questions about Prophet Muhammad's biography  
**Collection:** `seerah_passages` (100+ vectors)

**Key Features:**
- Chronological event retrieval
- Battle and treaty details
- Companion interactions
- Historical context enrichment

### 5.4 GeneralIslamicAgent

**File:** `src/agents/general_islamic_agent.py`  
**Purpose:** Handle general Islamic knowledge questions  
**Collection:** `general_islamic` (5+ vectors)

**Key Features:**
- Fallback agent for 7 intent types (tafsir, aqeedah, usul_fiqh, etc.)
- Broad knowledge coverage
- Template-based responses for common questions

### 5.5 ChatbotAgent

**File:** `src/agents/chatbot_agent.py`  
**Purpose:** Handle greetings, small talk, and conversational queries  
**Retrieval:** None (template-based)

**Key Features:**
- Arabic and English greeting responses
- Ramadan/Eid seasonal greetings
- Polite fallback for out-of-scope queries
- No LLM call required (fast <10ms response)

### 5.6 BaseRAGAgent (Shared Base Class)

**File:** `src/agents/base_rag_agent.py`  
**Purpose:** Eliminate code duplication across RAG agents

**Why this exists:** Before BaseRAGAgent, each of the 7 RAG agents had ~800 lines of duplicated code (initialization, retrieval, formatting, generation, citation normalization). BaseRAGAgent reduces this to class-level constants:

```python
class MyAgent(BaseRAGAgent):
    COLLECTION = "my_collection"
    SYSTEM_PROMPT = "أنت متخصص في..."
    USER_PROMPT = "السؤال: {query}\nالنصوص:\n{passages}"
    TOP_K_RETRIEVAL = 12
    TEMPERATURE = 0.15
```

**Shared Pipeline Steps:**
1. Initialize embedding model, vector store, LLM client
2. Encode query → 1024-dim vector
3. Retrieve passages (with optional faceted filtering or hierarchical retrieval)
4. Enrich passages (title context, hadith grading, book weighting)
5. Format passages with [C1], [C2] markers
6. Generate answer via LLM
7. Normalize citations
8. Calculate confidence score
9. Return AgentOutput

---

## 6. Deterministic Tools (5)

Deterministic tools produce identical outputs for identical inputs — no LLM, no randomness. This is critical for financial calculations (zakat, inheritance) and astronomical calculations (prayer times, Hijri dates).

### 6.1 ZakatCalculator

**File:** `src/tools/zakat_calculator.py`  
**Types Supported:** 8 (wealth, gold, silver, trade_goods, stocks, livestock, crops, minerals)

| Asset Type | Nisab | Rate | Notes |
|------------|-------|------|-------|
| Wealth (cash, bank) | 85g gold value | 2.5% | Standard rate |
| Gold | 85 grams | 2.5% | By weight |
| Silver | 595 grams (672g Hanafi) | 2.5% | Hanafi uses 672g |
| Trade goods | 85g gold value | 2.5% | Market value |
| Stocks | 85g gold value | 2.5% | Zakatable portion varies |
| Livestock | Specific thresholds | 1/40 or 1/30 | Camels, cattle, sheep |
| Crops | 5 wasq (~653kg) | 5% or 10% | Irrigation-dependent |
| Minerals | 85g gold value | 20% | Rikaz (treasure trove) |

**Madhhab Differences:**
- **Hanafi:** Silver nisab = 672g (higher threshold)
- **Shafi'i/Maliki/Hanbali:** Silver nisab = 595g
- **Gold nisab:** 85g (universal)

**Why deterministic?** Financial calculations must be reproducible and auditable. A 0.01 difference in zakat calculation can have real financial consequences.

### 6.2 InheritanceCalculator

**File:** `src/tools/inheritance_calculator.py`  
**Rules:** Fara'id (Islamic inheritance jurisprudence)

**Heir Categories:**
- **Quranic heirs:** Husband, wife, father, mother, daughter(s), son(s), full sister(s)
- **Agnatic heirs (Asabah):** Full brother, paternal brother, paternal uncle
- **Residuary heirs:** Receive remainder after fixed shares

**Calculation Flow:**
1. Deduct debts and funeral expenses
2. Deduct bequests (max 1/3 of estate)
3. Distribute fixed shares (Fard) to Quranic heirs
4. Distribute remainder to residuary heirs (Asabah)
5. Handle special cases (Awl, Radd, Hajb)

**Why deterministic?** Inheritance distribution is mathematically precise in Islamic law. The same heirs and estate must always produce the same distribution.

### 6.3 PrayerTimesTool

**File:** `src/tools/prayer_times_tool.py`  
**Methods:** 6 calculation methods + Qibla direction

| Method | Region | Fajr Angle | Isha Angle |
|--------|--------|------------|------------|
| Egyptian | Egypt, Middle East | 18° | 17° |
| Karachi | Pakistan, India | 18° | 18° |
| Umm al-Qura | Saudi Arabia | 18.5° | 90 min after Maghrib |
| Dubai | UAE | 18.2° | 18.2° |
| Moonsighting Committee | Global | 18° | 18° |
| ISNA | North America | 15° | 15° |

**Additional Features:**
- Qibla direction calculation (bearing from coordinates)
- Sunnah prayer times (Duha, Tahajjud)
- Sunrise and sunset times

### 6.4 HijriCalendarTool

**File:** `src/tools/hijri_calendar_tool.py`  
**Calendar:** Umm al-Qura (Saudi Arabia official)

**Features:**
- Gregorian → Hijri conversion
- Hijri → Gregorian conversion
- Ramadan dates prediction
- Eid al-Fitr and Eid al-Adha dates
- Islamic month names (Arabic/English)

**Why Umm al-Qura?** It's the official calendar used in Saudi Arabia and most Islamic applications. Based on actual moon sighting calculations.

### 6.5 DuaRetrievalTool

**File:** `src/tools/dua_retrieval_tool.py`  
**Sources:** Hisn al-Muslim (Fortress of the Muslim) + Azkar database

**Features:**
- Search by keyword (Arabic/English)
- Filter by occasion (morning, evening, travel, etc.)
- Filter by category (protection, gratitude, repentance)
- Arabic text with transliteration and translation
- Reference to source hadith

**Data Source:** `data/seed/duas.json` (seeded from Hisn al-Muslim)

---

## 7. RAG Infrastructure

### 7.1 Embedding Model

**File:** `src/knowledge/embedding_model.py`  
**Model:** BAAI/bge-m3 (replaced Qwen3-Embedding-0.6B)

| Parameter | Value | Why |
|-----------|-------|-----|
| Dimensions | 1024 | Standard for modern embedding models |
| Max tokens | 8192 | Supports long Islamic passages (books, chapters) |
| Batch size | 64 | Optimal for GPU memory (T4, A10) |
| Precision | Half (FP16) | 2x faster inference, minimal quality loss |
| Device | CUDA → MPS → CPU | Automatic fallback |
| Cache | Redis (7-day TTL) | Avoids re-embedding identical passages |

**Why BAAI/bge-m3?**
- **Multilingual:** Trained on 100+ languages including Arabic (critical for Islamic texts)
- **Long context:** 8192 tokens vs 512 for Qwen3-Embedding-0.6B
- **Retrieval-optimized:** Specifically designed for search/RAG tasks
- **Performance:** Higher MTEB benchmark scores than Qwen3-Embedding

**Caching Strategy:**
```
Query: "ما حكم صلاة الجمعة؟"
  → SHA-256 hash of query text
  → Check Redis cache
     → Hit: Return cached embedding (5ms)
     → Miss: Encode with model (50ms), store in Redis (7-day TTL)
```

### 7.2 Vector Store

**File:** `src/knowledge/vector_store.py`  
**Database:** Qdrant (self-hosted)

| Collection | Dimension | Vectors | Description | Status |
|------------|-----------|---------|-------------|--------|
| fiqh_passages | 1024 | 10,132+ | Fiqh books and fatwas | ✅ Active |
| hadith_passages | 1024 | 160+ | Hadith collections | 🔄 Growing |
| general_islamic | 1024 | 5+ | General knowledge | ⏳ Seeded |
| quran_tafsir | 1024 | — | Tafsir passages | ⏳ Ready |
| duas_adhkar | 1024 | 10+ | Duas and adhkar | ✅ Seeded |
| aqeedah_passages | 1024 | 90+ | Creed and theology | ✅ Active |
| seerah_passages | 1024 | 100+ | Prophet biography | ✅ Active |
| islamic_history_passages | 1024 | 270+ | Islamic history | ✅ Active |
| arabic_language_passages | 1024 | 240+ | Arabic language | ✅ Active |
| spirituality_passages | 1024 | 150+ | Spirituality and ethics | ✅ Active |

**Total:** 11,147+ vectors across 10 collections

**Initialization Flow:**
1. Connect to Qdrant (`http://localhost:6333`)
2. Check if collection exists
3. Create collection if needed (1024 dims, Cosine distance)
4. Upload vectors with payloads (content, metadata, book_id, author, etc.)

### 7.3 Hybrid Search

**File:** `src/knowledge/hybrid_search.py`  
**Approach:** Reciprocal Rank Fusion (RRF) combining semantic and keyword search

```
Semantic Search (cosine similarity)
  → Top-20 results ranked by vector distance
Keyword Search (BM25-like text matching)
  → Top-20 results ranked by keyword overlap
Reciprocal Rank Fusion (k=60)
  → score = 1/(k + rank_semantic) + 1/(k + rank_keyword)
  → Combined ranking balances both signals
Final: Top-12 results returned to agent
```

**Why hybrid?** Semantic search alone misses exact keyword matches (e.g., "zakat" in English query matching Arabic "زكاة" passage). Keyword search alone misses semantic similarity (e.g., "صلاة" matching "عبادة"). Combined, they capture both.

**Faceted Search Support:**
```python
filters = {
    "author": "Imam Bukhari",
    "era": "classical",          # prophetic, tabiun, classical, medieval, ottoman, modern
    "book_id": 123,
    "category": "hanafi",
    "author_death_min": 200,
    "author_death_max": 500,
}
results = await searcher.search_with_facets(query, embedding, collection, top_k, filters)
```

### 7.4 Hierarchical Retriever

**File:** `src/knowledge/hierarchical_retriever.py`  
**Purpose:** Retrieve coherent book-level context instead of scattered passages

**Problem:** Standard RAG retrieves top-15 individual passages, which may come from 15 different books with no coherent context. For fiqh questions, it's better to retrieve 3-5 complete chapters from the most relevant books.

**Solution:**
1. Retrieve top-50 passages (expanded set)
2. Group passages by book_id
3. Select top-3 books by passage count and score
4. For each book, retrieve top-5 passages per chapter
5. Return passages with book/chapter hierarchy context

**Result:** More coherent, book-context-aware answers with proper scholarly attribution.

### 7.5 Book Weighter

**File:** `src/knowledge/book_weighter.py`  
**Purpose:** Score passages by book importance and author authority

**Scoring Factors:**
- Author death year (earlier scholars = higher authority for classical texts)
- Book category (Sahih collections weighted higher than general books)
- Collection size (larger collections may be more comprehensive)
- Citation count (how often the book is referenced)

**Formula:**
```
weighted_score = semantic_score * book_importance_multiplier
```

### 7.6 Hadith Grader

**File:** `src/knowledge/hadith_grader.py`  
**Purpose:** Grade hadith authenticity for retrieved passages

**Grades:**
- **Sahih (صحيح):** Authentic, reliable
- **Hasan (حسن):** Good, acceptable
- **Da'if (ضعيف):** Weak, caution needed
- **Mawdu (موضوع):** Fabricated, reject

**Enrichment:**
```python
passages = hadith_grader.enrich_passages_with_authenticity(passages)
# Each passage gets: {"authenticity_grade": "sahih", "grade_source": "Al-Albani"}
```

### 7.7 Title Loader

**File:** `src/knowledge/title_loader.py`  
**Purpose:** Enrich passages with chapter/section context

**Problem:** A passage may be "صلاة الجمعة فرض عين" without context of which book, chapter, or section it's from.

**Solution:** Load title hierarchy from passage metadata and prepend to content:
```
Before: "صلاة الجمعة فرض على كل مسلم"
After:  "كتاب الصلاة - باب فضل صلاة الجمعة - صلاة الجمعة فرض على كل مسلم"
```

---

## 8. Citation System

### 8.1 CitationNormalizer

**File:** `src/core/citation.py`  
**Purpose:** Convert various citation formats to standardized `[C1]`, `[C2]` tags with structured metadata

### 8.2 Supported Citation Formats

| Format | Pattern | Example | Citation Type |
|--------|---------|---------|---------------|
| Quran (surah:ayah) | `Quran \d+:\d+` | "Quran 2:255" | `quran` |
| Quran (Arabic) | `القرآن \d+:\d+` | "القرآن 2:255" | `quran` |
| Quran (surah name) | `سورة ... آية \d+` | "سورة البقرة آية 255" | `quran` |
| Hadith (Arabic) | `صحيح البخاري حديث \d+` | "صحيح البخاري، حديث 1234" | `hadith` |
| Hadith (simplified) | `رواه البخاري` | "رواه البخاري" | `hadith` |
| Fatwa | `فتوى رقم \d+` | "فتوى رقم 12345" | `fatwa` |
| Fiqh book | `كتاب ... باب ... رقم \d+` | "كتاب الصلاة، باب الجمعة، رقم 5" | `fiqh_book` |

### 8.3 Metadata Enrichment

Each citation is enriched with passage metadata:

| Field | Source | Example |
|-------|--------|---------|
| `book_id` | Passage metadata | 123 |
| `book_title` | Passage metadata | "صحيح البخاري" |
| `author` | Passage metadata | "Imam Bukhari" |
| `author_death` | Passage metadata | 256 (Hijri) |
| `scholarly_era` | Calculated from death year | "classical" (200-500 AH) |
| `page` | Passage metadata | 45 |
| `chapter` | Passage metadata | "باب فضل صلاة الجمعة" |
| `section` | Passage metadata | "فصل في حكمها" |
| `collection` | Passage metadata | "hadith_passages" |
| `display_source` | Computed | "Imam Bukhari - صحيح البخاري, p. 45" |

### 8.4 Era Classification

Scholars are classified into 6 eras based on death year (Hijri):

| Era | Range (AH) | Description | Examples |
|-----|-----------|-------------|----------|
| Prophetic | 0-100 | Companions of the Prophet | Abu Bakr, Umar, Uthman, Ali |
| Tabi'un | 100-200 | Successors | Imam Abu Hanifa, Imam Malik |
| Classical | 200-500 | Golden age of Islamic scholarship | Imam Bukhari, Imam Muslim, Ibn Kathir |
| Medieval | 500-900 | Post-classical period | Al-Nawawi, Ibn Taymiyyah |
| Ottoman | 900-1300 | Ottoman era scholars | Various regional scholars |
| Modern | 1300+ | Contemporary scholars | Al-Albani, Ibn Baz, Al-Uthaymin |

### 8.5 External URL Mappings

| Source | URL Template | Example |
|--------|-------------|---------|
| Quran | `https://quran.com/{surah}/{ayah}` | quran.com/2/255 |
| Sahih Bukhari | `https://sunnah.com/bukhari/{number}` | sunnah.com/bukhari/1234 |
| Sahih Muslim | `https://sunnah.com/muslim/{number}` | sunnah.com/muslim/567 |
| Sunan al-Tirmidhi | `https://sunnah.com/tirmidhi/{number}` | sunnah.com/tirmidhi/890 |
| Sunan Abu Dawud | `https://sunnah.com/abudawud/{number}` | sunnah.com/abudawud/123 |
| Sunan al-Nasa'i | `https://sunnah.com/nasai/{number}` | sunnah.com/nasai/456 |
| Sunan Ibn Majah | `https://sunnah.com/ibnmajah/{number}` | sunnah.com/ibnmajah/789 |
| Fatwa | `https://www.islamweb.net/en/fatwa/{id}` | islamweb.net/en/fatwa/12345 |

---

## 9. Data Pipeline

### 9.1 Source Data

#### ElShamela Library (المكتبة الشاملة)

**Source:** https://shamela.ws/  
**Size:** 8,425 books, 17.16 GB, 3,146 authors, 1,400 years of scholarship

**Processing Pipeline:**
```
ElShamela Database (books.db, SQLite)
  → Extract books as .txt files (Lucene-based extraction)
  → Chunk into passages (hierarchical_chunker.py)
     → Book → Chapter → Section → Passage
  → Enrich with metadata
     → book_id, title, author, author_death, page, chapter, section
  → Embed with BAAI/bge-m3
  → Upload to Qdrant collections
```

**Category Distribution:**
| Category | Books | Percentage |
|----------|-------|------------|
| Fiqh | 2,150+ | 25.5% |
| Hadith | 1,800+ | 21.4% |
| Tafsir | 950+ | 11.3% |
| Seerah | 680+ | 8.1% |
| Aqeedah | 520+ | 6.2% |
| Arabic Language | 480+ | 5.7% |
| Islamic History | 420+ | 5.0% |
| Spirituality | 380+ | 4.5% |
| Usul al-Fiqh | 350+ | 4.2% |
| Other | 695+ | 8.3% |

#### Sanadset Hadith

**Source:** Sanadset dataset  
**Size:** 650,986 hadith, 1.43 GB

**Fields:** sanad (chain of narration), matn (text), grade, source

**Processing:**
```
Sanadset JSON files
  → Parse hadith (sanad, matn, metadata)
  → Grade hadith authenticity
  → Embed matn text
  → Upload to hadith_passages collection
```

#### System Book Datasets

**Size:** 1,000+ book databases (.db files)

### 9.2 Mini-Dataset (GitHub-Friendly)

**Location:** `data/mini_dataset/`  
**Size:** 1.7 MB, 1,623 documents across 8 collections

**Purpose:** Demonstrate and test the system without requiring 17+ GB of data. Committed to Git for easy cloning.

| File | Documents | Size |
|------|-----------|------|
| fiqh_passages.jsonl | 347 | 400 KB |
| hadith_passages.jsonl | 126 | 150 KB |
| general_islamic.jsonl | 300 | 350 KB |
| islamic_history_passages.jsonl | 270 | 300 KB |
| arabic_language_passages.jsonl | 240 | 250 KB |
| aqeedah_passages.jsonl | 90 | 100 KB |
| spirituality_passages.jsonl | 150 | 170 KB |
| seerah_passages.jsonl | 100 | 120 KB |

**Creation:** `python scripts/create_mini_dataset.py`

### 9.3 Chunking Strategy

**File:** `src/knowledge/hierarchical_chunker.py`

**Approach:** Hierarchical chunking preserves book structure:

```
Book: صحيح البخاري
├── Chapter: كتاب الإيمان
│   ├── Section: باب فضل الإيمان
│   │   ├── Passage 1: "إنما الأعمال بالنيات..."
│   │   └── Passage 2: "آية الإيمان أن يحب لأخيه..."
│   └── Section: باب علامات الإيمان
│       └── Passage 3: "لا يؤمن أحدكم حتى أكون أحب إليه..."
└── Chapter: كتاب الصلاة
    └── ...
```

**Chunk Size:**
- Target: 512 tokens (optimal for embedding)
- Max: 1024 tokens (fits bge-m3 context window)
- Overlap: 50 tokens (prevents information loss at boundaries)

### 9.4 Ingestion Scripts

| Script | Purpose |
|--------|---------|
| `scripts/generate_embeddings.py` | Batch embedding generator |
| `scripts/create_mini_dataset.py` | Mini-dataset creator |
| `scripts/embed_sanadset_hadith.py` | Hadith embedding pipeline |
| `scripts/seed_mvp_data.py` | MVP data seeder |

---

## 10. Configuration System

### 10.1 Pydantic Settings

**File:** `src/config/settings.py`

Burhan uses Pydantic `BaseSettings` for automatic environment variable parsing with type validation, defaults, and custom validators.

**Key Configuration Groups:**

| Group | Variables | Example |
|-------|-----------|---------|
| **Application** | app_name, app_env, debug, secret_key | `APP_ENV=production` |
| **Database** | database_url, pool_size, max_overflow | `DATABASE_URL=postgresql+asyncpg://...` |
| **Redis** | redis_url, max_connections | `REDIS_URL=redis://localhost:6379/0` |
| **Qdrant** | qdrant_url, qdrant_api_key, collection names | `QDRANT_URL=http://localhost:6333` |
| **LLM** | llm_provider, openai_api_key, groq_api_key, models | `LLM_PROVIDER=groq` |
| **Embeddings** | embedding_model, embedding_dimension | `EMBEDDING_MODEL=BAAI/bge-m3` |
| **Routing** | confidence_threshold, fallback_enabled | `ROUTER_CONFIDENCE_THRESHOLD=0.75` |
| **Rate Limiting** | rate_limit_enabled, per_minute | `RATE_LIMIT_PER_MINUTE=60` |
| **Security** | api_key_enabled, cors_max_age | `API_KEY_ENABLED=false` |
| **Caching** | llm_cache_enabled, ttl | `LLM_CACHE_TTL=3600` |
| **CORS** | cors_origins | `CORS_ORIGINS=http://localhost:3000` |
| **API** | timeout, max_query_length | `MAX_QUERY_LENGTH=1000` |

### 10.2 Environment Variables (.env.example)

**File:** `.env.example` (50+ variables)

```bash
# ==========================================
# Application
# ==========================================
APP_ENV=development
DEBUG=true
SECRET_KEY=change-this-in-production-please-use-random-string

# ==========================================
# Database (PostgreSQL 16)
# ==========================================
DATABASE_URL=postgresql+asyncpg://Burhan:Burhan_password@localhost:5432/Burhan_db
DATABASE_POOL_SIZE=10
DATABASE_MAX_OVERFLOW=20

# ==========================================
# Redis
# ==========================================
REDIS_URL=redis://localhost:6379/0
REDIS_MAX_CONNECTIONS=50

# ==========================================
# Qdrant (Vector Database)
# ==========================================
QDRANT_URL=http://localhost:6333
QDRANT_API_KEY=

# ==========================================
# LLM Provider
# ==========================================
LLM_PROVIDER=groq
GROQ_API_KEY=your-key-here
GROQ_MODEL=qwen/qwen3-32b
OPENAI_API_KEY=
OPENAI_MODEL=gpt-4o-mini
LLM_TEMPERATURE=0.1
LLM_MAX_TOKENS=2048

# ==========================================
# Embeddings
# ==========================================
EMBEDDING_MODEL=BAAI/bge-m3
EMBEDDING_DIMENSION=1024
HF_TOKEN=your-huggingface-token

# ==========================================
# Security
# ==========================================
API_KEY_ENABLED=false
RATE_LIMIT_ENABLED=true
RATE_LIMIT_PER_MINUTE=60

# ==========================================
# CORS
# ==========================================
CORS_ORIGINS=http://localhost:3000,http://localhost:8000
CORS_MAX_AGE=600
```

### 10.3 Validation & Warnings

The settings class includes custom validators:

```python
@field_validator("secret_key")
def validate_secret_key(cls, v):
    if v == "change-this-in-production-please-use-random-string":
        warnings.warn("Using default secret key! Change this in production.", UserWarning)
    return v

@field_validator("cors_origins", mode="before")
def parse_cors_origins(cls, v):
    if isinstance(v, str):
        return [origin.strip() for origin in v.split(",") if origin.strip()]
    return v

@property
def is_production(self) -> bool:
    return self.app_env == "production"
```

### 10.4 Constants

**File:** `src/config/constants.py`

Centralized constants for retrieval and LLM configuration:

```python
class RetrievalConfig:
    TOP_K_FIQH = 15
    TOP_K_GENERAL = 12
    SEMANTIC_SCORE_THRESHOLD = 0.65

class LLMConfig:
    FIQH_TEMPERATURE = 0.1
    GENERAL_TEMPERATURE = 0.15
    DEFAULT_MAX_TOKENS = 2048
```

---

## 11. API Endpoints (18 Total)

### 11.1 Query Endpoint

| Endpoint | Method | Purpose | Status |
|----------|--------|---------|--------|
| `/api/v1/query` | POST | Main query with intent classification | ✅ Working |

**Request:**
```json
{
  "query": "ما حكم صلاة الجمعة؟",
  "language": "ar",
  "madhhab": "hanafi"
}
```

**Query Parameters (Faceted Search):**
- `author`: Filter by author name
- `era`: Filter by scholarly era (prophetic, tabiun, classical, medieval, ottoman, modern)
- `book_id`: Filter by specific book ID
- `category`: Filter by category/madhhab
- `death_year_min`, `death_year_max`: Filter by author death year range
- `hierarchical`: Use hierarchical retrieval (boolean)

**Response:**
```json
{
  "query_id": "uuid-...",
  "intent": "fiqh",
  "intent_confidence": 0.92,
  "answer": "بناءً على النصوص المسترجاعة...",
  "citations": [
    {
      "id": "C1",
      "type": "fiqh_book",
      "source": "Imam Bukhari - صحيح البخاري",
      "reference": "باب فضل صلاة الجمعة",
      "url": null,
      "metadata": {"book_id": 123, "author_death": 256, "scholarly_era": "classical"}
    }
  ],
  "metadata": {
    "agent": "fiqh_agent",
    "processing_time_ms": 257,
    "classification_method": "keyword",
    "retrieved_count": 15,
    "used_count": 5
  },
  "follow_up_suggestions": ["ما هي شروط صلاة الجمعة؟", "هل صلاة الجمعة واجبة على النساء؟"]
}
```

### 11.2 Tool Endpoints (5)

| Endpoint | Method | Purpose | Calculator |
|----------|--------|---------|------------|
| `/api/v1/tools/zakat` | POST | Calculate zakat | ZakatCalculator |
| `/api/v1/tools/inheritance` | POST | Inheritance distribution | InheritanceCalculator |
| `/api/v1/tools/prayer-times` | POST | Prayer times + Qibla | PrayerTimesTool |
| `/api/v1/tools/hijri` | POST | Date conversion | HijriCalendarTool |
| `/api/v1/tools/duas` | POST | Dua retrieval | DuaRetrievalTool |

### 11.3 Quran Endpoints (6)

| Endpoint | Method | Purpose | Engine |
|----------|--------|---------|--------|
| `/api/v1/quran/surahs` | GET | List all 114 surahs | VerseRetrievalEngine |
| `/api/v1/quran/surahs/{n}` | GET | Specific surah details | VerseRetrievalEngine |
| `/api/v1/quran/ayah/{s}:{a}` | GET | Specific ayah | VerseRetrievalEngine |
| `/api/v1/quran/search` | POST | Verse search | VerseRetrievalEngine |
| `/api/v1/quran/validate` | POST | Quotation validation | QuotationValidator |
| `/api/v1/quran/analytics` | POST | NL2SQL queries | NL2SQLEngine |
| `/api/v1/quran/tafsir/{s}:{a}` | GET | Tafsir retrieval | TafsirRetrievalEngine |

### 11.4 RAG Endpoints (3)

| Endpoint | Method | Purpose | Agent |
|----------|--------|---------|-------|
| `/api/v1/rag/fiqh` | POST | Fiqh RAG questions | FiqhAgent |
| `/api/v1/rag/general` | POST | General Islamic RAG | GeneralIslamicAgent |
| `/api/v1/rag/stats` | GET | RAG system statistics | — |

### 11.5 Health Endpoints (2)

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/health` | GET | Health check (service status) |
| `/ready` | GET | Readiness probe (dependencies ready) |

### 11.6 Endpoint Summary

| Category | Count | Status | Avg Response Time |
|----------|-------|--------|-------------------|
| Query | 1 | ✅ Working | ~257ms (fiqh RAG) |
| Tools | 5 | ✅ Working | <10ms (deterministic) |
| Quran | 6 | ✅ Working | ~50ms (database lookup) |
| RAG | 3 | ✅ Working | ~200ms |
| Health | 2 | ✅ Working | <5ms |
| **Total** | **18** | **17/18 PASS** | — |

---

## 12. Security Architecture

### 12.1 Middleware Stack

FastAPI middleware executes in reverse order of registration (last added = outermost):

```
HTTP Request
    │
    ▼
┌─────────────────────────────────────┐
│ 1. Security Headers Middleware       │ ← Outermost (src/api/middleware/security.py)
│    - X-Content-Type-Options: nosniff │
│    - X-Frame-Options: DENY           │
│    - X-XSS-Protection: 1; mode=block │
│    - Strict-Transport-Security       │
│    - Content-Security-Policy         │
└────────────────┬────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────┐
│ 2. Rate Limiting Middleware          │ ← Production only
│    - In-memory sliding window        │
│    - 60 requests/minute default      │
│    - X-RateLimit-* headers           │
│    - 429 on exceeded                 │
└────────────────┬────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────┐
│ 3. CORS Middleware                   │
│    - Configurable origins            │
│    - Credentials support             │
│    - Preflight handling              │
└────────────────┬────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────┐
│ 4. Error Handler Middleware          │ ← Innermost
│    - Exception → JSON response       │
│    - Structured logging              │
│    - Stack trace in dev only         │
└────────────────┬────────────────────┘
                 │
                 ▼
            Route Handler
```

### 12.2 Rate Limiting

**File:** `src/api/middleware/security.py`  
**Implementation:** In-memory sliding window (production should use Redis-based)

```python
class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, requests_per_minute: int = 60):
        self.requests_per_minute = requests_per_minute
        self.requests: dict[str, list[float]] = defaultdict(list)

    async def dispatch(self, request: Request, call_next):
        # Skip for health checks
        if request.url.path in ["/health", "/docs", "/openapi.json", "/redoc"]:
            return await call_next(request)

        client_id = self._get_client_id(request)  # API key hash or IP
        if not self._check_rate_limit(client_id):
            raise HTTPException(status_code=429, detail="Rate limit exceeded.")

        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(self.requests_per_minute)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        return response
```

**Client Identification:**
1. API key hash (if `X-API-Key` header present) → SHA-256 hash
2. IP address fallback (from `X-Forwarded-For` or direct IP)

**Production Note:** In-memory rate limiting resets on server restart. For production, use Redis-based rate limiting with `INCR` and `EXPIRE`.

### 12.3 Security Headers

```python
class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Content-Security-Policy"] = "default-src 'self'"
        return response
```

### 12.4 CORS Configuration

**Settings:** `src/config/settings.py`
```python
cors_origins: list[str] = ["http://localhost:3000"]
cors_max_age: int = 600  # 10 minutes preflight cache
```

**Middleware:**
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### 12.5 API Key Support

**Header:** `X-API-Key`  
**Status:** Disabled by default (`api_key_enabled: bool = False`)

**Planned Implementation:**
```python
API_KEY_HEADER = "X-API-Key"
api_key_header = APIKeyHeader(name=API_KEY_HEADER, auto_error=False)

async def verify_api_key(api_key: str = Depends(api_key_header)):
    if api_key not in settings.valid_api_keys:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return api_key
```

**Production Note:** Enable API key authentication in production and configure rate limiting per key.

### 12.6 Error Handler

**File:** `src/api/middleware/error_handler.py`

Converts all exceptions to structured JSON responses:
```python
async def error_handler_middleware(request: Request, call_next):
    try:
        return await call_next(request)
    except HTTPException as e:
        # Standard HTTP errors (400, 401, 404, 429, 500)
        return JSONResponse(
            status_code=e.status_code,
            content={"error": e.detail, "status": e.status_code}
        )
    except Exception as e:
        # Unexpected errors
        logger.error("unhandled_error", error=str(e), exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"error": "Internal server error", "status": 500}
        )
```

---

## 13. Deployment Architecture

### 13.1 Docker Compose

**File:** `docker/docker-compose.dev.yml`  
**Services:** 5 (PostgreSQL, Qdrant, Redis, API, Frontend)

```yaml
version: '3.9'

services:
  postgres:
    image: postgres:16-alpine
    container_name: Burhan-postgres
    environment:
      POSTGRES_DB: Burhan_db
      POSTGRES_USER: Burhan
      POSTGRES_PASSWORD: Burhan_password
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./init-db:/docker-entrypoint-initdb.d
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U Burhan -d Burhan_db"]
      interval: 10s
      timeout: 5s
      retries: 5
    networks:
      - Burhan-network

  qdrant:
    image: qdrant/qdrant:latest
    container_name: Burhan-qdrant
    ports:
      - "6333:6333"
      - "6334:6334"
    volumes:
      - qdrant_data:/qdrant/storage
    healthcheck:
      test: ["CMD", "bash", "-c", "echo > /dev/tcp/localhost/6333"]
      interval: 10s
      timeout: 5s
      retries: 5
    networks:
      - Burhan-network

  redis:
    image: redis:7-alpine
    container_name: Burhan-redis
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    command: redis-server --appendonly yes
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5
    networks:
      - Burhan-network

  api:
    build:
      context: ..
      dockerfile: docker/Dockerfile.api
    container_name: Burhan-api
    ports:
      - "8000:8000"
    volumes:
      - ../src:/app/src
      - ../tests:/app/tests
    environment:
      DATABASE_URL: postgresql+asyncpg://Burhan:Burhan_password@postgres:5432/Burhan_db
      REDIS_URL: redis://redis:6379/0
      QDRANT_URL: http://qdrant:6333
      OPENAI_API_KEY: ${OPENAI_API_KEY:-}
    depends_on:
      postgres: { condition: service_healthy }
      redis: { condition: service_healthy }
      qdrant: { condition: service_healthy }
    command: uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload
    networks:
      - Burhan-network

  frontend:
    image: node:20-alpine
    container_name: Burhan-frontend
    ports:
      - "3000:3000"
    profiles:
      - frontend  # Optional: docker compose --profile frontend up
    depends_on:
      - api
    networks:
      - Burhan-network

volumes:
  postgres_data:
  qdrant_data:
  redis_data:

networks:
  Burhan-network:
    driver: bridge
```

### 13.2 Service Dependencies

```
┌────────────────────────────────────────────────────────────┐
│                    Startup Order                            │
├────────────────────────────────────────────────────────────┤
│                                                            │
│  1. PostgreSQL  ───┐                                       │
│  2. Qdrant     ────┼──► 3. API (depends on all healthy)   │
│  3. Redis      ────┘                                       │
│                          │                                 │
│                          ▼                                 │
│                    4. Frontend (optional)                  │
│                                                            │
│  Health checks ensure services are ready before API starts│
└────────────────────────────────────────────────────────────┘
```

### 13.3 Resource Recommendations

| Service | CPU | RAM | Disk | Notes |
|---------|-----|-----|------|-------|
| PostgreSQL | 1-2 cores | 2-4 GB | 10-50 GB | Depends on Quran data size |
| Qdrant | 2-4 cores | 8-16 GB | 50-200 GB | Vector storage for 11K+ vectors |
| Redis | 0.5 core | 1-2 GB | 1-5 GB | Embedding cache only |
| API | 2-4 cores | 4-8 GB | — | LLM client, embedding model |
| Frontend | 1 core | 1-2 GB | — | Next.js development server |

### 13.4 CI/CD Pipeline (Planned)

**Platform:** GitHub Actions

```yaml
# .github/workflows/ci.yml (planned)
name: CI/CD

on:
  push:
    branches: [main, dev]
  pull_request:
    branches: [main]

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Install Poetry
        run: pipx install poetry
      - name: Install dependencies
        run: poetry install --with dev
      - name: Lint with ruff
        run: poetry run ruff check src/
      - name: Type check with mypy
        run: poetry run mypy src/

  test:
    runs-on: ubuntu-latest
    needs: lint
    services:
      postgres:
        image: postgres:16
      redis:
        image: redis:7
    steps:
      - uses: actions/checkout@v4
      - name: Run tests
        run: poetry run pytest tests/ -v --cov=src

  build:
    runs-on: ubuntu-latest
    needs: test
    if: github.ref == 'refs/heads/main'
    steps:
      - uses: actions/checkout@v4
      - name: Build Docker image
        run: docker build -f docker/Dockerfile.api -t Burhan-api:latest .
      - name: Push to registry
        run: docker push Burhan-api:latest
```

**Pipeline Stages:**
1. **Lint** → Ruff + MyPy (fail fast on code quality issues)
2. **Test** → Pytest with coverage (91%+ required)
3. **Build** → Docker image (main branch only)
4. **Deploy** → (Future) Kubernetes/Docker Compose production

---

## 14. Current State & Future Work

### 14.1 Production Readiness Score

**Current Score: 8.1/10** (improved from 6.6/10)

| Area | Score | Notes |
|------|-------|-------|
| Code Quality | 8.5/10 | Dead code eliminated, consistent patterns |
| Testing | 9.0/10 | 91% coverage, 121 passing tests |
| Security | 7.5/10 | Headers, rate limiting, missing: SSL, Sentry |
| Deployment | 7.0/10 | Docker Compose dev, missing: production Docker |
| Monitoring | 6.5/10 | Structured logging, missing: APM, dashboards |
| Documentation | 9.0/10 | Comprehensive docs, API specs, architecture |
| Data Pipeline | 8.5/10 | Mini-dataset working, full embedding pending |
| Performance | 8.0/10 | <300ms response time, caching implemented |

### 14.2 Completed Improvements

| Improvement | Before | After | Impact |
|-------------|--------|-------|--------|
| Dead code elimination | 3,691 lines of orphans | Removed | Cleaner codebase, easier maintenance |
| BaseRAGAgent | 7 agents × 800 lines duplicated | Shared base class | ~5,600 lines saved |
| Test coverage | ~70% | ~91% | Higher confidence in deployments |
| Embedding model | Qwen3-Embedding-0.6B | BAAI/bge-m3 | Better multilingual support |
| Configuration | Hardcoded values | Pydantic Settings | Environment-aware deployment |
| Security | None | Headers + Rate limiting | Production-ready baseline |

### 14.3 Pending Work

#### High Priority

| Item | Description | Effort | Impact |
|------|-------------|--------|--------|
| **SSL/TLS** | HTTPS for production deployment | 2 days | Critical for security |
| **Sentry Integration** | Error tracking and monitoring | 1 day | Production observability |
| **Full Agent Set (13)** | Implement TafsirAgent, AqeedahAgent, UsulFiqhAgent, HistoryAgent, ArabicLanguageAgent | 5 days | Complete feature set |
| **Redis Rate Limiting** | Replace in-memory with Redis-based | 1 day | Production-scale rate limiting |
| **API Key Management** | Per-user API keys with quotas | 2 days | Monetization and access control |

#### Medium Priority

| Item | Description | Effort | Impact |
|------|-------------|--------|--------|
| **Full Embedding** | Embed all 2.9M vectors from ElShamela | 13 hours (T4 GPU) | Complete RAG coverage |
| **Authentication System** | User accounts, sessions, preferences | 1 week | Personalized experience |
| **CI/CD Pipeline** | GitHub Actions workflow | 2 days | Automated testing/deployment |
| **APM Dashboards** | Grafana/Prometheus monitoring | 3 days | Production observability |
| **Load Testing** | k6 or Locust performance tests | 2 days | Capacity planning |

#### Low Priority

| Item | Description | Effort | Impact |
|------|-------------|--------|--------|
| **Embedding Fallback** | Tier 3 classifier with labeled examples | 3 days | Marginal accuracy improvement |
| **Multi-LLM Fallback** | OpenAI → Groq → Local LLM fallback | 2 days | Reliability improvement |
| **Arabic NLP Pipeline** | Stemming, diacritic removal, morphological analysis | 1 week | Retrieval quality improvement |
| **Frontend (Next.js)** | React UI with RTL support | 2 weeks | User-facing interface |
| **Mobile App (Flutter)** | Cross-platform mobile app | 4 weeks | Mobile user experience |

### 14.4 Known Issues

| Issue | Severity | Status | Workaround |
|-------|----------|--------|------------|
| Hadith collection small (160 vectors) | Medium | In progress | Embed full Sanadset dataset |
| General Islamic collection small (5 vectors) | Medium | Planned | Seed from mini-dataset |
| In-memory rate limiting resets on restart | Low | Planned | Use Redis-based rate limiting |
| API key authentication not enforced | Low | Planned | Enable in production |
| Embedding classifier (Tier 3) not implemented | Low | Phase 5 | LLM classifier handles 90% |

### 14.5 Architecture Decisions Log

| Decision | Date | Rationale | Alternatives Considered |
|----------|------|-----------|----------------------|
| BAAI/bge-m3 over Qwen3-Embedding | April 2026 | Better multilingual support, 8192 tokens | Qwen3-Embedding-0.6B, text-embedding-3-small |
| Qdrant over Pinecone | March 2026 | Open-source, self-hostable, payload filtering | Pinecone, Weaviate, Milvus |
| Groq over OpenAI for LLM | March 2026 | 10x faster, lower cost for Qwen3-32B | OpenAI GPT-4, Anthropic Claude |
| PostgreSQL over MongoDB | February 2026 | ACID compliance, native full-text search | MongoDB, SQLite |
| 4-layer architecture | February 2026 | Clean separation, testability, replaceability | 3-layer, microservices |
| BaseRAGAgent pattern | April 2026 | Eliminate 5,600 lines of duplication | Individual agent implementations |

---

## Appendix A: File Structure Reference

```
K:\business\projects_v2\Burhan\
├── src/
│   ├── config/
│   │   ├── settings.py           # Pydantic Settings (50+ vars)
│   │   ├── intents.py            # 16 intents + keyword patterns
│   │   ├── constants.py          # RetrievalConfig, LLMConfig
│   │   └── logging_config.py     # structlog configuration
│   │
│   ├── api/
│   │   ├── main.py               # FastAPI app factory (create_app)
│   │   ├── routes/
│   │   │   ├── query.py          # POST /api/v1/query
│   │   │   ├── health.py         # GET /health, /ready
│   │   │   ├── tools.py          # 5 tool endpoints
│   │   │   ├── quran.py          # 6 Quran endpoints (+ tafsir)
│   │   │   └── rag.py            # 3 RAG endpoints
│   │   ├── middleware/
│   │   │   ├── security.py       # Rate limiting, security headers
│   │   │   └── error_handler.py  # Exception → JSON
│   │   └── schemas/
│   │       ├── request.py        # Pydantic request models
│   │       └── response.py       # Pydantic response models
│   │
│   ├── core/
│   │   ├── router.py             # HybridQueryClassifier (3-tier)
│   │   └── citation.py           # CitationNormalizer
│   │
│   ├── agents/
│   │   ├── base.py               # BaseAgent, AgentInput, AgentOutput
│   │   ├── base_rag_agent.py     # BaseRAGAgent (shared RAG logic)
│   │   ├── fiqh_agent.py         # FiqhAgent (RAG, fiqh_passages)
│   │   ├── hadith_agent.py       # HadithAgent (RAG, hadith_passages)
│   │   ├── seerah_agent.py       # SeerahAgent (RAG, seerah_passages)
│   │   ├── general_islamic_agent.py  # GeneralIslamicAgent (RAG)
│   │   └── chatbot_agent.py      # ChatbotAgent (template-based)
│   │
│   ├── tools/
│   │   ├── base.py               # BaseTool, ToolInput, ToolOutput
│   │   ├── zakat_calculator.py   # ZakatCalculator (8 types)
│   │   ├── inheritance_calculator.py # InheritanceCalculator
│   │   ├── prayer_times_tool.py  # PrayerTimesTool (6 methods)
│   │   ├── hijri_calendar_tool.py # HijriCalendarTool (Umm al-Qura)
│   │   └── dua_retrieval_tool.py # DuaRetrievalTool (Hisn al-Muslim)
│   │
│   ├── knowledge/
│   │   ├── embedding_model.py    # BAAI/bge-m3 wrapper + cache
│   │   ├── embedding_cache.py    # Redis caching layer
│   │   ├── vector_store.py       # Qdrant client
│   │   ├── hybrid_search.py      # HybridSearcher (semantic + BM25)
│   │   ├── hierarchical_retriever.py  # Book-level retrieval
│   │   ├── title_loader.py       # Chapter/context enrichment
│   │   ├── hadith_grader.py      # Authenticity grading
│   │   ├── book_weighter.py      # Importance scoring
│   │   └── hierarchical_chunker.py    # Book → Chapter → Passage
│   │
│   ├── quran/
│   │   ├── verse_retrieval.py    # Verse lookup engine
│   │   ├── nl2sql.py             # Natural language → SQL
│   │   ├── quotation_validator.py # Quran quote verification
│   │   └── tafsir_retrieval.py   # Tafsir lookup
│   │
│   ├── data/
│   │   ├── models/               # SQLAlchemy models
│   │   └── ingestion/            # Data loaders
│   │
│   └── infrastructure/
│       ├── db.py                 # PostgreSQL async connection
│       ├── db_sync.py            # PostgreSQL sync connection
│       ├── redis.py              # Redis connection
│       └── llm_client.py         # Groq/OpenAI client factory
│
├── data/
│   ├── mini_dataset/             # 1.7 MB, 1,623 documents
│   ├── seed/                     # Seed data (duas, quran samples)
│   └── processed/                # Chunked documents
│
├── datasets/                     # Full datasets (excluded from Git)
│   ├── data/extracted_books/     # 8,425 books (17.16 GB)
│   └── Sanadset*/                # 650,986 hadith (1.43 GB)
│
├── docker/
│   ├── docker-compose.dev.yml    # 5 services
│   └── Dockerfile.api            # API Docker image
│
├── tests/                        # 9 test files, 121 tests
│   ├── conftest.py               # Pytest fixtures
│   ├── test_router.py            # Intent classifier
│   ├── test_api.py               # API endpoints
│   └── test_*_calculator.py      # Tool tests
│
├── scripts/                      # 37+ utility scripts
├── docs/                         # 14 documentation directories
├── migrations/                   # Database migrations (Alembic)
├── pyproject.toml                # Poetry dependencies
├── Makefile                      # Build commands
├── .env.example                  # Environment template
└── README.md                     # Project overview
```

---

## Appendix B: Key Design Patterns

### Command Pattern (Agents)

All agents implement the `execute()` method accepting `AgentInput` and returning `AgentOutput`:

```python
class BaseAgent(ABC):
    @abstractmethod
    async def execute(self, input: AgentInput) -> AgentOutput:
        pass

@dataclass
class AgentInput:
    query: str
    language: str = "ar"
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class AgentOutput:
    answer: str
    citations: List[Citation] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    confidence: float = 0.0
    requires_human_review: bool = False
```

### Strategy Pattern (Intent Classification)

Three classification strategies with fallback chain:
1. Keyword matching (fast)
2. LLM classification (accurate)
3. Embedding similarity (backup)

### Repository Pattern (Knowledge Layer)

Data access abstracted behind repository interfaces:
- `VectorStore` → Qdrant operations
- `VerseRetrievalEngine` → PostgreSQL queries
- `EmbeddingModel` → BAAI/bge-m3 wrapper

### Factory Pattern (App Creation)

```python
def create_app() -> FastAPI:
    app = FastAPI(...)
    # Add middleware
    # Register routes
    return app

app = create_app()
```

---

## Appendix C: Performance Benchmarks

| Operation | Time | Notes |
|-----------|------|-------|
| Greeting response | <10ms | Template-based, no LLM |
| Intent classification (keyword) | <1ms | In-memory pattern matching |
| Intent classification (LLM) | ~200ms | Groq Qwen3-32B |
| Zakat calculation | <5ms | Deterministic math |
| Prayer times calculation | <10ms | Astronomical formulas |
| Fiqh RAG query | ~257ms | Embedding + search + LLM |
| Quran verse lookup | ~50ms | PostgreSQL query |
| Embedding generation | ~50ms/query | BAAI/bge-m3, GPU |
| Embedding batch (64 docs) | ~800ms | Optimized batch processing |

---

## Appendix D: References

- **Fanar-Sadiq Architecture Paper:** `docs/Fanar-Sadiq A Multi-Agent Architecture for Grounded Islamic QA.pdf`
- **BAAI/bge-m3 Model:** https://huggingface.co/BAAI/bge-m3
- **Qdrant Documentation:** https://qdrant.tech/documentation/
- **Groq API:** https://console.groq.com/
- **ElShamela Library:** https://shamela.ws/
- **Quran.com API:** https://quran.api-docs.io/
- **Sunnah.com Hadith:** https://sunnah.com/

---

<div align="center">

**Burhan Islamic QA System — Architecture Documentation**  
Built with ❤️ for the Muslim community  
Based on Fanar-Sadiq Multi-Agent Architecture  
Version 0.5.0 | Phase 6 | April 13, 2026

</div>
