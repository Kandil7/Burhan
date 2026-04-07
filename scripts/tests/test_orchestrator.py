import asyncio
from src.core.orchestrator import ResponseOrchestrator
from src.config.intents import Intent

async def test():
    orch = ResponseOrchestrator()
    print(f"Registry agents: {list(orch.registry.agents.keys())}")
    print(f"Registry tools: {list(orch.registry.tools.keys())}")
    print(f"Registry initialized: {orch.registry._initialized}")
    
    # Test greeting lookup
    instance, is_agent = orch.registry.get_for_intent(Intent.GREETING)
    print(f"Greeting lookup: instance={instance is not None}, is_agent={is_agent}")
    
    # Test direct chatbot_agent lookup
    agent = orch.registry.get_agent("chatbot_agent")
    print(f"Direct chatbot_agent lookup: {agent is not None}")
    
    # Try routing a query
    result = await orch.route_query("السلام عليكم", Intent.GREETING, language="ar")
    print(f"\nRoute result: intent={result.intent if hasattr(result, 'intent') else 'N/A'}")
    print(f"Answer: {result.answer[:100] if hasattr(result, 'answer') else 'N/A'}")

asyncio.run(test())
