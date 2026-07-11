from pydantic import BaseModel, ConfigDict, Field


class VersioningStrategy(BaseModel):
    """Describes versioning intent for doctrine, schema, and specification documents."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    description: str = Field(description="Versioning strategy overview")
    format: str = Field(description="Version format pattern (e.g. MAJOR.MINOR.PATCH)")
    major_increment_criteria: str = Field(description="When to increment MAJOR version")
    minor_increment_criteria: str = Field(description="When to increment MINOR version")
    patch_increment_criteria: str = Field(description="When to increment PATCH version")
    migration_intent: str = Field(description="Migration rules when crossing MAJOR version boundaries")
    synchronization_intent: str = Field(description="How versions synchronize across documents")
