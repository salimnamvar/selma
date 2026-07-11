"""Domain Model Base.

Shared immutable base, protocols, mixins, and small validation helpers.

Construction and serialization use Pydantic v2 natively:
    - model_validate / model_validate_json
    - model_dump / model_dump_json
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Callable, Hashable, Iterator, Sequence
from functools import cached_property
from typing import Any, Protocol, TypeVar, cast, runtime_checkable

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
    """Raise ValueError when the sequence contains duplicate identifiers."""
    dupes = {id_ for id_, count in Counter(a_ids).items() if count > 1}
    if dupes:
        raise ValueError(f"Duplicate {a_label} found: {dupes}")


def none_as_empty(a_value: Any) -> Any:
    """Coerce YAML/JSON null to an empty tuple for optional sequence fields."""
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

    def find(self: TNode, a_predicate: Callable[[TNode], bool]) -> TNode | None:
        """Return the first node matching ``a_predicate``, or None."""
        result: TNode | None = self if a_predicate(self) else None
        for child in self._child_nodes():
            if result is None:
                result = child.find(a_predicate)
        return result

    def find_by_id(self: TNode, a_id: Hashable) -> TNode | None:
        """Return the first node whose ``id`` equals ``a_id``, or None."""
        return self.find(lambda node: getattr(node, "id", None) == a_id)

    def depth(self, a_current: int = 0) -> int:
        """Return maximum depth from this node to any leaf (leaf depth = ``a_current``)."""
        children: Sequence[TreeNodeMixin] = cast(Sequence[TreeNodeMixin], cast(Any, self).children)
        return a_current if not children else max(child.depth(a_current + 1) for child in children)
