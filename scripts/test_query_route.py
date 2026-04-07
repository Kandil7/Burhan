import asyncio
import sys
sys.path.insert(0, '.')

# Simulate FastAPI import order
from src.api.routes.query import get_orchestrator, router
from src.config.intents import Intent

async def test():
    print("Getting orchestrator via get_orchestrator()...")
    orch = get_orchestrator()
    print(f"Agents: {list(orch.registry.agents.keys())}")
    print(f"Tools: {list(orch.registry.tools.keys())}")
    
    # Test lookup
    instance, is_agent = orch.registry.get_for_intent(Intent.GREETING)
    print(f"Greeting lookup: found={instance is not None}")
    
    # Route a query
    result = await orch.route_query("السلام عليكم", Intent.GREETING, language="ar")
    print(f"Answer: {result.answer[:100] if hasattr(result, 'answer') else 'N/A'}")

asyncio.run(test())
