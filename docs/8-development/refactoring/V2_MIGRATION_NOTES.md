# Athar v2 Architecture Migration

## Overview

This document describes the migration from the legacy Athar architecture to the v2 architecture.

## What Changed

### Agent Structure

**Old (Legacy)**:
- `src/agents/fiqh_agent.py` - Direct RAG implementation
- `src/agents/hadith_agent.py` - Direct RAG implementation
- etc.

**New (v2)**:
- `src/agents/legacy/` - Deprecated but available for backward compatibility
- `src/agents/collection/` - Canonical v2 config-backed agents

### Configuration

**Old**:
- Agent prompts embedded in Python files
- Config in code constants

**New**:
- YAML configs in `config/agents/*.yaml`
- System prompts in `prompts/*.txt`
- Runtime config in `src/config_runtime/`

### Retrieval

**Old**:
- `src/knowledge/` - Mixed retrieval logic

**New**:
- `src/retrieval/` - Canonical retrieval layer
- `src/infrastructure/qdrant/` - Qdrant infrastructure
- `src/verification/` - First-class verification layer

### Routing

**Old**:
- `src/application/router/router_agent.py` - Monolithic router

**New**:
- `src/application/routing/` - Split routing (intent_router, planner, executor)

## Migration Status

| Component | Status |
|-----------|--------|
| Legacy agents isolated | ✅ |
| Collection agents created | ✅ |
| Config split | ✅ |
| Retrieval canonical | ✅ |
| Qdrant infrastructure | ✅ |
| Verification layer | ✅ |
| Routing split | ✅ |
| Generation contracts | ✅ |
| Observability | ✅ |

## Backward Compatibility

Legacy agents are still available but show deprecation warnings:

```python
# Old (deprecated but works)
from src.agents import FiqhAgent

# New (canonical)
from src.agents.collection import FiqhCollectionAgent
```

## New Canonical Paths

- Agents: `src/agents/collection/`
- Config: `config/agents/`
- Prompts: `prompts/`
- Retrieval: `src/retrieval/`
- Verification: `src/verification/`
- Routing: `src/application/routing/`
- Qdrant: `src/infrastructure/qdrant/`

## Testing

Run tests to verify migration:

```bash
pytest tests/ -v
```

## Next Steps

1. Update all imports to use new canonical paths
2. Remove legacy code after verifying parity
3. Update documentation to reflect v2 as default