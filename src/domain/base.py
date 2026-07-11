"""Shared Pydantic config and tiny validation helpers."""

from __future__ import annotations

from collections import Counter
from collections.abc import Hashable, Sequence
from typing import Any

from pydantic import ConfigDict

VO_CONFIG = ConfigDict(
    frozen=True,
    extra="forbid",
    populate_by_name=True,
)

ROOT_CONFIG = ConfigDict(frozen=True)


def require_unique(ids: Sequence[Hashable], *, label: str) -> None:
    """Raise ValueError when the sequence contains duplicate identifiers."""
    dupes = {item for item, count in Counter(ids).items() if count > 1}
    if dupes:
        raise ValueError(f"Duplicate {label} found: {dupes}")


def none_as_empty(value: Any) -> Any:
    """Coerce YAML/JSON null to an empty tuple for optional sequence fields."""
    result: Any = value
    if value is None:
        result = ()
    return result