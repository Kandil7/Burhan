# 📖 Master Class: Infrastructure & Knowledge Facades

## 🕌 Introduction
This document explores how Burhan connects to the "Outside World" (Infrastructure) and how it organizes its internal data access patterns (Knowledge Facades). This layer is critical for performance, caching, and reliability.

---

## 📁 src/infrastructure/ - The Connectivity Layer

### 1. `src/infrastructure/database.py`
**Purpose**: Managed access to PostgreSQL. 
**Deep Logic**:
- **Dual Connection Pool**: Implements both `SyncSessionLocal` (for management tasks) and `AsyncDatabaseManager` (via `asyncpg`) for high-concurrency API requests.
- **Auto-Initialization**: The `initialize()` method parses the `DATABASE_URL` to create an optimal connection pool size (`min_size=5, max_size=20`).
- **N+1 Prevention**: Explicitly configured for `joinedload` patterns used in the Quran module.

### 2. `src/infrastructure/redis.py`
**Purpose**: Asynchronous caching for embeddings and rate limiting.
**Deep Logic**:
- **Non-Blocking I/O**: Migrated to `redis.asyncio` to ensure cache hits/misses don't block the FastAPI event loop.
- **Fail-Open Strategy**: If Redis is down, the system logs a warning but continues operating using in-memory fallbacks, ensuring high availability.

### 3. `src/infrastructure/llm_client.py`
**Purpose**: Unified abstraction for OpenAI and Groq.
**Deep Logic**:
- **Thinking Filter**: The `_strip_thinking()` function uses a regex (`<think>.*?</think>`) to remove internal chain-of-thought tokens from Qwen3 and DeepSeek models before returning the text to the user.
- **JSON Mode Guard**: Implements a `_supports_response_format()` check because Groq doesn't support the explicit `json_object` flag; it relies on prompt-level instruction instead.

---

## 📁 src/knowledge/ - The Legacy Facades (v1)

### 1. `src/knowledge/embedding_model.py`
**Purpose**: Wrapper for the **BGE-M3** model.
**Deep Logic**:
- **Order-Preserving Cache**: When encoding a batch, it checks Redis for each text. If some are missing, it encodes *only* the missing ones but reassembles the final list in the exact original order.
- **Hardware Acceleration**: Automatically detects `cuda` -> `mps` (Mac) -> `cpu`.
- **Dimension Consistency**: Hardcoded to `1024`, matching the Qdrant collection schemas.

### 2. `src/knowledge/vector_store.py`
**Purpose**: High-level wrapper for Qdrant.
**Deep Logic**:
- **Deterministic IDs**: Uses `hashlib.sha256` of document content to generate point IDs. This ensures that re-indexing the same data doesn't create duplicate vectors.
- **Faceted Search**: Implements `FieldCondition` and `Filter` logic to allow agents to search within specific Madhhabs or historical eras.

### 3. `src/knowledge/hadith_grader.py`
**Purpose**: Re-exports logic from the verifiers module to provide a consistent "Grade" for every retrieved Hadith.
**Deep Logic**:
- **Weighted Relevance**: Authentic Hadiths (*Sahih*) get a multiplier of `1.0`, while weak Hadiths (*Da'if*) are penalized with `0.5`, effectively pushing them to the bottom of the answer context.

---

## 📊 Summary of File Responsibilities

| File | Tech Stack | Performance Strategy |
|------|------------|----------------------|
| `database.py` | SQLAlchemy + asyncpg | Connection Pooling |
| `redis.py` | Redis.asyncio | Non-blocking I/O |
| `llm_client.py` | OpenAI / Groq | CoT Filtering |
| `embedding_model.py` | Transformers + PyTorch | Order-Aware Caching |
| `vector_store.py` | Qdrant Client | Deterministic Point IDs |

---

**Next:** Doc 24 will cover the Indexing and Data Engine.
