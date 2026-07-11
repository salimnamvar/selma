"""Priority hierarchy value objects."""

from __future__ import annotations

from functools import cached_property

from pydantic import ConfigDict, Field, model_validator

from domain.base import DomainValueObject
from domain.enums import PriorityCategory
from domain.identifiers import GovernanceText


class PriorityLevel(DomainValueObject):
    """An authority level in the governance priority hierarchy."""

    id: PriorityCategory = Field(description="Unique level identifier")
    level: int = Field(ge=1, description="Numeric authority rank (1 = highest)")
    title: GovernanceText = Field(description="Human-readable level name")
    description: GovernanceText = Field(description="Scope and authority of this level")
    examples: tuple[GovernanceText, ...] = Field(
        default=(),
        description="Typical rules at this authority level",
    )

    @model_validator(mode="after")
    def check_rank_matches_category(self) -> PriorityLevel:
        """Ensure numeric level matches the category's canonical rank when known."""
        if self.level != self.id.rank:
            msg = f"Priority level '{self.id}' has level={self.level}, expected canonical rank {self.id.rank}"
            raise ValueError(msg)
        return self


class CrossLayerPrecedence(DomainValueObject):
    """How conflict-resolution precedence maps across layers.

    Mirrors ``priority_hierarchy.cross_layer_precedence`` in the doctrine.
    Distinct from ``ConflictResolutionBinding``, which describes each layer's
    *role* rather than the precedence mapping itself.
    """

    normative_algorithm: GovernanceText = Field(description="Where the normative resolution algorithm is defined")
    structural_override: GovernanceText = Field(description="Schema-level override mechanism for conflict resolution")
    policy_role: GovernanceText = Field(description="Policy layer's role in precedence")
    order: GovernanceText = Field(description="Precedence chain order")


class PriorityHierarchy(DomainValueObject):
    """Declares authority levels and conflict-resolution intent."""

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
        ignored_types=(cached_property,),
    )

    description: GovernanceText = Field(description="How priority hierarchy works")
    levels: tuple[PriorityLevel, ...] = Field(
        min_length=1,
        description="Ordered authority levels",
    )
    conflict_resolution_intent: GovernanceText = Field(
        description="Governance intent for how priority affects conflict resolution"
    )
    cross_layer_precedence: CrossLayerPrecedence = Field(
        description="How precedence maps across policy/schema/spec layers"
    )

    @model_validator(mode="after")
    def check_levels(self) -> PriorityHierarchy:
        """Validate ordering, uniqueness, and completeness of priority levels."""
        # Strict ascending order as authored (no silent re-sort).
        for index, level in enumerate(self.levels, start=1):
            if level.level != index:
                msg = (
                    f"Priority level '{level.id}' at position {index} has "
                    f"level={level.level}, expected {index}. Levels must be "
                    "ordered and contiguous starting from 1."
                )
                raise ValueError(msg)

        category_ids = [level.id for level in self.levels]
        if len(category_ids) != len(set(category_ids)):
            raise ValueError("Duplicate priority categories are not allowed")

        expected = set(PriorityCategory)
        present = set(category_ids)
        missing = expected - present
        if missing:
            raise ValueError(f"Priority hierarchy missing categories: {sorted(c.value for c in missing)}")

        return self

    @cached_property
    def _level_index(self) -> dict[PriorityCategory, PriorityLevel]:
        return {level.id: level for level in self.levels}

    def get_level(self, category: PriorityCategory) -> PriorityLevel | None:
        """Return the priority level for a category, or None if absent."""
        return self._level_index.get(category)

    def resolve(self, category: PriorityCategory) -> PriorityLevel | None:
        """Alias for :meth:`get_level` (lookup by authority category)."""
        return self.get_level(category)

    def outranks(self, left: PriorityCategory, right: PriorityCategory) -> bool:
        """Return True if *left* has higher authority (lower rank number) than *right*."""
        left_level = self._level_index[left]
        right_level = self._level_index[right]
        return left_level.level < right_level.level
