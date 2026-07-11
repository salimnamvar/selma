"""Domain identifiers and scalar value types.

Scalar identities and domain text are real value objects (not bare Annotated
strings): they coerce from strings, validate, and can grow behavior.
"""

from __future__ import annotations

from functools import total_ordering
from re import fullmatch
from typing import Annotated, Any, ClassVar

from pydantic import ConfigDict, Field, RootModel, field_validator

from domain.base import StringCoercibleVO


class DomainText(RootModel[str]):
    """Non-empty governance prose (immutable scalar value object)."""

    model_config = ConfigDict(frozen=True)

    root: Annotated[str, Field(min_length=1)]

    def __str__(self) -> str:
        return self.root

    def __eq__(self, other: object) -> bool:
        result: Any = NotImplemented
        if isinstance(other, DomainText):
            result = self.root == other.root
        elif isinstance(other, str):
            result = self.root == other
        return result

    def __hash__(self) -> int:
        return hash(("DomainText", self.root))

    def __contains__(self, item: object) -> bool:
        return str(item) in self.root

    def lower(self) -> str:
        """Return lower-cased text content."""
        return self.root.lower()


# Semantic roles — same constraints, distinct types for precision.
class GovernancePurpose(DomainText):
    """Purpose / role description for a governance layer or artifact."""


class GovernanceGuidance(DomainText):
    """Authoring or operational guidance text."""


class GovernanceConstraint(DomainText):
    """Constraint or prohibition statement."""


class GovernanceDescription(DomainText):
    """General descriptive prose."""


# Backward-compatible alias used across the model where role is generic.
GovernanceText = DomainText


class _PatternId(RootModel[str]):
    """Base for pattern-constrained identifier value objects."""

    model_config = ConfigDict(frozen=True)
    _PATTERN: ClassVar[str] = r".+"
    _LABEL: ClassVar[str] = "identifier"

    root: Annotated[str, Field(min_length=1)]

    @field_validator("root")
    @classmethod
    def _validate_pattern(cls, value: str) -> str:
        if fullmatch(cls._PATTERN, value) is None:
            raise ValueError(f"Invalid {cls._LABEL}: {value!r} (expected /{cls._PATTERN}/)")
        return value

    def __str__(self) -> str:
        return self.root

    def __eq__(self, other: object) -> bool:
        result: Any = NotImplemented
        if isinstance(other, _PatternId):
            result = type(self) is type(other) and self.root == other.root
        elif isinstance(other, str):
            result = self.root == other
        return result

    def __hash__(self) -> int:
        return hash((type(self).__name__, self.root))


class MachineId(_PatternId):
    """Immutable lineage identifier assigned at directive authoring time.

    Pattern: ``^[A-Z][A-Z0-9]+-[0-9]+$`` (e.g. AUTH-001, PAY-800).
    Maps exclusively to lineage_id — never an execution id.
    """

    _PATTERN: ClassVar[str] = r"^[A-Z][A-Z0-9]+-[0-9]+$"
    _LABEL: ClassVar[str] = "Machine ID"

    @property
    def prefix(self) -> str:
        """Namespace prefix before the hyphen."""
        return self.root.split("-", maxsplit=1)[0]

    @property
    def number(self) -> str:
        """Numeric suffix after the hyphen."""
        return self.root.split("-", maxsplit=1)[1]


class WritingPrincipleId(_PatternId):
    """Writing principle identifier (``WP-NNN``)."""

    _PATTERN: ClassVar[str] = r"^WP-\d{3}$"
    _LABEL: ClassVar[str] = "writing principle id"


class SectionId(_PatternId):
    """Document section identifier (snake_case token)."""

    _PATTERN: ClassVar[str] = r"^[a-z][a-z0-9_]*$"
    _LABEL: ClassVar[str] = "section id"


class RuleContractId(_PatternId):
    """Compatible rule schema identifier."""

    _PATTERN: ClassVar[str] = r"^[a-z][a-z0-9-]*$"
    _LABEL: ClassVar[str] = "rule contract id"


@total_ordering
class SemanticVersion(StringCoercibleVO):
    """Semantic version with structured components and MAJOR compatibility."""

    major: int = Field(ge=0, description="Breaking changes that require migration")
    minor: int = Field(ge=0, description="New backward-compatible features")
    patch: int = Field(ge=0, description="Bug fixes and clarifications")

    @classmethod
    def _parse_string(cls, value: str) -> dict[str, Any]:
        parts = value.split(".")
        if len(parts) != 3 or not all(part.isdigit() for part in parts):
            raise ValueError(f"Invalid semantic version {value!r}; expected MAJOR.MINOR.PATCH")
        return {"major": int(parts[0]), "minor": int(parts[1]), "patch": int(parts[2])}

    def __str__(self) -> str:
        return f"{self.major}.{self.minor}.{self.patch}"

    def is_compatible(self, other: SemanticVersion) -> bool:
        """Return True when both versions share the same MAJOR component."""
        return self.major == other.major

    def __lt__(self, other: object) -> bool:
        result: Any = NotImplemented
        if isinstance(other, SemanticVersion):
            result = (self.major, self.minor, self.patch) < (
                other.major,
                other.minor,
                other.patch,
            )
        return result


class FieldPath(StringCoercibleVO):
    """Structured location of an identity field across layers."""

    collection: str = Field(min_length=1, description="Collection or container name")
    field: str = Field(min_length=1, description="Field name within the collection")
    raw: str = Field(min_length=1, description="Original path expression as authored")

    @classmethod
    def _parse_string(cls, value: str) -> dict[str, Any]:
        raw = value.strip()
        if not raw:
            raise ValueError("Field path must be non-empty")
        collection: str
        field: str
        if "[]." in raw:
            collection, field = raw.rsplit("[].", maxsplit=1)
        elif "." in raw:
            collection, field = raw.rsplit(".", maxsplit=1)
        else:
            collection, field = raw, raw
        return {
            "collection": collection.strip(),
            "field": field.strip(),
            "raw": raw,
        }

    def __str__(self) -> str:
        return self.raw

    def is_field(self, name: str) -> bool:
        """Return True when this path ends at the given field name."""
        return self.field == name
