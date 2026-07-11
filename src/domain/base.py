"""Domain model base: immutable VOs, protocols, mixins, and shared helpers.

Construction and serialization use Pydantic v2 natively:
    model_validate / model_dump / model_validate_json / model_dump_json

Method naming convention
------------------------
    get / get_where / get_*   optional retrieval (T | None)
    require / require_*       mandatory retrieval or invariant (raises)
    has / is_*                boolean predicates
    iter_*                    lazy multi-result walks
    collect_*                 eager multi-result gathers
    from_*                    factories
    _validate_*               Pydantic / domain validators (private)
    _*                        other private helpers
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Callable, Hashable, Iterator, Mapping, Sequence
from functools import cached_property
from typing import Any, Protocol, TypeVar, cast, runtime_checkable

from pydantic import BaseModel, ConfigDict, model_validator

TId = TypeVar("TId", bound=Hashable, covariant=True)
TKey = TypeVar("TKey", bound=Hashable)
TItem = TypeVar("TItem")
TNode = TypeVar("TNode", bound="TreeNodeMixin")


@runtime_checkable
class Identifiable(Protocol[TId]):
    """Protocol for domain objects with a stable identifier."""

    @property
    def id(self) -> TId:
        """Unique identifier for this object."""
        ...


@runtime_checkable
class Nameable(Protocol):
    """Protocol for domain objects with a human-readable name."""

    @property
    def name(self) -> str:
        """Human-readable name for this object."""
        ...


class DomainValueObject(BaseModel):
    """Immutable value-object base with strict validation.

    Does not strip whitespace: governance prose must be preserved exactly.
    """

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
        populate_by_name=True,
        ignored_types=(cached_property,),
    )


class StringCoercibleVO(DomainValueObject):
    """Value object constructible from a formatted string.

    Subclasses implement ``_parse_string``. Pydantic routes string input
    through the before-validator automatically via ``model_validate``.
    """

    @model_validator(mode="before")
    @classmethod
    def _coerce_string(cls, data: Any) -> Any:
        result: Any = data
        if isinstance(data, str):
            result = cls._parse_string(data)
        return result

    @classmethod
    def _parse_string(cls, value: str) -> dict[str, Any]:
        raise NotImplementedError(f"{cls.__name__} must implement _parse_string")

    def __str__(self) -> str:
        raise NotImplementedError(f"{type(self).__name__} must implement __str__")


class IndexedLookupMixin[TKey: Hashable, TItem]:
    """Shared keyed lookup over a host-provided ``_index`` mapping.

    Host classes implement ``_index`` (often via ``@cached_property``).
    Public API is the domain-wide lookup trio: ``get`` / ``require`` / ``has``.
    """

    def _lookup_index(self) -> Mapping[TKey, TItem]:
        return cast(Mapping[TKey, TItem], cast(Any, self)._index)

    def get(self, key: TKey) -> TItem | None:
        """Return the item for ``key``, or None when absent."""
        return self._lookup_index().get(key)

    def require(self, key: TKey) -> TItem:
        """Return the item for ``key``, or raise KeyError when absent."""
        index = self._lookup_index()
        try:
            result = index[key]
        except KeyError as exc:
            raise KeyError(f"Item with key '{key}' not found") from exc
        return result

    def has(self, key: TKey) -> bool:
        """Return True if an item with ``key`` exists."""
        return key in self._lookup_index()

    @property
    def ids(self) -> tuple[TKey, ...]:
        """Return keys in index order."""
        return tuple(self._lookup_index())


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


class NameableMixin:
    """Expose a ``title`` field as ``name`` for the Nameable protocol."""

    @property
    def name(self) -> str:
        """Human-readable name (alias for title)."""
        return self.title  # type: ignore[attr-defined]


class TreeNodeMixin:
    """Hierarchical traversal for hosts that expose a ``children`` sequence.

    Depth uses node-counting semantics (a leaf has depth 1), matching the
    governance rule “do not exceed N levels of nested sections”.

    Lookup style matches :class:`IndexedLookupMixin`:
    ``get`` / ``require`` by id; ``get_where`` / ``collect_where`` by predicate.
    """

    def _child_nodes(self: TNode) -> Sequence[TNode]:
        return cast(Sequence[TNode], cast(Any, self).children)

    def iter_nodes(self: TNode) -> Iterator[TNode]:
        """Yield this node and all descendants in pre-order."""
        yield self
        for child in self._child_nodes():
            yield from child.iter_nodes()

    # Alias kept for graph/tree vocabulary call sites.
    traverse = iter_nodes

    def get_where(self: TNode, predicate: Callable[[TNode], bool]) -> TNode | None:
        """Return the first node matching ``predicate``, or None."""
        result: TNode | None = None
        for node in self.iter_nodes():
            if predicate(node):
                result = node
                break
        return result

    def collect_where(self: TNode, predicate: Callable[[TNode], bool]) -> list[TNode]:
        """Return all nodes matching ``predicate`` (pre-order)."""
        return [node for node in self.iter_nodes() if predicate(node)]

    def get(self: TNode, key: Hashable) -> TNode | None:
        """Return the first node whose ``id`` equals ``key``, or None."""
        return self.get_where(lambda node: getattr(node, "id", None) == key)

    def require(self: TNode, key: Hashable) -> TNode:
        """Return the first node whose ``id`` equals ``key``, or raise KeyError."""
        result = self.get(key)
        if result is None:
            raise KeyError(f"Item with key '{key}' not found")
        return result

    def has(self, key: Hashable) -> bool:
        """Return True if a node with ``id`` equal to ``key`` exists."""
        return self.get(key) is not None

    def max_depth(self, current: int = 1) -> int:
        """Return maximum depth from this node to any leaf (leaf depth = ``current``)."""
        children = self._child_nodes()
        result = current
        if children:
            result = max(child.max_depth(current + 1) for child in children)
        return result
