"""Frozen door: the Qdrant payload schema does not change by accident.

The hardening plan freezes two contracts: the 26-path HTTP contract and the
Qdrant payload schema. 3.3 million points are already stored, and the
citation code reads payload keys, so a key change means re-uploading the
corpus. This test reads one live point from every collection and asserts the
key set against the frozen schema below.

If it fails, the payload schema changed. That is a one-way door: update this
test only together with a re-upload plan, never on its own.

The test skips itself when Qdrant is not reachable.
"""

import pytest

qdrant_client = pytest.importorskip("qdrant_client")

# Keys the citation and response code reads from every payload. Removing any
# of these breaks citations in live responses.
REQUIRED_KEYS = {
    "content",
    "book_title",
    "collection",
    "content_type",
    "page_number",
    "section_title",
    "author",
    "author_death",
}

# Frozen per-collection key sets, captured from live points on 2026-10-22.
FULL_CORPUS_KEYS = {
    "author",
    "author_death",
    "book_id",
    "book_title",
    "category",
    "chapter",
    "collection",
    "content",
    "content_type",
    "page",
    "page_number",
    "section",
    "section_title",
    "title",
}
DENSE_LOADED_KEYS = {
    "author",
    "author_death",
    "book_id",
    "book_title",
    "category",
    "collection",
    "content",
    "content_type",
    "hierarchy",
    "page_number",
    "section_title",
}
DUA_KEYS = {
    "book_title",
    "category",
    "collection",
    "content",
    "content_type",
    "grade",
    "hadith_source",
    "page_number",
    "reference",
    "repeat_count",
    "section_title",
}

FROZEN_SCHEMA = {
    "aqeedah_passages": FULL_CORPUS_KEYS,
    "arabic_language_passages": FULL_CORPUS_KEYS,
    "duas_adhkar": DUA_KEYS,
    "fiqh_passages": DENSE_LOADED_KEYS,
    "general_islamic": DENSE_LOADED_KEYS,
    "hadith_passages": DENSE_LOADED_KEYS,
    "islamic_history_passages": DENSE_LOADED_KEYS,
    "quran_tafsir": FULL_CORPUS_KEYS,
    "seerah_passages": FULL_CORPUS_KEYS,
    "spirituality_passages": FULL_CORPUS_KEYS,
    "usul_fiqh": FULL_CORPUS_KEYS,
}


@pytest.fixture(scope="module")
def client():
    from qdrant_client import QdrantClient

    from src.config.settings import settings

    try:
        c = QdrantClient(url=settings.qdrant_url)
        c.get_collections()
    except Exception:
        pytest.skip("Qdrant is not reachable")
    return c


@pytest.mark.parametrize("collection", sorted(FROZEN_SCHEMA))
def test_payload_keys_are_frozen(client, collection):
    points, _ = client.scroll(collection_name=collection, limit=1, with_payload=True)
    if not points:
        pytest.skip(f"{collection} has no points yet")

    keys = set((points[0].payload or {}).keys())
    frozen = FROZEN_SCHEMA[collection]

    missing = REQUIRED_KEYS - keys if collection != "duas_adhkar" else set()
    assert not missing, f"{collection} lost payload keys the citations read: {sorted(missing)}"

    unexpected = keys - frozen
    assert not unexpected, (
        f"{collection} gained payload keys: {sorted(unexpected)}. "
        "The payload schema is a one-way door; see the test docstring."
    )
