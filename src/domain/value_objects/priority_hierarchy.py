from typing import Optional

from pydantic import Field, model_validator

from domain.enums import PriorityCategory
from domain.value_objects.base import DomainValueObject


class PriorityLevel(DomainValueObject):
    """An authority level in the governance priority hierarchy."""

    id: PriorityCategory = Field(description="Unique level identifier")
    level: int = Field(ge=1, le=5, description="Numeric authority rank (1 = highest)")
    title: str = Field(description="Human-readable level name")
    description: str = Field(description="Scope and authority of this level")
    examples: tuple[str, ...] = Field(description="Typical rules at this authority level")


class CrossLayerPrecedence(DomainValueObject):
    """Describes how conflict resolution maps across layers."""

    normative_algorithm: str = Field(description="Where the algorithm lives")
    structural_override: str = Field(description="Schema-level override mechanism")
    policy_role: str = Field(description="Policy layer's role")
    order: str = Field(description="Precedence chain order")


class PriorityHierarchy(DomainValueObject):
    """Declares the authority levels and conflict resolution intent.

    Enforces that levels are declared in strict ascending order by authority rank.
    """

    description: str = Field(description="How priority hierarchy works")
    levels: tuple[PriorityLevel, ...] = Field(description="Ordered authority levels")
    conflict_resolution_intent: str = Field(description="Governance intent for conflict resolution")
    cross_layer_precedence: CrossLayerPrecedence = Field(description="How precedence maps across layers")

    @model_validator(mode="after")
    def _validate_level_ordering(self) -> "PriorityHierarchy":
        for expected_num, level in enumerate(self.levels, start=1):
            if level.level != expected_num:
                raise ValueError(
                    f"Priority level '{level.id}' has level={level.level}, "
                    f"expected {expected_num} at position {expected_num}"
                )
        return self

    def get_level(self, category: PriorityCategory) -> Optional[PriorityLevel]:
        """Retrieve a priority level by its category."""
        return next((level for level in self.levels if level.id == category), None)
