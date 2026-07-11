from pydantic import BaseModel, ConfigDict, Field


class VersionIntent(BaseModel):
    """Describes when to increment each version component."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    major: str = Field(description="When to increment MAJOR version")
    minor: str = Field(description="When to increment MINOR version")
    patch: str = Field(description="When to increment PATCH version")


class VersioningStrategy(BaseModel):
    """Describes versioning intent for doctrine, schema, and specification documents."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    version_format: str = Field(description="Version format pattern")
    intent: VersionIntent = Field(description="Version increment intent")
    migration_intent: str = Field(description="Migration rules when crossing MAJOR boundaries")
    synchronization_intent: str = Field(description="How versions synchronize across documents")
