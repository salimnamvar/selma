from pydantic import BaseModel, ConfigDict, Field

from domain.enums import VersionComponent
from domain.identifiers import Prose


class VersionComponentIntent(BaseModel):
    """Describes the governance intent for a specific version component."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    component: VersionComponent = Field(description="The version component")
    intent: Prose = Field(description="Governance intent for this component")


class VersioningPolicy(BaseModel):
    """Describes versioning intent for doctrine, schema, and specification documents."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    format: str = Field(description="Version format pattern")
    intents: tuple[VersionComponentIntent, ...] = Field(description="Component-specific intents")
    migration_rules: Prose = Field(description="Migration rules when crossing MAJOR boundaries")
