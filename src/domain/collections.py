"""Indexed collection base for identified domain items.

Provides the shared ``get`` / ``find`` / ``__len__`` / ``__contains__`` surface
used by list-rooted value objects. Domain-specific uniqueness and structure
rules stay in subclasses as Pydantic validators.

Standardized collection methods:
    - get(id) -> Optional[T]: Safe lookup (returns None if not found)
    - find(id) -> T: Strict lookup (raises KeyError if not found)
    - get_all(ids) -> list[T]: Batch safe lookup
    - find_all(ids) -> list[T]: Batch strict lookup
    - has(id) -> bool: Check if ID exists
    - has_item(item) -> bool: Check if item exists
    - ids -> list[TId]: All identifiers
    - items -> list[tuple[TId, TItem]]: (id, item) tuples
    - values -> list[TItem]: All items
    - first -> TItem: First item
    - last -> TItem: Last item
"""

from __future__ import annotations

from collections.abc import Callable, Hashable, Iterator
from functools import cached_property
from typing import Any, Dict, List, Optional, Protocol, Sequence, Tuple, TypeVar, runtime_checkable

from pydantic import ConfigDict, Field, RootModel, model_validator

from domain.base import require_unique

TId = TypeVar("TId", bound=Hashable)
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

    Iteration, length, and membership operate on the collection items (not on
    Pydantic model fields).

    Standardized methods provide consistent API across all domain collections.
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
        """Build and cache a lookup index by item identifier."""
        result: Dict[TId, TItem] = {self._item_id(item): item for item in self.root}
        return result

    # Standardized lookup methods
    def get(self, a_id: TId) -> Optional[TItem]:
        """Return the item for ``a_id``, or None when absent.

        Args:
            a_id: Item identifier.

        Returns:
            Matching item, or None.
        """
        result: Optional[TItem] = self._index.get(a_id)
        return result

    def find(self, a_id: TId) -> TItem:
        """Return the item for ``a_id``, or raise KeyError when absent.

        Args:
            a_id: Item identifier.

        Returns:
            Matching item.

        Raises:
            KeyError: If no item with the given identifier exists.
        """
        result: Optional[TItem] = self._index.get(a_id)
        if result is None:
            raise KeyError(f"Item with id '{a_id}' not found in collection")
        return result

    def get_all(self, a_ids: Sequence[TId]) -> List[TItem]:
        """Return items for the given identifiers (preserves order, skips missing).

        Args:
            a_ids: Sequence of item identifiers to lookup.

        Returns:
            List of matching items in the order requested; missing items are skipped.
        """
        return [self._index[id_] for id_ in a_ids if id_ in self._index]

    def find_all(self, a_ids: Sequence[TId]) -> List[TItem]:
        """Return items for the given identifiers (raises if any are missing).

        Args:
            a_ids: Sequence of item identifiers to lookup.

        Returns:
            List of matching items in the order requested.

        Raises:
            KeyError: If any identifier is not found in the collection.
        """
        result: List[TItem] = []
        for id_ in a_ids:
            if id_ not in self._index:
                raise KeyError(f"Item with id '{id_}' not found in collection")
            result.append(self._index[id_])
        return result

    # Standardized property access methods
    @property
    def ids(self) -> List[TId]:
        """Return list of all item identifiers in declaration order."""
        return list(self._index.keys())

    @property
    def items(self) -> List[tuple[TId, TItem]]:
        """Return list of (id, item) tuples in declaration order."""
        return list(self._index.items())

    @property
    def values(self) -> List[TItem]:
        """Return list of all items in declaration order."""
        return list(self.root)

    @property
    def first(self) -> TItem:
        """Return the first item in declaration order."""
        return self.root[0]

    @property
    def last(self) -> TItem:
        """Return the last item in declaration order."""
        return self.root[-1]

    @property
    def count(self) -> int:
        """Return the number of items in the collection."""
        return len(self.root)

    @property
    def empty(self) -> bool:
        """Return True if the collection is empty."""
        return len(self.root) == 0

    # Standardized query methods
    def filter(self, a_predicate: Callable[[TItem], bool]) -> List[TItem]:
        """Return items matching the given predicate.

        Args:
            a_predicate: Callable that returns True for matching items.

        Returns:
            List of items for which the predicate returns True.
        """
        return [item for item in self.root if a_predicate(item)]

    def filter_by(self, **kwargs: Any) -> List[TItem]:
        """Return items whose attributes match all given keyword arguments.

        Args:
            **kwargs: Attribute name/value pairs to match.

        Returns:
            List of items where all specified attributes match the given values.
        """
        return [
            item for item in self.root
            if all(getattr(item, key) == value for key, value in kwargs.items())
        ]

    def map(self, a_func: Callable[[TItem], Any]) -> List[Any]:
        """Apply function to all items and return results.

        Args:
            a_func: Function to apply to each item.

        Returns:
            List of function results for each item.
        """
        return [a_func(item) for item in self.root]

    # Standardized membership testing
    def has(self, a_id: TId) -> bool:
        """Return True if collection contains an item with the given identifier.

        Args:
            a_id: Item identifier to check.

        Returns:
            True if the identifier exists, False otherwise.
        """
        return a_id in self._index

    def has_item(self, a_item: object) -> bool:
        """Return True if collection contains the specific item instance.

        Args:
            a_item: Item instance to check.

        Returns:
            True if the item exists in the collection, False otherwise.
        """
        return a_item in self.root

    # Iterator methods
    def __iter__(self) -> Iterator[TItem]:  # type: ignore[override]
        """Yield top-level collection items in declaration order."""
        yield from self.root

    def __len__(self) -> int:
        """Return the number of items in the collection."""
        return len(self.root)

    def __contains__(self, a_item: object) -> bool:
        """Return True if ``a_item`` is present in the collection by identifier."""
        # Support both item instance and identifier lookup
        if hasattr(a_item, "id"):
            return a_item.id in self._index
        return a_item in self._index