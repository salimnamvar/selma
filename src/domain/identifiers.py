"""Domain identifiers and scalar value types."""

from __future__ import annotations

from functools import total_ordering
from typing import Annotated, Any

from pydantic import Field

from domain.base import StringCoercibleVO

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
class SemanticVersion(StringCoercibleVO):
    """Semantic version with structured components and MAJOR compatibility.

    Accepts component kwargs or a ``MAJOR.MINOR.PATCH`` string via
    ``model_validate``.
    """

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
    """Structured location of an identity field across layers.

    Accepts a dotted path string (e.g. ``rules[].lineage_id``) or components
    via ``model_validate``.
    """

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
