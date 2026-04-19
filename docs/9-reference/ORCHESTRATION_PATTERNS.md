# Athar Multi-Agent Orchestration Patterns

## Overview

This document describes the orchestration patterns for coordinating multiple agents in the Athar Islamic QA system.

---

## Orchestration Patterns

### 1. Sequential Pattern

Agents are executed one after another, with output feeding into the next:

```
Query → Agent1 → Output1 → Agent2 → Output2 → Final Answer
```

**Use Cases:**
- Follow-up questions
- Multi-step reasoning
- Agent → Usul → Hadith chain

```python
plan = OrchestrationPlan(
    pattern=OrchestrationPattern.SEQUENTIAL,
    tasks=[
        AgentTask(agent_name="fiqh_agent", priority=1),
        AgentTask(agent_name="usul_fiqh_agent", priority=2),
    ],
    primary_agent="fiqh_agent",
    fallback_agent="general_islamic_agent"
)
```

### 2. Parallel Pattern

Multiple agents execute simultaneously and results are merged:

```
       ┌──────────────┐
Query →│ Agent1       │→ Results → Fusion → Final Answer
       │ Agent2       │
       │ Agent3       │
       └──────────────┘
```

**Use Cases:**
- Multi-domain queries
- Cross-collection questions
- Comprehensive answers

```python
plan = OrchestrationPlan(
    pattern=OrchestrationPattern.PARALLEL,
    tasks=[
        AgentTask(agent_name="fiqh_agent", priority=1),
        AgentTask(agent_name="hadith_agent", priority=1),
        AgentTask(agent_name="aqeedah_agent", priority=1),
    ],
    primary_agent="fiqh_agent",
    fallback_agent="general_islamic_agent"
)
```

### 3. Hierarchical Pattern

Primary agent leads with secondary agents as tools:

```
       ┌──────────────┐
Query →│ Primary      │→ Sub-queries → Secondary Agents → Final Answer
       │ (as orchestrator)
       └──────────────┘
```

**Use Cases:**
- Complex queries requiring multiple sources
- Primary agent routes to specialists
- Tool integration

```python
plan = OrchestrationPlan(
    pattern=OrchestrationPattern.HIERARCHICAL,
    tasks=[
        AgentTask(agent_name="general_islamic_agent", priority=1, is_primary=True),
        AgentTask(agent_name="fiqh_agent", priority=2, is_secondary=True),
        AgentTask(agent_name="hadith_agent", priority=2, is_secondary=True),
    ],
    primary_agent="general_islamic_agent",
    fallback_agent="general_islamic_agent"
)
```

---

## Decision Tree Routing

### Confidence Thresholds

```python
PRIMARY_THRESHOLD = 0.7       # Direct routing to single agent
SECONDARY_THRESHOLD = 0.4     # Multi-agent orchestration
LOW_CONFIDENCE_THRESHOLD = 0.2  # Fallback to general agent
```

### Keyword-Based Routing

Simple rule-based routing by keyword detection:

| Keywords | Agent | Example |
|----------|-------|---------|
| آية، قرآن، سورة | tafsir_agent | "ما تفسير آية كذا؟" |
| حديث، صحيح، سنن | hadith_agent | "ما صحة هذا الحديث؟" |
| حكم، فقه، حلال | fiqh_agent | "ما حكم كذا؟" |
| زكاة، صيام، حج | fiqh_agent | "ما حكم الزكاة؟" |
| عقيدة، توحيد | aqeedah_agent | "ما هي عقيدة أهل السنة؟" |
| سيرة، غزوة | seerah_agent | "اذكر غزوة بدر" |
| تاريخ | history_agent | "متى تأسست الدولة الأموية؟" |
| نحو، صرف | language_agent | "ما إعراب كلمة كذا؟" |

---

## Implementation

### Creating an Orchestration Plan

```python
from src.application.router.orchestration import (
    create_orchestration_plan,
    OrchestrationPattern,
    AgentTask
)

# For simple query - sequential
plan = create_orchestration_plan(
    query="ما حكم صلاة الجمعة؟",
    intent=Intent.FIQH
)
# Returns: SEQUENTIAL with single task

# For complex query - parallel
plan = create_orchestration_plan(
    query="ما حكم الزكاة ومتى فرضت؟",
    intent=Intent.FIQH
)
# Returns: PARALLEL with multiple relevant tasks
```

### Multi-Agent Orchestrator

```python
from src.application.router.orchestration import MultiAgentOrchestrator

orchestrator = MultiAgentOrchestrator(registry=agent_registry)

# Execute plan
result = await orchestrator.execute_plan(
    plan=plan,
    query="ما حكم صلاة الجماعة في الإسلام؟"
)

print(result.answer)
print(result.citations)
```

### Fallback Handling

```python
# When confidence is low
if result.confidence < LOW_CONFIDENCE_THRESHOLD:
    fallback = await orchestrator.route_to_fallback(query)
    # Falls back to general_islamic_agent or chatbot
```

---

## Multi-Agent Router

**Location**: `src/application/router/multi_agent.py`

```python
from src.application.router.multi_agent import MultiAgentRouter

router = MultiAgentRouter(classifier=classifier)

# Route to multiple agents
decision = router.route_multi("ما حكم الصلاة وما صحة هذا الحديث؟")

print(f"Agents: {decision.agents}")       # ["fiqh_agent", "hadith_agent"]
print(f"Collections: {decision.collections}")  # ["fiqh", "hadith"]
print(f"Response Mode: {decision.response_mode}")  # "answer"

# Check if orchestration needed
if router.should_orchestrate("complex query"):
    # Use MultiAgentOrchestrator
    ...
```

---

## Query Complexity Detection

### Simple Queries (Sequential)

- Single domain intent
- Clear keywords
- No ambiguity

Examples:
- "ما حكم الزكاة؟"
- "ما تفسير سورة الإخلاص؟"
- "من هو الصحابي فلان؟"

### Complex Queries (Parallel)

- Multiple domain keywords
- Cross-collection question
- Ambiguous intent

Examples:
- "ما حكم الزكاة ومتى فرضت؟" (Fiqh + History)
- "اذكر آية وحديث عن الصبر" (Quran + Hadith)
- "ما رأي المذاهب في كذا؟" (Fiqh + Multiple madhhabs)

### Hierarchical Queries

- Need primary agent to decide sub-agents
- Tool integration needed
- Long conversational context

Examples:
- "أريد أن أفهم موضوع الزكاة بشكل كامل"
- "احسب لي الزكاة واذكر الحكم الشرعي"

---

## Agent Selection Logic

### By Intent

```python
from src.domain.intents import INTENT_ROUTING

def get_agent_for_intent(intent: Intent) -> str:
    return INTENT_ROUTING.get(intent)
```

### By Multiple Intents

```python
def get_agents_for_intents(intents: list[Intent]) -> list[str]:
    agents = []
    for intent in intents:
        agent = get_agent_for_intent(intent)
        if agent and agent not in agents:
            agents.append(agent)
    return agents
```

### With Confidence

```python
async def route_with_confidence(classifier, query: str):
    result = await classifier.classify(query)
    
    if result.confidence >= PRIMARY_THRESHOLD:
        # Single agent
        agent = get_agent_for_intent(result.intent)
        return SEQUENTIAL, [agent]
    
    elif result.confidence >= SECONDARY_THRESHOLD:
        # Multiple agents - need orchestration
        intents = get_potential_intents(query)
        agents = get_agents_for_intents(intents)
        return PARALLEL, agents
    
    else:
        # Low confidence - fallback
        return HIERARCHICAL, ["general_islamic_agent"]
```

---

## Response Modes

| Mode | Description | Trigger |
|------|-------------|---------|
| `answer` | Direct answer with citations | High confidence |
| `clarify` | Ask clarifying question | Ambiguous query |
| `abstain` | No answer, suggest alternatives | Low confidence, no evidence |
| `review` | Flag for human review | Verification failed |

---

## Examples

### Example 1: Simple Fiqh Query

**Query:** "ما حكم ترك صلاة الجمعة؟"

```python
# Route decision
decision = router.route("ما حكم ترك صلاة星期五؟")
# Result:
# - intent: FIQH
# - confidence: 0.92
# - route: fiqh_agent
# - pattern: SEQUENTIAL
```

**Execution:**
```
Query → FiqhAgent → Answer + Citations
```

### Example 2: Multi-Domain Query

**Query:** "ما حكم الزكاة وماذا قال عنه ابن باز؟"

```python
# Route decision
decision = router.route_multi("ما حكم الزكاة وماذا قال عنه ابن باز؟")
# Result:
# - agents: ["fiqh_agent", "history_agent"]
# - pattern: PARALLEL
```

**Execution:**
```
Query
    ├── FiqhAgent → Answer about Zakat
    └── HistoryAgent → Info about Ibn Baz
    ↓
    Fusion → Combined Answer + Citations
```

### Example 3: Complex Hierarchical

**Query:** "أريد أن أفهم حكم الزكاة بشكل كامل مع الأدلة"

```python
# Route decision
decision = router.route("أريد أن أفهم...")
# Result:
# - agents: ["general_islamic_agent"]
# - pattern: HIERARCHICAL
```

**Execution:**
```
Query → GeneralIslamicAgent (orchestrator)
    ├── FiqhAgent → rulings
    ├── HadithAgent → hadiths about Zakat
    ├── QuranAgent → Quran verses
    ↓
    Synthesis → Comprehensive Answer
```

---

## Configuration

### Adjust Thresholds

```python
# In router configuration
router = RouterAgent(
    classifier=classifier,
    conf_threshold=0.6  # Custom threshold
)
```

### Enable/Disable Patterns

```python
# Force parallel for all multi-domain queries
orchestrator = MultiAgentOrchestrator(
    registry=registry,
    force_parallel=True
)
```

---

## Testing

```python
@pytest.mark.asyncio
async def test_sequential_pattern():
    plan = create_orchestration_plan("ما حكم الصلاة؟", Intent.FIQH)
    assert plan.pattern == OrchestrationPattern.SEQUENTIAL

@pytest.mark.asyncio
async def test_parallel_pattern():
    plan = create_orchestration_plan("ما حكم الزكاة ومتى فرضت؟", Intent.FIQH)
    assert plan.pattern == OrchestrationPattern.PARALLEL

@pytest.mark.asyncio
async def test_fallback():
    orchestrator = MultiAgentOrchestrator(registry)
    result = await orchestrator.route_to_fallback("random text")
    assert result.agent_id == "general_islamic_agent"
```

---

## See Also

- [Phase 10 Index](./PHASE10_INDEX.md) - Navigation guide
- [Multi-Agent Architecture](./MULTI_AGENT_COLLECTION_ARCHITECTURE.md) - Main architecture
- [API Collections](./API_COLLECTIONS.md) - API endpoints
- [Retrieval Strategies](./RETRIEVAL_STRATEGIES.md) - Retrieval configuration
- [Verification Framework](./VERIFICATION_FRAMEWORK.md) - Verification system

- [Multi-Agent Collection Architecture](./MULTI_AGENT_COLLECTION_ARCHITECTURE.md)
- [Retrieval Strategies](./RETRIEVAL_STRATEGIES.md)
- [Verification Framework](./VERIFICATION_FRAMEWORK.md)