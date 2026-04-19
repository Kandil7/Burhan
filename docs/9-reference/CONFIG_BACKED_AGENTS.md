# Config-Backed Agent System Documentation

This document describes the declarative configuration system for the Multi-Agent Collection-Aware RAG system in Athar.

## Overview

The config-backed agent system allows you to define agent behavior declaratively through YAML configuration files and text prompt files. This separation enables:

- **Easy modification** of retrieval/verification settings without code changes
- **Version control** of agent configurations
- **Testing** different configurations easily
- **Maintenance** of consistent behavior across agents

## Directory Structure

```
athar/
├── config/
│   └── agents/           # Agent configuration files
│       ├── fiqh.yaml
│       ├── hadith.yaml
│       ├── tafsir.yaml
│       ├── aqeedah.yaml
│       ├── seerah.yaml
│       ├── history.yaml
│       ├── language.yaml
│       ├── tazkiyah.yaml
│       ├── general.yaml
│       └── usul_fiqh.yaml
├── prompts/              # System prompt files
│   ├── _shared_preamble.txt
│   ├── fiqh_agent.txt
│   ├── hadith_agent.txt
│   ├── tafsir_agent.txt
│   ├── aqeedah_agent.txt
│   ├── seerah_agent.txt
│   ├── history_agent.txt
│   ├── language_agent.txt
│   ├── tazkiyah_agent.txt
│   ├── general_agent.txt
│   └── usul_fiqh_agent.txt
└── src/
    ├── config/           # Config loader module
    │   ├── __init__.py
    │   └── loader.py
    └── application/router/
        └── config_router.py
```

## Configuration Schema

### Agent YAML Config

Each agent configuration has the following structure:

```yaml
name: FiqhAgent
domain: fiqh
collection_name: fiqh_passages

retrieval:
  primary: hybrid        # dense | sparse | hybrid
  alpha: 0.6            # dense weight [0, 1]
  topk_initial: 80       # initial retrieval count
  topk_reranked: 12     # after reranking
  min_relevance: 0.45   # minimum score threshold
  metadata_filters_priority:
    - madhhab
    - category_sub
    - era

verification:
  fail_fast: true       # stop on first failure
  checks:
    - name: quote_validator
      enabled: true
      fail_policy: abstain  # abstain | warn | proceed

    - name: source_attributor
      enabled: true
      fail_policy: warn

    - name: contradiction_detector
      enabled: true
      fail_policy: proceed

    - name: evidence_sufficiency
      enabled: true
      fail_policy: abstain

fallback:
  strategy: chatbot     # chatbot | human_review | clarify
  message: null         # custom message (optional)

abstention:
  high_risk_personal_fatwa: true
  require_diverse_evidence: true
  minimum_sources: 3
```

### Field Descriptions

| Field | Type | Description |
|-------|------|-------------|
| `name` | string | Agent display name |
| `domain` | string | Domain identifier |
| `collection_name` | string | Qdrant collection name |
| `retrieval.primary` | string | Primary retrieval method |
| `retrieval.alpha` | float | Dense weight (1-alpha = sparse weight) |
| `retrieval.topk_initial` | int | Initial candidate count |
| `retrieval.topk_reranked` | int | Final candidate count after reranking |
| `retrieval.min_relevance` | float | Minimum score threshold |
| `verification.fail_fast` | bool | Stop on first failed check |
| `verification.checks[].name` | string | Check identifier |
| `verification.checks[].enabled` | bool | Whether check is active |
| `verification.checks[].fail_policy` | string | Action on failure |
| `fallback.strategy` | string | Fallback strategy |
| `fallback.message` | string | Custom fallback message |

## Fail Policy Options

| Policy | Behavior |
|--------|----------|
| `abstain` | Stop execution, return abstain response |
| `warn` | Continue but add warning to metadata |
| `proceed` | Continue execution normally |

## Domain-Specific Configurations

### Fiqh Agent (`fiqh.yaml`)
- **Primary**: hybrid (alpha=0.6)
- **Verification**: Strict - abstain on quote validation failure
- **Abstention**: Requires 3+ diverse sources for personal fatwa

### Hadith Agent (`hadith.yaml`)
- **Primary**: hybrid (alpha=0.3) - sparse-heavy for exact matching
- **Verification**: Grade checker enabled
- **Abstention**: Require sahih for aqeedah/ahkam

### Tafsir Agent (`tafsir.yaml`)
- **Primary**: hybrid (alpha=0.7) - dense-heavy for semantic understanding
- **Verification**: Maqasid checker (themes/objectives)
- **Abstention**: Require authentic tafsir sources

### Aqeedah Agent (`aqeedah.yaml`)
- **Primary**: hybrid (alpha=0.7)
- **Verification**: Very strict - abstain on source attribution failure
- **Abstention**: Block kufr/tafreet statements

### General Agent (`general.yaml`)
- **Primary**: hybrid (alpha=0.5)
- **Verification**: Minimal - warn only
- **Abstention**: No minimum sources required

## Prompt Structure

### Shared Preamble (`_shared_preamble.txt`)

Contains rules common to all agents:
- Don't issue personal fatwas
- Attribute all claims to sources
- State when evidence is insufficient
- Use Arabic proper terminology

### Agent-Specific Prompts

Each agent prompt contains:
- **ROLE**: Agent identity and purpose
- **SCOPE**: Domain boundaries
- **OBJECTIVES**: Task definitions
- **CONSTRAINTS**: Limitations
- **CITATIONS**: Reference format
- **ABSTENTION**: When to refuse answering

## Usage

### Loading Configuration

```python
from src.config import get_config_manager

# Get config manager (singleton)
cm = get_config_manager()

# Load agent config
config = cm.load_config("fiqh")

# Load system prompt
prompt = cm.load_system_prompt("fiqh")

# Get CollectionAgentConfig
agent_config = cm.get_collection_agent_config("fiqh")
```

### Using Config Router

```python
from src.application.router.config_router import get_config_router

router = get_config_router()

# Single agent routing
result = router.route("ما حكم صلاة الجماعة؟")
# Returns: agent_name="fiqh_agent", confidence=0.85

# Multi-agent routing (for complex queries)
results = router.route_multi("ما حكم الصلاة وما صحة هذا الحديث؟")
# Returns: [fiqh_agent, hadith_agent]
```

### Creating Agents from Config

```python
from src.config import get_config_manager
from src.agents.fiqh_collection_agent import FiqhCollectionAgent

cm = get_config_manager()

# Get full config with prompts
config = cm.get_collection_agent_config("fiqh", include_prompt=True)

# Create agent instance
agent = FiqhCollectionAgent(config=config)

# Execute query
result = await agent.run("ما حكم صيام رمضان؟")
```

## Testing

Run the config-backed agent tests:

```bash
python -m pytest tests/test_config_backed_agents.py -v
```

This runs 27 tests covering:
- Config loading for all 10 agents
- System prompt loading
- ConfigRouter routing for all domains
- Orchestration integration
- Retrieval strategy mapping
- Verification suite mapping
- Fallback policy mapping

## Adding New Agents

To add a new agent:

1. Create `config/agents/new_agent.yaml` with appropriate configuration
2. Create `prompts/new_agent_agent.txt` with agent-specific system prompt
3. Update `DOMAIN_KEYWORDS` in `src/application/router/config_router.py`
4. Add tests for the new agent in `tests/test_config_backed_agents.py`

## Migration Guide

If you're using the old hardcoded approach:

**Before:**
```python
# Hardcoded strategy
strategy = RetrievalStrategy(
    dense_weight=0.6,
    sparse_weight=0.4,
    top_k=12,
)
```

**After:**
```python
# Config-based strategy
from src.config import get_config_manager
cm = get_config_manager()
config = cm.get_collection_agent_config("fiqh", include_prompt=False)
strategy = config.strategy
```

## See Also

- [ORCHESTRATION_PATTERNS.md](./ORCHESTRATION_PATTERNS.md)
- [RETRIEVAL_STRATEGIES.md](./RETRIEVAL_STRATEGIES.md)
- [VERIFICATION_FRAMEWORK.md](./VERIFICATION_FRAMEWORK.md)
- [MULTI_AGENT_COLLECTION_ARCHITECTURE.md](./MULTI_AGENT_COLLECTION_ARCHITECTURE.md)