#!/usr/bin/env python3
"""
RAG Evaluation Script for Seerah Passages
Tests the 20 questions against the Athar API and calculates metrics.

Usage:
    python rag_eval_seerah.py                    # Run against localhost:8002
    python rag_eval_seerah.py --url http://localhost:8000  # Custom URL
    python rag_eval_seerah.py --k 5                   # Custom top-k
"""

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Any, Dict, List

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

# The 20 evaluation questions from the eval plan
EVAL_DATA = [
    {"query": "ما الحدث التاريخي الذي تدور حوله الفقرة الأولى؟", "gold_passages": [{"book_id": 77, "page_number": 1}]},
    {
        "query": "ما النص الذي أورده الكاتب عند دخول النبي المدينة؟",
        "gold_passages": [{"book_id": 77, "page_number": 1}],
    },
    {"query": "ما وصف الكاتب لأثر الهجرة على التاريخ؟", "gold_passages": [{"book_id": 77, "page_number": 2}]},
    {"query": "لماذا اعتنى المسلمون بسيرة النبي؟", "gold_passages": [{"book_id": 77, "page_number": 2}]},
    {"query": "ما الغاية من ذكرى الهجرة اليوم؟", "gold_passages": [{"book_id": 77, "page_number": 2}]},
    {"query": "متى بدأت الهجرة النبوية؟", "gold_passages": [{"book_id": 77, "page_number": 2}]},
    {"query": "من أمر بجعل الهجرة بداية التقويم؟", "gold_passages": [{"book_id": 77, "page_number": 2}]},
    {"query": "ما اسم المدينة التي هاجر إليها النبي؟", "gold_passages": [{"book_id": 77, "page_number": 2}]},
    {"query": "ما القيم الاجتماعية في الحديث المذكور؟", "gold_passages": [{"book_id": 77, "page_number": 1}]},
    {"query": "ما الشاهد الشعري عن الزهد في الدنيا؟", "gold_passages": [{"book_id": 77, "page_number": 1}]},
    {"query": "ما وصف بيان النبي عند دخوله المدينة؟", "gold_passages": [{"book_id": 77, "page_number": 1}]},
    {"query": "ما مكانة النبي بين الخلق؟", "gold_passages": [{"book_id": 77, "page_number": 2}]},
    {"query": "ما العلاقة بين السيرة وحل المشاكل؟", "gold_passages": [{"book_id": 77, "page_number": 2}]},
    {"query": "ما الحديث عن الدنيا والآخرة؟", "gold_passages": [{"book_id": 77, "page_number": 1}]},
    {"query": "من هو محمد مهدي قشلان؟", "gold_passages": [{"book_id": 77}]},
    {"query": "ما فئة النصوص في المجموعة؟", "gold_passages": [{"book_id": 77}]},
    {"query": "ما اسم الكتاب الأول؟", "gold_passages": [{"book_id": 77}]},
    {"query": "في أي صفحة بدأت عبرة الهجرة الأولى؟", "gold_passages": [{"book_id": 77, "page_number": 1}]},
    {"query": "ما العنوان الفرعي للصفحة الثانية؟", "gold_passages": [{"book_id": 77, "page_number": 2}]},
    {"query": "ما الهدف من خطبة المدينة؟", "gold_passages": [{"book_id": 77, "page_number": 1}]},
]


def query_rag(question: str, url: str = API_URL) -> Dict[str, Any]:
    """Send question to the RAG API and return the response."""
    payload = {"query": question}
    try:
        resp = requests.post(url, headers=HEADERS, json=payload, timeout=30)
        resp.raise_for_status()
        return resp.json()
    except requests.exceptions.RequestException as e:
        return {"error": str(e), "query": question}


def extract_retrieved_ids(response: Dict) -> set:
    """Extract (book_id, page_number) tuples from the response citations."""
    retrieved = set()
    categories = set()

    if "error" in response:
        return retrieved

    citations = response.get("citations", [])
    for c in citations:
        if not isinstance(c, dict):
            continue

        # Try different field names the API actually uses
        # source_id first (most common)
        source_id = c.get("source_id", "")

        # page or page_number
        page = c.get("page") or c.get("page_number") or c.get("page", "")

        # Collection/category for seerah
        collection = c.get("collection", "")

        if source_id:
            if page:
                retrieved.add((str(source_id), str(page)))
            else:
                retrieved.add((str(source_id), None))

        # Collect category for matching
        if c.get("category"):
            categories.add(c["category"])
        if collection:
            categories.add(collection)

    # Also check source_id directly in citation
    for c in citations:
        if isinstance(c, dict) and c.get("source_id"):
            retrieved.add(str(c.get("source_id")))

    return retrieved


def build_gold_set(gold_passages: List[Dict]) -> set:
    """Build set of (book_id, page_number) tuples from gold passages."""
    gold = set()
    for g in gold_passages:
        book_id = str(g.get("book_id", ""))
        page_number = g.get("page_number")
        if page_number:
            gold.add((book_id, str(page_number)))
        elif book_id:
            gold.add((book_id, None))  # Book-only match

    # If looking for book 77 (الهجرة النبوية), also check for seerah category
    has_book_77 = any("77" in str(g.get("book_id", "")) for g in gold_passages)
    if has_book_77:
        gold.add(("seerah_category", None))

    return gold


def evaluate_response(response: Dict, gold_passages: List[Dict], k: int = 10) -> Dict[str, Any]:
    """Calculate metrics for a single response."""
    if "error" in response:
        return {"hit_rate": 0, "precision": 0, "mrr": 0, "citations": 0, "error": response["error"]}

    retrieved = extract_retrieved_ids(response)
    gold = build_gold_set(gold_passages)

    if not retrieved:
        return {"hit_rate": 0, "precision": 0, "mrr": 0, "citations": 0}

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
    parser.add_argument("--output", default="rag_eval_results.csv", help="Output CSV file")
    parser.add_argument("--delay", type=float, default=0.5, help="Delay between requests (seconds)")
    args = parser.parse_args()

    results = []

    print(f"\n🧪 Running evaluation on {len(EVAL_DATA)} questions...")
    print(f"📡 API: {args.url}")

    for i, item in enumerate(tqdm(EVAL_DATA, desc="Testing")):
        time.sleep(args.delay)  # Rate limiting

        response = query_rag(item["query"], args.url)
        metrics = evaluate_response(response, item["gold_passages"], args.k)

        retrieved = metrics.pop("retrieved_ids", [])

        results.append(
            {
                **metrics,
                "query": item["query"][:60] + "...",
                "query_full": item["query"],
                "gold_books": [str(g["book_id"]) for g in item["gold_passages"]],
                "retrieved_books": [r[0] for r in retrieved],
                "intent": response.get("intent"),
                "confidence": response.get("intent_confidence", 0),
                "processing_time": response.get("metadata", {}).get("processing_time_ms", 0)
                if "error" not in response
                else 0,
            }
        )

    # Save results
    df = pd.DataFrame(results)
    df.to_csv(args.output, index=False, encoding="utf-8-sig")

    # Print summary
    print("\n" + "=" * 60)
    print("📊 RESULTS SUMMARY - Seerah RAG Evaluation")
    print("=" * 60)
    print(f"Questions Tested: {len(EVAL_DATA)}")
    print(f"Hit Rate: {df['hit_rate'].mean():.1%}")
    print(f"Precision: {df['precision'].mean():.3f}")
    print(f"MRR (Mean Reciprocal Rank): {df['mrr'].mean():.3f}")
    print(f"Citations/Question: {df['citations'].mean():.1f}")
    print(f"Intent Accuracy: {df[df['intent'] == 'seerah'].shape[0] / len(df):.1%}")
    print(f"Avg Intent Confidence: {df['confidence'].mean():.3f}")
    print(f"Avg Processing Time: {df['processing_time'].mean():.0f}ms")

    # Top/Bottom performers
    print("\n🏆 Top 5 Questions:")
    top5 = df.nlargest(5, "precision")[["query", "precision", "hit_rate"]]
    for _, row in top5.iterrows():
        print(f"  • {row['query'][:50]} | P={row['precision']:.2f}")

    print("\n❌ Bottom 5 Questions:")
    bot5 = df.nsmallest(5, "precision")[["query", "precision", "hit_rate"]]
    for _, row in bot5.iterrows():
        print(f"  • {row['query'][:50]} | P={row['precision']:.2f}")

    print(f"\n💾 Results saved to: {args.output}")
    print("✅ Done!")

    return df


if __name__ == "__main__":
    main()
