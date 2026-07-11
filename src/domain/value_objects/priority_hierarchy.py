"""Priority hierarchy — authority ranks and conflict-resolution intent."""

from __future__ import annotations

from typing import Self

from pydantic import BaseModel, Field, PrivateAttr, model_validator

from domain.base import VO_CONFIG
from domain.enums import PriorityCategory
from domain.identifiers import GovernanceText


class Level(BaseModel):
    """One entry in the policy_doctrine.yaml ``priority_hierarchy.levels`` collection."""

    model_config = VO_CONFIG

    category: PriorityCategory = Field(description="Unique rank identifier")
    rank: int = Field(ge=1, description="Numeric authority rank (1 = highest)")
    title: GovernanceText = Field(description="Human-readable rank name")
    description: GovernanceText = Field(description="Scope and authority of this rank")
    examples: tuple[GovernanceText, ...] = Field(default=(), description="Typical rules")


class CrossLayerPrecedence(BaseModel):
    """Declarative precedence intent across layers (not an algorithm)."""

    model_config = VO_CONFIG

    precedence_algorithm: GovernanceText = Field(
        description="Where the normative resolution algorithm is defined (reference only)"
    )
    structural_override: GovernanceText = Field(
        description="Schema-level override mechanism for conflict resolution"
    )
    policy_role: GovernanceText = Field(description="Policy layer's role in precedence")
    order: GovernanceText = Field(
        description="Precedence chain order as governance prose (not executable)"
    )


class PriorityHierarchy(BaseModel):
    """Declares authority levels and conflict-resolution intent."""

    model_config = VO_CONFIG

    description: GovernanceText = Field(description="How priority hierarchy works")
    levels: tuple[Level, ...] = Field(min_length=1, description="Ordered authority levels")
    conflict_resolution: GovernanceText = Field(
        description="Governance intent for how priority affects conflict resolution"
    )
    cross_layer_precedence: CrossLayerPrecedence = Field(
        description="How precedence maps across policy/schema/spec layers"
    )

    _levels_by_category: dict[PriorityCategory, Level] = PrivateAttr(default_factory=dict)

    @model_validator(mode="after")
    def _validate_levels(self) -> Self:
        levels_by_category: dict[PriorityCategory, Level] = {}
        for index, levels_entry in enumerate(self.levels, start=1):
            if levels_entry.rank != index:
                raise ValueError(
                    f"Priority rank '{levels_entry.category}' at position {index} has "
                    f"rank={levels_entry.rank}, expected {index}. Levels must be "
                    "ordered and contiguous starting from 1."
                )
            if levels_entry.category in levels_by_category:
                raise ValueError(
                    f"Duplicate priority categories found: {levels_entry.category!r}"
                )
            levels_by_category[levels_entry.category] = levels_entry
        missing = set(PriorityCategory) - set(levels_by_category)
        if missing:
            raise ValueError(
                f"Priority hierarchy missing categories: {sorted(c.value for c in missing)}"
            )
        object.__setattr__(self, "_levels_by_category", levels_by_category)
        return self

    def get_levels(self, category: PriorityCategory) -> Level | None:
        """Return the ``levels`` entry for ``category``, or None."""
        return self._levels_by_category.get(category)

    def outranks(self, left: PriorityCategory, right: PriorityCategory) -> bool:
        """Return True if left has higher authority than right."""
        return self._levels_by_category[left].rank < self._levels_by_category[right].rank