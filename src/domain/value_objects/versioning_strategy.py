from pydantic import BaseModel, ConfigDict, Field

from domain.identifiers import Guidance


class VersionIntent(BaseModel):
    """Describes when to increment each version component."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    major: Guidance = Field(description="When to increment MAJOR version")
    minor: Guidance = Field(description="When to increment MINOR version")
    patch: Guidance = Field(description="When to increment PATCH version")


class VersioningStrategy(BaseModel):
    """Describes versioning intent for doctrine, schema, and specification documents."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    version_format: str = Field(description="Version format pattern")
    intent: VersionIntent = Field(description="Version increment intent")
    migration_intent: Guidance = Field(description="Migration rules when crossing MAJOR boundaries")
    synchronization_intent: Guidance = Field(description="How versions synchronize across documents")
