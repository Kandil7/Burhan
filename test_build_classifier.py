#!/usr/bin/env python3
"""Test the classifier factory directly in a clean environment."""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.application.classifier_factory import build_classifier

# Test with no embedding model
classifier = build_classifier(embedding_model=None)
print(f"Classifier type: {type(classifier).__name__}")
print(f"Has _embedding_classifier: {hasattr(classifier, '_embedding_classifier')}")
print(f"_embedding_classifier value: {classifier._embedding_classifier}")

import asyncio


async def test():
    result = await classifier.classify("صلاة")
    print(f"Result: intent={result.intent.value}, confidence={result.confidence}, method={result.method}")


asyncio.run(test())
