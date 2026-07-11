"""Indexed collection base for identified domain items.

Provides O(1) lookup by item id. Domain-specific structure rules live in
subclasses as Pydantic validators.

Lookup style (shared via :class:`~domain.base.IndexedLookupMixin`)
------------------------------------------------------------------
    get(key)     -> T | None
    require(key) -> T          (raises KeyError when absent)
    has(key)     -> bool
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
    IndexedLookupMixin[TId, TItem],
):
    """Immutable RootModel collection with O(1) lookup by item identifier.

    Items should expose an ``.id`` property (see :class:`IdentifiedItem`).
    Subclasses own length and structure invariants.
    """

    model_config = ConfigDict(frozen=True)

    root: tuple[TItem, ...]

    def _item_id(self, item: TItem) -> TId:
        return item.id  # type: ignore[attr-defined]

    @model_validator(mode="after")
    def _validate_ids(self) -> Self:
        require_unique([self._item_id(item) for item in self.root], label="IDs")
        return self

    @cached_property
    def _index(self) -> dict[TId, TItem]:
        return {self._item_id(item): item for item in self.root}

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
        key = item.id if hasattr(item, "id") else item  # type: ignore[attr-defined]
        return self.has(key)  # type: ignore[arg-type]
