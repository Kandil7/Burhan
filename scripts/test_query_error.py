"""Test script to reproduce the query endpoint error with full traceback."""
import asyncio
import sys
import traceback

# Add project root to path
sys.path.insert(0, r"K:\business\projects_v2\Athar")

from src.config.settings import settings

async def test_query():
    """Test the full query pipeline."""
    print("=" * 80)
    print("TESTING QUERY PIPELINE")
    print("=" * 80)
    
    # Step 1: Import and setup
    print("\n[1] Setting up logging...")
    from src.config.logging_config import setup_logging
    setup_logging()
    
    # Step 2: Initialize registry
    print("\n[2] Initializing registry...")
    from src.core.registry import initialize_registry
    registry = initialize_registry()
    print(f"  Agents: {registry.list_agents()}")
    print(f"  Tools: {registry.list_tools()}")
    
    # Step 3: Get classifier
    print("\n[3] Getting classifier...")
    from src.core.router import HybridQueryClassifier
    from src.infrastructure.llm_client import get_llm_client
    llm_client = await get_llm_client()
    classifier = HybridQueryClassifier(llm_client=llm_client)
    
    # Step 4: Classify intent
    print("\n[4] Classifying intent for 'ما حكم الصلاة'...")
    query = "ما حكم الصلاة"
    result = await classifier.classify(query)
    print(f"  Intent: {result.intent}")
    print(f"  Confidence: {result.confidence}")
    print(f"  Method: {result.method}")
    
    # Step 5: Get agent for intent
    print("\n[5] Getting agent for intent...")
    agent, is_agent = registry.get_for_intent(result.intent)
    print(f"  Agent: {agent}")
    print(f"  Is Agent: {is_agent}")
    
    if agent:
        # Step 6: Execute agent
        print("\n[6] Executing agent...")
        from src.agents.base import AgentInput
        agent_input = AgentInput(
            query=query,
            language=result.language,
            metadata={"madhhab": None, "filters": None, "hierarchical": False}
        )
        
        try:
            agent_result = await agent.execute(agent_input)
            print(f"  Answer: {agent_result.answer[:100]}...")
            print(f"  Citations: {len(agent_result.citations)}")
            print(f"  Metadata: {agent_result.metadata}")
        except Exception as e:
            print(f"\n{'='*80}")
            print(f"ERROR: {type(e).__name__}: {e}")
            print(f"{'='*80}")
            tb = traceback.format_exc()
            print(tb)
            return

    print("\n" + "=" * 80)
    print("TEST COMPLETED SUCCESSFULLY")
    print("=" * 80)

if __name__ == "__main__":
    asyncio.run(test_query())
