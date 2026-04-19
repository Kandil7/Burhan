"""
Qdrant Collection Management.

Provides collection configuration and management utilities.
"""

from __future__ import annotations

from typing import Any


class CollectionConfig:
    """Configuration for a Qdrant collection."""

    def __init__(
        self,
        name: str,
        dimension: int = 1024,
        description: str = "",
        vector_config: dict[str, Any] | None = None,
    ):
        self.name = name
        self.dimension = dimension
        self.description = description
        self.vector_config = vector_config or {}


# Predefined collection configurations
COLLECTION_CONFIGS: dict[str, CollectionConfig] = {
    "fiqh_passages": CollectionConfig(
        name="fiqh_passages",
        dimension=1024,
        description="Fiqh books, fatwas, and rulings",
    ),
    "hadith_passages": CollectionConfig(
        name="hadith_passages",
        dimension=1024,
        description="Hadith collections and narrations",
    ),
    "tafsir_passages": CollectionConfig(
        name="tafsir_passages",
        dimension=1024,
        description="Quran tafsir (interpretation)",
    ),
    "quran_tafsir": CollectionConfig(
        name="quran_tafsir",
        dimension=1024,
        description="Quran tafsir passages",
    ),
    "aqeedah_passages": CollectionConfig(
        name="aqeedah_passages",
        dimension=1024,
        description="Aqeedah and Islamic creed",
    ),
    "seerah_passages": CollectionConfig(
        name="seerah_passages",
        dimension=1024,
        description="Prophet biography (Seerah)",
    ),
    "history_passages": CollectionConfig(
        name="history_passages",
        dimension=1024,
        description="Islamic history",
    ),
    "islamic_history_passages": CollectionConfig(
        name="islamic_history_passages",
        dimension=1024,
        description="Islamic history passages",
    ),
    "language_passages": CollectionConfig(
        name="language_passages",
        dimension=1024,
        description="Arabic language and grammar",
    ),
    "arabic_language_passages": CollectionConfig(
        name="arabic_language_passages",
        dimension=1024,
        description="Arabic language passages",
    ),
    "tazkiyah_passages": CollectionConfig(
        name="tazkiyah_passages",
        dimension=1024,
        description="Spirituality and ethics",
    ),
    "spirituality_passages": CollectionConfig(
        name="spirituality_passages",
        dimension=1024,
        description="Spirituality passages",
    ),
    "usul_fiqh_passages": CollectionConfig(
        name="usul_fiqh_passages",
        dimension=1024,
        description="Principles of Islamic jurisprudence",
    ),
    "usul_fiqh": CollectionConfig(
        name="usul_fiqh",
        dimension=1024,
        description="Usul Fiqh collection",
    ),
    "general_islamic": CollectionConfig(
        name="general_islamic",
        dimension=1024,
        description="General Islamic knowledge",
    ),
}


def get_collection_config(name: str) -> CollectionConfig | None:
    """Get collection configuration by name."""
    return COLLECTION_CONFIGS.get(name)


def list_all_collections() -> list[str]:
    """List all available collection names."""
    return list(COLLECTION_CONFIGS.keys())


def get_collections_by_domain(domain: str) -> list[str]:
    """Get collections for a specific domain."""
    domain_map = {
        "fiqh": ["fiqh_passages", "usul_fiqh", "usul_fiqh_passages"],
        "hadith": ["hadith_passages"],
        "tafsir": ["tafsir_passages", "quran_tafsir"],
        "aqeedah": ["aqeedah_passages"],
        "seerah": ["seerah_passages"],
        "history": ["history_passages", "islamic_history_passages"],
        "language": ["language_passages", "arabic_language_passages"],
        "tazkiyah": ["tazkiyah_passages", "spirituality_passages"],
        "general": ["general_islamic"],
    }
    return domain_map.get(domain, [])


__all__ = [
    "CollectionConfig",
    "COLLECTION_CONFIGS",
    "get_collection_config",
    "list_all_collections",
    "get_collections_by_domain",
]
