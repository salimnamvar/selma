"""Domain Model Base.

Shared immutable base, protocols, mixins, and small validation helpers.

Construction and serialization use Pydantic v2 natively:
    - model_validate / model_validate_json
    - model_dump / model_dump_json
"""

from __future__ import annotations

from collections.abc import Callable, Hashable, Iterator, Sequence
from functools import cached_property
from typing import Any, Optional, Protocol, Set, TypeVar, cast, runtime_checkable

from pydantic import BaseModel, ConfigDict

TId = TypeVar("TId", bound=Hashable, covariant=True)
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
    """Protocol for domain objects with a name/title."""

    @property
    def name(self) -> str:
        """Human-readable name for this object."""
        ...


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
        seen: Set[Hashable] = set()
        duplicates: Set[Hashable] = set()
        for id_ in a_ids:
            if id_ in seen:
                duplicates.add(id_)
            seen.add(id_)
        raise ValueError(f"Duplicate {a_label} found: {duplicates}")


def none_as_empty(a_value: Any) -> Any:
    """Coerce YAML/JSON null to an empty tuple for optional sequence fields.

    Args:
        a_value: Raw input value.

    Returns:
        Empty tuple when ``a_value`` is None, otherwise ``a_value`` unchanged.
    """
    return () if a_value is None else a_value


class NameableMixin:
    """Expose a ``title`` field as ``name`` for the Nameable protocol."""

    @property
    def name(self) -> str:
        """Human-readable name (alias for title)."""
        return self.title  # type: ignore[attr-defined]


class TreeNodeMixin:
    """Hierarchical traversal for objects that expose a ``children`` sequence.

    Host classes must provide ``children`` (e.g. a Pydantic field). This mixin
    does not declare ``children`` so it cannot shadow model fields.
    """

    def _child_nodes(self: TNode) -> Sequence[TNode]:
        """Return child nodes from the host's ``children`` attribute."""
        return cast(Sequence[TNode], cast(Any, self).children)

    def traverse(self: TNode) -> Iterator[TNode]:
        """Yield this node and all descendants in pre-order."""
        yield self
        for child in self._child_nodes():
            yield from child.traverse()

    def find(self: TNode, a_predicate: Callable[[TNode], bool]) -> Optional[TNode]:
        """Return the first node matching ``a_predicate``, or None."""
        if a_predicate(self):
            return self
        for child in self._child_nodes():
            found: Optional[TNode] = child.find(a_predicate)
            if found is not None:
                return found
        return None

    def find_by_id(self: TNode, a_id: Hashable) -> Optional[TNode]:
        """Return the first node whose ``id`` equals ``a_id``, or None."""
        return self.find(lambda node: getattr(node, "id", None) == a_id)

    def depth(self, a_current: int = 0) -> int:
        """Return maximum depth from this node to any leaf (leaf depth = ``a_current``)."""
        children: Sequence[TreeNodeMixin] = cast(Sequence[TreeNodeMixin], cast(Any, self).children)
        if not children:
            return a_current
        return max(child.depth(a_current + 1) for child in children)
