# Config & Prompts Directory

This directory contains the declarative configuration and system prompts for the Multi-Agent Collection-Aware RAG system.

## Structure

```
config/
├── agents/
│   ├── fiqh.yaml         # Fiqh agent configuration
│   ├── hadith.yaml       # Hadith agent configuration
│   ├── tafsir.yaml       # Tafsir agent configuration
│   ├── aqeedah.yaml      # Aqeedah agent configuration
│   ├── seerah.yaml       # Seerah agent configuration
│   ├── history.yaml      # History agent configuration
│   ├── language.yaml     # Language agent configuration
│   ├── tazkiyah.yaml     # Tazkiyah agent configuration
│   ├── general.yaml      # General Islamic agent configuration
│   └── usul_fiqh.yaml    # Usul Fiqh agent configuration
│
└── (future: router.yaml  # Router configuration)

prompts/
├── _shared_preamble.txt  # Common rules for all agents
├── fiqh_agent.txt        # FiqhAgent system prompt
├── hadith_agent.txt      # HadithAgent system prompt
├── tafsir_agent.txt      # TafsirAgent system prompt
├── aqeedah_agent.txt     # AqeedahAgent system prompt
├── seerah_agent.txt      # SeerahAgent system prompt
├── history_agent.txt     # HistoryAgent system prompt
├── language_agent.txt    # LanguageAgent system prompt
├── tazkiyah_agent.txt    # TazkiyahAgent system prompt
├── general_agent.txt     # GeneralIslamicAgent system prompt
└── usul_fiqh_agent.txt   # UsulFiqhAgent system prompt
```

## Quick Start

### Loading an Agent Config

```python
from src.config import get_config_manager

cm = get_config_manager()

# Load config
config = cm.load_config("fiqh")
print(config.name)  # "FiqhAgent"
print(config.retrieval.primary)  # "hybrid"

# Load system prompt
prompt = cm.load_system_prompt("fiqh")
```

### Using the Router

```python
from src.application.router.config_router import get_config_router

router = get_config_router()
result = router.route("ما حكم الصيام؟")

print(result.agent_name)  # "fiqh_agent"
print(result.confidence)  # 0.85
```

## Agent Comparison

| Agent | Domain | Alpha | TopK | Fail Policy | Use Case |
|-------|--------|-------|-----|--------------|----------|
| FiqhAgent | fiqh | 0.6 | 12 | abstain | Islamic law rulings |
| HadithAgent | hadith | 0.3 | 20 | abstain | Hadith retrieval & grading |
| TafsirAgent | tafsir | 0.7 | 10 | abstain | Quran interpretation |
| AqeedahAgent | aqeedah | 0.7 | 8 | abstain | Theological matters |
| SeerahAgent | seerah | 0.5 | 12 | warn | Prophet biography |
| HistoryAgent | history | 0.5 | 12 | warn | Islamic history |
| LanguageAgent | language | 0.4 | 10 | proceed | Arabic grammar |
| TazkiyahAgent | tazkiyah | 0.6 | 10 | proceed | Spiritual development |
| UsulFiqhAgent | usul_fiqh | 0.7 | 10 | abstain | Fiqh principles |
| GeneralIslamicAgent | general | 0.5 | 8 | proceed | General questions |

## Changing Configuration

### Modify Retrieval Settings

Edit `config/agents/fiqh.yaml`:

```yaml
retrieval:
  alpha: 0.7  # Increase dense weight
  topk_reranked: 15  # Get more candidates
```

### Modify Verification Checks

Edit `config/agents/fiqh.yaml`:

```yaml
verification:
  fail_fast: false  # Don't stop on first failure
  checks:
    - name: quote_validator
      enabled: false  # Disable this check
```

### Modify Agent Prompts

Edit `prompts/fiqh_agent.txt`:

```text
[OBJECTIVES]
1. New objective here
2. Another objective
```

## Adding a New Agent

1. Create `config/agents/new_agent.yaml`
2. Create `prompts/new_agent_agent.txt`
3. Add keywords to `DOMAIN_KEYWORDS` in `src/application/router/config_router.py`
4. Add tests in `tests/test_config_backed_agents.py`

## Related Documentation

- [CONFIG_BACKED_AGENTS.md](../9-reference/CONFIG_BACKED_AGENTS.md)
- [DOMAIN_KEYWORDS.md](../9-reference/DOMAIN_KEYWORDS.md)
- [ORCHESTRATION_PATTERNS.md](../9-reference/ORCHESTRATION_PATTERNS.md)