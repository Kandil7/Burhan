# Current State

Verified on 2026-10-21 against the running Docker stack.

## What Runs Today

- **API:** FastAPI container `Burhan-api` on port 8000, hot reload from the
  bind-mounted `src/`.
- **Datastores:** `Burhan-postgres`, `Burhan-redis`, `Burhan-qdrant`, all healthy.
- **Endpoints:** 26 paths in `/openapi.json`. Every route was exercised with a
  real request; the tool, Quran, RAG, and health paths return 200.
  `/api/v1/fiqh/test` returns 404 unless `DEBUG=true`.
- **Agents:** 11 registered (10 collection agents plus `chatbot_agent`).
- **Tests:** 647 pass. `ruff check src tests` and `mypy src` are clean.

## Answer Modes

`/api/v1/ask` returns one of four modes in `answer_mode`:

| Mode | Meaning |
|------|---------|
| `answer` | The LLM composed an answer from verified evidence |
| `clarify` | The query needs more detail before an answer is possible |
| `abstain` | Verification found the evidence insufficient |
| `evidence` | The LLM call failed or is not configured; the response is the raw verified evidence text |

`evidence` responses also carry a `generation_fallback` verification issue and
set `requires_human_review`. This matters on metered providers: Groq's free
tier caps output at 1000 tokens per minute for some models, so a generation
request above that ceiling is rejected and the endpoint degrades to `evidence`.
Each agent now clamps its own budget to `LLM_MAX_TOKENS` and retries with a
smaller budget when the provider refuses over the output quota, so the
degradation only happens when the provider refuses every budget. Lowering
`LLM_MAX_TOKENS` to 1000 still removes the first rejection.

## Data

| Store | Rows / points | Notes |
|-------|---------------|-------|
| Postgres `surahs` | 114 | Full Quran index |
| Postgres `ayahs` | 6,236 | `text_uthmani` and `text_simple` populated |
| Postgres `translations` | 6,236 | Saheeh International |
| Postgres `tafsirs` | 18,676 | al-jalalayn 6,236, al-qurtubi 6,235, ibn-kathir 6,205 |
| Qdrant `aqeedah_passages` | 745,835 | Full HF embeddings |
| Qdrant `arabic_language_passages` | 1,001,088 | Full HF embeddings |
| Qdrant `quran_tafsir` | 394,176 | Book pages, not verse-keyed tafsir |
| Qdrant `seerah_passages` | 295,175 | Full HF embeddings |
| Qdrant `spirituality_passages` | 439,568 | Full HF embeddings |
| Qdrant `usul_fiqh` | 371,148 | Full HF embeddings |
| Qdrant `fiqh_passages` | 365,824 | Full corpus load in progress, paused (2,397,988 rows total) |
| Qdrant `hadith_passages` | 10,000 | Mini-dataset sample |
| Qdrant `islamic_history_passages` | 2,048 | Test-clobbered sample, full load pending |
| Qdrant `general_islamic` | 10,000 | Mini-dataset sample |
| Qdrant `duas_adhkar` | 355 | Dua and azkar seed entries, embedded for search |

The four sample collections are being replaced by full-corpus loads through
`scripts/data/embed_full_to_qdrant.py`. **The load is paused by request** (no
Hugging Face transfers for now). Fiqh holds 365,824 of 2,397,988 corpus rows;
point ids equal corpus row indices, so the run resumes with
`--collection fiqh_passages --start-row 365000 --device cuda --half` and never
duplicates rows. The other three still hold sample rows and are rebuilt with
`--recreate` when the load resumes.

Verse-level tafsir is seeded from upstream APIs, not from the Qdrant
`quran_tafsir` book pages:

```bash
python scripts/data/seed_tafsir_data.py                 # all three sources
python scripts/data/seed_tafsir_data.py --source al-jalalayn --surah-start 1 --surah-end 10
```

- `al-jalalayn` and `al-qurtubi` come from `api.alquran.cloud`.
- `ibn-kathir` comes from `api.quran.com` tafsir id 14.
- Rows upsert on `(ayah_id, source_name)`, so re-running is safe.
- Ibn Kathir has 31 verses with no upstream commentary; those stay absent.

The dua tool reads `data/seed/duas.json` (10 hand-curated duas) plus
`data/seed/azkar_imported.json` (345 azkar-db entries). Regenerate the second
file with:

```bash
python scripts/ingestion/import_azkar_db.py
```

`scripts/data/embed_duas_to_qdrant.py` embeds both files into `duas_adhkar`,
so `search/simple?collection=duas_adhkar` returns the same 355 entries.

`data/` is bind-mounted into the dev API container, so a regenerated seed file
takes effect on the next request without an image rebuild.

## Ask Routing

`/api/v1/ask` routes by intent before retrieval:

- Questions about zakat and inheritance rulings go to the `fiqh_passages`
  collection. The classifiers that back `/api/v1/tools/zakat` and
  `/api/v1/tools/inheritance` need amounts or named heirs, so a question
  without either is a knowledge question.
- `زكاة 100000 ريال` still resolves to the zakat intent, and the route answers
  with a pointer to `/api/v1/tools/zakat` because the calculator is HTTP-only.
- Hijri and prayer-time results are rendered as Arabic text, not raw JSON.

## Security Posture

- `API_KEY_ENABLED=false` and `RATE_LIMIT_ENABLED=false` in the current
  environment. Both must be enabled before any public deployment.
- `/api/v1/fiqh/test` and `/metrics/reset` return 404 unless `DEBUG=true`.
- Metrics reset accepts POST only.
- `.env` is not committed; `.env.example` lists the settings the code reads.

## Known Gaps

1. **Ibn Kathir gaps:** 31 verses have no Ibn Kathir commentary upstream, so
   those verses return two sources instead of three. Al-Qurtubi has one blank
   entry upstream. Both are upstream data limits, not pipeline faults.
2. **Sparse collections:** fiqh, hadith, history, and general still hold
   sample rows. The evaluation harness measured what that costs: for those four
   collections the curated questions have no answering passage at all, while
   the six full collections return an on-topic passage for every question.
   The samples are missing the subject matter, not merely fewer passages.
   The fix is the full-corpus load with `scripts/data/embed_full_to_qdrant.py`;
   it is paused (no Hugging Face transfers for now), with fiqh at 365,824 of
   2,397,988 rows.
3. **Unwired scaffolding:** several modules are imported only by their own
   package, never by a request path: `src/indexing/vectorstores` FAISS/Chroma
   branches, `src/indexing/lexical/tantivy_index.py`, `bm25_index.py`,
   `src/indexing/embeddings/e5.py`, `bge_m3.py`, `src/retrieval/planning/`,
   `src/retrieval/policies/`, `src/indexing/pipelines/ingest_athar.py`, and
   `sync_metadata.py`. Treat them as unimplemented design notes, not features.
4. **Heuristic verification:** `contradiction_detector` and the quote checkers
   are string heuristics. They catch mechanical failures (a negated statement
   against an affirming passage, a fabricated quote), not semantic ones.
   `contradiction_detector` runs with `fail_policy="proceed"`, so a hit marks
   the answer unverified even though the answer is still returned.
5. **No frontend in this repository:** the API is the only deliverable here.

## Verification Commands

```bash
ruff check src tests
mypy src
pytest -q
Get-Content migrations\versions\003_align_unique_constraint_names.sql -Raw |
  docker exec -i Burhan-postgres psql -U Burhan -d Burhan_db -v ON_ERROR_STOP=1
python scripts/data/embed_mini_v2_to_qdrant.py --all --device cuda --half
python scripts/data/embed_duas_to_qdrant.py
python scripts/data/seed_tafsir_data.py --dry-run
python scripts/ingestion/import_azkar_db.py
```

Live probes used for this snapshot:

```bash
curl -s http://localhost:8000/ready
curl -s http://localhost:8000/api/v1/quran/tafsir/2:255
curl -s http://localhost:8000/api/v1/search/stats
curl -s -X POST http://localhost:8000/api/v1/tools/duas \
  -H "Content-Type: application/json" \
  -d '{"query": "أدعية الصباح", "limit": 3}'
curl -s -X POST http://localhost:8000/api/v1/tools/zakat \
  -H "Content-Type: application/json" \
  -d '{"assets": {"cash": 10000, "gold_grams": 50, "silver_grams": 500, "trade_goods": 5000, "stocks": 20000}}'
curl -s -X POST http://localhost:8000/api/v1/ask \
  -H "Content-Type: application/json" \
  -d '{"query": "ما هي أدعية الصباح؟", "language": "ar"}'
```
