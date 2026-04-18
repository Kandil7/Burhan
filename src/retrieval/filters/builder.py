"""
Filter Builder for Retrieval Layer.

Builds metadata filters for Qdrant queries.
"""

from __future__ import annotations

from typing import Any

from src.retrieval.schemas import FilterConfig


class FilterBuilder:
    """
    Builder for creating Qdrant-compatible filter conditions.

    Usage:
        builder = FilterBuilder()
        filter_dict = builder.build([
            FilterConfig(field="source", operator="eq", value="fiqh"),
            FilterConfig(field="author_death", operator="gte", value=0),
        ])
    """

    @staticmethod
    def build(filters: list[FilterConfig]) -> dict[str, Any]:
        """
        Build filter conditions from FilterConfig list.

        Args:
            filters: List of FilterConfig objects

        Returns:
            Qdrant-compatible filter dictionary
        """
        if not filters:
            return {}

        conditions = []
        for f in filters:
            condition = FilterBuilder._build_condition(f)
            if condition:
                conditions.append(condition)

        if not conditions:
            return {}

        if len(conditions) == 1:
            return conditions[0]

        return {"must": conditions}

    @staticmethod
    def _build_condition(config: FilterConfig) -> dict[str, Any] | None:
        """Build a single filter condition."""
        field = config.field
        operator = config.operator
        value = config.value

        # Field path mapping for nested metadata
        field_path = f"metadata.{field}"

        op_map = {
            "eq": "eq",
            "ne": "ne",
            "gt": "gt",
            "gte": "gte",
            "lt": "lt",
            "lte": "lte",
        }

        if operator in op_map:
            return {"key": field_path, op_map[operator]: value}

        if operator == "in":
            return {"key": field_path, "in": value if isinstance(value, list) else [value]}

        if operator == "nin":
            return {"key": field_path, "nin": value if isinstance(value, list) else [value]}

        return None

    @staticmethod
    def build_range(field: str, min_val: float | None, max_val: float | None) -> dict[str, Any]:
        """Build a range filter."""
        conditions = []

        if min_val is not None:
            conditions.append({"key": f"metadata.{field}", "gte": min_val})

        if max_val is not None:
            conditions.append({"key": f"metadata.{field}", "lte": max_val})

        if not conditions:
            return {}

        if len(conditions) == 1:
            return conditions[0]

        return {"must": conditions}

    @staticmethod
    def build_text_match(field: str, text: str) -> dict[str, Any]:
        """Build a text match filter using match clause."""
        return {"key": f"metadata.{field}", "match": {"text": text}}


__all__ = ["FilterBuilder"]
