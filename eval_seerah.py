#!/usr/bin/env python3
"""
RAG Evaluation Script for Seerah Passages - Fixed Version

Loads evaluation data from JSONL file and tests against Burhan API.

Usage:
    python eval_seerah.py                    # Run against localhost:8002
    python eval_seerah.py --url http://localhost:8000  # Custom URL
    python eval_seerah.py --k 5                   # Custom top-k
"""

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Set

# Fix Windows console encoding for emojis
if sys.platform == "win32":
    import io

    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

import pandas as pd
import requests
from tqdm import tqdm

# Default API endpoint - correct v1 path
API_URL = "http://localhost:8002/api/v1/ask"
HEADERS = {"accept": "application/json", "Content-Type": "application/json"}


def load_golden_set(jsonl_path: str) -> List[Dict]:
    """Load evaluation data from JSONL file."""
    data = []
    with open(jsonl_path, encoding="utf-8") as f:
        for line in f:
            if line.strip():
                data.append(json.loads(line))
    return data


def query_rag(question: str, url: str = API_URL) -> Dict[str, Any]:
    """Send question to the RAG API and return the response."""
    payload = {"query": question}
    try:
        resp = requests.post(url, headers=HEADERS, json=payload, timeout=60)
        resp.raise_for_status()
        data = resp.json()
        # Add processing time from headers if available
        data["_raw_processing_time"] = float(resp.headers.get("x-process-time-ms", 0))
        return data
    except requests.exceptions.RequestException as e:
        return {"error": str(e), "query": question}


def extract_retrieved_ids(response: Dict) -> Set:
    """Extract (source_id, page) tuples from the API response citations."""
    retrieved = set()

    if "error" in response:
        return retrieved

    citations = response.get("citations", [])
    for c in citations:
        if not isinstance(c, dict):
            continue

        # The API returns: source_id, page (not metadata)
        source_id = c.get("source_id", "")
        page = c.get("page", "")

        if source_id:
            if page:
                retrieved.add((str(source_id), str(page)))
            else:
                retrieved.add((str(source_id), None))

    return retrieved


def build_gold_set(gold_passages: List[Dict]) -> Set:
    """Build set of (book_id, page_number) tuples from gold passages."""
    gold = set()
    for g in gold_passages:
        book_id = str(g.get("book_id", ""))
        page_number = g.get("page_number")
        if page_number:
            gold.add((book_id, str(page_number)))
        elif book_id:
            gold.add((book_id, None))
    return gold


def evaluate_response(response: Dict, gold_passages: List[Dict], k: int = 10) -> Dict[str, Any]:
    """Calculate metrics for a single response."""
    if "error" in response:
        return {
            "hit_rate": 0,
            "precision": 0,
            "mrr": 0,
            "citations": 0,
            "retrieved_ids": [],
            "error": response.get("error", "Unknown error"),
        }

    retrieved = extract_retrieved_ids(response)
    gold = build_gold_set(gold_passages)

    if not retrieved:
        return {"hit_rate": 0, "precision": 0, "mrr": 0, "citations": 0, "retrieved_ids": []}

    # Hit Rate: At least one gold passage retrieved?
    hit = 1 if any(r in gold for r in retrieved) else 0

    # Precision: Ratio of correct citations
    correct = sum(1 for r in retrieved if r in gold)
    precision = correct / len(retrieved) if retrieved else 0

    # MRR: Position of first correct hit
    mrr = 0
    retrieved_list = list(retrieved)
    for i, r in enumerate(retrieved_list, 1):
        if r in gold:
            mrr = 1 / i
            break

    return {
        "hit_rate": hit,
        "precision": precision,
        "mrr": mrr,
        "citations": len(retrieved),
        "retrieved_ids": list(retrieved),
    }


def main():
    parser = argparse.ArgumentParser(description="RAG Evaluation for Seerah Passages")
    parser.add_argument("--url", default=API_URL, help="API URL")
    parser.add_argument("--k", type=int, default=10, help="Top-k to consider")
    parser.add_argument("--output", default="eval_results.csv", help="Output CSV file")
    parser.add_argument("--delay", type=float, default=0.5, help="Delay between requests (seconds)")
    parser.add_argument("--data", default="src/evaluation/seerah_real_user_eval.jsonl", help="Input JSONL file")
    args = parser.parse_args()

    # Load evaluation data from JSONL
    data_path = Path(args.data)
    if not data_path.exists():
        print(f"Error: Data file not found: {args.data}", file=sys.stderr)
        sys.exit(1)

    eval_data = load_golden_set(str(data_path))
    print(f"Loaded {len(eval_data)} evaluation questions from {args.data}")
    print(f"API URL: {args.url}")
    print("-" * 50)

    results = []

    for item in tqdm(eval_data, desc="Evaluating"):
        time.sleep(args.delay)

        response = query_rag(item["query"], args.url)
        metrics = evaluate_response(response, item.get("gold_passages", []), args.k)

        retrieved = metrics.pop("retrieved_ids", [])

        # Extract gold book IDs
        gold_books = [str(g.get("book_id", "")) for g in item.get("gold_passages", [])]
        gold_pages = [str(g.get("page_number", "")) for g in item.get("gold_passages", []) if g.get("page_number")]

        results.append(
            {
                **metrics,
                "query": item["query"][:50] + "..." if len(item["query"]) > 50 else item["query"],
                "query_full": item["query"],
                "query_type": item.get("query_type", ""),
                "gold_books": gold_books,
                "gold_pages": gold_pages[:3],
                "retrieved": [r[0] + (f":{r[1]}" if r[1] else "") for r in retrieved[:5]],
                "intent": response.get("intent", "") if "error" not in response else "",
                "confidence": response.get("intent_confidence", 0) if "error" not in response else 0,
            }
        )

    # Save results
    df = pd.DataFrame(results)
    df.to_csv(args.output, index=False, encoding="utf-8-sig")

    # Print summary
    print("\n" + "=" * 50)
    print("EVALUATION RESULTS")
    print("=" * 50)
    print(f"Questions Tested: {len(eval_data)}")
    print(f"Hit Rate: {df['hit_rate'].mean():.1%}")
    print(f"Precision: {df['precision'].mean():.3f}")
    print(f"MRR: {df['mrr'].mean():.3f}")
    print(f"Avg Citations: {df['citations'].mean():.1f}")

    # Show some examples
    hits = df[df["hit_rate"] == 1]
    misses = df[df["hit_rate"] == 0]

    print(f"\nHits: {len(hits)} ({len(hits) / len(df) * 100:.1f}%)")
    print(f"Misses: {len(misses)} ({len(misses) / len(df) * 100:.1f}%)")

    if len(hits) > 0:
        print("\n✓ Sample Hit:")
        h = hits.iloc[0]
        print(f"  Query: {h['query']}")
        print(f"  Gold: {h['gold_pages']}")
        print(f"  Retrieved: {h['retrieved']}")

    if len(misses) > 0:
        print("\n✗ Sample Miss:")
        m = misses.iloc[0]
        print(f"  Query: {m['query']}")
        print(f"  Gold: {m['gold_pages']}")
        print(f"  Retrieved: {m['retrieved']}")

    print(f"\nResults saved to: {args.output}")
    print("Done!")


if __name__ == "__main__":
    main()
