"""
Qdrant Payload Index Configuration.

Defines payload field indexes for efficient filtering.
"""

from __future__ import annotations

from typing import Any


class PayloadIndexConfig:
    """Configuration for a payload field index."""

    def __init__(
        self,
        field_name: str,
        field_type: str,
        description: str = "",
    ):
        self.field_name = field_name
        self.field_type = field_type  # keyword, integer, float, text, bool
        self.description = description


# Predefined payload index configurations
PAYLOAD_INDEXES: dict[str, list[PayloadIndexConfig]] = {
    "fiqh_passages": [
        PayloadIndexConfig("madhhab", "keyword", "Islamic legal school"),
        PayloadIndexConfig("book_title", "keyword", "Book title"),
        PayloadIndexConfig("author", "keyword", "Author name"),
        PayloadIndexConfig("author_death", "integer", "Author death year"),
        PayloadIndexConfig("page_number", "integer", "Page number"),
        PayloadIndexConfig("chapter", "text", "Chapter name"),
    ],
    "hadith_passages": [
        PayloadIndexConfig("grade", "keyword", "Hadith authenticity grade"),
        PayloadIndexConfig("source_book", "keyword", "Source book"),
        PayloadIndexConfig("narrator", "keyword", "Narrator name"),
        PayloadIndexConfig("chapter", "text", "Chapter"),
    ],
    "tafsir_passages": [
        PayloadIndexConfig("mufassir", "keyword", "Mufassir (commentator)"),
        PayloadIndexConfig("sura", "integer", "Quran chapter number"),
        PayloadIndexConfig("ayah_start", "integer", "Start verse"),
        PayloadIndexConfig("ayah_end", "integer", "End verse"),
    ],
    "aqeedah_passages": [
        PayloadIndexConfig("aqeedah_school", "keyword", "Theological school"),
        PayloadIndexConfig("topic", "keyword", "Topic"),
    ],
    "seerah_passages": [
        PayloadIndexConfig("period", "keyword", "Historical period"),
        PayloadIndexConfig("event_type", "keyword", "Event type"),
    ],
    "general_islamic": [
        PayloadIndexConfig("category", "keyword", "Content category"),
        PayloadIndexConfig("topic", "keyword", "Topic"),
    ],
}


def get_payload_indexes(collection: str) -> list[PayloadIndexConfig]:
    """Get payload index config for a collection."""
    return PAYLOAD_INDEXES.get(collection, [])


def create_index_operations(collection: str) -> list[dict[str, Any]]:
    """Generate Qdrant index creation operations."""
    indexes = get_payload_indexes(collection)
    operations = []

    for idx in indexes:
        if idx.field_type == "keyword":
            operations.append(
                {
                    "type": "field_index",
                    "field": f"metadata.{idx.field_name}",
                    "field_index": {
                        "type": "keyword",
                    },
                }
            )
        elif idx.field_type == "integer":
            operations.append(
                {
                    "type": "field_index",
                    "field": f"metadata.{idx.field_name}",
                    "field_index": {
                        "type": "integer",
                    },
                }
            )

    return operations


__all__ = [
    "PayloadIndexConfig",
    "PAYLOAD_INDEXES",
    "get_payload_indexes",
    "create_index_operations",
]
