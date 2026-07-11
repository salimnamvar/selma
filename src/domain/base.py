"""Domain Model Base.

Shared immutable base and small validation helpers for governance value objects.
"""

from __future__ import annotations

from collections.abc import Hashable, Sequence
from functools import cached_property
from typing import Any

from pydantic import BaseModel, ConfigDict


class DomainValueObject(BaseModel):
    """Immutable value-object base with strict validation and alias support."""

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
        populate_by_name=True,
        str_strip_whitespace=True,
        ignored_types=(cached_property,),
    )


def require_unique(a_ids: Sequence[Hashable], *, a_label: str) -> None:
    """Raise ValueError when the sequence contains duplicate identifiers.

    Args:
        a_ids: Identifiers to check.
        a_label: Human-readable label used in the error message.

    Raises:
        ValueError: If any identifier appears more than once.
    """
    if len(a_ids) != len(set(a_ids)):
        raise ValueError(f"Duplicate {a_label} are not allowed")


def none_as_empty(a_value: Any) -> Any:
    """Coerce YAML/JSON null to an empty tuple for optional sequence fields.

    Args:
        a_value: Raw input value.

    Returns:
        Empty tuple when ``a_value`` is None, otherwise ``a_value`` unchanged.
    """
    return () if a_value is None else a_value
