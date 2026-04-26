# Burhan Retrieval Strategies

## Overview

This document describes the retrieval strategy system for the Multi-Agent Collection-Aware RAG system. Each agent has optimized configurations for dense/sparse retrieval, reranking, and score thresholds.

---

## Strategy Matrix

| Agent | Dense Weight | Sparse Weight | Top K | Rerank | Score Threshold | Collection |
|-------|--------------|---------------|-------|--------|------------------|-------------|
| fiqh_agent | 0.6 | 0.4 | 80 | True | 0.65 | fiqh |
| hadith_agent | 0.5 | 0.5 | 60 | True | 0.70 | hadith |
| tafsir_agent | 0.7 | 0.3 | 40 | True | 0.75 | quran |
| aqeedah_agent | 0.6 | 0.4 | 50 | True | 0.65 | aqeedah |
| seerah_agent | 0.5 | 0.5 | 50 | True | 0.60 | seerah |
| usul_fiqh_agent | 0.7 | 0.3 | 60 | True | 0.70 | usul_fiqh |
| history_agent | 0.5 | 0.5 | 50 | True | 0.60 | islamic_history |
| language_agent | 0.4 | 0.6 | 40 | True | 0.65 | arabic_language |
| general_islamic_agent | 0.5 | 0.5 | 30 | False | 0.55 | general_islamic |

---

## Strategy Selection Logic

### Dense Weight Selection

- **High dense (0.7)**: Tafsir, UsulFiqh - Require semantic understanding
- **Medium dense (0.5-0.6)**: Fiqh, Hadith, Aqeedah - Balance semantic and keyword
- **Low dense (0.4)**: Language - Heavy keyword matching for grammar

### Top K Selection

- **Large (80)**: Fiqh - Many candidates for verification
- **Medium (40-60)**: Hadith, Tafsir, Aqeedah - Balanced
- **Small (30)**: General - Quick responses

### Score Threshold

- **High (0.70-0.75)**: Tafsir, Hadith - Require high confidence
- **Medium (0.65)**: Fiqh, Aqeedah - Standard confidence
- **Low (0.55-0.60)**: General, History - Allow more candidates

---

## Implementation

### Using Strategies

```python
from src.retrieval.strategies import (
    get_strategy_for_agent,
    get_collection_for_agent,
    RetrievalStrategy
)

# Get strategy for an agent
strategy = get_strategy_for_agent("fiqh_agent")
print(strategy.dense_weight)  # 0.6
print(strategy.top_k)          # 80
print(strategy.score_threshold)  # 0.65

# Get collection for an agent
collection = get_collection_for_agent("fiqh_agent")
print(collection)  # "fiqh"
```

### Strategy Configuration

```python
# Custom strategy
custom_strategy = RetrievalStrategy(
    dense_weight=0.7,
    sparse_weight=0.3,
    top_k=50,
    rerank=True,
    score_threshold=0.7
)

# Use in agent
agent = FiqhCollectionAgent(config=CollectionAgentConfig(
    collection_name="fiqh",
    strategy=custom_strategy
))
```

---

## Hybrid Retrieval

### Alpha Parameter

The alpha parameter controls dense/sparse balance:

```python
alpha = dense_weight  # 0.6 for FiqhAgent
# alpha = 0 means pure BM25
# alpha = 1 means pure semantic
```

### Search Pipeline

```
Query → Embedding → BM25 → Fusion (alpha) → Rerank → Filter → Top K
```

---

## Reranking

### When Reranking is Enabled

Reranking is enabled for most agents (except general_islamic_agent) to improve result quality.

### Reranking Process

1. **Initial Retrieval**: Get top_k * 2 candidates
2. **Cross-Encoder Scoring**: Score each candidate against query
3. **Fusion**: Combine semantic + rerank scores
4. **Filtering**: Apply score_threshold
5. **Final Selection**: Return top_k results

---

## Qdrant Collection Configuration

### Dense Vector Settings

```python
DenseVectorConfig(
    size=1024,              # Embedding dimension
    distance=Distance.COSINE  # Cosine similarity
)
```

### Sparse Vector Settings (BM25)

```python
SparseVectorConfig(
    type="BM25",
    k1=1.5,                # Term frequency saturation
    b=0.75                 # Document length normalization
)
```

### HNSW Configuration

```python
HNSWPreset.LARGE = {
    "m": 32,               # Number of connections
    "ef_construct": 256,   # Search width during build
    "full_scan_threshold": 10000
}

HNSWPreset.MEDIUM = {
    "m": 16,
    "ef_construct": 128,
    "full_scan_threshold": 10000
}

HNSWPreset.SMALL = {
    "m": 8,
    "ef_construct": 64,
    "full_scan_threshold": 10000
}
```

### Quantization

```python
QuantizationConfig(
    type="INT8",           # 8-bit integer quantization
    always_ram=False       # Keep in disk if possible
)
```

---

## Collection-Specific Configurations

### Fiqh Collection

```python
COLLECTION_CONFIGS["fiqh"] = CollectionConfig(
    dense=DenseVectorConfig(size=1024, distance=Distance.COSINE),
    sparse=SparseVectorConfig(type="BM25", k1=1.5, b=0.75),
    quantization=QuantizationConfig(type="INT8", always_ram=False),
    hnsw=HNSWConfig(m=32, ef_construct=256, full_scan_threshold=10000),
    # Alpha = 0.6 (dense-heavy)
)
```

### Hadith Collection

```python
COLLECTION_CONFIGS["hadith"] = CollectionConfig(
    dense=DenseVectorConfig(size=1024, distance=Distance.COSINE),
    sparse=SparseVectorConfig(type="BM25", k1=1.5, b=0.75),
    quantization=QuantizationConfig(type="INT8", always_ram=False),
    hnsw=HNSWConfig(m=16, ef_construct=128, full_scan_threshold=10000),
    # Alpha = 0.5 (balanced)
)
```

### Tafsir Collection

```python
COLLECTION_CONFIGS["tafsir"] = CollectionConfig(
    dense=DenseVectorConfig(size=1024, distance=Distance.COSINE),
    sparse=SparseVectorConfig(type="BM25", k1=1.2, b=0.75),
    quantization=QuantizationConfig(type="INT8", always_ram=False),
    hnsw=HNSWConfig(m=32, ef_construct=256, full_scan_threshold=10000),
    # Alpha = 0.7 (semantic-heavy)
)
```

---

## Metadata Filtering

### Available Filters

| Filter | Example |
|--------|---------|
| `author` | "ابن قدامة" |
| `era` | "classical" |
| `madhhab` | "hanafi" |
| `book_id` | 123 |
| `category` | "fiqh" |
| `author_death_min` | 200 |
| `author_death_max` | 500 |

### Using Filters

```python
# In retrieval request
filters = {
    "madhhab": "hanafi",
    "era": "classical"
}

results = await vector_store.search(
    collection="fiqh",
    query_embedding=embedding,
    top_k=80,
    filters=filters
)
```

---

## Performance Optimization

### Indexing

1. **Batch Upserts**: Process in batches of 1000
2. **Async Operations**: Use async Qdrant client
3. **Deterministic IDs**: Use content hash to prevent duplicates

### Querying

1. **Pre-filtering**: Apply metadata filters before vector search
2. **Score Threshold**: Early filtering to reduce processing
3. **Caching**: Cache frequently queried embeddings

---

## Troubleshooting

### Low Recall

- Decrease score_threshold
- Increase top_k
- Adjust alpha (more dense or sparse)

### Low Precision

- Increase score_threshold
- Enable reranking
- Add more metadata filters

### Slow Response

- Reduce top_k
- Use smaller HNSW config
- Enable quantization

---

## See Also

- [Phase 10 Index](./PHASE10_INDEX.md) - Navigation guide
- [Multi-Agent Architecture](./MULTI_AGENT_COLLECTION_ARCHITECTURE.md) - Main architecture
- [API Collections](./API_COLLECTIONS.md) - API endpoints
- [Verification Framework](./VERIFICATION_FRAMEWORK.md) - Verification system
- [Orchestration Patterns](./ORCHESTRATION_PATTERNS.md) - Multi-agent patterns