"""Domain identifiers — Annotated scalar aliases and SemanticVersion."""

from __future__ import annotations

import re
from typing import Annotated, Any

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field
from pydantic import model_validator

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

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
    )

    major: int = Field(ge=0, description="MAJOR version component")
    minor: int = Field(ge=0, description="MINOR version component")
    patch: int = Field(ge=0, description="PATCH version component")

    @model_validator(mode="before")
    @classmethod
    def _parse_string(cls, value: Any) -> Any:
        if isinstance(value, str):
            if not re.match(r"^\d+\.\d+\.\d+$", value):
                raise ValueError(f"Invalid semantic version {value!r}; expected MAJOR.MINOR.PATCH")
            major, minor, patch = value.split(".")
            value = {"major": int(major), "minor": int(minor), "patch": int(patch)}
        elif not isinstance(value, (cls, dict)):
            raise TypeError(f"Cannot validate SemanticVersion from {type(value)!r}")
        return value

    def is_compatible(self, other: SemanticVersion) -> bool:
        """Return True when both versions share the same MAJOR component."""
        return self.major == other.major

    def __str__(self) -> str:
        return f"{self.major}.{self.minor}.{self.patch}"
