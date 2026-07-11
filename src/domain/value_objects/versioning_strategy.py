from pydantic import BaseModel, Field


class VersioningStrategy(BaseModel):
    """Describes versioning intent for doctrine, schema, and specification documents."""

    model_config = {"frozen": True}

    version_format: str = Field(description="Version format pattern")
    major_intent: str = Field(description="When to increment MAJOR version")
    minor_intent: str = Field(description="When to increment MINOR version")
    patch_intent: str = Field(description="When to increment PATCH version")
    migration_intent: str = Field(description="Migration rules when crossing MAJOR boundaries")
    synchronization_intent: str = Field(description="How versions synchronize across documents")
