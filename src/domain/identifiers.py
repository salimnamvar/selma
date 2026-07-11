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
"""

from __future__ import annotations

import re
from typing import Annotated, Any, ClassVar, Dict, Match, Optional, Pattern, Self

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


class SemanticVersion(DomainValueObject):
    """Semantic version with structured components and MAJOR compatibility.

    Attributes:
        major (int): Breaking changes that require migration.
        minor (int): New backward-compatible features.
        patch (int): Bug fixes and clarifications.
    """

    _PATTERN: ClassVar[Pattern[str]] = re.compile(r"^(\d+)\.(\d+)\.(\d+)$")

    major: int = Field(ge=0, description="Breaking changes that require migration")
    minor: int = Field(ge=0, description="New backward-compatible features")
    patch: int = Field(ge=0, description="Bug fixes and clarifications")

    @model_validator(mode="before")
    @classmethod
    def _parse_string(cls, a_data: Any) -> Any:
        """Parse a MAJOR.MINOR.PATCH string into component fields.

        Args:
            a_data (Any): Raw input (string or mapping).

        Returns:
            Any: Parsed mapping or original input.
        """
        result: Any = a_data
        if isinstance(a_data, str):
            match: Optional[Match[str]] = cls._PATTERN.fullmatch(a_data)
            if match is None:
                msg: str = f"Invalid semantic version {a_data!r}; expected MAJOR.MINOR.PATCH"
                raise ValueError(msg)
            result = {
                "major": int(match.group(1)),
                "minor": int(match.group(2)),
                "patch": int(match.group(3)),
            }
        return result

    def __str__(self) -> str:
        return f"{self.major}.{self.minor}.{self.patch}"

    def __repr__(self) -> str:
        return f"SemanticVersion({self!s})"

    def is_compatible_with(self, a_other: SemanticVersion) -> bool:
        """Return True when both versions share the same MAJOR component.

        Args:
            a_other (SemanticVersion): Version to compare against.

        Returns:
            bool: True if MAJOR versions match.
        """
        result: bool = self.major == a_other.major
        return result

    def __lt__(self, a_other: object) -> bool:
        result: bool = NotImplemented  # type: ignore[assignment]
        if isinstance(a_other, SemanticVersion):
            result = (self.major, self.minor, self.patch) < (
                a_other.major,
                a_other.minor,
                a_other.patch,
            )
        return result

    def __le__(self, a_other: object) -> bool:
        result: bool = NotImplemented  # type: ignore[assignment]
        if isinstance(a_other, SemanticVersion):
            result = self == a_other or self < a_other
        return result

    def __gt__(self, a_other: object) -> bool:
        result: bool = NotImplemented  # type: ignore[assignment]
        if isinstance(a_other, SemanticVersion):
            result = (self.major, self.minor, self.patch) > (
                a_other.major,
                a_other.minor,
                a_other.patch,
            )
        return result

    def __ge__(self, a_other: object) -> bool:
        result: bool = NotImplemented  # type: ignore[assignment]
        if isinstance(a_other, SemanticVersion):
            result = self == a_other or self > a_other
        return result

    @classmethod
    def from_string(cls, a_value: str) -> Self:
        """Construct from a MAJOR.MINOR.PATCH string.

        Args:
            a_value (str): Version string.

        Returns:
            Self: Parsed semantic version.
        """
        result: Self = cls.model_validate(a_value)
        return result


class FieldPath(DomainValueObject):
    """Structured location of an identity field across layers.

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
    def _parse_path(cls, a_data: Any) -> Any:
        """Parse a dotted path string into collection/field components.

        Args:
            a_data (Any): Raw input (string or mapping).

        Returns:
            Any: Parsed mapping or original input.
        """
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
            parsed: Dict[str, str] = {
                "collection": collection.strip(),
                "field": field.strip(),
                "raw": raw,
            }
            result = parsed
        return result

    def __str__(self) -> str:
        return self.raw
