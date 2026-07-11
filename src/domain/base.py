"""Domain Model Base.

Shared immutable base and small validation helpers for governance value objects.
"""

from __future__ import annotations

from collections.abc import Callable, Hashable, Iterator, Sequence
from functools import cached_property
from typing import Any, Dict, FrozenSet, Optional, Protocol, runtime_checkable, Set, TypeVar

from pydantic import BaseModel
from pydantic import ConfigDict

TId = TypeVar("TId", bound=Hashable)
TItem = TypeVar("TItem")


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
    """Immutable value-object base with strict validation, alias support, and standardized serialization.

    Standardized methods:
        - from_dict(data) -> Self: Create from dictionary (alias for model_validate)
        - from_json(json_str) -> Self: Create from JSON string (alias for model_validate_json)
        - to_dict() -> dict: Convert to dictionary (alias for model_dump)
        - to_json(**kwargs) -> str: Convert to JSON string (alias for model_dump_json)
        - validate() -> Self: Validate the model (returns self)
    """

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
        populate_by_name=True,
        str_strip_whitespace=True,
        ignored_types=(cached_property,),
    )

    # Standardized class methods for construction
    @classmethod
    def from_dict(cls, a_data: Dict[str, Any]) -> "DomainValueObject":
        """Create instance from dictionary.

        Args:
            a_data: Dictionary containing model field values.

        Returns:
            Validated instance of the model.

        Raises:
            ValidationError: If the data does not conform to the model schema.
        """
        return cls.model_validate(a_data)

    @classmethod
    def from_json(cls, a_json_str: str, **kwargs: Any) -> "DomainValueObject":
        """Create instance from JSON string.

        Args:
            a_json_str: JSON string containing model data.
            **kwargs: Additional arguments passed to model_validate_json.

        Returns:
            Validated instance of the model.

        Raises:
            ValidationError: If the JSON does not conform to the model schema.
        """
        return cls.model_validate_json(a_json_str, **kwargs)

    # Standardized instance methods for serialization
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary.

        Returns:
            Dictionary representation of the model.
        """
        return self.model_dump()

    def to_json(self, **kwargs: Any) -> str:
        """Convert to JSON string.

        Args:
            **kwargs: Additional arguments passed to model_dump_json.

        Returns:
            JSON string representation of the model.
        """
        return self.model_dump_json(**kwargs)

    # Standardized validation method
    def validate(self) -> "DomainValueObject":
        """Validate the model instance.

        Pydantic performs validation automatically during construction.
        This method is provided for API consistency and can be overridden
        in subclasses for additional validation logic.

        Returns:
            Self, for method chaining.
        """
        # Pydantic validation is automatic on construction
        return self


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


def ensure_non_empty(a_value: str, a_field_name: str) -> str:
    """Ensure string value is non-empty and stripped.

    Args:
        a_value: String value to check.
        a_field_name: Name of the field for error messages.

    Returns:
        Stripped string value.

    Raises:
        ValueError: If the string is empty or whitespace-only.
    """
    if not a_value or not a_value.strip():
        raise ValueError(f"{a_field_name} must be non-empty")
    return a_value.strip()


def validate_unique_field_values(
    a_items: Sequence[Any],
    a_field_name: str,
    a_label: str,
) -> None:
    """Generic validator for unique field values across a sequence of items.

    Args:
        a_items: Sequence of items to check.
        a_field_name: Name of the field to extract and check for uniqueness.
        a_label: Human-readable label for error messages.

    Raises:
        ValueError: If duplicate field values are found.
    """
    values: list[Any] = [getattr(item, a_field_name) for item in a_items]
    if len(values) != len(set(values)):
        seen: Set[Any] = set()
        duplicates: Set[Any] = set()
        for value in values:
            if value in seen:
                duplicates.add(value)
            seen.add(value)
        raise ValueError(f"Duplicate {a_label} found: {duplicates}")


def validate_required_fields(
    a_obj: Any,
    a_required_fields: Sequence[str],
    a_obj_type: str,
) -> None:
    """Generic validator for required fields.

    Args:
        a_obj: Object to validate.
        a_required_fields: List of field names that must be non-empty.
        a_obj_type: Type name for error messages.

    Raises:
        ValueError: If any required field is missing or empty.
    """
    missing: list[str] = [field for field in a_required_fields if not getattr(a_obj, field, None)]
    if missing:
        raise ValueError(f"{a_obj_type} missing required fields: {missing}")


def validate_enum_coverage(
    a_values: Sequence[Any],
    a_enum_type: type,
    a_field_name: str,
) -> None:
    """Generic validator for enum value coverage.

    Args:
        a_values: Sequence of enum values to check.
        a_enum_type: The enum class that defines valid values.
        a_field_name: Name of the field for error messages.

    Raises:
        ValueError: If values are missing from or outside the enum.
    """
    expected: FrozenSet[Any] = frozenset(a_enum_type)
    present: FrozenSet[Any] = frozenset(a_values)

    invalid: FrozenSet[Any] = present - expected
    if invalid:
        raise ValueError(f"Invalid {a_field_name} values: {invalid}")

    missing: FrozenSet[Any] = expected - present
    if missing:
        raise ValueError(f"Missing {a_field_name} values: {missing}")


class SerializableMixin:
    """Mixin class for standardized serialization support.

    Provides consistent serialization methods that delegate to Pydantic's
    built-in methods. This mixin ensures all domain objects have a
    predictable serialization API.
    """

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return self.model_dump()  # type: ignore[union-attr]

    def to_json(self, **kwargs: Any) -> str:
        """Convert to JSON string."""
        return self.model_dump_json(**kwargs)  # type: ignore[union-attr]

    @classmethod
    def from_dict(cls, a_data: Dict[str, Any]) -> "SerializableMixin":
        """Create from dictionary."""
        return cls.model_validate(a_data)  # type: ignore[union-attr]

    @classmethod
    def from_json(cls, a_json_str: str, **kwargs: Any) -> "SerializableMixin":
        """Create from JSON string."""
        return cls.model_validate_json(a_json_str, **kwargs)  # type: ignore[union-attr]


class NameableMixin:
    """Mixin class for domain objects that have a title field and wants to expose it as name.
    
    Provides a standardized `name` property that returns the `title` field.
    This eliminates duplicated property definitions in classes that have both
    title and name concepts.
    """

    @property
    def name(self) -> str:
        """Human-readable name for this object (alias for title)."""
        return self.title  # type: ignore[union-attr]


class TreeNodeMixin:
    """Mixin class for hierarchical/tree-structured domain objects.

    Provides standardized tree traversal and search methods. Subclasses
    must implement the `children` property.
    """

    @property
    def children(self) -> tuple:
        """Return child nodes.

        Must be implemented by subclasses.
        """
        raise NotImplementedError("TreeNodeMixin.children must be implemented by subclasses")

    def traverse(self) -> Iterator["TreeNodeMixin"]:
        """Yield this node and all descendants in pre-order.

        Returns:
            Iterator over all nodes in the tree rooted at this node.
        """
        yield self  # type: ignore[union-attr]
        for child in self.children:
            yield from child.traverse()  # type: ignore[union-attr]

    def find(self, a_predicate: Callable[[Any], bool]) -> Optional[Any]:
        """Find first node in tree matching predicate.

        Args:
            a_predicate: Callable that returns True for matching nodes.

        Returns:
            First node in pre-order traversal that matches the predicate,
            or None if no match is found.
        """
        if a_predicate(self):  # type: ignore[union-attr]
            return self  # type: ignore[union-attr]
        for child in self.children:
            found = child.find(a_predicate)  # type: ignore[union-attr]
            if found is not None:
                return found
        return None

    def find_by_id(self, a_id: Hashable) -> Optional[Any]:
        """Find node by ID in tree.

        Args:
            a_id: Identifier to search for.

        Returns:
            Node with matching ID, or None if not found.
        """
        return self.find(lambda node: getattr(node, "id", None) == a_id)  # type: ignore[union-attr]

    def depth(self, a_current: int = 0) -> int:
        """Calculate maximum depth of the subtree rooted at this node.

        Args:
            a_current: Current depth (used for recursion).

        Returns:
            Maximum depth from this node to any leaf.
        """
        if not self.children:  # type: ignore[union-attr]
            return a_current
        return max(child.depth(a_current + 1) for child in self.children)  # type: ignore[union-attr]
