#!/usr/bin/env python3
"""Minimal test to verify the fix works."""

import sys
import asyncio
import os
import io

# Fix Windows encoding
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

sys.path.insert(0, ".")

# Import directly from the canonical module
from src.application.router.classifier_factory import (
    KeywordBasedClassifier,
    MasterHybridClassifier,
)


async def main():
    print("=" * 50)
    print("Testing KeywordBasedClassifier directly")
    print("=" * 50)

    # Create keyword-only classifier
    classifier = KeywordBasedClassifier()

    # Test queries
    test_queries = [
        "صلاة",  # prayer
        "ما حكم الصلاة؟",  # what is the ruling on prayer?
        "زكاة",  # charity
        "حج",  # pilgrimage
        "غزوة بدر",  # battle of Badr
        "هجرة",  # hijra
    ]

    for query in test_queries:
        result = await classifier.classify(query)
        print(f"\nQuery: {query}")
        print(f"  Intent: {result.intent.value}")
        print(f"  Confidence: {result.confidence}")
        print(f"  Method: {result.method}")
        print(f"  Reasoning: {result.reasoning}")

    print("\n" + "=" * 50)
    print("Testing MasterHybridClassifier")
    print("=" * 50)

    # Create hybrid classifier without embedding
    hybrid = MasterHybridClassifier(embedding_model=None)

    for query in test_queries:
        result = await hybrid.classify(query)
        print(f"\nQuery: {query}")
        print(f"  Intent: {result.intent.value}")
        print(f"  Confidence: {result.confidence}")
        print(f"  Method: {result.method}")

    print("\nDone!")


asyncio.run(main())
