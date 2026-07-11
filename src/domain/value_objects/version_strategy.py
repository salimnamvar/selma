"""Version strategy — semantic versioning purpose across doctrine artifacts."""

from __future__ import annotations

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field


class Intent(BaseModel):
    """When to increment each semantic version component."""

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
    )

    major: str = Field(min_length=1, description="When to increment MAJOR version")
    minor: str = Field(min_length=1, description="When to increment MINOR version")
    patch: str = Field(min_length=1, description="When to increment PATCH version")


class VersionStrategy(BaseModel):
    """Versioning intent for doctrine, schema, and specification documents."""

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
    )

    description: str = Field(min_length=1, description="Versioning strategy overview")
    version_format: str = Field(min_length=1, description="Version format pattern")
    intent: Intent = Field(description="Version increment intent per component")
    migration_intent: str = Field(min_length=1, description="Migration rules when crossing MAJOR version boundaries")
    synchronization_intent: str = Field(min_length=1, description="How versions synchronize across documents")
