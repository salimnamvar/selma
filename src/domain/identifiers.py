"""Domain identifiers — Annotated scalar aliases and SemanticVersion."""

from __future__ import annotations

from typing import Annotated, Any

from pydantic import BaseModel, Field, model_validator

from domain.base import VO_CONFIG

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

type SchemaId = Annotated[
    str,
    Field(
        pattern=r"^[a-z][a-z0-9-]*$",
        min_length=1,
        description="Identifier of the compatible rule schema",
    ),
]


class SemanticVersion(BaseModel):
    """Three-component semantic version (MAJOR.MINOR.PATCH)."""

    model_config = VO_CONFIG

    major: int = Field(ge=0, description="MAJOR version component")
    minor: int = Field(ge=0, description="MINOR version component")
    patch: int = Field(ge=0, description="PATCH version component")

    @model_validator(mode="before")
    @classmethod
    def _parse_string(cls, value: Any) -> Any:
        if isinstance(value, cls):
            return value
        if isinstance(value, dict):
            return value
        if isinstance(value, str):
            parts = value.split(".")
            if len(parts) != 3 or not all(part.isdigit() for part in parts):
                raise ValueError(f"Invalid semantic version {value!r}; expected MAJOR.MINOR.PATCH")
            return {"major": int(parts[0]), "minor": int(parts[1]), "patch": int(parts[2])}
        raise TypeError(f"Cannot validate SemanticVersion from {type(value)!r}")

    def is_compatible(self, other: SemanticVersion) -> bool:
        """Return True when both versions share the same MAJOR component."""
        return self.major == other.major

    def __str__(self) -> str:
        return f"{self.major}.{self.minor}.{self.patch}"