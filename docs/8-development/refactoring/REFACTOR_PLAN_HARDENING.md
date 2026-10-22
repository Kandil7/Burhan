# Refactor plan: harden the live system

Status: authoritative. Date: 2026-10-21.
Basis: AST import-graph reachability measured from the entry points on
2026-10-21, plus a shape comparison of the ten collection agents.

This plan supersedes the earlier refactor documents in this folder. The v2 plan
(`REFRACTOR_PLAN_into_a_clearer_layered_architecture.md`) aimed at the same
layered shape and was never finished, which is why the tree still looks the
way it does. The difference here is the direction of travel: that plan tried
to add more structure, this one removes the structure that no request can
reach.

## The measurement

- `src` holds 237 modules and 27,067 code lines.
- 101 modules are reachable from `src/api/main.py`, `src/core/registry.py`,
  `src/config/settings.py`, and `src/evaluation/cli.py`.
- 136 modules, 9,914 code lines, 37 percent of `src`, are unreachable.
- The unreachable set is concentrated in the retrieval family, the indexing
  family, the generation composers and prompts, the second tool dispatch, the
  second classifier, the agent YAML loader, and the API schema duplicates.
- The ten collection agents are one pipeline copied ten times. The measured
  differences are the collection name, the prompt file, the intent keywords,
  the temperature, the top-k, the threshold, the no-passages message, and the
  verification suite.
- Four import cycles exist. The largest runs through `api.main`,
  `core.registry`, `api.lifespan`, `ask_service`, and `answer_query`.
- Thirty layer violations exist, including `core.registry` importing
  `api.main`, `retrieval` importing `agents`, `config` importing `agents`, and
  `verification` reaching the database.
- Fifteen or more domain classes are defined more than once. `Citation` is
  defined three times.

Consequence: a bug hunt pays a tax on 37 percent of the tree that cannot
run, and the green test suite partly validates the dead layer, including the
ten `config/agents/*.yaml` files that the product never loads.

## The decisions

| Decision | Chosen | Rejected | Axis |
|---|---|---|---|
| Goal | Harden the live system | Activate the designed subsystems, make the repo teachable, enable a second consumer | Depth of change against certainty |
| Dead code | Quarantine, then delete after one release | Delete now, restructure in place, split repositories | Reversibility against clarity |
| Retrieval | Measure first, then decide | Dense-only, wire hybrid now, one path with hybrid | Certainty against optionality |
| Agent layer | Make the YAML live | Keep config in code and delete the YAML, leave the agents as they are | Config-as-data against behavior risk |

## Target shape

Dependencies point downward only.

| Layer | May import | Must never import |
|---|---|---|
| `src/api` | `application`, `domain` | adapters, tools, quran, indexing |
| `src/application` | `domain`, `ports` | `api`, adapters |
| `src/domain` | nothing | everything |
| `src/agents` | `domain`, `ports`, `verification` | `api`, adapters |
| `src/verification` | `domain` | infrastructure |
| `src/adapters` | `domain`, `ports` | `api`, `application`, `agents` |
| `src/composition` | everything | nothing, it is only called |

The seam is four ports, so every effect on the outside world goes through one
narrow interface.

```python
# src/application/ports.py
class VectorSearchPort(Protocol):
    async def search(
        self, collection: str, embedding: NDArray, top_k: int, *, filters: Mapping[str, Any] | None = None
    ) -> list[ScoredPassage]: ...


class EmbeddingPort(Protocol):
    async def encode_query(self, text: str) -> NDArray: ...
    async def encode_documents(self, texts: Sequence[str]) -> NDArray: ...


class LLMPort(Protocol):
    async def complete(self, *, system: str, user: str, max_tokens: int, temperature: float) -> str: ...


class ToolPort(Protocol):
    name: str

    async def run(self, payload: Mapping[str, Any]) -> ToolResult: ...
```

The ten agent classes become one pipeline and one data record.

```python
# src/domain/agent_spec.py
@dataclass(frozen=True)
class AgentSpec:
    name: str
    collection: str
    system_prompt: str
    intent_keywords: tuple[str, ...]
    temperature: float
    top_k: int
    score_threshold: float
    no_passages_message: str
    verification_suite: VerificationSuite


# src/agents/pipeline.py
class RAGPipeline:
    def __init__(
        self, spec: AgentSpec, search: VectorSearchPort, embed: EmbeddingPort, llm: LLMPort, verifier: Verifier
    ) -> None: ...
    async def run(self, question: str, *, language: str) -> AgentOutput: ...
```

One wiring point replaces the three that exist today in `core/registry.py`,
`api/lifespan.py`, and the per-route helpers in `api/routes/fiqh.py` and
`api/routes/search.py`.

```python
# src/composition.py
@dataclass(frozen=True)
class Container:
    settings: Settings
    embedding: EmbeddingPort
    search: VectorSearchPort
    llm: LLMPort
    agents: Mapping[str, RAGPipeline]
    tools: Mapping[str, ToolPort]
    answer_query: AnswerQueryUseCase


def build_container(settings: Settings) -> Container: ...
```

## Phases

### Phase 0, harness and baseline

Build a golden set of questions whose evidence ids come from real Qdrant
payloads. The sample set in `src/evaluation/golden_set_schema.py` points at
ids that do not exist, so its precision-at-k reads zero. The harness reports
precision at 5, recall at 10, intent accuracy, mode distribution, and citation
counts, and it captures a structural fingerprint per answer: intent, mode,
collection, citation count, source names. The fingerprint compares structure,
not prose, because the LLM is not deterministic. Commit the baseline for the
current code.

**Built on 2026-10-21.** `scripts/quality/eval_harness.py` has three
commands, `retrieve` for the point ids, `score` for the metrics, and `ask` for
the fingerprint. `scripts/quality/golden_set.json` holds 20 questions, two
per collection, with a strict set of ids that answer the question and a
looser set of ids on the subject. Both sets were curated by reading the
passage text of a dense run. The baselines are under
`scripts/quality/baseline/`.

The first run produced a corpus finding, not a harness finding.

| Collection | Question | Strict evidence | Topic evidence |
|---|---|---|---|
| `fiqh_passages` | حكم صلاة الجماعة | 8 passages | 10 |
| `fiqh_passages` | حكم بيع الغرر | none | 10 on selling in general |
| `hadith_passages` | دلائل حديث إنما الأعمال بالنيات | none | 3 on hadith in general |
| `islamic_history_passages` | الهجرة النبوية | 1 | 3 |
| `islamic_history_passages` | من هو عمر بن الخطاب | none | 1 |
| `general_islamic` | أركان الإسلام | none | none |
| `general_islamic` | حكم التبرع | none | none |
| the six full collections | all twelve questions | every passage on topic | every passage on topic |

The four collections that still hold a 10k sample cannot answer the
questions asked of them. The six full collections answer every question with
an on-topic passage at the top of the list. The sample collections are not
merely smaller, they are missing the subject matter, so the retrieval
problem and the corpus problem are the same problem.

**The fingerprint produced a routing finding.** Fifteen of the twenty
questions reached the right collection. The five that did not were all
keyword table gaps: the Arabic language questions, the spirituality
questions, and the principles of jurisprudence question landed in the general
collection, and the ethics question landed in Seerah, because the ethics
words were in the Seerah table. The tables were corrected on 2026-10-21 and
the measured routing accuracy is now 20 of 20.

Verification: the harness runs and the baseline files are committed.

### Phase 1, fence the dead layer

Ship the reachability analysis as `scripts/quality/reachability_report.py`, a
manifest of the unreachable modules, and `tests/test_architecture.py` that
asserts no live module imports a manifest module and that the manifest never
grows. Dead code becomes a tracked, shrinking number.

**Built on 2026-10-21.** The report counts 108 live modules and 129
unreachable ones, 8,778 unreachable code lines, and no live module importing
the unreachable set. The manifest also carries the duplicate-name baseline, so
a third home for a name fails the test. Eight tests enforce it.

Verification: the test fails when a live module imports a manifest module.

### Phase 2, one home for the domain models

Move `Citation`, `AgentOutput`, `VerificationReport`, `VerificationStatus`,
`RetrievalResult`, `RoutingDecision`, and `ClassificationResult` into
`src/domain/models.py`, with one-release re-export shims that use explicit
aliases. This also removes the `retrieval` to `agents` inversion.

Verification: ruff, mypy, the full suite, and no import errors.

**Status (2026-10-22): done, with a documented scope adjustment.** Six models
moved into `src/domain/models.py` (`Citation`, `AgentOutput`,
`VerificationReport`, `VerificationStatus`, `RetrievalResult`,
`RoutingDecision`; `ClassificationResult` was already home). The old homes
re-export with explicit aliases: `src/agents/base.py`,
`src/agents/collection/base.py`, `src/verification/schemas.py`,
`src/application/interfaces.py`, `src/application/models.py`. The
`retrieval/mapping/citation_mapper.py` import moved to the domain home, which
removes the layer inversion.

Three same-name models stay where they are, deliberately:

1. `src/api/schemas/classify.py` keeps its own `ClassificationResult` and
   `RoutingDecision`: they are the `/classify` response DTOs and the 26-path
   HTTP contract is frozen. Unifying them with the domain value objects would
   add or drop response keys.
2. `src/core/citation.py` keeps its own `Citation`: it is a reference model
   (chapter, verse, hadith number, authority weight) for the citation
   service, not the quote model agents attach to answers.
3. `src/verification/schemas.py` keeps its own `VerificationReport`: the
   verification layer's report (issues, check results) is a different model
   from the agent answer summary.

The dead-layer duplicates (`src/domain/citations.py`,
`src/domain/evidence.py`, `src/retrieval/schemas.py`) keep their definitions
until Phase 7 deletes the modules.

### Phase 3, ports and one composition root

Add `src/application/ports.py` and `src/composition.py`. Make `api/lifespan`
build the container and store it on `app.state`. Replace the per-route
`get_fiqh_agent`, `get_vector_store`, and `get_llm_client` helpers with a
container dependency. Drop the `core.registry` to `api.main` edge, which is
the root of the largest cycle.

Verification: the harness fingerprint is unchanged and the cycle count is zero.

**Status (2026-10-22): done.** `src/application/ports.py` carries the four
ports, typed against the shapes the concrete clients already have, so
today's `EmbeddingModel`, `VectorStore`, `LLMClients`, and tools satisfy them
structurally with no wrapper. `src/composition.py` owns the `Container` and
`build_container`; the API lifespan calls it and stores the container on
`app.state`, keeping the old state names as transitional mirrors. The
per-route helpers are gone: `src/api/deps.py` exposes one `get_container`
dependency and the endpoints read what they need from the container. The
`core.registry` to `api.main` edge is gone; the registry takes its
infrastructure through `set_registry_dependencies`, called by the composition
root.

A second live cycle was found and broken on the way: the check registry
(`register_check` and its table) moved from `verification/suite_builder.py`
to `verification/base.py`, so the check modules no longer import the builder.
`scripts/quality/import_cycles.py` measures it: live cycles went from 2 to 0.
The one remaining cycle is the quarantined `tool_service`/`run_tool` pair
that Phase 7 deletes.

Two scope adjustments, both recorded here:

1. The ports describe today's method names (`generate_text`, `search`,
   `execute`) rather than the Phase 5 sketch (`complete`, `run`), so the
   current clients satisfy them with no behavior change. The pipeline in
   Phase 5 can narrow the signatures behind an adapter.
2. `ask.py` and `classify.py` still read `app.state` mirrors. They were not
   part of the three named helpers; they move behind the container when the
   pipeline lands.

Fingerprint verification: `eval_harness.py ask` run twice against the
restarted dev API, then compared to
`scripts/quality/baseline/ask_fingerprint_after_routing_fix.json`. Intent and
collection are identical for 20 of 20 questions. `answer_mode`,
`citation_count`, `sources`, and `requires_human_review` drift, but the
control run proves the drift is inherent: two runs of the same code differ on
9 of 20 questions in the same fields. The only outliers beyond that noise are
the two fiqh questions, whose sources changed because `fiqh_passages` now
holds 365,824 full-corpus rows instead of the 10,000-row sample the baseline
was recorded against.

### Phase 4, one retrieval path, with a measured gate

Both `/api/v1/ask` and `/api/v1/search/simple` call `VectorSearchPort`. The
first step keeps today's dense behavior and must reproduce the baseline
exactly. The second step adds the BM25 and reciprocal-rank-fusion adapter
behind the same port, which is where the unreachable retrieval layer gets its
chance. The gate: switch the default only if precision at 5 or recall at 10
improves on the golden set without regressing abstention behavior. If it does
not improve, that layer stays legacy and is deleted, and the result is
recorded either way.

**The gate ran on 2026-10-21, and it decided.** The harness scored the two
live paths on a 20-question set with curated evidence ids.

| Measure | Dense, the ask path | Dense plus keyword re-rank, the search path |
|---|---|---|
| precision at 5 | 0.853 | 0.653 |
| recall at 10 | 1.000 | 0.830 |
| mean reciprocal rank | 0.942 | 0.911 |
| topic precision at 5 | 0.833 | 0.711 |
| topic recall at 10 | 1.000 | 0.806 |

The keyword re-rank is worse on every measure. It pushed the aqeedah hit rate
from 1.0 to 0.5 and the tafsir hit rate from 1.0 to 0.0, and it only helped
the hadith collection. The re-rank scores the dense candidates it was given,
so it can only reorder what dense retrieval already found, and it reorders
strong semantic matches down.

Consequences for the plan.

- Phase 4 does not wire the designed hybrid path. It unifies both endpoints
  on the dense path, which is the better of the two measured, and the
  keyword re-rank leaves the live tree.
- The unreachable retrieval layer stays legacy and is deleted in Phase 7.
  A real BM25 index over the full corpus is a separate decision with its own
  cost, and it would have to beat 0.853 precision at 5 on this set to earn
  its place.
- The golden set is the record of the measurement. The files are under
  `scripts/quality/baseline/`.

Verification: the harness diff plus a written A/B result.

**Status (2026-10-22): unification done.** `RunRetrievalUseCase` no longer
builds a `HybridSearcher`; it calls `VectorSearchPort.search` per collection,
exactly the call the harness's dense mode makes, and merges by dense score.
The keyword re-rank is out of the live tree; `HybridSearcher` remains
reachable only through the harness's A/B runner, which is the record of the
measurement. The search path and the ask path now share one retrieval call,
and the agents' `embedding_model` and `vector_store` are typed as
`EmbeddingPort` and `VectorSearchPort` in `agents/collection/base.py`.
`RunRetrievalInput` lost the dead `enable_reranking` flag, and `filters` now
reach the store (every live caller passes none today).

Verification, three parts:

1. **One path proven at runtime.** For three golden queries,
   `/api/v1/search/simple` returns exactly the harness's dense-mode hits,
   same order and scores. The only differences are the documented
   presentation steps in the route: content dedup and capping. One query had
   five identical dense hits and serves one; one had a near-duplicate pair
   and serves four of five. The ranking changed against the old keyword
   re-rank output for two of the three queries, which is the intended effect
   of the gate decision.
2. **Scores re-recorded**: `scripts/quality/baseline/retrieval_dense_unified.json`
   and `score_dense_unified.json`. Precision at 5 is 0.787, recall at 10 is
   0.867, mean reciprocal rank is 0.867. These are below the 2026-10-21
   dense baseline (0.853 / 1.000 / 0.942) for data reasons, not code
   reasons. The fiqh corpus grew from the 10,000-row sample to 365,824
   full-corpus rows, so the curated evidence, which is still present and
   byte-identical at its ids (verified at fiqh id 1879), now ranks below the
   top-10 window against stronger matches. The islamic_history collection
   holds 2,048 test rows from the earlier clobber, so its curated id 5385 no
   longer exists. Both per-collection hit rates read 0.0 while the six
   untouched collections read 1.0 as before. The golden set needs
   re-curation against the full corpus after the paused load finishes.
3. **Suite and fences**: 660 tests pass, mypy clean in 240 files under both
   toolchains, live import cycles stay at 0.

### Phase 5, one pipeline, data-driven agents

Complete the ten YAML files so they match today's behavior field for field,
including the temperature difference and the no-passages message. Add a config
equivalence test that asserts the loaded spec equals the current hardcoded
values for every agent. Then move the seven-step flow into `RAGPipeline`,
delete the ten agent classes, and register the specs from YAML. Fix the agent
docstrings, which currently claim the YAML drives them.

Verification: the equivalence test, the harness fingerprint, and the suite.

### Phase 6, verification hygiene

Inject the Quran port into the exact-quote check so `verification` stops
importing `infrastructure.database`. Give every live check a unit test.

Verification: no verification module imports an adapter.

### Phase 7, delete

After one release, remove the legacy set slice by slice, shrinking the
manifest with each slice.

## Doors

Two are one-way and must not move.

- **The HTTP contract.** 26 paths with their request and response schemas.
- **The Qdrant payload schema.** 3.3 million points are already stored and the
  citations read payload keys, so a key change means re-uploading the corpus.
  The payload keys get frozen and asserted by a test that reads one live point
  from every collection.

Everything else is two-way: module layout, the config source, retrieval
internals, and the agent class shape.

## Risks

**The YAML cannot be assumed to become the single source of truth without a
behavior change.** The YAML declares alpha 0.6, initial top-k 80, and reranked
top-k 12, and a check list whose stages and order differ from the code
suites. The code declares dense 0.4, sparse 0.6, top-k 15, threshold 0.65, and
a temperature of 0.15 in most agents and 0.1 in hadith. Cheapest way to kill
this risk: the config equivalence test in Phase 5 plus the harness
fingerprint. Both must be green before the switch.

**Something in the unreachable set may still be needed.** Cheapest way to kill
this risk: the manifest plus a review of every module name against the
product roadmap. Anything the roadmap needs gets wired in Phase 4 or Phase 5
rather than left as legacy.

**The golden set is built by hand, so it encodes one author's view.** Cheapest
way to kill this risk: draw the questions from real query logs if any exist,
and keep the set small enough to re-read by eye.

## Success measures

| Measure | Today | Target |
|---|---|---|
| Unreachable code lines | 9,914 | 0 after the release |
| Live modules | 101 | about 70 |
| Duplicate domain classes | 15 or more | 1 home |
| Composition roots | 3 | 1 |
| Live retrieval paths | 2 | 1 |
| Import cycles | 4 | 0 |
| Agent pipeline lines | 675 | about 160 |

## Principle

A layer that no request can reach is not an unfinished feature, it is a
second architecture. Refactoring means deciding which architecture is the
product, then making the other one either true or gone.
