"""Minimal domain base: immutable VO config and small shared helpers."""

from __future__ import annotations

from collections import Counter
from collections.abc import Hashable, Sequence
from functools import cached_property
from typing import Any

from pydantic import BaseModel, ConfigDict


class DomainValueObject(BaseModel):
    """Immutable value-object base with strict validation."""

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
        populate_by_name=True,
        ignored_types=(cached_property,),
    )


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


