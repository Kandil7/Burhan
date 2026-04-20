from src.retrieval.multi_collection_retriever import MultiCollectionRetriever
from src.retrieval.collection_hybrid_retriever import CollectionHybridRetriever
from src.indexing.vectorstores.qdrant_store import vector_store
from src.indexing.embeddings.embedding_model import EmbeddingModel
from src.config.constants import CollectionNames  # اللي فيه *_passages

embedding_model = EmbeddingModel()
multi_retriever = MultiCollectionRetriever()

for coll in [
    CollectionNames.FIQH,
    CollectionNames.HADITH,
    CollectionNames.DUA,
    CollectionNames.GENERAL,
    CollectionNames.QURAN_TAFSIR,
    CollectionNames.AQEEDAH,
    CollectionNames.SEERAH,
    CollectionNames.ISLAMIC_HISTORY,
    CollectionNames.ARABIC_LANGUAGE,
    CollectionNames.SPIRITUALITY,
    CollectionNames.USUL_FIQH,
]:
    retr = CollectionHybridRetriever(
        collection=coll,
        vector_store=vector_store,
        embedding_model=embedding_model,
    )
    multi_retriever.register_retriever(coll, retr)

class CollectionHybridRetriever:
    """
    Adapter to use HybridSearcher as a retriever for a single collection.

    Usage:
        retr = CollectionHybridRetriever(collection="fiqh_passages", ...)
        results = await retr.retrieve(query="زكاة المال", top_k=10)
    """

    def __init__(self, collection: str, vector_store: VectorStore, embedding_model: Any):
        self.collection = collection
        self.embedding_model = embedding_model
        self.searcher = HybridSearcher(vector_store)

    async def retrieve(self, query: str, top_k: int = 10) -> List[Dict[str, Any]]:
        # 1) Embed query
        query_embedding: np.ndarray = await self.embedding_model.encode_query(query)

        # 2) Run hybrid search on the given collection
        results = await self.searcher.search(
            query=query,
            query_embedding=query_embedding,
            collection=self.collection,
            top_k=top_k,
        )

        # 3) Ensure collection is present in metadata
        for r in results:
            meta = r.get("metadata", {}) or {}
            meta.setdefault("collection", self.collection)
            r["metadata"] = meta

        return results