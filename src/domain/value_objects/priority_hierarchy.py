from typing import List

from pydantic import BaseModel, Field

from domain.entities.priority_level import PriorityLevel


class CrossLayerPrecedence(BaseModel):
    """Describes how conflict resolution maps across layers."""

    model_config = {"frozen": True}

    normative_algorithm: str = Field(description="Where the algorithm lives")
    structural_override: str = Field(description="Schema-level override mechanism")
    policy_role: str = Field(description="Policy layer's role")
    order: str = Field(description="Precedence chain order")


class PriorityHierarchy(BaseModel):
    """Declares the authority levels and conflict resolution intent."""

    model_config = {"frozen": True}

    description: str = Field(description="How priority hierarchy works")
    levels: List[PriorityLevel] = Field(description="Ordered authority levels")
    conflict_resolution_intent: str = Field(description="Governance intent for conflict resolution")
    cross_layer_precedence: CrossLayerPrecedence = Field(description="How precedence maps across layers")
