"""Indexed collection base for identified domain items.

Provides ``get`` / ``find`` / secondary-attribute lookup used by list-rooted
value objects. Domain-specific uniqueness and structure rules stay in
subclasses as Pydantic validators.
"""

from __future__ import annotations

from collections.abc import Callable, Hashable, Iterator, Sequence
from functools import cached_property
from typing import Any, Dict, List, Optional, Protocol, Tuple, TypeVar, runtime_checkable

from pydantic import ConfigDict, Field, RootModel, model_validator

from domain.base import require_unique

TId = TypeVar("TId", bound=Hashable, covariant=True)
TItem = TypeVar("TItem")


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

    Iteration, length, and membership operate on collection items (not on
    Pydantic model fields).
    """

    model_config = ConfigDict(frozen=True)

    root: Tuple[TItem, ...] = Field(min_length=1)

    def _item_id(self, a_item: TItem) -> TId:
        """Extract the identifier from a collection item."""
        return a_item.id  # type: ignore[attr-defined]

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
        """Build and cache a lookup index by item identifier."""
        return {self._item_id(item): item for item in self.root}

    def get(self, a_id: TId) -> Optional[TItem]:
        """Return the item for ``a_id``, or None when absent."""
        return self._index.get(a_id)

    def find(self, a_id: TId) -> TItem:
        """Return the item for ``a_id``, or raise KeyError when absent."""
        try:
            return self._index[a_id]
        except KeyError as exc:
            raise KeyError(f"Item with id '{a_id}' not found in collection") from exc

    def get_all(self, a_ids: Sequence[TId]) -> List[TItem]:
        """Return items for the given identifiers (order preserved, missing skipped)."""
        return [self._index[id_] for id_ in a_ids if id_ in self._index]

    def find_all(self, a_ids: Sequence[TId]) -> List[TItem]:
        """Return items for the given identifiers (raises if any are missing)."""
        return [self.find(id_) for id_ in a_ids]

    def get_by(self, a_attr: str, a_value: Any) -> Optional[TItem]:
        """Return the first item whose attribute ``a_attr`` equals ``a_value``."""
        for item in self.root:
            if getattr(item, a_attr, None) == a_value:
                return item
        return None

    def find_by(self, a_attr: str, a_value: Any) -> TItem:
        """Return the first item whose attribute equals ``a_value``, or raise."""
        result = self.get_by(a_attr, a_value)
        if result is None:
            raise KeyError(f"Item with {a_attr}={a_value!r} not found in collection")
        return result

    @property
    def ids(self) -> List[TId]:
        """Return item identifiers in declaration order."""
        return list(self._index.keys())

    @property
    def values(self) -> List[TItem]:
        """Return all items in declaration order."""
        return list(self.root)

    def filter(self, a_predicate: Callable[[TItem], bool]) -> List[TItem]:
        """Return items matching the given predicate."""
        return [item for item in self.root if a_predicate(item)]

    def filter_by(self, **kwargs: Any) -> List[TItem]:
        """Return items whose attributes match all given keyword arguments."""
        return [
            item
            for item in self.root
            if all(getattr(item, key) == value for key, value in kwargs.items())
        ]

    def map(self, a_func: Callable[[TItem], Any]) -> List[Any]:
        """Apply ``a_func`` to each item and return the results."""
        return [a_func(item) for item in self.root]

    def has(self, a_id: TId) -> bool:
        """Return True if an item with ``a_id`` exists."""
        return a_id in self._index

    def __iter__(self) -> Iterator[TItem]:  # type: ignore[override]
        """Yield top-level collection items in declaration order."""
        yield from self.root

    def __len__(self) -> int:
        """Return the number of items in the collection."""
        return len(self.root)

    def __contains__(self, a_item: object) -> bool:
        """Support membership by item instance (with ``.id``) or by identifier."""
        if hasattr(a_item, "id"):
            return a_item.id in self._index  # type: ignore[attr-defined]
        return a_item in self._index
