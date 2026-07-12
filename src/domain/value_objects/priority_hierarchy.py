"""Priority hierarchy — authority ranks and conflict-resolution intent."""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


class PriorityCategory(StrEnum):
    """Authority levels in the governance priority hierarchy."""

    CONSTITUTIONAL = "constitutional"
    STATUTORY = "statutory"
    REGULATORY = "regulatory"
    OPERATIONAL = "operational"
    ADVISORY = "advisory"


class Level(BaseModel):
    """One entry in the policy_doctrine.yaml ``priority_hierarchy.levels`` collection."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    category: PriorityCategory = Field(description="Unique rank identifier")
    rank: int = Field(ge=1, description="Numeric authority rank (1 = highest)")
    title: str = Field(min_length=1, description="Human-readable rank name")
    description: str = Field(min_length=1, description="Scope and authority of this rank")
    examples: tuple[str, ...] = Field(default=(), description="Typical rules")


class CrossLayerPrecedence(BaseModel):
    """Declarative precedence intent across layers (not an algorithm)."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    precedence_algorithm: str = Field(
        min_length=1, description="Where the normative resolution algorithm is defined (reference only)"
    )
    structural_override: str = Field(
        min_length=1, description="Schema-level override mechanism for conflict resolution"
    )
    policy_role: str = Field(min_length=1, description="Policy layer's role in precedence")
    order: str = Field(min_length=1, description="Precedence chain order as governance prose (not executable)")


class PriorityHierarchy(BaseModel):
    """Declares authority levels and conflict-resolution intent."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    description: str = Field(min_length=1, description="How priority hierarchy works")
    levels: tuple[Level, ...] = Field(min_length=1, description="Ordered authority levels")
    conflict_resolution: str = Field(
        min_length=1, description="Governance intent for how priority affects conflict resolution"
    )
    cross_layer_precedence: CrossLayerPrecedence = Field(
        description="How precedence maps across policy/schema/spec layers"
    )
