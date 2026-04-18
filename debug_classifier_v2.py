
import asyncio
from src.application.classifier_factory import build_classifier
from src.application.router.router_agent import RouterAgent

async def main():
    classifier = build_classifier()
    print(f"Created classifier: {classifier}")
    print(f"Has classify: {hasattr(classifier, 'classify')}")
    
    router = RouterAgent(classifier=classifier)
    print(f"Router classifier: {router.classifier}")
    
    try:
        decision = await router.route("ما حكم الصيام؟")
        print(f"Route success: {decision.route}")
        print(f"Intent: {decision.result.intent}")
    except Exception as e:
        print(f"Route fail: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
