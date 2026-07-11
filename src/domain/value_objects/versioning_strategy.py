"""Versioning Strategy Value Objects.

Version increment intent for doctrine, schema, and specification documents.
"""

from __future__ import annotations

from pydantic import Field

from domain.base import DomainValueObject
from domain.identifiers import GovernanceText


class VersionIntent(DomainValueObject):
    """When to increment each semantic version component.

    Attributes:
        major (GovernanceText): When to increment MAJOR version.
        minor (GovernanceText): When to increment MINOR version.
        patch (GovernanceText): When to increment PATCH version.
    """

    major: GovernanceText = Field(description="When to increment MAJOR version")
    minor: GovernanceText = Field(description="When to increment MINOR version")
    patch: GovernanceText = Field(description="When to increment PATCH version")


class VersioningStrategy(DomainValueObject):
    """Versioning intent for doctrine, schema, and specification documents.

    Attributes:
        description (GovernanceText): Versioning strategy overview.
        format (GovernanceText): Version format pattern.
        intent (VersionIntent): Version increment intent per component.
        migration_intent (GovernanceText): MAJOR-boundary migration rules.
        synchronization_intent (GovernanceText): Cross-document version sync.
    """

    description: GovernanceText = Field(description="Versioning strategy overview")
    format: GovernanceText = Field(description="Version format pattern (e.g. MAJOR.MINOR.PATCH)")
    intent: VersionIntent = Field(description="Version increment intent per component")
    migration_intent: GovernanceText = Field(description="Migration rules when crossing MAJOR version boundaries")
    synchronization_intent: GovernanceText = Field(description="How versions synchronize across documents")
