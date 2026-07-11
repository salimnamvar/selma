"""Version strategy — semantic versioning purpose across doctrine artifacts."""

from __future__ import annotations

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field

from domain.identifiers import GovernanceText


class Intent(BaseModel):
    """When to increment each semantic version component."""

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
    )

    major: GovernanceText = Field(description="When to increment MAJOR version")
    minor: GovernanceText = Field(description="When to increment MINOR version")
    patch: GovernanceText = Field(description="When to increment PATCH version")


class VersionStrategy(BaseModel):
    """Versioning intent for doctrine, schema, and specification documents."""

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
    )

    description: GovernanceText = Field(description="Versioning strategy overview")
    version_format: GovernanceText = Field(description="Version format pattern")
    intent: Intent = Field(description="Version increment intent per component")
    migration_intent: GovernanceText = Field(description="Migration rules when crossing MAJOR version boundaries")
    synchronization_intent: GovernanceText = Field(description="How versions synchronize across documents")
