"""Versioning intent — semantic versioning purpose across doctrine artifacts."""

from __future__ import annotations

from pydantic import Field

from domain.base import DomainValueObject
from domain.identifiers import GovernanceDescription, GovernanceGuidance


class VersionComponentIntent(DomainValueObject):
    """When to increment each semantic version component."""

    major: GovernanceGuidance = Field(description="When to increment MAJOR version")
    minor: GovernanceGuidance = Field(description="When to increment MINOR version")
    patch: GovernanceGuidance = Field(description="When to increment PATCH version")


class VersioningIntent(DomainValueObject):
    """Versioning intent for doctrine, schema, and specification documents."""

    description: GovernanceDescription = Field(description="Versioning strategy overview")
    version_format: GovernanceGuidance = Field(
        description="Version format pattern (e.g. MAJOR.MINOR.PATCH)"
    )
    intent: VersionComponentIntent = Field(description="Version increment intent per component")
    migration_intent: GovernanceGuidance = Field(
        description="Migration rules when crossing MAJOR version boundaries"
    )
    synchronization_intent: GovernanceGuidance = Field(
        description="How versions synchronize across documents"
    )


# YAML key remains version_strategy.
VersionStrategy = VersioningIntent
VersionIntent = VersionComponentIntent
