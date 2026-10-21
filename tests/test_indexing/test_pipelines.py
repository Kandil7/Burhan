"""
Tests for the indexing pipeline placeholders.

Both pipeline modules are documented placeholders. They must raise instead of
returning zero counts, otherwise a caller believes indexing succeeded.
"""

import pytest

from src.indexing.pipelines.build_catalog_indexes import (
    CatalogIndexer,
    CatalogIndexError,
    build_catalog_indexes,
)
from src.indexing.pipelines.build_collection_indexes import (
    CollectionIndexer,
    CollectionIndexError,
    build_collection_indexes,
)


class TestCollectionIndexer:
    """The collection indexer is a placeholder and must fail loudly."""

    @pytest.mark.asyncio
    async def test_index_collections_raises(self):
        indexer = CollectionIndexer()

        with pytest.raises(CollectionIndexError, match="not implemented"):
            await indexer.index_collections(["fiqh_passages"])

    @pytest.mark.asyncio
    async def test_index_collection_raises(self):
        indexer = CollectionIndexer()

        with pytest.raises(CollectionIndexError, match="not implemented"):
            await indexer.index_collection("fiqh_passages")

    @pytest.mark.asyncio
    async def test_convenience_function_raises(self):
        with pytest.raises(CollectionIndexError, match="not implemented"):
            await build_collection_indexes(["fiqh_passages"])


class TestCatalogIndexer:
    """The catalog indexer is a placeholder and must fail loudly."""

    @pytest.mark.asyncio
    async def test_index_catalog_raises(self):
        indexer = CatalogIndexer()

        with pytest.raises(CatalogIndexError, match="not implemented"):
            await indexer.index_catalog()

    @pytest.mark.asyncio
    async def test_index_book_raises(self):
        indexer = CatalogIndexer()

        with pytest.raises(CatalogIndexError, match="not implemented"):
            await indexer.index_book(1)

    @pytest.mark.asyncio
    async def test_index_titles_raises(self):
        indexer = CatalogIndexer()

        with pytest.raises(CatalogIndexError, match="not implemented"):
            await indexer.index_titles()

    @pytest.mark.asyncio
    async def test_convenience_function_raises(self):
        with pytest.raises(CatalogIndexError, match="not implemented"):
            await build_catalog_indexes()
