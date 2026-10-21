import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.application.router.classifier_factory import MasterHybridClassifier, KeywordBasedClassifier


async def test():
    # Create keyword-only classifier
    classifier = KeywordBasedClassifier()

    # Test
    result = await classifier.classify("صلاة")
    print(f"Result for 'صلاة': {result.intent.value}, {result.confidence}, {result.method}")
    print(f"Reasoning: {result.reasoning}")

    result2 = await classifier.classify("ما حكم الصلاة؟")
    print(f"Result for 'ما حكم الصلاة؟': {result2.intent.value}, {result2.confidence}, {result2.method}")
    print(f"Reasoning: {result2.reasoning}")


asyncio.run(test())
