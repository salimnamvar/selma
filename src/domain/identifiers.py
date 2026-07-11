"""Domain Identifiers.

Scalar types and structured identifiers for the policy doctrine domain.

Type Aliases:
    GovernanceText: Non-empty governance prose.
    MachineId: Immutable lineage identifier pattern.
    WritingPrincipleId: Writing principle identifier pattern.
    SectionId: Document section identifier pattern.
    RuleContractId: Compatible rule schema identifier pattern.

Classes:
    SemanticVersion: Structured MAJOR.MINOR.PATCH with compatibility checks.
    FieldPath: Structured cross-layer identity field location.

Construction and validation use Pydantic v2 (``model_validate`` / field
constraints). Callers should not wrap these with custom factory methods.
"""

from __future__ import annotations

from functools import total_ordering
from typing import Annotated, Any

from pydantic import Field, model_validator

from domain.base import DomainValueObject

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


@total_ordering
class SemanticVersion(DomainValueObject):
    """Semantic version with structured components and MAJOR compatibility.

    Accepts component kwargs or a ``MAJOR.MINOR.PATCH`` string via
    ``model_validate`` (Pydantic before-validator coercion).

    Attributes:
        major (int): Breaking changes that require migration.
        minor (int): New backward-compatible features.
        patch (int): Bug fixes and clarifications.
    """

    major: int = Field(ge=0, description="Breaking changes that require migration")
    minor: int = Field(ge=0, description="New backward-compatible features")
    patch: int = Field(ge=0, description="Bug fixes and clarifications")

    @model_validator(mode="before")
    @classmethod
    def _coerce_string(cls, a_data: Any) -> Any:
        """Coerce a MAJOR.MINOR.PATCH string into component fields."""
        result: Any = a_data
        if isinstance(a_data, str):
            parts: list[str] = a_data.split(".")
            if len(parts) != 3 or not all(part.isdigit() for part in parts):
                raise ValueError(f"Invalid semantic version {a_data!r}; expected MAJOR.MINOR.PATCH")
            result = {
                "major": int(parts[0]),
                "minor": int(parts[1]),
                "patch": int(parts[2]),
            }
        return result

    def __str__(self) -> str:
        return f"{self.major}.{self.minor}.{self.patch}"

    def is_compatible_with(self, a_other: SemanticVersion) -> bool:
        """Return True when both versions share the same MAJOR component."""
        result: bool = self.major == a_other.major
        return result

    def __lt__(self, a_other: object) -> bool:
        result: bool = NotImplemented
        if isinstance(a_other, SemanticVersion):
            result = (self.major, self.minor, self.patch) < (
                a_other.major,
                a_other.minor,
                a_other.patch,
            )
        return result


class FieldPath(DomainValueObject):
    """Structured location of an identity field across layers.

    Accepts a dotted path string (e.g. ``rules[].lineage_id``) or components
    via ``model_validate``.

    Attributes:
        collection (str): Collection or container name.
        field (str): Field name within the collection.
        raw (str): Original path expression as authored.
    """

    collection: str = Field(min_length=1, description="Collection or container name")
    field: str = Field(min_length=1, description="Field name within the collection")
    raw: str = Field(min_length=1, description="Original path expression as authored")

    @model_validator(mode="before")
    @classmethod
    def _coerce_string(cls, a_data: Any) -> Any:
        """Coerce a dotted path string into collection/field components."""
        result: Any = a_data
        if isinstance(a_data, str):
            raw: str = a_data.strip()
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
            result = {"collection": collection.strip(), "field": field.strip(), "raw": raw}
        return result

    def __str__(self) -> str:
        return self.raw
