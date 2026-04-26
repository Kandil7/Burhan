#!/usr/bin/env python3
"""Test exactly what the API does."""

import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


async def test():
    print("=== Testing API flow ===")

    # Step 1: Import build_classifier like the API does
    from src.application.classifier_factory import build_classifier

    # Step 2: Create a mock embedding model (simulating what API does)
    class MockEmbeddingModel:
        pass

    embedding_model = MockEmbeddingModel()
    print(f"Created mock embedding model: {embedding_model}")

    # Step 3: Build classifier like the API does
    classifier = build_classifier(embedding_model=embedding_model)
    print(f"Built classifier: {type(classifier).__name__}")
    print(f"  - has _embedding_classifier: {hasattr(classifier, '_embedding_classifier')}")
    if hasattr(classifier, "_embedding_classifier"):
        print(f"  - _embedding_classifier: {classifier._embedding_classifier}")

    # Step 4: Classify a query
    result = await classifier.classify("صلاة")
    print(f"Result: intent={result.intent}, confidence={result.confidence}, method={result.method}")


if __name__ == "__main__":
    asyncio.run(test())
