# 🏗️ Burhan Architecture Documentation

Detailed technical architecture of the Burhan Islamic QA system.

---

## 📋 Table of Contents

- [System Overview](#system-overview)
- [Architectural Principles](#architectural-principles)
- [Layer Architecture](#layer-architecture)
- [Component Details](#component-details)
- [Data Flow](#data-flow)
- [Database Schema](#database-schema)
- [API Design](#api-design)
- [RAG Pipeline](#rag-pipeline)
- [Security Considerations](#security-considerations)
- [Performance Considerations](#performance-considerations)
- [Scalability](#scalability)

---

## 🎯 System Overview

Burhan is a **multi-agent Islamic QA system** based on the Fanar-Sadiq research architecture. It provides grounded, citation-backed answers to Islamic questions using:

- **Intent Classification**: Route questions to specialized pipelines
- **Deterministic Calculators**: Accurate zakat and inheritance calculations
- **RAG Pipelines**: Retrieval-Augmented Generation with verified sources
- **Citation Normalization**: Standardized references [C1], [C2], etc.

### Key Design Decisions

1. **Separation of Concerns**: Each intent has dedicated agent/tool
2. **Deterministic over Generative**: Math calculations use code, not LLMs
3. **Grounded Answers**: RAG answers based only on retrieved passages
4. **Citation Tracking**: Every answer linked to verifiable sources

---

## 🏛️ Architectural Principles

### 1. Intent-Aware Routing

Not all questions should go through the same pipeline:
- **Zakat calculation** → Deterministic calculator
- **Quran verse** → Exact lookup
- **Fiqh ruling** → RAG with citations
- **Greeting** → Template response

### 2. Three-Tier Classification

Hybrid Intent Classifier balances speed and accuracy:
1. **Keyword matching** (fast, 90%+ confidence)
2. **LLM classification** (flexible, 75%+ confidence)
3. **Embedding fallback** (robust backup)

### 3. Deterministic Calculators

Never use LLMs for math:
- Zakat calculations use fixed formulas
- Inheritance uses fara'id rules
- Prayer times use astronomical equations

### 4. Citation Normalization

Every answer must be verifiable:
- Detect various citation formats
- Normalize to [C1], [C2] format
- Provide structured metadata and URLs

---

## 🏗️ Layer Architecture

### Layer 1: API Layer (FastAPI + Next.js)

**Responsibilities:**
- Receive HTTP requests
- Validate input (Pydantic models)
- Route to orchestrator
- Return structured responses

**Endpoints:**
```
POST /api/v1/query       # Main query endpoint
POST /api/v1/rag/fiqh    # Fiqh RAG endpoint
POST /api/v1/rag/general # General Islamic knowledge
GET  /health             # Health check
GET  /ready              # Readiness probe
GET  /docs               # Swagger UI
GET  /redoc              # ReDoc UI
```

---

### Layer 2: Orchestration Layer

**Responsibilities:**
- Classify query intent
- Route to appropriate agent/tool
- Assemble final response
- Normalize citations

**Components:**

#### HybridQueryClassifier
```python
class HybridQueryClassifier:
    async def classify(self, query: str) -> RouterResult:
        # Tier 1: Keyword matching
        if keyword_match >= 0.90:
            return keyword_result
        
        # Tier 2: LLM classification
        llm_result = await llm_classify(query)
        if llm_result.confidence >= 0.75:
            return llm_result
        
        # Tier 3: Embedding fallback
        return await embedding_classify(query)
```

#### ResponseOrchestrator
```python
class ResponseOrchestrator:
    async def route_query(self, query, intent, **kwargs) -> AgentOutput:
        target = INTENT_ROUTING[intent]
        
        if target in self.agents:
            return await self.agents[target].execute(...)
        elif target in self.tools:
            return await self.tools[target].execute(...)
        else:
            return fallback_response()
```

#### CitationNormalizer
```python
class CitationNormalizer:
    def normalize(self, text: str) -> str:
        # Detect citation patterns
        # Replace with [C1], [C2], etc.
        # Build structured citation objects
        return normalized_text
```

---

### Layer 3: Agents & Tools Layer

**Agents** (require reasoning/RAG):
- FiqhAgent - Islamic jurisprudence with RAG
- QuranAgent - Quran lookup, NL2SQL, tafsir
- GeneralIslamicAgent - History, biography, theology
- ChatbotAgent - Greetings, small talk

**Tools** (deterministic):
- ZakatCalculator - Wealth, livestock, crops
- InheritanceCalculator - Fara'id rules
- PrayerTimesTool - Astronomical calculations
- HijriCalendarTool - Umm al-Qura calendar
- DuaRetrievalTool - Verified adhkar database

**Agent Interface:**
```python
class BaseAgent(ABC):
    @abstractmethod
    async def execute(self, input: AgentInput) -> AgentOutput:
        pass
```

**Tool Interface:**
```python
class BaseTool(ABC):
    @abstractmethod
    async def execute(self, **kwargs) -> ToolOutput:
        pass
```

---

### Layer 4: Knowledge Layer

**PostgreSQL 16:**
- Quran verses (6,236 ayahs)
- Translations (multi-language)
- Tafsir (commentaries)
- Query logs (analytics)

**Qdrant (Vector DB):**
- Fiqh passages (500k+)
- Hadith passages
- Dua/Adhkar
- General Islamic knowledge

**Redis 7:**
- Response caching
- Embedding cache
- Session management

**LLM Provider:**
- OpenAI (GPT-4o-mini)
- Used for: Intent classification, RAG generation

---

## 🔄 Data Flow

### Query Processing Flow

```
User Query
    │
    ▼
┌──────────────────────┐
│  API Validation      │  Pydantic models
└────────┬─────────────┘
         │
         ▼
┌──────────────────────┐
│ Intent Classifier    │  3-tier classification
└────────┬─────────────┘
         │
         │ RouterResult {
         │   intent: "zakat",
         │   confidence: 0.92,
         │   method: "keyword"
         │ }
         ▼
┌──────────────────────┐
│ Orchestrator         │  Route to agent/tool
└────────┬─────────────┘
         │
         ▼
┌──────────────────────┐
│ Agent/Tool Execution │
│  - ZakatCalculator   │
│  - FiqhAgent (RAG)   │
│  - QuranAgent        │
└────────┬─────────────┘
         │
         │ AgentOutput {
         │   answer: "...",
         │   citations: [...],
         │   metadata: {...}
         │ }
         ▼
┌──────────────────────┐
│ Citation Normalizer  │  [C1], [C2], ...
└────────┬─────────────┘
         │
         ▼
┌──────────────────────┐
│ Response Assembly    │  QueryResponse
└────────┬─────────────┘
         │
         ▼
    User Response
```

---

## 🗄️ Database Schema

### Core Tables

#### `surahs`
```sql
CREATE TABLE surahs (
    id SERIAL PRIMARY KEY,
    number INT UNIQUE,           -- 1-114
    name_ar VARCHAR(100),        -- البقرة
    name_en VARCHAR(100),        -- Al-Baqarah
    verse_count INT,             -- 286
    revelation_type VARCHAR(7)   -- meccan/medinan
);
```

#### `ayahs`
```sql
CREATE TABLE ayahs (
    id SERIAL PRIMARY KEY,
    surah_id INT REFERENCES surahs(id),
    number_in_surah INT,         -- 1, 2, 3...
    text_uthmani TEXT,           -- Uthmani script
    text_simple TEXT,            -- Simplified text
    juz INT,                     -- 1-30
    page INT,                    -- 1-604
    UNIQUE(surah_id, number_in_surah)
);

-- Indexes
CREATE INDEX idx_ayah_text_search ON ayahs 
    USING GIN (to_tsvector('simple', text_uthmani));
```

#### `query_logs`
```sql
CREATE TABLE query_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_query TEXT,
    intent VARCHAR(30),
    intent_confidence FLOAT,
    agent_used VARCHAR(50),
    citations JSONB,
    latency_ms INT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

---

## 🔌 API Design

### Request/Response Pattern

**Request:**
```json
POST /api/v1/query
{
  "query": "ما حكم زكاة المال؟",
  "language": "ar",
  "madhhab": "hanafi"
}
```

**Response:**
```json
{
  "query_id": "550e8400-e29b-41d4-a716-446655440000",
  "intent": "zakat",
  "intent_confidence": 0.92,
  "answer": "زكاة المال تجب إذا بلغ النصاب...",
  "citations": [
    {
      "id": "C1",
      "type": "quran",
      "source": "Quran 9:103",
      "reference": "Surah At-Tawbah, Ayah 103",
      "url": "https://quran.com/9/103"
    }
  ],
  "metadata": {
    "agent": "zakat_tool",
    "processing_time_ms": 150
  }
}
```

---

## 🧠 RAG Pipeline

### Retrieval-Augmented Generation Flow

```
User Question
    │
    ▼
┌──────────────────┐
│ Encode Query     │  Qwen3-Embedding
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ Vector Search    │  Qdrant (cosine similarity)
└────────┬─────────┘
         │
         │ Top-15 passages
         ▼
┌──────────────────┐
│ Hybrid Search    │  Semantic + BM25 keyword
└────────┬─────────┘
         │
         │ Top-5 re-ranked
         ▼
┌──────────────────┐
│ LLM Generation   │  Grounded answer (temp 0.1)
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ Citations        │  Normalize to [C1], [C2]
└────────┬─────────┘
         │
         ▼
    Final Answer
```

### Fiqh Agent Configuration

```python
class FiqhAgent(BaseAgent):
    TOP_K_RETRIEVAL = 15
    TOP_K_RERANK = 5
    TEMPERATURE = 0.1  # Very low for fiqh
    
    FIQH_GENERATION_PROMPT = """
أجب بناءً ONLY على النصوص المسترجاعة.

السؤال: {query}
النصوص: {passages}

التعليمات:
1. أجب بناءً على النصوص فقط
2. اذكر الافتراضات
3. استخدم المراجع [C1], [C2]
4. لا تخترع مصادر خارجية
"""
```

---

## 🔒 Security Considerations

### Phase 1-5 (Current)
- No authentication (development only)
- CORS configured for localhost
- Input validation (Pydantic)
- SQL injection prevention (parameterized queries)

### Phase 6+ (Planned)
- API key authentication
- Rate limiting (Redis)
- Request sanitization
- XSS prevention (output encoding)

---

## ⚡ Performance Considerations

### Caching Strategy
- **Response Cache**: Cache identical queries (1 hour TTL)
- **Embedding Cache**: Cache query embeddings (7 days)
- **Intent Cache**: Cache frequent query intents

### Database Optimization
- **Indexes**: Full-text search on Quran text
- **Connection Pooling**: 10 connections max
- **Query Optimization**: EXPLAIN ANALYZE for slow queries

### LLM Optimization
- **Temperature**: 0.1 for fiqh (deterministic)
- **Max Tokens**: 2048 limit
- **Prompt Caching**: Cache system prompts

---

## 📈 Scalability

### Horizontal Scaling

**API Layer:**
- Stateless FastAPI instances
- Load balancer (Nginx/Traefik)
- Multiple replicas

**Database:**
- PostgreSQL read replicas
- Connection pooling (PgBouncer)

**Vector DB:**
- Qdrant cluster mode
- Sharding by collection

**Cache:**
- Redis cluster
- Key distribution

### Vertical Scaling

**Resource Requirements:**
- **Development**: 2 CPU, 4GB RAM
- **Production**: 8 CPU, 32GB RAM
- **Vector DB**: 4 CPU, 16GB RAM (minimum)

---

## 📊 Monitoring & Observability

### Metrics (Phase 6+)
- Query volume (queries/minute)
- Intent distribution (% by intent type)
- Response latency (p50, p95, p99)
- Cache hit rate
- Error rate

### Logging
- Structured JSON logs
- Request ID tracking
- Error tracing

---

## 🧩 Extension Points

### Adding New Agents

1. Create agent class inheriting `BaseAgent`
2. Implement `execute()` method
3. Register with orchestrator
4. Add intent to `INTENT_ROUTING`

### Adding New Tools

1. Create tool class inheriting `BaseTool`
2. Implement `execute()` method
3. Register with orchestrator
4. Add intent to `INTENT_ROUTING`

### Adding New Data Sources

1. Create data loader in `src/data/ingestion/`
2. Define Pydantic models
3. Create database migration
4. Add to vector DB collection

---

<div align="center">

**Architecture Version:** 1.0  
**Last Updated:** Phase 5 Complete  
**Status:** Production-Ready

</div>
