import asyncio
import sys
sys.path.insert(0, '.')

from src.agents.sanadset_hadith_agent import SanadsetHadithAgent
from src.agents.base import AgentInput

async def test():
    print("=== Testing SanadsetHadithAgent ===\n")
    
    agent = SanadsetHadithAgent()
    await agent.initialize()
    
    print(f"Initialized: {agent._initialized}")
    print(f"Embedding model: {agent.embedding_model is not None}")
    print(f"Vector store: {agent.vector_store is not None}")
    print(f"LLM available: {agent._llm_available}")
    
    # Test query
    print("\n--- Query: صلاة الجمعة ---")
    result = await agent.execute(AgentInput(query="صلاة الجمعة", language="ar"))
    
    print(f"Answer: {result.answer[:200]}...")
    print(f"Confidence: {result.confidence}")
    print(f"Metadata: {result.metadata}")
    
    # Check if retrieval worked
    meta = result.metadata
    retrieved = meta.get("retrieved_count", 0)
    used = meta.get("used_count", 0)
    print(f"\nRetrieved: {retrieved} passages")
    print(f"Used: {used} passages")
    
    if retrieved > 0:
        print("✅ Retrieval working!")
    else:
        print("⚠️ No passages retrieved (collection may be empty)")

asyncio.run(test())
