from pydantic import Field

from domain.value_objects.base import DomainValueObject


class VersionIntent(DomainValueObject):
    """Describes when to increment each version component."""

    major: str = Field(description="When to increment MAJOR version")
    minor: str = Field(description="When to increment MINOR version")
    patch: str = Field(description="When to increment PATCH version")


class VersioningStrategy(DomainValueObject):
    """Describes versioning intent for doctrine, schema, and specification documents."""

    version_format: str = Field(description="Version format pattern")
    intent: VersionIntent = Field(description="Version increment intent")
    migration_intent: str = Field(description="Migration rules when crossing MAJOR boundaries")
    synchronization_intent: str = Field(description="How versions synchronize across documents")
