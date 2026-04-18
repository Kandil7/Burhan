
import asyncio
from src.application.router.classifier_factory import classifier_factory
from src.application.router.router_agent import RouterAgent

async def main():
    print(f"Factory instance: {classifier_factory}")
    classifier = classifier_factory.create_default()
    print(f"Created classifier: {classifier}")
    print(f"Has classify: {hasattr(classifier, 'classify')}")
    
    router = RouterAgent(classifier=classifier)
    print(f"Router classifier: {router.classifier}")
    
    try:
        await router.route("test")
        print("Route success")
    except Exception as e:
        print(f"Route fail: {e}")

if __name__ == "__main__":
    asyncio.run(main())
