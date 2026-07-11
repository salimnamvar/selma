"""Priority hierarchy — authority ranks and conflict-resolution intent."""

from __future__ import annotations

from typing import Self

from pydantic import BaseModel, ConfigDict, Field, model_validator

from domain.enums import PriorityCategory


class Level(BaseModel):
    """One entry in the policy_doctrine.yaml ``priority_hierarchy.levels`` collection."""

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
    )

    category: PriorityCategory = Field(description="Unique rank identifier")
    rank: int = Field(ge=1, description="Numeric authority rank (1 = highest)")
    title: str = Field(min_length=1, description="Human-readable rank name")
    description: str = Field(min_length=1, description="Scope and authority of this rank")
    examples: tuple[str, ...] = Field(default=(), description="Typical rules")


class CrossLayerPrecedence(BaseModel):
    """Declarative precedence intent across layers (not an algorithm)."""

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
    )

    precedence_algorithm: str = Field(
        min_length=1,
        description="Where the normative resolution algorithm is defined (reference only)",
    )
    structural_override: str = Field(
        min_length=1, description="Schema-level override mechanism for conflict resolution"
    )
    policy_role: str = Field(min_length=1, description="Policy layer's role in precedence")
    order: str = Field(min_length=1, description="Precedence chain order as governance prose (not executable)")


class PriorityHierarchy(BaseModel):
    """Declares authority levels and conflict-resolution intent."""

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
    )

    description: str = Field(min_length=1, description="How priority hierarchy works")
    levels: tuple[Level, ...] = Field(min_length=1, description="Ordered authority levels")
    conflict_resolution: str = Field(
        min_length=1,
        description="Governance intent for how priority affects conflict resolution",
    )
    cross_layer_precedence: CrossLayerPrecedence = Field(
        description="How precedence maps across policy/schema/spec layers"
    )

    @model_validator(mode="after")
    def _validate_levels(self) -> Self:
        categories: list[PriorityCategory] = []
        for index, levels_entry in enumerate(self.levels, start=1):
            if levels_entry.rank != index:
                raise ValueError(
                    f"Priority rank '{levels_entry.category}' at position {index} has "
                    f"rank={levels_entry.rank}, expected {index}. Levels must be "
                    "ordered and contiguous starting from 1."
                )
            categories.append(levels_entry.category)
        if len(categories) != len(set(categories)):
            raise ValueError(f"Duplicate priority categories found: {set(categories)}")
        missing = set(PriorityCategory) - set(categories)
        if missing:
            raise ValueError(f"Priority hierarchy missing categories: {sorted(c.value for c in missing)}")
        return self

    def get_levels(self, category: PriorityCategory) -> Level | None:
        """Return the ``levels`` entry for ``category``, or None."""
        return next((entry for entry in self.levels if entry.category == category), None)

    def outranks(self, left: PriorityCategory, right: PriorityCategory) -> bool:
        """Return True if left has higher authority than right."""
        left_entry = self.get_levels(left)
        right_entry = self.get_levels(right)
        if left_entry is None or right_entry is None:
            raise KeyError(f"Unknown priority category: {left!r} or {right!r}")
        return left_entry.rank < right_entry.rank
