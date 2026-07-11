from pydantic import BaseModel, ConfigDict, Field

from domain.identifiers import Prose


class ConflictResolutionPolicy(BaseModel):
    """Declares the precedence order for conflict resolution."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    precedence_order: tuple[Prose, ...] = Field(description="Ordered precedence chain for conflict resolution")


class CrossLayerPolicy(BaseModel):
    """Describes the structural relationship between policy, schema, and specification layers."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    normative_source: str = Field(description="The authoritative behavioral source")
    enforcement_model: Prose = Field(description="How governance intent is enforced")
    conflict_resolution: ConflictResolutionPolicy = Field(description="Conflict resolution policy across layers")
