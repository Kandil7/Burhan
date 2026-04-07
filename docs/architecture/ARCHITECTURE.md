# Athar - Architecture & Design Document

**Version:** 2.0  
**Date:** April 7, 2026  
**Based on:** Fanar-Sadiq Multi-Agent Architecture

---

## 1. System Overview

### 1.1 Purpose

Athar is an Islamic QA system that provides accurate, citation-backed answers to religious questions using verified sources from Quran, Hadith, and Fiqh.

### 1.2 Design Principles

1. **Grounded Answers** - Every answer linked to verified sources
2. **Multi-Agent Specialization** - Each agent expert in one domain
3. **Deterministic Where Possible** - Calculators for math, RAG for knowledge
4. **Citation Transparency** - Users see exact sources
5. **Scholarly Accuracy** - Respects Islamic scholarly tradition

### 1.3 Key Requirements

| Requirement | Implementation |
|-------------|----------------|
| Answer accuracy | RAG with verified sources only |
| Source attribution | Citation system [C1], [C2], etc. |
| Multi-intent support | 16 intent types |
| Fast response | Hybrid intent classification |
| Scalability | Microservices architecture |
| Extensibility | Agent registry pattern |

---

## 2. Architectural Decisions

### 2.1 Why Multi-Agent?

**Problem:** Islamic questions span diverse domains (fiqh, quran, hadith, calculations)

**Solution:** Specialized agents per domain

```
User: "ما حكم الصلاة؟" → FiqhAgent (RAG)
User: "احسب زكاة مالي" → ZakatCalculator (deterministic)
User: "ما معنى آية الكرسي؟" → QuranAgent (NL2SQL)
User: "متى رمضان؟" → HijriCalendarTool (deterministic)
```

**Benefits:**
- ✅ Domain expertise per agent
- ✅ Independent development/testing
- ✅ Easy to add new domains
- ✅ Clear separation of concerns

### 2.2 Why Hybrid Intent Classification?

**Problem:** LLM classification is slow/expensive, keyword matching is inaccurate

**Solution:** 3-tier hybrid approach

```
Tier 1: Keyword Matching (fast, ≥0.90 confidence)
  ↓ if not confident
Tier 2: LLM Classification (accurate, ≥0.75 confidence)
  ↓ if not confident
Tier 3: Embedding Similarity (fallback)
```

**Performance:**
- 60% queries: Tier 1 (instant)
- 35% queries: Tier 2 (~500ms)
- 5% queries: Tier 3 (~100ms)

### 2.3 Why RAG?

**Problem:** LLMs hallucinate religious rulings

**Solution:** Retrieval-Augmented Generation

```
Query → Retrieve verified docs → Generate from docs only → Cite sources
```

**Benefits:**
- ✅ No hallucination (grounded in sources)
- ✅ Citations provided
- ✅ Update knowledge without retraining
- ✅ Transparent reasoning

### 2.4 Technology Choices

| Component | Choice | Why |
|-----------|--------|-----|
| **Backend** | FastAPI | Async, type-safe, auto-docs |
| **Frontend** | Next.js 15 | SSR, i18n, RTL support |
| **Vector DB** | Qdrant | Fast, HNSW, metadata filtering |
| **Embeddings** | Qwen3-Embedding-0.6B | Arabic-optimized, open-source |
| **LLM** | Groq Qwen3-32B | Fast, cheap, good Arabic |
| **Cache** | Redis | Fast, TTL support |
| **Database** | PostgreSQL 16 | Relational, ACID |

---

## 3. System Architecture

### 3.1 Component Diagram

```
┌──────────────────────────────────────────────────────────────┐
│                         CLIENT LAYER                         │
│                                                              │
│  Next.js Frontend (http://localhost:3000)                   │
│  • Chat interface                                            │
│  • RTL support                                               │
│  • Arabic/English i18n                                       │
│  • Calculator forms                                          │
└───────────────────────┬──────────────────────────────────────┘
                        │ HTTP/WebSocket
┌───────────────────────▼──────────────────────────────────────┐
│                        API LAYER                             │
│                                                              │
│  FastAPI Backend (http://localhost:8000)                    │
│  • 18 REST endpoints                                         │
│  • OpenAPI auto-docs                                         │
│  • CORS middleware                                           │
│  • Error handler                                             │
│  • Request validation                                        │
└───────────────────────┬──────────────────────────────────────┘
                        │
┌───────────────────────▼──────────────────────────────────────┐
│                   ORCHESTRATION LAYER                        │
│                                                              │
│  ┌─────────────────┐  ┌──────────────────┐                  │
│  │ Intent Router   │  │ Response         │                  │
│  │ (3-tier hybrid) │→ │ Orchestrator     │                  │
│  │                 │  │ (agent routing)  │                  │
│  │ • Keywords      │  │                  │                  │
│  │ • LLM           │  └────────┬─────────┘                  │
│  │ • Embeddings    │           │                             │
│  └─────────────────┘           ↓                             │
│                         ┌──────────────┐                     │
│                         │ Citation     │                     │
│                         │ Normalizer   │                     │
│                         │ ([C1],[C2])  │                     │
│                         └──────────────┘                     │
└───────────────────────┬──────────────────────────────────────┘
                        │
┌───────────────────────▼──────────────────────────────────────┐
│                    AGENTS & TOOLS LAYER                      │
│                                                              │
│  AGENTS (13):                   TOOLS (5):                   │
│  ┌────────────────────┐        ┌──────────────────┐         │
│  │ • FiqhAgent        │        │ • ZakatCalc      │         │
│  │ • HadithAgent      │        │ • InheritanceCalc│         │
│  │ • SanadsetAgent    │        │ • PrayerTimes    │         │
│  │ • TafsirAgent      │        │ • HijriCalendar  │         │
│  │ • AqeedahAgent     │        │ • DuaRetrieval   │         │
│  │ • SeerahAgent      │        └──────────────────┘         │
│  │ • HistoryAgent     │                                     │
│  │ • UsulFiqhAgent    │                                     │
│  │ • ArabicLangAgent  │                                     │
│  │ • GeneralAgent     │                                     │
│  │ • QuranAgent       │                                     │
│  │ • ChatbotAgent     │                                     │
│  └────────────────────┘                                     │
└───────────────────────┬──────────────────────────────────────┘
                        │
┌───────────────────────▼──────────────────────────────────────┐
│                    KNOWLEDGE LAYER                           │
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐  │
│  │ Vector Store │  │ PostgreSQL   │  │ Redis Cache      │  │
│  │ (Qdrant)     │  │ (Quran/Hadith│  │ (embeddings,     │  │
│  │ 10 collections│  │  tables)     │  │  sessions)       │  │
│  │ 1024-dim     │  │              │  │                  │  │
│  └──────────────┘  └──────────────┘  └──────────────────┘  │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ Data Sources:                                         │   │
│  │ • master.db (8,425 books catalog)                    │   │
│  │ • Lucene indexes (11M+ Arabic text docs)             │   │
│  │ • Sanadset (650K hadith with chains)                 │   │
│  │ • Shamela Library (8,425 books)                      │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ LLM Provider:                                         │   │
│  │ • Groq Qwen3-32B (primary)                           │   │
│  │ • OpenAI GPT-4o-mini (fallback)                      │   │
│  └──────────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────────┘
```

### 3.2 Data Flow: Query Processing

```
1. User submits query via POST /api/v1/query
   Example: "ما حكم زكاة الذهب؟"

2. Intent Router classifies intent
   Keywords: "زكاة" → Intent.ZAKAT (confidence: 0.95)

3. Orchestrator routes to ZakatCalculator

4. Calculator extracts parameters
   From query: الذهب (gold)

5. Calculator computes result
   Nisab threshold: 85g gold
   Rate: 2.5%
   Result: zakat_amount = gold_value × 0.025

6. Response formatted with citations
   {
     "answer": "زكاة الذهب تجب إذا بلغ 85 جرامًا...",
     "citations": [
       {"id": "C1", "source": "Quran 9:103"}
     ]
   }

7. Response returned to user
```

### 3.3 Data Flow: RAG Query

```
1. User: "ما حكم صلاة الجماعة؟"

2. Intent Router → Intent.FIQH (confidence: 0.88)

3. Orchestrator → FiqhAgent

4. FiqhAgent.retrieve():
   a. Embed query → 1024-dim vector
   b. Search Qdrant fiqh_passages collection
   c. Return top-10 similar passages
   d. Filter by metadata (category=fiqh)

5. FiqhAgent.generate():
   a. Build prompt with retrieved docs
   b. Send to LLM (Groq Qwen3-32B)
   c. Generate answer
   d. Extract citations from docs

6. Citation normalizer:
   Format sources as [C1], [C2], etc.

7. Response:
   {
     "answer": "صلاة الجماعة واجبة عند جمهور العلماء...",
     "citations": [
       {"id": "C1", "type": "hadith", "source": "Sahih Muslim 650"},
       {"id": "C2", "type": "fiqh", "source": "Al-Mughni 2:199"}
     ]
   }
```

---

## 4. Design Patterns

### 4.1 Strategy Pattern (Intent Routing)

```python
class IntentRouter:
    def route(self, query: str) -> Intent:
        # Try strategies in order
        if result := self.keyword_match(query):
            return result
        if result := self.llm_classify(query):
            return result
        return self.embedding_classify(query)
```

### 4.2 Registry Pattern (Agent Management)

```python
class AgentRegistry:
    def __init__(self):
        self._agents: Dict[str, BaseAgent] = {}
        self._intent_map: Dict[Intent, str] = {}
    
    def register_agent(self, name: str, agent: BaseAgent, intents: List[Intent]):
        self._agents[name] = agent
        for intent in intents:
            self._intent_map[intent] = name
    
    def get_for_intent(self, intent: Intent) -> BaseAgent:
        agent_name = self._intent_map.get(intent)
        return self._agents.get(agent_name)
```

### 4.3 Template Method Pattern (Agent Base Class)

```python
class BaseAgent(ABC):
    async def execute(self, input: AgentInput) -> AgentOutput:
        # Template method
        docs = await self.retrieve(input.query)
        answer = await self.generate(input.query, docs)
        citations = await self.extract_citations(docs)
        return AgentOutput(answer=answer, citations=citations)
    
    @abstractmethod
    async def retrieve(self, query: str) -> List[Document]:
        pass
    
    @abstractmethod
    async def generate(self, query: str, docs: List[Document]) -> str:
        pass
```

### 4.4 Observer Pattern (Logging)

```python
# Structured logging throughout
logger.info("router.intent_classified", 
            intent=intent.value, 
            confidence=confidence, 
            method=method)
```

---

## 5. Performance Considerations

### 5.1 Response Time Budget

| Component | Time | % of Total |
|-----------|------|------------|
| Intent classification | 50-500ms | 10-20% |
| Agent routing | <1ms | <1% |
| Document retrieval | 100-200ms | 20-40% |
| LLM generation | 300-800ms | 60-70% |
| Citation formatting | <10ms | <1% |
| **Total** | **500-1500ms** | **100%** |

### 5.2 Optimization Strategies

1. **Intent Classification:**
   - Keyword matching for common queries (instant)
   - Cache LLM classifications (Redis, 1hr TTL)

2. **Embedding:**
   - Redis cache for repeated queries (7-day TTL)
   - Local dict fallback when Redis unavailable

3. **Vector Search:**
   - HNSW index (M=16, ef_construct=128)
   - Metadata filtering before search
   - Batch retrieval for multiple queries

4. **LLM:**
   - Groq for speed (500ms avg)
   - Prompt caching
   - Temperature 0.1 for consistency

---

## 6. Security Considerations

### 6.1 API Security

- **Rate limiting:** Prevent abuse
- **CORS:** Restrict origins
- **Input validation:** Pydantic models
- **SQL injection:** Parameterized queries
- **Secrets management:** .env file (excluded from Git)

### 6.2 Data Security

- **PII:** None stored (Islamic texts only)
- **Encryption:** HTTPS in transit, encrypted at rest
- **Access control:** Database credentials via .env

### 6.3 LLM Safety

- **Prompt injection:** System prompt hardening
- **Output filtering:** Citation verification
- **Hallucination prevention:** Ground in retrieved docs only
- **Fallback:** Deterministic tools for calculations

---

## 7. Scalability

### 7.1 Current Scale

| Metric | Value |
|--------|-------|
| Books | 8,425 |
| Hadith | 650,986 |
| Vector collections | 10 |
| Total vectors | ~700K |
| API endpoints | 18 |
| Agents | 13 |

### 7.2 Scaling Strategies

**Horizontal:**
- Multiple API instances behind load balancer
- Stateless agents (no session storage)
- Redis for shared cache

**Vertical:**
- Larger Qdrant instance for more vectors
- More GPU for faster embedding
- Larger PostgreSQL instance for complex queries

**Data:**
- Shard vector collections by category
- Partition PostgreSQL tables
- Archive old queries

---

## 8. Monitoring & Observability

### 8.1 Logging

```python
# Structured JSON logging
logger.info("query.processed",
            query_id=uuid,
            intent=intent.value,
            confidence=confidence,
            agent=agent_name,
            time_ms=elapsed_ms)
```

### 8.2 Metrics

- Request rate (queries/min)
- Response time (p50, p95, p99)
- Error rate (5xx responses)
- Intent distribution
- Agent usage
- Cache hit rate

### 8.3 Health Checks

```bash
GET /health     # Basic health
GET /ready      # Readiness (all deps up)
```

---

## 9. Testing Strategy

### 9.1 Test Pyramid

```
        ┌─────┐
        │ E2E │  (10%) - Full pipeline tests
        ├─────┤
     ┌──────────┐
     │Integration│ (20%) - API endpoint tests
     ├──────────┤
  ┌────────────────┐
  │    Unit Tests   │ (70%) - Agent, tool, router tests
  └────────────────┘
```

### 9.2 Test Coverage

| Component | Coverage | Tests |
|-----------|----------|-------|
| Intent Router | ~100% | 50+ cases |
| Zakat Calculator | ~95% | 20+ cases |
| Inheritance Calculator | ~95% | 15+ cases |
| API Endpoints | ~97% | 30+ cases |
| **Overall** | **~91%** | **150+ tests** |

---

## 10. Future Enhancements

### 10.1 Planned Features

1. **User Authentication**
   - Save query history
   - Personalized recommendations

2. **Mobile App**
   - React Native
   - Offline mode

3. **Advanced Search**
   - Morphological search (S2.db roots)
   - Fuzzy hadith matching
   - Cross-reference navigation

4. **Scholarly Network**
   - Author citation graph
   - Chain of transmission analysis
   - Scholar influence mapping

5. **Multi-Language**
   - English translations
   - Urdu, Turkish, Indonesian

### 10.2 Infrastructure Improvements

1. **CI/CD Pipeline**
   - Automated testing
   - Staging deployment
   - Production deployment

2. **Monitoring**
   - Grafana dashboards
   - Alert rules
   - APM integration

3. **CDN**
   - Static asset caching
   - Geo-distribution

---

*Architecture document - Version 2.0, April 7, 2026*
