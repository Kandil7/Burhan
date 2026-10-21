#!/usr/bin/env python3
"""Directly test the classifier to see what's happening."""

import asyncio
import sys
import os

# Add parent dir to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


async def test():
    print("Starting test...")

    # Import directly from the canonical module
    from src.application.router.classifier_factory import MasterHybridClassifier

    print("Creating classifier...")
    classifier = MasterHybridClassifier(embedding_model=None)

    print("Calling classify...")
    result = await classifier.classify("صلاة")

    print(f"Result: intent={result.intent}, confidence={result.confidence}, method={result.method}")
    print(f"Reasoning: {result.reasoning}")


if __name__ == "__main__":
    asyncio.run(test())
