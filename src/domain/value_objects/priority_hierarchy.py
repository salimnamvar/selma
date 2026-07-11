from pydantic import BaseModel, ConfigDict, Field

from domain.enums import PriorityCategory


class PriorityLevel(BaseModel):
    """An authority level in the governance priority hierarchy."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: PriorityCategory
    level: int = Field(description="Numeric authority rank (lower = higher authority)")
    title: str = Field(description="Human-readable level name")
    description: str = Field(description="Scope and authority of this level")
    examples: tuple[str, ...] = Field(description="Typical rules at this authority level")


class CrossLayerPrecedence(BaseModel):
    """Describes how conflict resolution maps across layers."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    normative_algorithm: str = Field(description="Where the normative algorithm is defined")
    structural_override: str = Field(description="Schema-level override mechanism")
    policy_role: str = Field(description="Policy layer's role")
    order: str = Field(description="Precedence chain order")


class PriorityHierarchy(BaseModel):
    """Declares the authority levels and conflict resolution intent."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    description: str = Field(description="How priority hierarchy works")
    levels: tuple[PriorityLevel, ...] = Field(description="Authority levels")
    conflict_resolution_intent: str = Field(description="Governance intent for conflict resolution")
    cross_layer_precedence: CrossLayerPrecedence = Field(description="How precedence maps across layers")
