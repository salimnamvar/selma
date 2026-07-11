"""Domain identifiers — Annotated scalar aliases and field-path helpers."""

from __future__ import annotations

from typing import Annotated

from packaging.version import InvalidVersion, Version
from pydantic import BeforeValidator, Field

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

def _normalize_field_path(value: str) -> str:
    """Strip and reject empty field path strings."""
    raw = value.strip()
    if not raw:
        raise ValueError("Field path must be non-empty")
    return raw


type FieldPath = Annotated[
    str,
    BeforeValidator(_normalize_field_path),
    Field(min_length=1, description="Original path expression as authored"),
]


def parse_semver(value: SemanticVersion) -> Version:
    """Parse a validated semantic version string via packaging."""
    try:
        return Version(value)
    except InvalidVersion as exc:
        raise ValueError(f"Invalid semantic version {value!r}") from exc


def major_version(version: SemanticVersion) -> str:
    """Return the MAJOR component of a semantic version string."""
    return version.partition(".")[0]


def is_major_compatible(left: SemanticVersion, right: SemanticVersion) -> bool:
    """Return True when both versions share the same MAJOR component."""
    return major_version(left) == major_version(right)


def split_field_path(path: FieldPath) -> tuple[str, str]:
    """Parse a path expression into collection and field components."""
    raw = path.strip()
    if "[]." in raw:
        collection, field = raw.rsplit("[].", maxsplit=1)
    elif "." in raw:
        collection, field = raw.rsplit(".", maxsplit=1)
    else:
        collection, field = raw, raw
    return collection.strip(), field.strip()


def field_path_collection(path: FieldPath) -> str:
    """Return the collection component of a field path."""
    return split_field_path(path)[0]


def field_path_field(path: FieldPath) -> str:
    """Return the field component of a field path."""
    return split_field_path(path)[1]


def field_path_is_field(path: FieldPath, name: str) -> bool:
    """Return True when ``path`` ends at the given field name."""
    return field_path_field(path) == name