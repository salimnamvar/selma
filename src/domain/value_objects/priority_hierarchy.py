"""Priority Hierarchy Value Objects.

Authority levels and cross-layer conflict-resolution precedence.
"""

from __future__ import annotations

from functools import cached_property
from typing import Dict, List, Optional, Set, Tuple

from pydantic import ConfigDict, Field, model_validator

from domain.base import DomainValueObject
from domain.enums import PriorityCategory
from domain.identifiers import GovernanceText


class PriorityLevel(DomainValueObject):
    """An authority level in the governance priority hierarchy.

    Attributes:
        id (PriorityCategory): Unique level identifier.
        level (int): Numeric authority rank (1 = highest).
        title (GovernanceText): Human-readable level name.
        description (GovernanceText): Scope and authority of this level.
        examples (Tuple[GovernanceText, ...]): Typical rules at this level.
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
        result: PriorityLevel = self
        if self.level != self.id.rank:
            raise ValueError(
                f"Priority level '{self.id}' has level={self.level}, expected canonical rank {self.id.rank}"
            )
        return result


class CrossLayerPrecedence(DomainValueObject):
    """How conflict-resolution precedence maps across layers.

    Attributes:
        normative_algorithm (GovernanceText): Normative algorithm location.
        structural_override (GovernanceText): Schema-level override mechanism.
        policy_role (GovernanceText): Policy layer role in precedence.
        order (GovernanceText): Precedence chain order.
    """

    normative_algorithm: GovernanceText = Field(description="Where the normative resolution algorithm is defined")
    structural_override: GovernanceText = Field(description="Schema-level override mechanism for conflict resolution")
    policy_role: GovernanceText = Field(description="Policy layer's role in precedence")
    order: GovernanceText = Field(description="Precedence chain order")


class PriorityHierarchy(DomainValueObject):
    """Declares authority levels and conflict-resolution intent.

    Attributes:
        description (GovernanceText): How priority hierarchy works.
        levels (Tuple[PriorityLevel, ...]): Ordered authority levels.
        conflict_resolution_intent (GovernanceText): Conflict resolution intent.
        cross_layer_precedence (CrossLayerPrecedence): Cross-layer precedence map.
    """

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
        populate_by_name=True,
        str_strip_whitespace=True,
        ignored_types=(cached_property,),
    )

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
        result: PriorityHierarchy = self
        for index, level in enumerate(self.levels, start=1):
            if level.level != index:
                raise ValueError(
                    f"Priority level '{level.id}' at position {index} has "
                    f"level={level.level}, expected {index}. Levels must be "
                    "ordered and contiguous starting from 1."
                )

        category_ids: List[PriorityCategory] = [level.id for level in self.levels]
        if len(category_ids) != len(set(category_ids)):
            raise ValueError("Duplicate priority categories are not allowed")

        expected: Set[PriorityCategory] = set(PriorityCategory)
        present: Set[PriorityCategory] = set(category_ids)
        missing: Set[PriorityCategory] = expected - present
        if missing:
            names: List[str] = sorted(category.value for category in missing)
            raise ValueError(f"Priority hierarchy missing categories: {names}")

        return result

    @cached_property
    def _level_index(self) -> Dict[PriorityCategory, PriorityLevel]:
        result: Dict[PriorityCategory, PriorityLevel] = {level.id: level for level in self.levels}
        return result

    def get_level(self, a_category: PriorityCategory) -> Optional[PriorityLevel]:
        """Return the priority level for a category."""
        result: Optional[PriorityLevel] = self._level_index.get(a_category)
        return result

    def outranks(self, a_left: PriorityCategory, a_right: PriorityCategory) -> bool:
        """Return True if left has higher authority than right."""
        result: bool = self._level_index[a_left].level < self._level_index[a_right].level
        return result
