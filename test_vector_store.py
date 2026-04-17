"""Test vector store search directly."""
import asyncio
import numpy as np
from src.knowledge.vector_store import VectorStore
from src.knowledge.embedding_model import EmbeddingModel

async def test():
    print("Initializing embedding model...")
    embedding_model = EmbeddingModel(cache_enabled=False)
    await embedding_model.load_model()
    print(f"✅ Embedding model loaded: {embedding_model.MODEL_NAME}")
    
    print("\nInitializing vector store...")
    vector_store = VectorStore()
    await vector_store.initialize()
    print(f"✅ Vector store initialized")
    print(f"   Collections: {list(vector_store.COLLECTIONS.keys())}")
    
    # Test query
    query = "what is islam"
    print(f"\nEncoding query: '{query}'")
    query_embedding = await embedding_model.encode([query])
    print(f"✅ Query encoded: shape={query_embedding.shape}")
    
    # Test search on general_islamic
    collection = "general_islamic"
    print(f"\nSearching in '{collection}'...")
    try:
        results = await vector_store.search(
            collection=collection,
            query_embedding=query_embedding[0],
            top_k=5
        )
        print(f"✅ Search successful!")
        print(f"   Results: {len(results)}")
        for i, r in enumerate(results[:3], 1):
            print(f"\n   [{i}] Score: {r.get('score', 'N/A')}")
            print(f"       Content: {r.get('content', '')[:200]}...")
    except Exception as e:
        print(f"❌ Search failed: {e}")
        import traceback
        traceback.print_exc()
    
    # Test search on quran_tafsir
    collection = "quran_tafsir"
    print(f"\nSearching in '{collection}'...")
    try:
        results = await vector_store.search(
            collection=collection,
            query_embedding=query_embedding[0],
            top_k=5
        )
        print(f"✅ Search successful!")
        print(f"   Results: {len(results)}")
    except Exception as e:
        print(f"❌ Search failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test())
