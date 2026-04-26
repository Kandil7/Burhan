# Comprehensive Burhan Islamic QA System Documentation

This document provides an exhaustive explanation of the Burhan Islamic Question-Answering system, covering every file, every component, the complete architecture, and detailed instructions for building and running the project from scratch.

---

## 1. Project Overview and Purpose

### 1.1 What is Burhan?

Burhan (Arabic: أثر, meaning "Legacy" or "Trace") is a comprehensive Islamic Question-Answering system built on the Fanar-Sadiq multi-agent architecture. The system is designed to answer Islamic questions with verified sources and proper citations, drawing from the Quran, Hadith, and classical Islamic scholarly texts. The project represents a sophisticated integration of traditional Islamic knowledge with modern artificial intelligence technologies, implementing a hybrid approach that combines deterministic rule-based calculations with neural language model capabilities.

The system achieves remarkable accuracy through its three-tier intent classification mechanism, which first uses keyword matching for obvious queries, then leverages large language models for nuanced classification, and finally falls back to embedding-based semantic similarity when needed. This architecture ensures that users receive accurate, grounded responses whether they ask in Arabic or English, and regardless of whether their query is simple or complex.

Burhan supports nine distinct intent categories spanning Islamic jurisprudence (fiqh), Quranic inquiries, general Islamic knowledge, greetings and salutations, Zakat calculations, inheritance distribution calculations, supplications (dua), Hijri calendar conversions, and prayer times calculations. Each category is handled by specialized components that either utilize deterministic algorithms for mathematical calculations or retrieve relevant information from knowledge bases for question-answering tasks.

### 1.2 Core Objectives

The primary objectives of the Burhan project center on making Islamic knowledge accessible, accurate, and verifiable. Unlike general AI chatbots that may produce hallucinated content, Burhan grounds every answer in verified sources, providing proper citations that users can trace back to original texts. This grounding ensures that the system serves as a reliable educational tool rather than merely a conversational interface.

The system also aims to preserve and democratize access to traditional Islamic scholarship. By implementing classical calculation methods for Zakat and inheritance, the project ensures that users can perform important religious calculations according to established jurisprudential rules without requiring specialized scholarly knowledge. The inclusion of madhhab (Islamic school of jurisprudence) awareness allows users to receive answers appropriate to their specific legal tradition.

Furthermore, Burhan demonstrates a practical implementation of the Fanar-Sadiq research architecture, proving that multi-agent systems can effectively handle specialized domain question-answering. The project serves as both a functional application and a reference implementation for researchers and developers interested in building similar knowledge-based AI systems.

---

## 2. Technology Stack

### 2.1 Backend Technologies

The backend of Burhan is built entirely in Python 3.12, leveraging the async capabilities introduced in modern Python to handle high-concurrency workloads efficiently. FastAPI serves as the web framework, chosen for its native async support, automatic OpenAPI documentation generation, and excellent performance characteristics. The framework handles HTTP request processing, route dispatching, and middleware management, providing the foundation for all API endpoints.

For database operations, the project uses SQLAlchemy 2.0 with asyncpg for PostgreSQL interaction, enabling non-blocking database operations that scale well under load. The async approach is critical for maintaining responsiveness when the system processes multiple concurrent queries, each potentially requiring database lookups for intent classification, citation retrieval, or knowledge base queries. PostgreSQL 16 serves as the primary relational database, storing structured data including Quranic verses, user query logs, and application configuration.

Redis provides caching functionality through the redis-py library with hiredis parser, offering sub-millisecond response times for frequently accessed data. The caching layer stores embedding vectors, query results, and session data, significantly reducing the load on primary databases and improving response times for repeated queries. The caching strategy implements TTL (time-to-live) policies appropriate to each data type, ensuring cache freshness while maximizing hit rates.

The vector database component uses Qdrant for similarity search operations essential to the retrieval-augmented generation pipeline. Qdrant stores embedded representations of Islamic texts, enabling semantic search that goes beyond simple keyword matching. When users ask complex questions requiring contextual understanding, the system retrieves relevant passages from the vector store to provide grounding information for the language model.

For language model interactions, the system supports both OpenAI's GPT-4o-mini and Groq's Qwen3-32B models. The dual-provider support provides flexibility and redundancy, ensuring that the system remains operational even if one provider experiences availability issues. The llm_client module abstracts provider differences, presenting a unified interface for classification and generation tasks.

### 2.2 Frontend Technologies

The frontend employs Next.js 15 with TypeScript, providing a modern, server-rendered React application with excellent performance and SEO characteristics. The App Router architecture enables flexible routing and layout management, while TypeScript ensures type safety throughout the codebase, reducing runtime errors and improving developer experience.

Tailwind CSS handles styling, offering a utility-first approach that enables rapid UI development with consistent design tokens. The styling system supports RTL (right-to-left) layouts necessary for Arabic text display, with custom configuration for Islamic-themed color palettes and typography.

### 2.3 Infrastructure Technologies

Docker and Docker Compose provide containerization, enabling consistent deployment across development, staging, and production environments. The docker-compose.dev.yml file defines services for PostgreSQL, Qdrant, and Redis, along with the FastAPI application itself, creating a complete development environment with a single command.

---

## 3. Architecture Deep Dive

### 3.1 System Architecture Overview

The Burhan system follows a layered architecture pattern that separates concerns and enables independent evolution of each component. At the highest level, the architecture consists of five main layers: the user interface layer, the API gateway layer, the orchestration layer, the domain layer, and the knowledge layer. Each layer communicates only with adjacent layers, creating clear boundaries that simplify debugging and future development.

The user interface layer encompasses both the Next.js web application and the Swagger UI automatically generated by FastAPI. The web application provides a chat-based interface where users can type questions and receive formatted answers with citations. The Swagger documentation serves developers and API consumers who prefer direct HTTP interaction over the graphical interface.

The API gateway layer, implemented in src/api/main.py, handles HTTP request processing, applies CORS policies, manages middleware stack, and dispatches requests to appropriate route handlers. This layer performs input validation using Pydantic models, ensuring that only well-formed requests reach core business logic.

The orchestration layer, centered on the ResponseOrchestrator class in src/core/orchestrator.py, coordinates the flow of queries through the system. It receives classified intents from the router, selects appropriate agents or tools for processing, assembles responses, and adds citations. The orchestrator maintains registries of available agents and tools, enabling dynamic addition of new capabilities without modifying core logic.

The domain layer contains the specialized components that actually process queries. This includes the HybridQueryClassifier for intent classification, various agent implementations for question-answering, and tool implementations for deterministic calculations. Each component in this layer focuses on a specific type of processing, enabling clear separation of concerns.

The knowledge layer provides data access services abstraction, including database connections, caching, and vector store operations. This layer abstracts storage details from higher layers, enabling the domain layer to operate without knowledge of whether data comes from PostgreSQL, Redis, or Qdrant.

### 3.2 Query Processing Flow

Understanding the query processing flow reveals how the system transforms user questions into structured answers. The journey begins when a user submits a question through the POST /api/v1/query endpoint defined in src/api/routes/query.py. The endpoint validates the incoming QueryRequest, extracting the question text, optional language preference, location data for prayer times calculations, and madhhab selection for jurisprudential queries.

Once validated, the query enters the classification phase. The system instantiates a HybridQueryClassifier with the LLM client and passes the question through its three-tier classification pipeline. The first tier examines the query against KEYWORD_PATTERNS defined in src/config/intents.py, checking for explicit indicators like "زكاة" (zakat), "ميراث" (inheritance), or "صلاة" (prayer). If a keyword match achieves confidence of 0.90 or higher, the system skips the more expensive LLM classification and proceeds directly with the identified intent.

When keywords don't provide sufficient confidence, the second tier sends the query to the language model with a carefully crafted prompt that describes all available intents and requests JSON output with the classification decision, confidence score, detected language, and any sub-intent for Quran-related queries. The LLM classification prompt is defined in the LLM_CLASSIFIER_PROMPT constant within src/core/router.py, providing the model with comprehensive intent descriptions and examples for each category.

If the LLM classification returns confidence below the 0.75 threshold (CONFIDENCE_THRESHOLD), the third tier falls back to embedding-based classification using cosine similarity between the query embedding and pre-computed embeddings of example queries for each intent. This tier is particularly valuable for handling novel query phrasings that don't match obvious keywords but semantically resemble training examples.

After classification, the orchestrator receives the identified intent and routes the query to the appropriate handler. For Zakat, inheritance, prayer times, Hijri calendar, and dua queries, the system dispatches to deterministic tools that perform fixed calculations without any AI involvement. For fiqh and general Islamic knowledge queries, the system activates RAG-enabled agents that retrieve relevant passages from knowledge bases before generating answers. For Quran-specific queries, the system activates the Quran pipeline for verse lookup, tafsir retrieval, or analytics.

The final phase assembles the response, collecting any citations generated during processing and formatting them according to the CitationResponse schema defined in src/api/schemas/response.py. The complete response returns to the user with the answer text, citation list, intent classification details, and processing metadata including timing information.

---

## 4. Complete File Reference

This section provides detailed explanations for every file in the project, organized by their location in the directory structure.

### 4.1 Root Configuration Files

**pyproject.toml** serves as the central configuration file for the Python project, managed by Poetry for dependency resolution. The file defines all project dependencies including FastAPI, Pydantic, SQLAlchemy, asyncpg, redis, qdrant-client, openai, and various testing and linting tools. The project is configured with Python 3.12 as the minimum version, and dependencies are organized into main, dev, and optional (rag) groups. The rag group contains PyTorch and Transformers for embedding generation, installed separately due to their size.

**pyproject.toml** also configures the Ruff linter with specific rules targeting common Python issues, defines pytest options for async test execution, and sets up mypy for static type checking. The file establishes that the src directory contains the main package and that tests are included in the distribution.

The **.env** and **.env.example** files manage environment variables. The example file documents all required configuration options including database URLs, API keys for OpenAI and Groq, vector database settings, and logging preferences. Users copy the example to create their own configuration, ensuring that secrets remain outside version control.

### 4.2 Configuration Module (src/config/)

The configuration module centralizes all application settings, enabling environment-driven configuration without code changes. **src/config/settings.py** defines the Settings class using Pydantic BaseSettings, automatically loading values from environment variables with sensible defaults. The settings include database connection strings for PostgreSQL and Redis, Qdrant vector database configuration, LLM provider selection between OpenAI and Groq, model names and API keys, embedding model parameters, routing configuration including confidence thresholds, CORS origins for cross-origin requests, and logging preferences.

The settings class includes validation logic for log levels and CORS origins, ensuring that invalid configurations are caught at startup rather than causing runtime errors. Property methods provide convenient checks for production versus development environments, enabling conditional behavior based on deployment context.

**src/config/intents.py** defines the complete intent taxonomy for the system. The Intent enum enumerates nine primary intents: FIQH for jurisprudence questions, QURAN for Quranic inquiries, ISLAMIC_KNOWLEDGE for general questions, GREETING for salutations, ZAKAT for charity calculations, INHERITANCE for estate distribution, DUA for supplications, HIJRI_CALENDAR for calendar conversion, and PRAYER_TIMES for prayer schedule calculations. The QuranSubIntent enum further defines four sub-intents for Quran-related queries: VERSE_LOOKUP for specific verse retrieval, INTERPRETATION for tafsir requests, ANALYTICS for statistical queries, and QUOTATION_VALIDATION for verifying whether text is Quranic.

The module maps each intent to agent or tool names through the INTENT_ROUTING dictionary, which the orchestrator uses to determine routing destinations. KEYWORD_PATTERNS provides the first-tier classification data, listing Arabic and English keywords associated with each intent. The INTENT_DESCRIPTIONS dictionary supplies human-readable explanations of each intent for the LLM classification prompt.

**src/config/logging_config.py** sets up structured logging using Python's standard logging module combined with structlog for JSON-formatted log output. The configuration creates loggers that output timestamp, level, and contextual fields suitable for log aggregation systems. The get_logger() function returns configured logger instances throughout the application.

### 4.3 API Module (src/api/)

The API module implements the FastAPI application and all route handlers. **src/api/main.py** serves as the application factory, creating and configuring the FastAPI instance through the create_app() function. The function registers CORS middleware with configurable origins, adds error handling middleware, includes all route routers with appropriate prefixes, and configures OpenAPI documentation endpoints.

The lifespan context manager handles startup and shutdown events, enabling database connection pooling initialization and graceful cleanup. The root endpoint at GET / provides API metadata including available endpoints and version information, serving as a discovery mechanism for API consumers.

**src/api/routes/query.py** implements the primary query endpoint at POST /api/v1/query. The endpoint accepts QueryRequest objects with the question text and optional parameters, then orchestrates the complete query processing pipeline. A singleton ResponseOrchestrator instance ensures that agents and tools are initialized once and reused across requests, avoiding the overhead of repeated initialization.

The route handler measures processing time for performance monitoring, generates unique query IDs for tracking, logs all operations for debugging, and transforms agent outputs into QueryResponse objects. Error handling catches validation errors for user-friendly error messages and unexpected exceptions for logging and generic error responses.

**src/api/routes/tools.py** provides direct access to deterministic calculators through dedicated endpoints. Each tool receives its own route with appropriate parameter validation: GET /api/v1/tools/zakat accepts monetary amounts and calculates Zakat due, GET /api/v1/tools/inheritance accepts heir definitions and estate value for distribution calculation, GET /api/v1/tools/prayer-times accepts coordinates and date for prayer schedule retrieval, GET /api/v1/tools/hijri accepts Gregorian dates for Hijri conversion, and GET /api/v1/tools/duas retrieves supplications by category.

**src/api/routes/quran.py** exposes Quran-related functionality through specialized endpoints. GET /api/v1/quran/surahs returns the list of all 114 Quranic chapters with metadata. GET /api/v1/quran/ayah/{ref} retrieves specific verses using the surah:ayah notation. POST /api/v1/quran/search enables natural language searching through the Quran text. POST /api/v1/quran/validate checks whether provided text matches Quranic verses. GET /api/v1/quran/analytics provides statistical information about the Quran. GET /api/v1/quran/tafsir/{ref} retrieves commentary for specific verses.

**src/api/routes/rag.py** provides endpoints for direct RAG pipeline interaction. POST /api/v1/rag/fiqh sends queries directly to the fiqh agent, bypassing the classification step. POST /api/v1/rag/general similarly enables direct access to the general Islamic knowledge agent. GET /api/v1/rag/stats returns information about indexed collections and document counts.

**src/api/routes/health.py** implements health check endpoints. GET /health returns a simple status indicating the application is running. GET /ready extends health checking to include database connectivity verification, enabling orchestration systems to confirm full readiness before routing traffic.

**src/api/schemas/request.py** defines Pydantic models for request validation. QueryRequest requires a question string and accepts optional language, location, madhhab, and session_id parameters. ToolRequest provides base parameters for tool execution. Each schema includes validation logic appropriate to its field types.

**src/api/schemas/response.py** defines response structures. QueryResponse includes query_id, intent, intent_confidence, answer, citations, metadata, and follow_up_suggestions fields. CitationResponse structures individual citations with id, type, source, reference, url, and text_excerpt. ToolResponse wraps tool execution results with success flag and error messages.

**src/api/middleware/error_handler.py** implements custom error handling that catches exceptions throughout the request processing chain and transforms them into proper HTTP error responses with appropriate status codes and error messages.

### 4.4 Core Module (src/core/)

The core module contains the central business logic components that orchestrate query processing. **src/core/router.py** implements the HybridQueryClassifier, the three-tier intent classification system. The class implements classify() as the main entry point, which first attempts keyword matching, then LLM classification, and finally embedding similarity as fallbacks.

The _keyword_match() method iterates through KEYWORD_PATTERNS looking for matches, returning a RouterResult with high confidence (0.92) when keywords are found. The _llm_classify() method sends queries to the LLM with a carefully constructed prompt requesting JSON output with classification decisions, confidence scores, language detection, and sub-intents for Quran queries. The method parses JSON responses and normalizes intent strings to Intent enum values. The _embedding_classify() method provides placeholder functionality for future embedding-based classification.

The RouterResult model captures classification output including intent, confidence score, classification method (keyword, llm, or embedding), detected language, retrieval requirement flag, sub-intent for Quran queries, and reasoning for the classification decision.

**src/core/orchestrator.py** implements the ResponseOrchestrator class that coordinates query processing. The orchestrator maintains registries of agents and tools, initializing default tools and agents during construction. The _register_default_fallbacks() method imports and registers the five deterministic tools (ZakatCalculator, InheritanceCalculator, PrayerTimesTool, HijriCalendarTool, DuaRetrievalTool) and the ChatbotAgent.

The _register_rag_agents() method conditionally initializes RAG components, checking for the availability of PyTorch and Transformers before attempting to load embedding models and vector stores. This conditional initialization ensures that the system runs even when heavy ML dependencies are unavailable, falling back to the chatbot agent for queries that would normally require RAG processing.

The route_query() method implements the main routing logic, looking up the target agent or tool from INTENT_ROUTING, executing the appropriate handler, and assembling results with citations. The method includes fallback logic for handling RAG failures gracefully, falling back to the chatbot agent when RAG processing encounters errors.

**src/core/citation.py** implements the CitationNormalizer class for processing citations in AI-generated responses. The class extracts citation patterns like [Q1], [B2] from text, maps them to verified sources, and generates canonical URLs for verification. This component ensures that citations provided in responses actually correspond to retrievable source material.

### 4.5 Agents Module (src/agents/)

**src/agents/base.py** defines the abstract base class that all agents implement. The BaseAgent abstract class defines the execute() method that agents must implement, taking AgentInput and returning AgentOutput. The class also defines the name property that each agent must provide, enabling agent identification in logs and routing.

**src/agents/chatbot_agent.py** implements simple greeting and chitchat handling. The agent recognizes greetings like "السلام عليكم" (peace be upon you) and "hello" and responds with appropriate Islamic greetings. This agent serves as the fallback for queries that cannot be handled by more specialized components.

**src/agents/fiqh_agent.py** implements the Fiqh RAG Agent for Islamic jurisprudence questions. The agent uses the embedding model and vector store to retrieve relevant passages from fiqh texts, then uses the LLM to generate grounded answers. The agent includes madhhab awareness for schools with differing rulings.

**src/agents/general_islamic_agent.py** handles general Islamic knowledge questions using the RAG pipeline. The agent searches general Islamic collections and generates answers with citations from retrieved sources.

### 4.6 Tools Module (src/tools/)

**src/tools/base.py** defines the BaseTool abstract base class. Tools implement the execute() method taking query, language, location, madhhab, and session_id parameters and returning ToolOutput. The ToolOutput includes result data, success flag, error message, and metadata.

**src/tools/zakat_calculator.py** implements deterministic Zakat calculations following classical Islamic jurisprudence. The ZakatCalculator class supports multiple asset types including cash, gold, silver, trade goods, stocks, receivables, livestock, crops, and minerals. The calculate() method accepts ZakatAssets dataclass with values for each asset type, debts to deduct, madhhab selection for rule variations, and crop irrigation type for agricultural calculations.

The calculator implements the nisab (threshold) calculation based on either gold (85 grams) or silver (595 grams), using whichever is lower to benefit the poor. The standard Zakat rate of 2.5% applies to wealth exceeding the nisab threshold after deducting liabilities. The class includes specialized calculation methods for livestock Zakat (following hadith-specified rates for camels, cows, and sheep) and crop Zakat (5% for irrigated, 10% for rain-fed).

The ZakatResult dataclass encapsulates complete calculation results including nisab thresholds, asset values, Zakat amount due, detailed breakdown, applicable madhhab, metal prices, explanatory notes, and scholarly references.

**src/tools/inheritance_calculator.py** implements Islamic inheritance distribution (fara'id) using exact fraction arithmetic to avoid floating-point errors. The InheritanceCalculator class accepts estate value, Heirs definition, madhhab selection, debts to deduct, and wasiyyah (bequest) amounts.

The Heirs dataclass defines all possible heirs with boolean and integer fields: husband, wives, father, mother, paternal grandfather, sons, daughters, grandsons, full siblings, paternal half-siblings, maternal siblings, and uterine siblings. The calculate() method processes heirs through multiple phases: deducting debts and bequests, removing blocked heirs who are prevented from inheriting, calculating fixed shares (furood), handling 'awl (proportional reduction) when shares exceed 100%, handling asabah (residuary) inheritance when fixed shares are less than 100%, and applying radd (redistribution) when no residuary heirs exist.

The class implements the complete classical inheritance system including the 2:1 ratio between male and female heirs in residuary cases, special rules for the Umariyatan (father and spouse both present) scenario, and blocking rules where male descendants prevent paternal relatives from inheriting. Results are returned as InheritanceResult containing distribution shares, total distributed amount, remaining estate, calculation method used, and scholarly references.

**src/tools/prayer_times_tool.py** calculates daily prayer schedules using astronomical algorithms. The PrayerTimesTool class implements the BaseTool interface and supports multiple calculation methods: Egyptian General Authority, Muslim World League (MWL), Islamic Society of North America (ISNA), Umm al-Qura, University of Karachi, and Dubai.

The _calculate_prayer_times() method computes fajr (dawn), sunrise, dhuhr (noon), asr (afternoon), maghrib (sunset), and isha (night) times using Julian date calculations, sun declination, equation of time, and hour angle formulas. Each method has specific fajr and isha angle thresholds defined in METHOD_PARAMS.

The _calculate_qibla() method determines direction to Mecca using great-circle bearing calculations from any latitude/longitude to Mecca's coordinates (21.4225°N, 39.8262°E). The result provides compass degrees from North.

**src/tools/hijri_calendar_tool.py** converts between Gregorian and Hijri calendars. The tool implements both forward (Gregorian to Hijri) and reverse (Hijri to Gregorian) conversions, supporting date calculations for Islamic events like Ramadan and Eid.

**src/tools/dua_retrieval_tool.py** retrieves supplications from the Hisn al-Muslim collection. The tool supports multiple categories including morning/evening duas, sleep-related duas, travel supplications, food-related prayers, rain prayers, and eclipse prayers.

### 4.7 Knowledge Module (src/knowledge/)

**src/knowledge/embedding_model.py** wraps the Qwen3-Embedding model for generating vector embeddings. The EmbeddingModel class provides encode() and encode_batch() methods for single and batch text embedding generation. The model produces 1024-dimensional vectors stored in Qdrant for similarity search.

**src/knowledge/embedding_cache.py** implements Redis caching for embedding vectors. The cache uses SHA256 hashes of input text as keys, storing vectors with 7-day TTL to reduce redundant embedding generation for frequently queried text.

**src/knowledge/vector_store.py** manages Qdrant operations for document storage and retrieval. The VectorStore class provides methods for adding documents with embeddings, searching by query embedding with configurable limit and score threshold, deleting collections, and listing available collections. The class supports multiple named collections for different Islamic text categories.

**src/knowledge/hybrid_search.py** combines semantic (embedding-based) and keyword (BM25) search results using reciprocal rank fusion. The hybrid approach improves recall by capturing both semantic similarity and exact term matching.

**src/knowledge/chunker.py** implements text splitting strategies for document preprocessing. The chunker supports fixed-size overlapping chunks, paragraph-based splitting, heading-based splitting, and semantic splitting using embeddings.

### 4.8 Infrastructure Module (src/infrastructure/)

**src/infrastructure/db.py** manages async PostgreSQL connections using SQLAlchemy async support and asyncpg driver. The module provides get_async_session() for obtaining database sessions and includes initialization and cleanup functions.

**src/infrastructure/db_sync.py** provides synchronous PostgreSQL access using psycopg2 for scripts and one-off operations that don't benefit from async processing. The sync connection is used by seed scripts that load initial data.

**src/infrastructure/redis.py** manages Redis connections through connection pooling. The module provides get_redis() returning a configured Redis client with appropriate decoding and connection handling.

**src/infrastructure/llm_client.py** creates and manages LLM client instances. The get_llm_client() factory function returns either an OpenAI or Groq client based on configuration settings. The client abstraction enables runtime provider selection without code changes.

### 4.9 Quran Module (src/quran/)

**src/quran/verse_retrieval.py** implements the VerseRetrievalEngine for querying the Quran database. The engine supports retrieval by surah and ayah number, range retrieval for passages, and translation lookup in multiple languages.

**src/quran/nl2sql.py** converts natural language queries about Quran statistics into SQL queries. The module handles queries like "How many verses are in Surah Al-Baqarah?" by parsing the intent and generating appropriate database queries.

**src/quran/quotation_validator.py** verifies whether provided text matches actual Quranic verses. The validator checks text against the database and returns matching verses with confidence scores.

**src/quran/tafsir_retrieval.py** retrieves tafsir (exegesis) for specific verses from various classical sources.

**src/quran/quran_router.py** routes Quran-related queries to appropriate sub-handlers based on the classified sub-intent.

**src/quran/quran_agent.py** implements the Quran QA Agent combining retrieval and generation for answering Quran-related questions.

**src/quran/named_verses.json** contains a reference mapping of famous Quranic verses by their descriptive names (e.g., "Ayat al-Kursi" for 2:255).

### 4.10 Tests Module (tests/)

The tests directory contains comprehensive test suites for validation. **tests/conftest.py** defines pytest fixtures including mock LLM clients, sample query data, and test configuration. **tests/test_router.py** validates the intent classification pipeline with test cases for each intent and classification tier. **tests/test_zakat_calculator.py** tests Zakat calculations against known expected values for various asset configurations. **tests/test_inheritance_calculator.py** validates inheritance distribution against classical problems with known solutions. **tests/test_prayer_times_tool.py** compares calculated prayer times against known correct values for specific locations and dates. **tests/test_hijri_calendar_tool.py** validates calendar conversion accuracy. **tests/test_dua_retrieval_tool.py** tests supplication retrieval by category. **tests/test_api.py** performs integration testing against running API endpoints.

---

## 5. Building the Project Step by Step

### 5.1 Environment Setup

Begin by ensuring Python 3.12 or higher is installed on the system. Verify the version by running `python --version` in a terminal. Node.js 20+ is required for the frontend component. Docker Desktop should be running to provide the database and caching services.

Clone the repository to the local workspace using Git:

```
git clone https://github.com/Kandil7/Burhan.git
cd Burhan
```

### 5.2 Python Environment Configuration

Install Poetry if not already present:

```
pip install poetry
```

Install project dependencies:

```
poetry install
```

This command reads pyproject.toml and installs all required packages. The install process creates a virtual environment in the project directory. Activate the environment:

```
poetry shell
```

### 5.3 Environment Variables

Copy the example environment file and configure appropriately:

```
copy .env.example .env
```

Edit the .env file providing required values:

```
DATABASE_URL=postgresql+asyncpg://Burhan:Burhan_password@localhost:5432/Burhan_db
REDIS_URL=redis://localhost:6379/0
QDRANT_URL=http://localhost:6333
OPENAI_API_KEY=sk-your-openai-key-here
GROQ_API_KEY=gsk_your-groq-key-here
```

Obtain API keys from OpenAI (https://platform.openai.com) and optionally Groq (https://console.groq.com) for language model access.

### 5.4 Infrastructure Services

Start the required services using Docker Compose:

```
docker-compose -f docker/docker-compose.dev.yml up -d
```

This command starts PostgreSQL on port 5432, Qdrant on port 6333, and Redis on port 6379. Verify services are running:

```
docker ps
```

### 5.5 Database Setup

The application automatically creates necessary tables on startup through SQLAlchemy's create_all mechanism. For manual database initialization or migrations, use Alembic commands:

```
alembic upgrade head
```

### 5.6 Data Seeding

Seed the Quran database with initial verses:

```
poetry run python scripts/seed_quran_data.py
```

Process Islamic books for the RAG pipeline:

```
poetry run python scripts/complete_ingestion.py
```

Generate embeddings for semantic search:

```
poetry run python scripts/generate_embeddings.py
```

### 5.7 Running the Application

Start the FastAPI server using Uvicorn:

```
uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000
```

The API becomes accessible at http://localhost:8000. OpenAPI documentation is available at http://localhost8000/docs.

### 5.8 Running Tests

Execute the comprehensive test suite:

```
pytest tests/ -v
```

Run specific test files:

```
pytest tests/test_zakat_calculator.py -v
pytest tests/test_inheritance_calculator.py -v
```

### 5.9 Build System Commands

The build.bat file provides convenient commands for common operations:

```
build.bat setup          # Full initial setup
build.bat start         # Start application
build.bat stop          # Stop all services
build.bat test          # Run tests
build.bat status        # Check status
build.bat data:ingest    # Process books/hadith
build.bat data:embed    # Generate embeddings
build.bat data:quran    # Seed Quran database
build.bat db:migrate    # Run migrations
```

---

## 6. API Endpoints Reference

### 6.1 Health Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| / | GET | Root endpoint returning API metadata |
| /health | GET | Basic health check |
| /ready | GET | Readiness check with database |
| /docs | GET | Swagger documentation |
| /redoc | GET | ReDoc alternative documentation |

### 6.2 Query Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| /api/v1/query | POST | Main query processing endpoint |
| /api/v1/query/classify | POST | Standalone intent classification |

### 6.3 Tool Endpoints

| Endpoint | Method | Parameters | Description |
|----------|--------|------------|-------------|
| /api/v1/tools/zakat | GET | amount, debts, madhhab | Zakat calculation |
| /api/v1/tools/inheritance | GET | estate_value, heirs JSON | Inheritance distribution |
| /api/v1/tools/prayer-times | GET | lat, lng, date, method | Prayer schedule |
| /api/v1/tools/hijri | GET | date | Calendar conversion |
| /api/v1/tools/duas | GET | category | Supplication retrieval |

### 6.4 Quran Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| /api/v1/quran/surahs | GET | List all surahs |
| /api/v1/quran/ayah/{ref} | GET | Get specific verse |
| /api/v1/quran/search | POST | Search Quran text |
| /api/v1/quran/validate | POST | Validate Quranic text |
| /api/v1/quran/analytics | GET | Quran statistics |
| /api/v1/quran/tafsir/{ref} | GET | Get tafsir |

### 6.5 RAG Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| /api/v1/rag/fiqh | POST | Direct fiqh query |
| /api/v1/rag/general | POST | Direct general query |
| /api/v1/rag/stats | GET | Collection statistics |

---

## 7. Development Workflow

### 7.1 Adding New Intents

To add a new intent category, update src/config/intents.py by adding the intent to the Intent enum, providing intent description in INTENT_DESCRIPTIONS, adding routing entry in INTENT_ROUTING, and including keyword patterns in KEYWORD_PATTERNS. Then implement the handling logic in either a new agent (for AI-generated responses) or a new tool (for deterministic processing).

### 7.2 Adding New Tools

Create a new file in src/tools/ implementing the BaseTool interface. Implement the execute() method with appropriate logic and return ToolOutput. Add the tool registration in the orchestrator's _register_default_fallbacks() method.

### 7.3 Testing Best Practices

Write tests before implementation following TDD principles. Include edge cases and error conditions. Test both success and failure paths. Verify error messages are user-friendly. Use pytest fixtures for common test data.

---

## 8. Conclusion

The Burhan Islamic QA System represents a comprehensive implementation of multi-agent architecture for specialized domain question-answering. The system successfully combines deterministic rule-based calculators with AI-powered retrieval and generation, providing accurate, grounded responses to Islamic questions. With its clean architecture, comprehensive test coverage, and extensive documentation, the project serves as both a functional application and a reference implementation for building similar knowledge-based AI systems.