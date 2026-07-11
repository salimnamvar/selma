"""Domain identifiers — constrained string aliases and FieldPath."""

from __future__ import annotations

from typing import Annotated, Any

from pydantic import Field, model_validator

from domain.base import DomainValueObject

type GovernanceText = Annotated[
    str,
    Field(min_length=1, description="Non-empty governance guidance, description, or intent"),
]

type MachineId = Annotated[
    str,
    Field(
        pattern=r"^[A-Z][A-Z0-9]+-[0-9]+$",
        description="Immutable lineage identifier assigned at directive authoring time",
    ),
]

type WritingPrincipleId = Annotated[
    str,
    Field(pattern=r"^WP-\d{3}$", description="Unique writing principle identifier"),
]

type SectionId = Annotated[
    str,
    Field(pattern=r"^[a-z][a-z0-9_]*$", description="Unique document section identifier"),
]

type RuleContractId = Annotated[
    str,
    Field(
        pattern=r"^[a-z][a-z0-9-]*$",
        min_length=1,
        description="Identifier of the compatible rule schema",
    ),
]

type SemanticVersion = Annotated[
    str,
    Field(
        pattern=r"^\d+\.\d+\.\d+$",
        description="Semantic version in MAJOR.MINOR.PATCH format",
    ),
]


def major_version(version: SemanticVersion) -> str:
    """Return the MAJOR component of a semantic version string."""
    return version.partition(".")[0]


def is_major_compatible(left: SemanticVersion, right: SemanticVersion) -> bool:
    """Return True when both versions share the same MAJOR component."""
    return major_version(left) == major_version(right)


class FieldPath(DomainValueObject):
    """Structured location of an identity field (string-coercible)."""

    collection: str = Field(min_length=1, description="Collection or container name")
    field: str = Field(min_length=1, description="Field name within the collection")
    raw: str = Field(min_length=1, description="Original path expression as authored")

    @model_validator(mode="before")
    @classmethod
    def _parse_string(cls, value: Any) -> Any:
        result: Any = value
        if isinstance(value, str):
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
            result = {
                "collection": collection.strip(),
                "field": field.strip(),
                "raw": raw,
            }
        return result

    def __str__(self) -> str:
        return self.raw

    def is_field(self, name: str) -> bool:
        """Return True when this path ends at the given field name."""
        return self.field == name