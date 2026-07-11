"""Priority Hierarchy Value Objects.

Authority levels and cross-layer conflict-resolution precedence.
"""

from __future__ import annotations

from functools import cached_property
from typing import Dict, List, Optional, Set, Tuple

from pydantic import Field, model_validator

from domain.base import DomainValueObject, NameableMixin, require_unique
from domain.enums import PriorityCategory
from domain.identifiers import GovernanceText


class PriorityLevel(DomainValueObject, NameableMixin):
    """An authority level in the governance priority hierarchy.

    Attributes:
        id: Unique level identifier.
        level: Numeric authority rank (1 = highest).
        title: Human-readable level name.
        description: Scope and authority of this level.
        examples: Typical rules at this level.
    """

    id: PriorityCategory = Field(description="Unique level identifier")
    level: int = Field(ge=1, description="Numeric authority rank (1 = highest)")
    title: GovernanceText = Field(description="Human-readable level name")
    description: GovernanceText = Field(description="Scope and authority of this level")
    examples: Tuple[GovernanceText, ...] = Field(
        default=(),
        description="Typical rules at this authority level",
    )

    @model_validator(mode="after")
    def check_rank_matches_category(self) -> PriorityLevel:
        """Ensure numeric level matches the category canonical rank."""
        if self.level != self.id.rank:
            raise ValueError(
                f"Priority level '{self.id}' has level={self.level}, expected canonical rank {self.id.rank}"
            )
        return self


class CrossLayerPrecedence(DomainValueObject):
    """How conflict-resolution precedence maps across layers.

    Attributes:
        normative_algorithm: Normative algorithm location.
        structural_override: Schema-level override mechanism.
        policy_role: Policy layer role in precedence.
        order: Precedence chain order.
    """

    normative_algorithm: GovernanceText = Field(description="Where the normative resolution algorithm is defined")
    structural_override: GovernanceText = Field(description="Schema-level override mechanism for conflict resolution")
    policy_role: GovernanceText = Field(description="Policy layer's role in precedence")
    order: GovernanceText = Field(description="Precedence chain order")


class PriorityHierarchy(DomainValueObject):
    """Declares authority levels and conflict-resolution intent.

    Attributes:
        description: How priority hierarchy works.
        levels: Ordered authority levels.
        conflict_resolution_intent: Conflict resolution intent.
        cross_layer_precedence: Cross-layer precedence map.
    """

    description: GovernanceText = Field(description="How priority hierarchy works")
    levels: Tuple[PriorityLevel, ...] = Field(
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
        for index, level in enumerate(self.levels, start=1):
            if level.level != index:
                raise ValueError(
                    f"Priority level '{level.id}' at position {index} has "
                    f"level={level.level}, expected {index}. Levels must be "
                    "ordered and contiguous starting from 1."
                )

        category_ids: List[PriorityCategory] = [level.id for level in self.levels]
        require_unique(category_ids, a_label="priority categories")

        expected: Set[PriorityCategory] = set(PriorityCategory)
        present: Set[PriorityCategory] = set(category_ids)
        missing: Set[PriorityCategory] = expected - present
        if missing:
            names: List[str] = sorted(category.value for category in missing)
            raise ValueError(f"Priority hierarchy missing categories: {names}")

        return self

    @cached_property
    def _levels_index(self) -> Dict[PriorityCategory, PriorityLevel]:
        """Index priority levels by category for O(1) lookup."""
        return {level.id: level for level in self.levels}

    def get(self, a_category: PriorityCategory) -> Optional[PriorityLevel]:
        """Return the priority level for a category, or None if not found."""
        return self._levels_index.get(a_category)

    def find(self, a_category: PriorityCategory) -> PriorityLevel:
        """Return the priority level for a category, raising if not found."""
        try:
            return self._levels_index[a_category]
        except KeyError as exc:
            raise KeyError(f"Priority level for category '{a_category}' not found") from exc

    def outranks(self, a_left: PriorityCategory, a_right: PriorityCategory) -> bool:
        """Return True if left has higher authority than right (lower level number)."""
        return self._levels_index[a_left].level < self._levels_index[a_right].level

    def highest(self) -> PriorityLevel:
        """Return the highest authority level."""
        return self.levels[0]

    def lowest(self) -> PriorityLevel:
        """Return the lowest authority level."""
        return self.levels[-1]
