# Search Service Module
"""Service for handling search operations."""

from typing import Optional, Dict, Any, List

from src.config.constants import CollectionNames
from src.application.use_cases.run_retrieval import (
    RunRetrievalInput,
    RunRetrievalOutput,
    RunRetrievalUseCase,
)

# Unified default collections used when caller requests "all"
DEFAULT_COLLECTIONS: list[str] = [
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
]


class SearchService:
    """Service for processing search queries."""

    def __init__(self, run_retrieval_uc: RunRetrievalUseCase) -> None:
        self._run_retrieval_uc = run_retrieval_uc

    async def search(
        self,
        query: str,
        collections: Optional[List[str]] = None,
        top_k: int = 10,
        filters: Optional[Dict[str, Any]] = None,
    ) -> RunRetrievalOutput:
        """
        Process a search query.

        Args:
            query: Search query
            collections:
                - None  -> search over DEFAULT_COLLECTIONS ("all")
                - [..]  -> specific collections
            top_k: Number of results
            filters: Optional filters

        Returns:
            RunRetrievalOutput with results
        """
        effective_collections = collections or DEFAULT_COLLECTIONS

        input_data = RunRetrievalInput(
            query=query,
            collections=effective_collections,
            top_k=top_k,
            enable_reranking=True,
            enable_expansion=True,
            filters=filters,
        )

        # Delegate to RunRetrievalUseCase
        output = await self._run_retrieval_uc.execute(input_data)
        return output


# Default service instance - will be initialized properly in the application container
# DO NOT use this directly - get it from the container after proper initialization
search_service: "SearchService | None" = None


def get_search_service(
    run_retrieval_uc: RunRetrievalUseCase,
) -> SearchService:
    """Factory function to create a properly initialized SearchService instance."""
    return SearchService(run_retrieval_uc=run_retrieval_uc)
