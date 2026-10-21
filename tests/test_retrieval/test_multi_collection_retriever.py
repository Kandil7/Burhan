"""Tests for the multi-collection retriever."""

import pytest

from src.retrieval.retrievers.multi_collection_retriever import (
    MultiCollectionRetriever,
)


class _StubRetriever:
    def __init__(self, result=None, error=None):
        self.result = result
        self.error = error

    async def retrieve(self, query, top_k):
        if self.error is not None:
            raise self.error
        return self.result


@pytest.mark.asyncio
async def test_merges_results_per_collection():
    retriever = MultiCollectionRetriever(
        {
            "fiqh_passages": _StubRetriever(result=[{"content": "a"}]),
            "hadith_passages": _StubRetriever(result=[{"content": "b"}]),
        }
    )

    results = await retriever.retrieve("query", ["fiqh_passages", "hadith_passages"])

    assert results["fiqh_passages"] == [{"content": "a"}]
    assert results["hadith_passages"] == [{"content": "b"}]


@pytest.mark.asyncio
async def test_failing_collection_is_isolated():
    retriever = MultiCollectionRetriever(
        {
            "fiqh_passages": _StubRetriever(result=[{"content": "a"}]),
            "hadith_passages": _StubRetriever(error=RuntimeError("qdrant down")),
        }
    )

    results = await retriever.retrieve("query", ["fiqh_passages", "hadith_passages"])

    assert results["fiqh_passages"] == [{"content": "a"}]
    assert results["hadith_passages"] == []


@pytest.mark.asyncio
async def test_unregistered_collection_returns_empty():
    retriever = MultiCollectionRetriever({})

    results = await retriever.retrieve("query", ["fiqh_passages"])

    assert results == {"fiqh_passages": []}
