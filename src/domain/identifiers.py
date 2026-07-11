"""Domain identifiers and scalar value types."""

from __future__ import annotations

import re
from typing import Annotated, Any, Self

from pydantic import Field, model_validator

from domain.base import DomainValueObject

# Non-empty governance prose (descriptions, guidance, intent statements).
GovernanceText = Annotated[
    str,
    Field(min_length=1, description="Non-empty governance guidance, description, or intent"),
]

MachineId = Annotated[
    str,
    Field(
        pattern=r"^[A-Z][A-Z0-9]+-[0-9]+$",
        description="Immutable lineage identifier assigned at directive authoring time",
    ),
]

WritingPrincipleId = Annotated[
    str,
    Field(pattern=r"^WP-\d{3}$", description="Unique writing principle identifier"),
]

SectionId = Annotated[
    str,
    Field(pattern=r"^[a-z][a-z0-9_]*$", description="Unique document section identifier"),
]

RuleContractId = Annotated[
    str,
    Field(
        pattern=r"^[a-z][a-z0-9-]*$",
        min_length=1,
        description="Identifier of the compatible rule schema",
    ),
]

_SEMVER_RE = re.compile(r"^(\d+)\.(\d+)\.(\d+)$")


class SemanticVersion(DomainValueObject):
    """Semantic version with structured components and MAJOR compatibility rules.

    Accepts either component kwargs or a ``MAJOR.MINOR.PATCH`` string so
    doctrine documents can load versions directly from YAML scalars.
    """

    major: int = Field(ge=0, description="Breaking changes that require migration")
    minor: int = Field(ge=0, description="New backward-compatible features")
    patch: int = Field(ge=0, description="Bug fixes and clarifications")

    @model_validator(mode="before")
    @classmethod
    def _parse_string(cls, data: Any) -> Any:
        if isinstance(data, str):
            match = _SEMVER_RE.fullmatch(data)
            if match is None:
                msg = f"Invalid semantic version {data!r}; expected MAJOR.MINOR.PATCH"
                raise ValueError(msg)
            return {
                "major": int(match.group(1)),
                "minor": int(match.group(2)),
                "patch": int(match.group(3)),
            }
        return data

    def __str__(self) -> str:
        return f"{self.major}.{self.minor}.{self.patch}"

    def __repr__(self) -> str:
        return f"SemanticVersion({self!s})"

    def is_compatible_with(self, other: SemanticVersion) -> bool:
        """Return True when both versions share the same MAJOR component.

        This is the doctrine synchronization rule: documents must share the
        same MAJOR family; MINOR and PATCH may diverge independently.
        """
        return self.major == other.major

    def __lt__(self, other: object) -> bool:
        if not isinstance(other, SemanticVersion):
            return NotImplemented
        return (self.major, self.minor, self.patch) < (other.major, other.minor, other.patch)

    def __le__(self, other: object) -> bool:
        if not isinstance(other, SemanticVersion):
            return NotImplemented
        return self == other or self < other

    def __gt__(self, other: object) -> bool:
        if not isinstance(other, SemanticVersion):
            return NotImplemented
        return (self.major, self.minor, self.patch) > (other.major, other.minor, other.patch)

    def __ge__(self, other: object) -> bool:
        if not isinstance(other, SemanticVersion):
            return NotImplemented
        return self == other or self > other

    @classmethod
    def from_string(cls, value: str) -> Self:
        """Construct from a ``MAJOR.MINOR.PATCH`` string."""
        return cls.model_validate(value)


class FieldPath(DomainValueObject):
    """Structured location of an identity field across layers.

    Accepts either a dotted path string (e.g. ``rules[].lineage_id``) or
    explicit collection/field components.
    """

    collection: str = Field(min_length=1, description="Collection or container name")
    field: str = Field(min_length=1, description="Field name within the collection")
    raw: str = Field(min_length=1, description="Original path expression as authored")

    @model_validator(mode="before")
    @classmethod
    def _parse_path(cls, data: Any) -> Any:
        if isinstance(data, str):
            raw = data.strip()
            if not raw:
                raise ValueError("Field path must be non-empty")
            # Accept forms like "rules[].lineage_id" or "CG-IR nodes[].directive_id"
            if "[]." in raw:
                collection, field = raw.rsplit("[].", maxsplit=1)
            elif "." in raw:
                collection, field = raw.rsplit(".", maxsplit=1)
            else:
                collection, field = raw, raw
            return {"collection": collection.strip(), "field": field.strip(), "raw": raw}
        return data

    def __str__(self) -> str:
        return self.raw
