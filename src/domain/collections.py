"""Indexed collection base for identified domain items.

Lookup keys are normalized with ``str(...)`` so string literals and scalar
identifier value objects resolve the same entry.
"""

from __future__ import annotations

from collections.abc import Hashable, Iterator
from functools import cached_property
from typing import Protocol, Self, TypeVar, runtime_checkable

from pydantic import ConfigDict, RootModel, model_validator

from domain.base import IndexedLookupMixin, require_unique

TId = TypeVar("TId", bound=Hashable, covariant=True)
TItem = TypeVar("TItem")


@runtime_checkable
class IdentifiedItem(Protocol[TId]):
    """Protocol for items with a stable identifier property."""

    @property
    def id(self) -> TId:
        """Unique identifier for this item."""
        ...


class IdentifiedCollection[TId: Hashable, TItem](
    RootModel[tuple[TItem, ...]],
    IndexedLookupMixin[str, TItem],
):
    """Immutable RootModel collection with O(1) lookup by item identifier.

    The public lookup key type is ``str`` (normalized form of item ids).
    """

    model_config = ConfigDict(frozen=True)

    root: tuple[TItem, ...]

    def _item_id(self, item: TItem) -> str:
        return str(item.id)  # type: ignore[attr-defined]

    @model_validator(mode="after")
    def _validate_ids(self) -> Self:
        require_unique([self._item_id(item) for item in self.root], label="IDs")
        return self

    @cached_property
    def _index(self) -> dict[str, TItem]:
        return {self._item_id(item): item for item in self.root}

    def get(self, key: Hashable) -> TItem | None:
        """Return the item for ``key``, or None when absent."""
        return super().get(str(key))

    def require(self, key: Hashable) -> TItem:
        """Return the item for ``key``, or raise KeyError when absent."""
        return super().require(str(key))

    def has(self, key: Hashable) -> bool:
        """Return True if an item with ``key`` exists."""
        return super().has(str(key))

    @property
    def items(self) -> tuple[TItem, ...]:
        """Return all items in declaration order."""
        return self.root

    def __iter__(self) -> Iterator[TItem]:  # type: ignore[override]
        yield from self.root

    def __len__(self) -> int:
        return len(self.root)

    def __contains__(self, item: object) -> bool:
        """Membership by item instance (with ``.id``) or by identifier."""
        key = str(item.id) if hasattr(item, "id") else str(item)  # type: ignore[attr-defined]
        return self.has(key)
