from pydantic import Field

from domain.identifiers import Guidance
from domain.value_objects.base import DomainValueObject


class VersionIntent(DomainValueObject):
    """Describes when to increment each version component."""

    major: Guidance = Field(description="When to increment MAJOR version")
    minor: Guidance = Field(description="When to increment MINOR version")
    patch: Guidance = Field(description="When to increment PATCH version")


class VersioningStrategy(DomainValueObject):
    """Describes versioning intent for doctrine, schema, and specification documents."""

    version_format: str = Field(description="Version format pattern")
    intent: VersionIntent = Field(description="Version increment intent")
    migration_intent: Guidance = Field(description="Migration rules when crossing MAJOR boundaries")
    synchronization_intent: Guidance = Field(description="How versions synchronize across documents")
