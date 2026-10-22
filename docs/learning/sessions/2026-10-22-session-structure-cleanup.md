# 2026-10-22 — Root Structure Cleanup, Alembic Removal, Data Untracking

Continuation of the session logged in
`2026-10-21-session-verification-routing-cli.md`. The user asked to
"implement all steps" of the root-order review, then stopped the Hugging Face
data load partway.

## Ritual Capture (2026-10-22)

Raw answers, kept short.

- **Worked on:** root structure cleanup, 424 MB of datasets untracked from Git,
  Alembic removed and CI merged, everything committed as `807f6bf`.
- **Learned:** ruff 0.7.4 rejects the `UP046` selector the config used, so CI
  lint would have failed on locked tools. `project-log` is path-locked to
  `docs/learning/`, so merging session logs into `docs/11-learning/` was the
  wrong direction. Qdrant point ids equal corpus row ids, so the full loader
  resumes with `--start-row` while `--recreate` would have wiped 365k rows. A
  checkpoint hook auto-committed the 54 staged moves before I reached them.
- **Still fuzzy:** when to resume the HF load and the remaining ~2M fiqh rows;
  the `.opencode.json` deletion stays unstaged and undecided.
- **Next time:** start Phase 2 of the hardening refactor (ports, one
  composition root, YAML-as-config).

## Phase 3 addendum (same day)

Ports and one composition root, per the plan. `src/application/ports.py`,
`src/composition.py`, `src/api/deps.py` are new; the lifespan, the fiqh and
search routes, and `core/registry.py` now wire through the container. The
verification check registry moved from `suite_builder` to `verification/base`
to break a second live cycle. Measured with the new
`scripts/quality/import_cycles.py`: live cycles 2 to 0, one legacy cycle left
for Phase 7.

The fingerprint check needed a control run to be meaningful: two runs of the
same code already drift on `answer_mode`, `citation_count`, `sources`, and
`requires_human_review` for 9 of 20 questions. Against that noise, intent and
collection match the baseline 20 out of 20, and only the two fiqh questions
drift beyond it, because `fiqh_passages` changed from the 10k sample to
365,824 full-corpus rows. Lesson for Phase 4: record retrieval baselines
(data-only, deterministic) separately from ask fingerprints (LLM-curated).

## Phase 4 addendum (same day)

One retrieval path, per the gate decision already recorded in the plan.
`RunRetrievalUseCase` dropped `HybridSearcher` and calls the dense
`VectorSearchPort.search`; `/search/simple` and `/ask` now share the
retrieval call. Runtime proof: three golden queries served by
`/search/simple` match the harness's dense mode hit for hit, differing only
by the route's documented content dedup. The ranking changed against the old
keyword re-rank output on two of three queries, which is the point of the
gate.

The score drop against the 2026-10-21 baseline is data, not code: the fiqh
corpus grew to 365,824 rows, so the curated evidence (byte-identical at its
ids, verified at fiqh id 1879) now ranks below the top-10, and history's
curated id 5385 is gone with the 2,048-row test clobber. The golden set must
be re-curated after the paused full-corpus load finishes.

## What Was Done

### 1. One home per script

Moved (mostly already committed as `ec8abe5`):

- Root scratch scripts to `scripts/tools/` (`debug_*`, `launch_server.py`,
  `upload_readme_v3.py`), root `test_*.py` renamed to `probe_*.py`.
- `eval_seerah.py`, `rag_eval_seerah.py` and their outputs to
  `scripts/evaluation/`.
- Launchers to `scripts/windows/` (`build.bat`, `start-*.bat`, `stop-athar.bat`,
  `download-embeddings-to-qdrant.bat`, `extract_all_lucene.bat`).
- `QWEN.md`, `V2_ARCHITECTURE_REPORT.md` to `docs/2-architecture/`.
- `notebooks/` merged into `docs/8-development/notebooks/` (no filename
  collisions; the `full colab notebook in detials` pair differs by extension).
- `scripts/tests/` renamed to `scripts/smoke/` with a README; loose
  `scripts/*.py` helpers settled into `scripts/data/`, `scripts/tools/`, and
  `scripts/smoke/`.

Rename rule applied: every non-pytest script named `test_*` became `smoke_*` or
`probe_*`, including `scripts/smoke/test_query_error.py`, which the new
architecture test caught on its first run.

### 2. Naming guard

`tests/test_architecture.py` gained `TestTestFilePlacement`: it fails when any
`.py` file outside `tests/` is named `test_*.py`. Evidence: first run failed on
`scripts/smoke/test_query_error.py`; after the rename, 9/9 pass.

### 3. Duplicate homes resolved

- **Alembic removed** (scaffold, `alembic.ini`, dependency). It had zero
  revisions while `migrations/*.sql` carried the whole schema. `poetry remove
  alembic` rewrote only the lock entry for alembic + mako. Makefile db targets
  and `scripts/windows/start-athar.bat` now call `scripts/cli.py db migrate`.
  `migrations/README.md` records the decision.
- **Data untracked from Git** (policy: data never in Git): `data/mini_dataset/`
  (v1, superseded) and 15 payload files under `data/mini_dataset_v2/`
  (424 MB) are `git rm --cached` and gitignored. `stats.json` and a new
  `data/mini_dataset_v2/README.md` stay tracked. The loader
  `embed_mini_v2_to_qdrant.py` now fetches a missing file from
  `Kandil7/Athar-Mini-Dataset-v2` (9 of the 10 collections are on the Hub;
  `usul_fiqh` is not, and its full corpus is loaded anyway).
- **Learning homes split, not merged:** session logs live in
  `docs/learning/sessions/` because the `project-log` tool is path-locked to
  `docs/learning/`; curated guides stay in `docs/11-learning/`. Each artifact
  type has exactly one home. `docs/learning/README.md` records the split.
- Old refactor plans: `impl_plan.md` and `REFACTOR_PLAN_SPECILIZED_AGENT.md`
  now carry the same "historical record" banner the other six already had.

### 4. CI merged

`.github/workflows/ci-cd.yml` deleted; `ci.yml` now has lint, test (with a
real `psql` schema step against `migrations/*.sql`), security (bandit artifact,
non-blocking), and the Docker build on main. The placeholder `owner/Burhan`
deploy gates are gone (no Kubernetes manifests exist in the repository).

### 5. Reference fixes

Command paths updated in `scripts/cli.py`, `scripts/README.md` (rewritten to
the actual tree), the root `README.md`, `docs/4-guides/setup.md`,
`docs/5-api/COMPLETE_DOCUMENTATION.md`, `docs/9-reference/FILE_REFERENCE.md`,
`docs/9-reference/SANADSET_HADITH_AGENT.md`,
`docs/9-reference/COMPLETE_DATA_DRIVEN_PLAN.md`, and
`docs/10-operations/LUCENE_MERGE_COMPLETE.md`.

## Verification

- `ruff check src/ tests/` — all checks passed (ruff 0.16.4).
- `mypy src/` — no issues in 237 files (mypy 2.3.1).
- `python -m pytest -q` — **660 passed** (659 before + 1 new placement test).
- `python scripts/quality/reachability_report.py --write-manifest` — fence
  refreshed after the alembic removal: 107 live / 130 unreachable modules,
  8,781 unreachable lines, 0 live-to-legacy imports. The architecture tests
  pass against the new manifest.

CI toolchain alignment: `poetry.lock` pinned ruff 0.7.4 and mypy 1.20.0,
older than the gate tools and too old for the `UP046` selector in
`pyproject.toml`. The pins moved to `ruff ^0.16.4` and `mypy ^2.3` and the
lock now carries ruff 0.16.10 / mypy 2.4.0. The lazy `chroma_store` import in
`src/indexing/vectorstores/factory.py` (dead scaffolding, the module does not
exist) now carries a `# type: ignore` on the statement line, so every mypy
version accepts it. Verified with the locked tools as well as the PATH tools.

## Paused: Full-Corpus Load

The `embed_full_to_qdrant.py` background sequence (fiqh resume, then hadith,
history, general with `--recreate`) was stopped at the user's request: "dont
load data from hf for now".

State at stop (verified static after kill):

| Collection | Rows | Corpus rows |
| --- | --- | --- |
| fiqh_passages | 365,824 | 2,397,988 |
| hadith_passages | 10,000 (stale mini) | — |
| islamic_history_passages | 2,048 (test clobber) | — |
| general_islamic | 10,000 (stale mini) | — |

Resume command when transfers are allowed again:

```bash
python scripts/data/embed_full_to_qdrant.py --collection fiqh_passages --start-row 365000 --device cuda --half
python scripts/data/embed_full_to_qdrant.py --collection hadith_passages --recreate --device cuda --half
python scripts/data/embed_full_to_qdrant.py --collection islamic_history_passages --recreate --device cuda --half
python scripts/data/embed_full_to_qdrant.py --collection general_islamic --recreate --device cuda --half
```

Point ids equal corpus row indices, so the overlap of 824 rows rewrites
idempotently. Measured rate was ~76 rows/s on CUDA, so the remaining ~2M fiqh
rows alone take roughly 7-8 hours.

After any full load, re-curate the golden set point ids in
`scripts/quality/golden_set.json` (they point at absolute row ids) and
re-record the harness baselines.

## Not Done

- Nothing committed or pushed by this session; the moves staged earlier were
  committed as `ec8abe5` (auto-checkpoint), and the rest of this work is
  uncommitted pending the user's call.
- `.opencode.json` (the repo-level MCP registration for `code-review-graph`)
  was deleted outside this session's work. The server is registered globally,
  so the tools still load. The deletion is left unstaged for the user to
  confirm or restore.
- Phase 2+ of `docs/8-development/refactoring/REFACTOR_PLAN_HARDENING.md`
  (ports, one composition root, YAML-as-config) are untouched.
