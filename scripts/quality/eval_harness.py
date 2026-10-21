#!/usr/bin/env python3
"""Evaluation harness for the Burhan retrieval and answer paths.

Two jobs, one question set.

``retrieve`` runs the retrieval strategies in process, so the point ids are
known, and writes the candidate list for every question. It is the input to
the dense versus keyword-rerank comparison.

``score`` compares a retrieval run against the curated ids in the question
set and reports precision at 5, recall at 10, and mean reciprocal rank.

``ask`` calls the running API for every question and writes the behavioural
fingerprint: intent, answer mode, collection, citation count, and source
names. It is the regression guard for a refactor, so it compares structure
rather than prose, because the language model is not deterministic.

Usage:
    python scripts/quality/eval_harness.py retrieve --mode dense --out run_dense.json
    python scripts/quality/eval_harness.py retrieve --mode keyword_rerank --out run_hybrid.json
    python scripts/quality/eval_harness.py score --run run_dense.json
    python scripts/quality/eval_harness.py ask --out baseline.json
    python scripts/quality/eval_harness.py compare --current run_dense.json --baseline baseline.json
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

DEFAULT_QUESTIONS = PROJECT_ROOT / "scripts" / "quality" / "golden_set.json"
DEFAULT_API = "http://localhost:8000"


# ── Question set ────────────────────────────────────────────────────────


def load_questions(path: Path) -> list[dict[str, Any]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    return data["items"] if isinstance(data, dict) else data


def snippet(hit: dict[str, Any], limit: int = 110) -> str:
    """Short preview of a passage, for judging relevance by eye."""
    metadata = hit.get("metadata") or {}
    text = str(hit.get("content") or "").replace("\r", " ").replace("\n", " ").strip()
    title = str(metadata.get("section_title") or metadata.get("book_title") or "")
    return f"{title} | {text[:limit]}"


# ── Retrieval ───────────────────────────────────────────────────────────


async def build_store() -> Any:
    from src.indexing.embeddings.embedding_model import EmbeddingModel
    from src.indexing.vectorstores.qdrant_store import VectorStore

    encoder = EmbeddingModel(cache_enabled=False)
    await encoder.load_model()
    try:
        import torch

        if torch.cuda.is_available():
            encoder.model.to("cuda")
            encoder.model.half()
    except Exception:  # noqa: BLE001 - the harness also runs on cpu
        pass
    print(f"encoder on {next(encoder.model.parameters()).device}", flush=True)

    store = VectorStore()
    await store.initialize()
    return encoder, store


async def run_retrieval(
    questions: list[dict[str, Any]],
    mode: str,
    top_k: int,
) -> list[dict[str, Any]]:
    from src.retrieval.retrievers.hybrid_searcher import HybridSearcher

    encoder, store = await build_store()
    searcher = HybridSearcher(store)

    results: list[dict[str, Any]] = []
    for item in questions:
        collection = item["collection"]
        started = time.time()
        embedding = await encoder.encode_query(item["question"])

        if mode == "dense":
            hits = await store.search(collection, embedding, top_k=top_k)
        elif mode == "keyword_rerank":
            hits = await searcher.search(item["question"], embedding, collection, top_k=top_k)
        else:
            raise SystemExit(f"unknown mode: {mode}")

        results.append(
            {
                "id": item["id"],
                "question": item["question"],
                "collection": collection,
                "mode": mode,
                "elapsed_ms": int((time.time() - started) * 1000),
                "results": [
                    {
                        "id": hit.get("id"),
                        "score": round(float(hit.get("score") or 0.0), 4),
                        "snippet": snippet(hit),
                    }
                    for hit in hits
                ],
            }
        )
        print(
            f"  {item['id']:<14} {collection:<26} {len(hits):>3} hits ({results[-1]['elapsed_ms']} ms)",
            flush=True,
        )
    return results


# ── Scoring ─────────────────────────────────────────────────────────────


def score_run(run: list[dict[str, Any]], questions: list[dict[str, Any]]) -> dict[str, Any]:
    """Compare a retrieval run against the curated ids.

    Two measures. The strict one asks whether the passages that answer the
    question were retrieved, and it only runs for questions that have such
    passages. The topic one asks whether passages on the subject were
    retrieved, and it runs for every question that has them. The count of
    questions with no topic evidence is reported too, because a question the
    corpus cannot answer is a corpus finding.
    """
    by_id = {item["id"]: item for item in questions}
    per_item: list[dict[str, Any]] = []
    strict_precision = strict_recall = strict_reciprocal = 0.0
    topic_precision = topic_recall = 0.0
    strict_scored = topic_scored = 0
    without_topic: list[str] = []
    per_collection: dict[str, list[int]] = {}

    for entry in run:
        item = by_id.get(entry["id"], {})
        collection = entry.get("collection", "?")
        retrieved = [str(hit["id"]) for hit in entry["results"] if hit.get("id") is not None]
        gold = {str(value) for value in item.get("relevant_ids") or []}
        topic = {str(value) for value in item.get("topic_ids") or []}

        record: dict[str, Any] = {"id": entry["id"], "collection": collection}

        if gold:
            strict_scored += 1
            hits5 = len([value for value in retrieved[:5] if value in gold])
            hits_all = len([value for value in retrieved if value in gold])
            precision = hits5 / len(retrieved[:5]) if retrieved[:5] else 0.0
            recall = hits_all / len(gold)
            rank = next((i + 1 for i, value in enumerate(retrieved) if value in gold), 0)
            reciprocal = 1.0 / rank if rank else 0.0
            strict_precision += precision
            strict_recall += recall
            strict_reciprocal += reciprocal
            record.update(
                {
                    "gold": len(gold),
                    "precision_at_5": round(precision, 4),
                    "recall_at_10": round(recall, 4),
                    "reciprocal_rank": round(reciprocal, 4),
                    "first_relevant_rank": rank,
                }
            )
        else:
            record["gold"] = 0
            record["skipped"] = True

        if topic:
            topic_scored += 1
            topic_hits5 = len([value for value in retrieved[:5] if value in topic])
            topic_hits_all = len([value for value in retrieved if value in topic])
            t_precision = topic_hits5 / len(retrieved[:5]) if retrieved[:5] else 0.0
            t_recall = topic_hits_all / len(topic)
            topic_precision += t_precision
            topic_recall += t_recall
            record["topic_precision_at_5"] = round(t_precision, 4)
            record["topic_recall_at_10"] = round(t_recall, 4)
            bucket = per_collection.setdefault(collection, [])
            bucket.append(1 if t_precision >= 0.5 else 0)
        else:
            without_topic.append(entry["id"])

        per_item.append(record)

    summary = {
        "strict_scored_items": strict_scored,
        "precision_at_5": round(strict_precision / strict_scored, 4) if strict_scored else 0.0,
        "recall_at_10": round(strict_recall / strict_scored, 4) if strict_scored else 0.0,
        "mrr": round(strict_reciprocal / strict_scored, 4) if strict_scored else 0.0,
        "topic_scored_items": topic_scored,
        "topic_precision_at_5": round(topic_precision / topic_scored, 4) if topic_scored else 0.0,
        "topic_recall_at_10": round(topic_recall / topic_scored, 4) if topic_scored else 0.0,
        "questions_without_topic_evidence": without_topic,
        "per_collection_topic_hit_rate": {
            collection: round(sum(values) / len(values), 4) for collection, values in sorted(per_collection.items())
        },
    }
    return {"summary": summary, "items": per_item}


# ── End to end fingerprint ──────────────────────────────────────────────


def call_api(path: str, payload: dict[str, Any], api: str, timeout: int = 300) -> tuple[int, Any]:
    request = urllib.request.Request(
        f"{api}{path}",
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return response.status, json.loads(response.read().decode("utf-8") or "{}")
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8")
        try:
            return exc.code, json.loads(raw or "{}")
        except json.JSONDecodeError:
            return exc.code, {"detail": raw[:200]}


def run_ask(questions: list[dict[str, Any]], api: str) -> dict[str, Any]:
    """Capture the behavioural fingerprint of the running API."""
    entries: list[dict[str, Any]] = []
    for item in questions:
        started = time.time()
        code, payload = call_api("/api/v1/ask", {"query": item["question"]}, api)
        metadata = payload.get("metadata") or {}
        citations = payload.get("citations") or []
        entries.append(
            {
                "id": item["id"],
                "question": item["question"],
                "code": code,
                "intent": payload.get("intent"),
                "answer_mode": metadata.get("answer_mode") or payload.get("answer_mode"),
                "collection": metadata.get("collection"),
                "citation_count": len(citations),
                "sources": sorted(
                    {str(citation.get("source_name") or citation.get("book_title") or "") for citation in citations}
                ),
                "requires_human_review": payload.get("requires_human_review"),
                "elapsed_ms": int((time.time() - started) * 1000),
            }
        )
        print(
            f"  {item['id']:<14} {entries[-1]['answer_mode']:<8} "
            f"{entries[-1]['collection'] or '-':<26} {entries[-1]['citation_count']:>3} citations",
            flush=True,
        )

    modes: dict[str, int] = {}
    for entry in entries:
        modes[str(entry["answer_mode"])] = modes.get(str(entry["answer_mode"]), 0) + 1
    return {
        "created_at": time.strftime("%Y-%m-%d"),
        "items": entries,
        "mode_distribution": modes,
    }


def run_route(questions: list[dict[str, Any]], api: str) -> dict[str, Any]:
    """Classify every question and check the intent against the expectation.

    A question can be served by more than one collection. A hadith question
    that is really a ruling question belongs in fiqh, and a question about the
    Hijra belongs in Seerah as much as in history. The expectation therefore
    lists the acceptable intents, and the question counts as routed when the
    classifier lands on one of them.
    """
    entries: list[dict[str, Any]] = []
    for item in questions:
        accepted = set(item.get("acceptable_intents") or [item.get("intent")])
        code, payload = call_api("/classify", {"query": item["question"]}, api)
        result = payload.get("result") or {}
        intent = result.get("intent")
        entries.append(
            {
                "id": item["id"],
                "question": item["question"],
                "code": code,
                "intent": intent,
                "confidence": result.get("confidence"),
                "method": result.get("method"),
                "expected": sorted(accepted),
                "routed_ok": intent in accepted,
            }
        )
        mark = "ok" if entries[-1]["routed_ok"] else "MISMATCH"
        print(f"  {item['id']:<14} {str(intent):<20} expected {sorted(accepted)}  {mark}", flush=True)

    correct = sum(1 for entry in entries if entry["routed_ok"])
    return {
        "created_at": time.strftime("%Y-%m-%d"),
        "routed_correct": correct,
        "routed_total": len(entries),
        "routing_accuracy": round(correct / len(entries), 4) if entries else 0.0,
        "items": entries,
    }


def compare_fingerprints(current: dict[str, Any], baseline: dict[str, Any]) -> dict[str, Any]:
    """Compare two fingerprints and list the differences."""
    base_items = {entry["id"]: entry for entry in baseline.get("items", [])}
    differences: list[dict[str, Any]] = []
    for entry in current.get("items", []):
        base = base_items.get(entry["id"])
        if base is None:
            continue
        changed = {
            key: {"baseline": base.get(key), "current": entry.get(key)}
            for key in ("intent", "answer_mode", "collection", "citation_count", "sources")
            if base.get(key) != entry.get(key)
        }
        if changed:
            differences.append({"id": entry["id"], "changed": changed})
    return {
        "compared": len(current.get("items", [])),
        "differences": differences,
        "identical": not differences,
    }


# ── CLI ─────────────────────────────────────────────────────────────────


def main() -> int:
    parser = argparse.ArgumentParser(description="Burhan evaluation harness")
    parser.add_argument("command", choices=["retrieve", "score", "ask", "route", "compare"])
    parser.add_argument("--questions", default=str(DEFAULT_QUESTIONS))
    parser.add_argument("--mode", default="dense", choices=["dense", "keyword_rerank"])
    parser.add_argument("--top-k", type=int, default=10)
    parser.add_argument("--out", help="Write the result to this file")
    parser.add_argument("--run", help="Retrieval run to score")
    parser.add_argument("--current", help="Current fingerprint")
    parser.add_argument("--baseline", help="Baseline fingerprint")
    parser.add_argument("--api", default=DEFAULT_API)
    args = parser.parse_args()

    questions = load_questions(Path(args.questions))

    if args.command == "retrieve":
        run = asyncio.run(run_retrieval(questions, args.mode, args.top_k))
        payload = {"mode": args.mode, "items": run}
    elif args.command == "score":
        run = json.loads(Path(args.run).read_text(encoding="utf-8"))
        items = run["items"] if isinstance(run, dict) else run
        payload = score_run(items, questions)
        for item in payload["items"]:
            if not item.get("skipped"):
                print(
                    f"  {item['id']:<14} p@5 {item['precision_at_5']:<7} "
                    f"r@10 {item['recall_at_10']:<7} first hit at {item['first_relevant_rank']}"
                )
        print(json.dumps(payload["summary"], indent=1))
    elif args.command == "ask":
        payload = run_ask(questions, args.api)
    elif args.command == "route":
        payload = run_route(questions, args.api)
        print(
            f"\nrouting accuracy {payload['routed_correct']}/{payload['routed_total']} ({payload['routing_accuracy']})"
        )
    else:
        current = json.loads(Path(args.current).read_text(encoding="utf-8"))
        baseline = json.loads(Path(args.baseline).read_text(encoding="utf-8"))
        payload = compare_fingerprints(current, baseline)
        print(json.dumps(payload, ensure_ascii=False, indent=1)[:4000])

    if args.out:
        Path(args.out).write_text(json.dumps(payload, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
        print(f"written to {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
