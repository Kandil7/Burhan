"""Direct test of embedding + vector store"""
import asyncio
import sys
sys.path.insert(0, 'K:/business/projects_v2/Athar')

from src.knowledge.embedding_model import EmbeddingModel
from src.knowledge.vector_store import VectorStore

async def test():
    print("1. Creating embedding model...")
    emb = EmbeddingModel(cache_enabled=False)
    await emb.load_model()
    print(f"   Model loaded: {emb._loaded}")
    
    print("\n2. Encoding query...")
    result = await emb.encode_query("what is islam")
    print(f"   Result type: {type(result)}")
    print(f"   Result shape: {result.shape if hasattr(result, 'shape') else 'N/A'}")
    print(f"   Is coroutine: {hasattr(result, '__await__')}")
    
    print("\n3. Creating vector store...")
    vs = VectorStore()
    await vs.initialize()
    print(f"   Vector store initialized: {vs._initialized}")
    
    print("\n4. Searching...")
    try:
        results = await vs.search(
            collection="general_islamic",
            query_embedding=result,
            top_k=3
        )
        print(f"   Search successful: {len(results)} results")
        for i, r in enumerate(results[:2], 1):
            print(f"\n   [{i}] Score: {r.get('score', 0):.4f}")
            content = r.get('content', '')
            print(f"       {content[:150]}...")
    except Exception as e:
        print(f"   Search failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test())
