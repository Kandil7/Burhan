# Session: full Burhan project repair, data load, and verification hardening

Date: 2026-10-21
Repo: `D:\AI\Projects\Burhan` (Burhan Islamic QA, FastAPI + Qdrant + Postgres + Redis)
Stack: FastAPI on uvicorn, `Burhan-api` / `Burhan-qdrant` / `Burhan-postgres` /
`Burhan-redis` on Docker Desktop with the WSL2 GPU backend, BGE-M3 embeddings
on the RTX 5000, Groq for generation.

## Context and goal

The repository was ~200 Python files of a multi-agent Islamic QA system that
did not start, did not answer, and did not verify its own output. The request
was to complete and improve the whole project: repair defects, load the
corpora into Qdrant and Postgres, and make every collection and endpoint
work.

Constraints agreed up front and honoured throughout:

- Never commit or push. The user decides.
- Never edit `.env`. Only `.env.example` was reconciled.
- Deleting tracked files is destructive. Repairs are in place; removals are
  proposed, not performed.
- Verification evidence is required for every "done" claim.
- `ruff` and `mypy` must pass per batch, tests after each batch.
- `scripts/` and `alembic/` are outside ruff scope; pre-existing findings
  there are left alone.

---

## Work stream 1: unblocking the import and startup path

The application could not even be imported, so nothing downstream could be
tested.

- `src/config/settings.py` failed to build the CORS and API key settings.
  The CORS origin list was not JSON-decoded, and the API key field did not
  exist. Both were repaired.
- Nine packages under `src/` had no `__init__.py`, so imports resolved
  inconsistently. All nine were created.
- After the fix every module under `src/` imports cleanly.

## Work stream 2: verification layer

The system claims "generation only consumes verified evidence", but the
verification layer did not enforce it.

- `src/verification/schemas.py` had no status inference. Checks now infer
  `PASSED`, `FAILED`, `SKIPPED`, or `WARNING` from their fields, and every
  check carries an explicit `stage` of `evidence`, `answer`, or `both`.
- Policy semantics were made explicit: `warn` lowers confidence but does not
  mark the answer unverified, `proceed` marks it unverified but still answers,
  and an unknown check fails closed.
- `src/verification/suite_builder.py` was rewritten. It previously built
  suites that never ran the registered check implementations.
- All ten collection agents now route through `CollectionAgent._verify`
  instead of their own partial implementations.

## Work stream 3: classifier, router, registry, API

- Eleven agents are registered (ten collection agents plus `chatbot_agent`),
  and the `fiqh_router` route is mounted.
- The API key middleware compares keys with `hmac.compare_digest` rather
  than `==`.
- Keyword duplicates that normalize to the same string are collapsed.
  Intent conflicts resolve count-first, with priority only breaking ties.
- `src/core/router.py::HybridQueryClassifier` was made to delegate to the
  canonical `KeywordBasedClassifier` instead of keeping a second
  implementation.

## Work stream 4: tool and domain logic fixes

- `src/tools/dua_retrieval_tool.py` scored only the Arabic text and missed
  the English `search_keywords` column. It now searches both, so
  "الاستغفار" matches.
- `src/utils/language_detection.py` mis-detected mixed Arabic and English.
- `src/core/exceptions.py` gained the domain exception types the routes
  expect.
- `src/tools/inheritance_calculator.py::_calculate_furood` gave each wife a
  full share instead of the wives sharing one fard (1/8 or 1/4). The rows
  are now also renamed from "Wife" to "Wives" when there is more than one.
- `src/api/routes/fiqh.py` was repaired.

## Work stream 5: tooling, packaging, deployment

- Ruff configuration was corrected so `ruff check src tests` reflects the
  intended scope.
- mypy needed `mypy_path` and `explicit_package_bases` to resolve the
  package layout. It now passes on 237 source files.
- The Dockerfile installed the wrong dependency group. Poetry 1.8.3 turns
  `--no-dev` into `--only main`, which silently dropped `--with rag`, so
  torch was never installed and every uvicorn worker exited at import. The
  Dockerfile now uses `--without dev`.
- The migrations directory was de-duplicated so `001_initial_schema.sql` and
  the later deltas do not define the same tables twice, and every file is
  idempotent.

## Work stream 6: documentation sweep

Twenty-four historical documents got a banner marking them as superseded, so
a reader does not follow stale instructions. Sixteen token renames were
applied across thirteen documents, and five renames were reverted after
checking that the old name was the correct historical one.

## Work stream 7: loading the corpora

Full-corpus embeddings were generated on the RTX 5000 and uploaded to Qdrant
through the gRPC path with on-disk vectors and payload, HNSW `m=0` during
upload and one final index build at `m=16, ef_construct=100`. The importer
streams shard by shard behind a thread pool, uses absolute row ids plus
`--start-shard`, `--end-shard`, `--row-start`, `--row-end`, and
`--defer-index`, and retries per shard and per batch. Qdrant runs with
`mem_limit: 3g` after low-virtual-memory events at 4g.

Loaded collections:

| Collection | Points | Source |
|---|---|---|
| `arabic_language_passages` | 1,001,088 | full corpus, absolute row ids |
| `aqeedah_passages` | 745,835 | full corpus |
| `spirituality_passages` | 439,568 | full corpus |
| `quran_tafsir` | 394,176 | full corpus, book pages |
| `usul_fiqh` | 371,148 | full corpus |
| `seerah_passages` | 295,175 | full corpus |
| `duas_adhkar` | 355 | dua and azkar seed files |
| `fiqh_passages` | 10,000 | mini sample |
| `hadith_passages` | 10,000 | mini sample |
| `islamic_history_passages` | 10,000 | mini sample |
| `general_islamic` | 10,000 | mini sample |

The four 10k collections exist because the Hugging Face Hub publishes no
full embeddings for them. They make every agent retrieve, and they are
samples, not corpora.

## Work stream 8: Quran and tafsir in Postgres

- The full Quran was loaded from Quran.com v4 with the Saheeh International
  translation: 114 surahs, 6236 ayahs, 6236 translations, no gaps.
- Global verse numbers come from a canonical 114-entry per-surah verse-count
  table (Kufan, sum 6236). Spot checks: `1:1=1`, `2:255=262`, `18:10=2150`,
  `114:6=6236`.
- Verse-level tafsir was seeded from upstream APIs, not from the Qdrant
  `quran_tafsir` book pages, whose payloads carry no surah or ayah key.
  `scripts/data/seed_tafsir_data.py` loads al-Jalalayn and al-Qurtubi from
  `api.alquran.cloud` and Ibn Kathir from `api.quran.com` tafsir id 14, and
  upserts on `(ayah_id, source_name)` with `index_elements`, so re-running is
  safe. Result: 18,676 rows (6,236 / 6,235 / 6,205).
- Ibn Kathir has 31 verses with no upstream commentary and al-Qurtubi has one
  blank entry. Both are upstream data limits.
- Tafsir ordering is deterministic: `order_by(source_name, id)` in
  `get_tafsir` and `order_by(id)` in `search_tafsir`.
- The tafsir contract was fixed. An existing verse with no commentary rows
  now returns 404 instead of an empty list.

## Work stream 9: quotation validation

The Quran quotation validator was repaired to compare an alef-insensitive
skeleton on both sides, query whole-input containment before applying word
filters, and match `text_simple` when it is present. 120 random verses were
validated with 0 misses above the 5-character minimum, and 108:1 returns
`is_quran=true` at confidence 1.0 while non-Quran text is rejected.

## Work stream 10: the `/api/v1/ask` pipeline

- The Zakat endpoint accepted only `trade_goods_value` and `stocks_value`,
  so its own documented example returned 500. Both the documented aliases
  and the model names now work, and unknown asset or heir keys return 422
  with the accepted field list instead of a 500.
- Deterministic tools in the ask pipeline were adapted to `AgentOutput`.
  Calculators without an `execute` method answer with a pointer to
  `/api/v1/tools/zakat` and `/api/v1/tools/inheritance` rather than a fake
  success payload.
- Classifier precision improved: "ما هو فضل طلب العلم؟" routes to
  `islamic_knowledge` instead of `duas`, and the generic keywords `طلب` and
  `إجابة` were removed from the duas intent.
- Arabic occasion hints were added to the dua tool, so "أدعية الصباح"
  returns morning adhkar.
- The dead service layer was repaired. `tool_service.py` delegates to the
  real prayer-times, Hijri, and dua tools and propagates failure,
  `run_tool.py` dispatches through it with lazy initialization,
  `classify_service.py` delegates to `ClassifyQueryUseCase`, and
  `trace_service.build_trace` delegates to `BuildTraceUseCase`.

## Work stream 11: honest answer modes

- `src/agents/collection/base.py` now sets `answer_mode="evidence"` when the
  LLM call fails or is absent, appends a `generation_fallback` verification
  issue, and forces `requires_human_review` when the answer equals the raw
  evidence text. `_format_passages` was added to the base contract so an
  agent can render passages for the prompt.
- The `evidence` mode is a fourth mode alongside `answer`, `clarify`, and
  `abstain`.
- `evidence_filtered_out` is raised only when every candidate was filtered
  out. Partial filtering keeps the 0.90 confidence cap and stays silent.
- Per-agent `max_tokens` budgets are clamped through
  `settings.resolve_max_tokens` at `src/config/settings.py:215`, so
  `LLM_MAX_TOKENS` can constrain all ten agents. `/api/v1/search/simple`
  applies the same clamp to `RAG_MAX_TOKENS` at
  `src/api/routes/search.py:288`.

## work stream 12: seed data and the azkar import

- `scripts/ingestion/import_azkar_db.py` was broken: wrong branch, wrong
  file, wrong project root. It now uses the `master` branch and
  `azkar_obj.json` with a SQLite-dump fallback, and writes 345 entries to
  `data/seed/azkar_imported.json`.
- Arabic azkar-db categories are mapped to the tool's English occasion ids
  at import time, because the stored Arabic occasions never matched
  `occasion="morning"`.
- The dev compose file bind-mounts `../data:/app/data` into the API, so a
  regenerated seed file takes effect without an image rebuild.
- `scripts/data/embed_duas_to_qdrant.py` embeds `duas.json` (10 entries,
  `book_title` "حصن المسلم") and `azkar_imported.json` (345 entries,
  `book_title` "الأذكار") into `duas_adhkar`. The API serves 355 duas.

## work stream 13: security and contract hardening

- `GET /api/v1/fiqh/test` and `POST /metrics/reset` return 404 unless
  `DEBUG=true`. `GET /metrics/reset` returns 405.
- The catalog and collection indexing pipelines returned zero counts while
  doing nothing. They now raise `CollectionIndexError` and
  `CatalogIndexError` pointing at the working embedding scripts.
- The multi-collection retriever logs per-collection failures instead of
  swallowing them.
- Tool request dictionaries accept documented aliases and reject unknown
  keys with 422 rather than 500.
- `.env.example` was reconciled with the code: the phantom
  `QDRANT_COLLECTION_*` fields were removed, and `API_KEY_ENABLED`,
  `API_KEY`, the RAG, classifier, and cache knobs were added.
  `LLM_MAX_TOKENS` is documented as an output ceiling with a note about the
  Groq free-tier quota.

## work stream 14: database constraint names

`001_initial_schema.sql` created three UNIQUE constraints without names, so
PostgreSQL named them after their columns while the SQLAlchemy models in
`src/data/models/quran.py` declare `uq_ayah_surah_number`, `uq_translation`,
and `uq_tafsir`. A future `drop_constraint("uq_tafsir")` would have failed.

`migrations/versions/003_align_unique_constraint_names.sql` renames each one
inside a guarded `DO` block, so it is idempotent and touches nothing when
the target name already exists. Renaming a constraint also renames its
backing index, and nothing queries these names at runtime.

- The file was added to the list in `scripts/cli.py::cmd_db_migrate` and to
  the table in `migrations/README.md`.
- Applied to the running database. Verified: `uq_ayah_surah_number`,
  `uq_translation`, `uq_tafsir`, with `surahs_number_key` left alone because
  the model declares that one without an explicit name.
- Re-running the tafsir seeder for surah 1 after the rename wrote the same 21
  rows and changed no counts. Data intact at 114 surahs, 6236 ayahs, 18676
  tafsirs.

## work stream 15: the contradiction detector

This was the largest remaining correctness defect and it was invisible in the
test suite.

**The bug.** `src/verification/checks/contradiction.py` flattened every
retrieved passage into one text block and then compared each answer sentence
against that block. Negation was detected with a substring test on `"لا "`,
which matches inside `إلا`, `بلا`, and `ألا`. The consequence: the block
almost always contained a negation, so every answer sentence that did not
contain one was reported as a contradiction, as long as it shared three
tokens with the block, which Arabic prose does easily. A live fiqh answer
reported 7 contradictions across 7 sentences, `is_verified` was false, and
`requires_human_review` was true on essentially every Arabic response.

**The repair.**

- One sentence is compared with one passage, so a negation is attributed to
  the passage that carries it.
- Negation is matched as a whole token: `لا`, `لم`, `لن`, `ليس`, `ليست`,
  `غير`, `not`, `no`, `never`, `neither`, `nor`.
- Idioms are stripped before tokenizing: `لا شك`, `لا ريب`, `لا بد`,
  `لا سيما`, `لا يخفى`, `لا جرم`, `لا محالة`.
- `لا ... إلا` and `not ... except` are read as restriction, not denial, at
  `src/verification/checks/contradiction.py:373`.
- A polarity conflict needs at least 3 shared content words and at least 60
  percent coverage of the statement's content words. Function words are
  excluded from the overlap count.
- Numeric conflicts are detected per passage, comparing two numbers that
  share a unit such as a verse count, a year, or a hadith number.
- Content tokens are compared after folding diacritics, tatweel, alef forms,
  alef maqsura, and ta-marbuta.

**Evidence.** The live fiqh answer dropped from 7 contradictions to 0. One
remaining hit was traced to a passage reading "لا يجوز إعادة صلاة الكسوف إلا
إن..." and was fixed by the restriction rule. After the thresholds were
tightened, a rerun of the same question reported no contradictions and the
API returned `is_verified: true` with confidence 0.9 and no issues. Ten new
tests cover the false positive, the true polarity conflict, the numeric
conflict, the idiomatic `لا شك`, the `إلا` substring, low overlap, empty
evidence, and the English path.

## work stream 16: exact-quote verification

`src/verification/checks/exact_quote.py` compared Arabic quotes without
folding, so a passage stored with tashkeel and an answer that dropped the
tashkeel were reported as a hallucination. The normalizer now uses
`normalize_arabic`, which folds diacritics, alef forms, and ta-marbuta, at
`src/verification/checks/exact_quote.py:195`. Four new tests cover the
diacritic case, the alef case, a fabricated quote, and an answer with no
quotes.

## work stream 17: intent routing for calculator intents

**The bug.** "ما هي أحكام زكاة عروض التجارة؟" matched ZAKAT and FIQH once
each. The tie was broken by priority, and the tool intent won, so the
calculator answered a knowledge question with "هذه الأداة تُستخدم عبر نقطة
النهاية المخصصة لها". The same happened for "كيف أقسم الميراث؟".

**The repair.** A calculator needs a case to compute, so a calculator intent
now requires one:

- Any digit in the query means a calculation.
- A ruling cue (حكم, أحكام, فضل, معنى, يجوز, مشروع, دليل, تعريف, شروط,
  أركان, نصيب, سهم, حصة) means a knowledge question, and the intent falls
  back to fiqh.
- Zakat without an amount is a knowledge question.
- Inheritance also accepts a case described in words, so named heirs
  (زوجة, أم, ابن, بنت, ...) reach the calculator.

The rule lives in `KeywordBasedClassifier._requests_calculation` at
`src/application/router/classifier_factory.py:190`.

**Evidence.** "ما هي أحكام زكاة عروض التجارة؟" now returns intent `fiqh`, 14
citations, `is_verified: true`, and a real fiqh answer. "زكاة 100000 ريال"
still resolves to the zakat intent and returns the endpoint pointer, which is
the documented design because the calculator is HTTP-only.

## work stream 18: keyword collisions

Live routing showed real questions landing on the wrong intent, all caused by
keywords that are too common after Arabic normalization.

- `علي` in the Seerah list matched the preposition `على`, so any question
  containing `على` became a Seerah question. It was replaced with
  `علي بن أبي طالب`.
- `أحد` matched "anyone" and was replaced with `غزوة أحد`.
- `مسلم` in the hadith list matched `المسلم`, an ordinary word for a Muslim
  person. It was replaced with `صحيح مسلم`.
- The bare month `رمضان` made "صيام رمضان" a calendar question. The month
  name stays, but calendar padding now ranks below fiqh on a tie at
  `src/domain/intents.py:149`.

`HybridQueryClassifier._keyword_match` was duplicating the classifier's
conflict resolution and reported a flat 0.92 confidence. It now delegates to
`KeywordBasedClassifier` and keeps the flat confidence the router expects.

Twenty new tests live in `tests/test_intent_classifier.py`, and the
expectations in `tests/test_router.py` were updated to the new semantics
where they encoded the old routing.

## work stream 19: readable tool answers

`/api/v1/ask` returned the raw JSON of the Hijri and prayer-time tools as the
answer. `AnswerQueryUseCase._format_tool_answer` now renders Hijri dates as
"التاريخ الهجري: 11 جمادى الأولى 1448 هـ" with the Gregorian date, and
prayer times as one labelled line per prayer with the Qibla direction, at
`src/application/use_cases/answer_query.py:262`. Two new tests cover both.

## work stream 20: the Windows CLI

`python scripts/cli.py db migrate` could not run on this workstation for two
independent reasons, and neither pointed at the real cause.

- It built `docker exec -i Burhan-postgres psql ... < file.sql`. The `<`
  operator does not exist in PowerShell, so the command failed with a parser
  error. The CLI now feeds each SQL file to `psql` as stdin from Python,
  which works on Windows and Linux alike, at `scripts/cli.py:243`. It also
  stops at the first failing migration instead of reporting success.
- The CLI printed status emoji to a cp1252 console and raised
  `UnicodeEncodeError` before doing any work. It now reconfigures stdout
  and stderr to UTF-8 with replacement.
- `subprocess.run(text=True)` decoded Docker output with the locale
  encoding, which mangled the ellipsis in the container command column. The
  call now passes `encoding="utf-8", errors="replace"`.

**Evidence.** `python scripts/cli.py db migrate` now applies all three
migrations in order and reports success for each, with the row counts
unchanged afterwards. `python scripts/cli.py status` and `help` run cleanly
and render the container table without mojibake.

## work stream 21: documentation accuracy

- `docs/10-operations/CHANGELOG.md` records every fix above under Added and
  Fixed, including the CLI and routing changes.
- `docs/10-operations/CURRENT_STATE.md` was created as the single snapshot of
  what runs today: 26 OpenAPI paths, 11 agents, 647 tests, the data
  inventory, the answer modes, the ask-routing rules, the security posture,
  the known gaps, and the verification commands. The route count was
  corrected from 27 to the measured 26.
- `docs/3-core-features/quran.md` was corrected from 50k+ and 20k+ to the
  actual 18,676 tafsir rows and 6,236 ayahs.
- `docs/5-api/COMPLETE_DOCUMENTATION.md` agent and endpoint tables and
  `docs/9-reference/FILE_REFERENCE.md` were updated to the current names.

---

## Design decisions taken

- Verification gets an explicit `stage` per check. `warn` does not mark an
  answer unverified, `proceed` does, and an unknown check fails closed.
- Broken but referenced modules are repaired in place. Stale tests are
  rewritten to the current architecture, not deleted.
- Keyword duplicates that normalize equal are collapsed, and intent conflicts
  resolve on match count first, with priority only breaking ties.
- Agent collection names live in class constants, not in YAML or settings.
- Raw SQL under `migrations/` is the source of truth. Alembic is scaffolded
  but unused.
- Quran seeding uses Quran.com v4 with the Saheeh International translation,
  and global verse numbers come from a canonical 114-entry table.
- Arabic matching compares an alef-insensitive skeleton on both sides.
- Zakat and inheritance are HTTP-only tools. In-process callers get a
  `ToolUnavailableError` naming the route.
- A calculator intent requires a calculation, because a calculator without
  inputs can only answer with a usage notice.
- A heuristic check reports honestly and lowers confidence. It never invents
  a pass.

## Key insights

- **Arabic string heuristics need per-segment comparison or they lie.** A
  substring negation test plus evidence-level comparison turned a correct
  fiqh answer into 7 false contradictions. The fix was structural, not
  threshold tuning: compare one sentence with one passage, match negation as
  a whole token, and treat `لا ... إلا` as restriction.
- **Live probes found what the test suite could not.** The contradiction
  defect, the routing defect, the JSON answer, and the CLI crash were all
  invisible to a green test run and obvious within one request.
- **Keyword tables are a precision problem, not a coverage problem.** Bare
  common words collide after normalization, and the collision is silent
  because the wrong intent still returns an answer.
- **Provider quotas are output limits, not request limits.** Groq's free tier
  rejects any request whose `max_tokens` exceeds 1000 output tokens per
  minute. Agent budgets must be clamped to the provider ceiling, otherwise
  every answer silently degrades to raw evidence.
- **Windows shells break Unix idioms quietly.** The missing `<` redirect, the
  cp1252 console, and the locale decode of Docker output each cost real
  time, and all three report errors that point somewhere else.
- **A schema written by hand drifts from the models.** The unnamed UNIQUE
  constraints were harmless until a future `drop_constraint` call, which is
  exactly the kind of failure that appears months later.

## Verification evidence

Gates, last run after every code change in this session:

```text
ruff check src tests   -> All checks passed!
mypy src               -> Success: no issues found in 237 source files
pytest -q              -> 647 passed, 30 warnings in 26.17s
```

Live stack, all four containers healthy, `/ready` reporting 11 collections:

| Probe | Result |
|---|---|
| `GET /ready` | 200, api, postgres, redis, qdrant healthy, 11 collections |
| `GET /api/v1/search/stats` | 200, 3,287,345 documents, `duas_adhkar` 355 green |
| `GET /api/v1/quran/tafsir/2:255` | 200, al-jalalayn, al-qurtubi, ibn-kathir in stable order |
| `POST /api/v1/quran/validate` | 200, `is_quran` true, confidence 1.0 for 112:1 |
| `POST /api/v1/tools/duas` | 200, 3 results for "أدعية الصباح" |
| `POST /api/v1/tools/zakat` | 200, 2500 on 100000 cash |
| `POST /api/v1/tools/inheritance` | 200, wife 12500, sons 87500, remaining 0 |
| `POST /api/v1/search/simple` | 200, 3 sources |
| `GET /api/v1/fiqh/test` | 404 with DEBUG off |
| `GET /metrics/reset` | 405 |
| `POST /metrics/reset` | 404 |
| `POST /api/v1/quran/analytics` | 200, real SQL, 286 ayahs for Al-Baqarah, in Arabic and English |
| `POST /api/v1/fiqh/answer` | 200, 1937-character answer, 14 citations |

Database after the migration re-run: 114 surahs, 6236 ayahs, 18676 tafsirs,
and the constraint names `uq_ayah_surah_number`, `uq_translation`,
`uq_tafsir`.

## Data inventory

- Postgres: 114 surahs, 6236 ayahs, 6236 translations, 18676 tafsirs.
- Qdrant: 11 collections, 3,287,345 vectors, none empty. Six at full corpus,
  four at 10k samples, `duas_adhkar` at 355.

## Open decisions for the user

- `LLM_MAX_TOKENS` is still 2048 in `.env`. The file was not edited. At or
  below 1000 the Groq quota stops forcing `evidence` mode.
- `API_KEY_ENABLED` and `RATE_LIMIT_ENABLED` are off and must be on before
  any public deployment.
- 54 files are modified and 15 are untracked, all uncommitted at `4cc46e2`.
  Whether to commit, and whether to stop the stack, is the user's call.
- Four collections still hold 10k samples. Full-corpus embeddings need the
  importer run against the Hugging Face shards.
- Tracked scratch files at the repo root (`debug_*.py`, `classifier_debug.txt`,
  `debug_output.txt`, `debug_keywords_output.txt`, `rag_eval_results.csv`,
  `rag_eval_seerah.jsonl`, `eval_seerah.py`, `launch_server.py`,
  `download-embeddings-to-qdrant.bat`) are candidates for removal, but
  removing tracked files is a user decision.

## Next steps

- Save the Arabic-negation and Windows-shell traps to cross-project memory.
  Done in this session at
  `C:\Users\Kandil\.config\opencode\memory\arabic-heuristics-and-windows-shells.md`.
- Lower `LLM_MAX_TOKENS` to 1000 or below in `.env`, then re-probe
  `/api/v1/ask` and confirm the mode is `answer` rather than `evidence`.
- Decide on the commit, the full-corpus embedding run, and the scratch file
  cleanup.
