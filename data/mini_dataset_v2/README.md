# Mini Dataset v2 (local cache)

The JSONL payload files in this directory are **not tracked in Git**. The
repository policy keeps large datasets out of Git (`AGENTS.md`, storage
policy); only `stats.json` remains tracked.

## What this is

Ten sampled collections (~230 MB total) used by
`scripts/data/embed_mini_v2_to_qdrant.py` to fill the six collections the
Hub's precomputed-embedding dump does not cover:

| File (per collection) | Hub copy available |
| --- | --- |
| aqeedah_passages.jsonl | yes |
| arabic_language_passages.jsonl | yes |
| fiqh_passages.jsonl | yes |
| general_islamic.jsonl | yes |
| hadith_passages.jsonl | yes |
| islamic_history_passages.jsonl | yes |
| quran_tafsir.jsonl | yes |
| seerah_passages.jsonl | yes |
| spirituality_passages.jsonl | yes |
| usul_fiqh.jsonl | **no** (needs the local file, or skip: the full corpus is loaded) |

The loader downloads a missing file automatically from the Hub dataset
[`Kandil7/Athar-Mini-Dataset-v2`](https://huggingface.co/datasets/Kandil7/Athar-Mini-Dataset-v2).

`stats.json` records how many rows and how many characters per collection the
sample holds, so you can verify a fetch without opening the files.

## Regenerating from scratch

`scripts/data/create_mini_dataset_v2.py` rebuilds the samples from
`data/processed/` catalogs. The v1 generator (`create_mini_dataset.py`) is
kept for history only; the `data/mini_dataset/` directory it wrote is
untracked and ignored.
