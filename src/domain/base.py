"""Shared Pydantic config and domain validation helpers."""

from __future__ import annotations

from collections import Counter
from collections.abc import Hashable, Sequence
from typing import Any


def require_unique(ids: Sequence[Hashable], *, label: str) -> None:
    """Raise ValueError when ``ids`` contains duplicates."""
    dupes = sorted(item for item, count in Counter(ids).items() if count > 1)
    if dupes:
        raise ValueError(f"Duplicate {label} found: {dupes}")


def none_as_empty(value: Any) -> Any:
    """Coerce YAML/JSON null to an empty tuple for optional sequence fields."""
    return () if value is None else value
