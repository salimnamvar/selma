from pydantic import BaseModel, ConfigDict, Field

from domain.enums import PriorityCategory
from domain.identifiers import Prose


class PriorityLevel(BaseModel):
    """An authority level in the governance priority hierarchy.

    Rank is derived from the PriorityCategory enum order, eliminating
    the redundant level integer.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: PriorityCategory = Field(description="Unique level identifier")
    title: str = Field(description="Human-readable level name")
    description: Prose = Field(description="Scope and authority of this level")
    examples: tuple[Prose, ...] = Field(description="Typical rules at this authority level")


class CrossLayerPrecedence(BaseModel):
    """Describes how conflict resolution maps across layers."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    normative_algorithm: str = Field(description="Where the algorithm lives")
    structural_override: str = Field(description="Schema-level override mechanism")
    policy_role: Prose = Field(description="Policy layer's role")
    order: Prose = Field(description="Precedence chain order")


class PriorityHierarchy(BaseModel):
    """Declares the authority levels and conflict resolution intent."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    description: Prose = Field(description="How priority hierarchy works")
    levels: tuple[PriorityLevel, ...] = Field(description="Ordered authority levels")
    conflict_resolution_intent: Prose = Field(description="Governance intent for conflict resolution")
    cross_layer_precedence: CrossLayerPrecedence = Field(description="How precedence maps across layers")
