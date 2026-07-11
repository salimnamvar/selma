"""Indexed collection base for identified domain items.

Provides the shared ``get`` / ``__len__`` / ``__contains__`` surface used by
list-rooted value objects. Domain-specific uniqueness and structure rules stay
in subclasses as Pydantic validators.
"""

from __future__ import annotations

from collections.abc import Hashable, Iterator
from functools import cached_property
from typing import Dict, Optional, Protocol, Tuple, TypeVar, runtime_checkable

from pydantic import ConfigDict, Field, RootModel, model_validator

from domain.base import require_unique

TId = TypeVar("TId", bound=Hashable)


@runtime_checkable
class IdentifiedItem(Protocol[TId]):
    """Protocol for items with a stable identifier property."""

    @property
    def id(self) -> TId:
        """Unique identifier for this item."""
        ...


class IdentifiedCollection[TId: Hashable, TItem](RootModel[Tuple[TItem, ...]]):
    """Immutable RootModel collection with O(1) lookup by item identifier.

    Items should expose an ``.id`` property (see :class:`IdentifiedItem`).
    The default uniqueness check applies to top-level items only; override
    :meth:`check_unique_ids` when nested identity rules apply.

    Iteration, length, and membership operate on the collection items (not on
    Pydantic model fields).
    """

    model_config = ConfigDict(frozen=True)

    root: Tuple[TItem, ...] = Field(min_length=1)

    def _item_id(self, a_item: TItem) -> TId:
        """Extract the identifier from a collection item.

        Args:
            a_item: Item stored in this collection.

        Returns:
            Stable hashable identifier for indexing and uniqueness checks.
        """
        return a_item.id

    @model_validator(mode="after")
    def check_unique_ids(self) -> IdentifiedCollection[TId, TItem]:
        """Reject collections that contain duplicate top-level identifiers."""
        require_unique(
            [self._item_id(item) for item in self.root],
            a_label="IDs",
        )
        return self

    @cached_property
    def _index(self) -> Dict[TId, TItem]:
        result: Dict[TId, TItem] = {self._item_id(item): item for item in self.root}
        return result

    def get(self, a_id: TId) -> Optional[TItem]:
        """Return the item for ``a_id``, or None when absent.

        Args:
            a_id: Item identifier.

        Returns:
            Matching item, or None.
        """
        result: Optional[TItem] = self._index.get(a_id)
        return result

    def __iter__(self) -> Iterator[TItem]:  # type: ignore[override]
        """Yield top-level collection items in declaration order."""
        yield from self.root

    def __len__(self) -> int:
        return len(self.root)

    def __contains__(self, a_item: object) -> bool:
        result: bool = a_item in self._index
        return result
