"""Shared Pydantic config and domain validation helpers."""

from __future__ import annotations

from collections.abc import Hashable, Sequence

from pydantic import ConfigDict

VO_CONFIG = ConfigDict(
    frozen=True,
    extra="forbid",
)


def require_unique(ids: Sequence[Hashable], *, label: str) -> None:
    """Raise ValueError when ``ids`` contains duplicates."""
    if len(set(ids)) == len(ids):
        return
    dupes = sorted({id_ for id_ in ids if ids.count(id_) > 1}, key=str)
    raise ValueError(f"Duplicate {label} found: {dupes}")