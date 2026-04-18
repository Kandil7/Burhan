"""
Filter Presets for Domain-Specific Retrieval.

Provides pre-configured filter sets for different Islamic knowledge domains.
"""

from __future__ import annotations

from src.retrieval.schemas import FilterConfig


class FilterPresets:
    """
    Pre-configured filter sets for different domains.

    Usage:
        filters = FilterPresets.for_fiqh(min_score=0.5)
        filters = FilterPresets.for_hadith(grades=["sahih", "hasan"])
    """

    @staticmethod
    def for_fiqh(
        min_score: float = 0.0,
        schools: list[str] | None = None,
    ) -> list[FilterConfig]:
        """Figh domain filters."""
        filters = []

        if min_score > 0:
            filters.append(FilterConfig(field="score", operator="gte", value=min_score))

        if schools:
            filters.append(FilterConfig(field="madhhab", operator="in", value=schools))

        return filters

    @staticmethod
    def for_hadith(
        grades: list[str] | None = None,
        sources: list[str] | None = None,
    ) -> list[FilterConfig]:
        """Hadith domain filters."""
        filters = []

        if grades:
            filters.append(FilterConfig(field="grade", operator="in", value=grades))

        if sources:
            filters.append(FilterConfig(field="source_book", operator="in", value=sources))

        return filters

    @staticmethod
    def for_tafsir(
        mufassirs: list[str] | None = None,
        sura: int | None = None,
    ) -> list[FilterConfig]:
        """Tafsir domain filters."""
        filters = []

        if mufassirs:
            filters.append(FilterConfig(field="mufassir", operator="in", value=mufassirs))

        if sura:
            filters.append(FilterConfig(field="sura", operator="eq", value=sura))

        return filters

    @staticmethod
    def for_aqeedah(
        schools: list[str] | None = None,
    ) -> list[FilterConfig]:
        """Aqeedah domain filters."""
        filters = []

        if schools:
            filters.append(FilterConfig(field="aqeedah_school", operator="in", value=schools))

        return filters

    @staticmethod
    def for_seerah(
        periods: list[str] | None = None,
    ) -> list[FilterConfig]:
        """Seerah domain filters."""
        filters = []

        if periods:
            filters.append(FilterConfig(field="period", operator="in", value=periods))

        return filters

    @staticmethod
    def for_usul_fiqh(
        methods: list[str] | None = None,
    ) -> list[FilterConfig]:
        """Usul Fiqh domain filters."""
        filters = []

        if methods:
            filters.append(FilterConfig(field="usul_method", operator="in", value=methods))

        return filters


__all__ = ["FilterPresets"]
