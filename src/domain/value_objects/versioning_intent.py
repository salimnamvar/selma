"""Versioning intent — semantic versioning purpose across doctrine artifacts."""

from __future__ import annotations

from pydantic import BaseModel, Field

from domain.base import VO_CONFIG
from domain.identifiers import GovernanceText


class VersionComponentIntent(BaseModel):
    """When to increment each semantic version component."""

    model_config = VO_CONFIG

    major: GovernanceText = Field(description="When to increment MAJOR version")
    minor: GovernanceText = Field(description="When to increment MINOR version")
    patch: GovernanceText = Field(description="When to increment PATCH version")


class VersioningIntent(BaseModel):
    """Versioning intent for doctrine, schema, and specification documents."""

    model_config = VO_CONFIG

    description: GovernanceText = Field(description="Versioning strategy overview")
    version_format: GovernanceText = Field(description="Version format pattern")
    intent: VersionComponentIntent = Field(description="Version increment intent per component")
    migration_intent: GovernanceText = Field(
        description="Migration rules when crossing MAJOR version boundaries"
    )
    synchronization_intent: GovernanceText = Field(
        description="How versions synchronize across documents"
    )