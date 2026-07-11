"""Priority Hierarchy Value Objects.

Authority levels and cross-layer conflict-resolution precedence.
"""

from __future__ import annotations

from functools import cached_property
from typing import Any, Dict, List, Optional, Set, Tuple

from pydantic import Field, model_validator

from domain.base import DomainValueObject, NameableMixin, require_unique
from domain.enums import PriorityCategory
from domain.identifiers import GovernanceText


class PriorityLevel(DomainValueObject, NameableMixin):
    """An authority level in the governance priority hierarchy.

    Attributes:
        id (PriorityCategory): Unique level identifier.
        level (int): Numeric authority rank (1 = highest).
        title (GovernanceText): Human-readable level name.
        description (GovernanceText): Scope and authority of this level.
        examples (Tuple[GovernanceText, ...]): Typical rules at this level.
    
    Standardized methods:
        - to_dict() -> dict: Convert to dictionary
        - to_json() -> str: Convert to JSON string
        - from_dict(data) -> PriorityLevel: Create from dictionary
        - from_json(json_str) -> PriorityLevel: Create from JSON string
        - validate() -> PriorityLevel: Validate the model
        - name -> str: Human-readable name (alias for title, from NameableMixin)
        - rank -> int: Numeric authority rank (alias for level)
    """

    id: PriorityCategory = Field(description="Unique level identifier")
    level: int = Field(ge=1, description="Numeric authority rank (1 = highest)")
    title: GovernanceText = Field(description="Human-readable level name")
    description: GovernanceText = Field(description="Scope and authority of this level")
    examples: Tuple[GovernanceText, ...] = Field(
        default=(),
        description="Typical rules at this authority level",
    )

    @property
    def rank(self) -> int:
        """Numeric authority rank (alias for level)."""
        return self.level

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
    
    Standardized methods:
        - to_dict() -> dict: Convert to dictionary
        - to_json() -> str: Convert to JSON string
        - from_dict(data) -> CrossLayerPrecedence: Create from dictionary
        - from_json(json_str) -> CrossLayerPrecedence: Create from JSON string
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
    
    Standardized methods:
        - get(category) -> Optional[PriorityLevel]: Safe lookup
        - find(category) -> PriorityLevel: Strict lookup (raises KeyError)
        - outranks(left, right) -> bool: Check if left has higher authority
        - is_higher(left, right) -> bool: Alias for outranks
        - is_lower(left, right) -> bool: Check if left has lower authority
        - compare(left, right) -> int: Compare two categories
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
        result: PriorityHierarchy = self
        for index, level in enumerate(self.levels, start=1):
            if level.level != index:
                raise ValueError(
                    f"Priority level '{level.id}' at position {index} has "
                    f"level={level.level}, expected {index}. Levels must be "
                    "ordered and contiguous starting from 1."
                )

        category_ids: List[PriorityCategory] = [level.id for level in self.levels]
        require_unique(category_ids, a_label="priority categories")

        # Check that all enum values are present (original logic)
        expected: Set[PriorityCategory] = set(PriorityCategory)
        present: Set[PriorityCategory] = set(category_ids)
        missing: Set[PriorityCategory] = expected - present
        if missing:
            names: List[str] = sorted(category.value for category in missing)
            raise ValueError(f"Priority hierarchy missing categories: {names}")

        return result

    @cached_property
    def _levels_index(self) -> Dict[PriorityCategory, PriorityLevel]:
        """Index priority levels by category for O(1) lookup."""
        result: Dict[PriorityCategory, PriorityLevel] = {level.id: level for level in self.levels}
        return result

    # Standardized lookup methods
    def get(self, a_category: PriorityCategory) -> Optional[PriorityLevel]:
        """Return the priority level for a category, or None if not found.

        Args:
            a_category: Priority category to lookup.

        Returns:
            PriorityLevel for the category, or None if not found.
        """
        result: Optional[PriorityLevel] = self._levels_index.get(a_category)
        return result

    def find(self, a_category: PriorityCategory) -> PriorityLevel:
        """Return the priority level for a category, raising if not found.

        Args:
            a_category: Priority category to lookup.

        Returns:
            PriorityLevel for the category.

        Raises:
            KeyError: If the category is not found.
        """
        result: Optional[PriorityLevel] = self._levels_index.get(a_category)
        if result is None:
            raise KeyError(f"Priority level for category '{a_category}' not found")
        return result

    # Standardized comparison methods
    def outranks(self, a_left: PriorityCategory, a_right: PriorityCategory) -> bool:
        """Return True if left has higher authority than right."""
        result: bool = self._levels_index[a_left].level < self._levels_index[a_right].level
        return result

    def is_higher(self, a_left: PriorityCategory, a_right: PriorityCategory) -> bool:
        """Alias for outranks - returns True if left has higher authority than right."""
        return self.outranks(a_left, a_right)

    def is_lower(self, a_left: PriorityCategory, a_right: PriorityCategory) -> bool:
        """Return True if left has lower authority than right."""
        return self._levels_index[a_left].level > self._levels_index[a_right].level

    def compare(self, a_left: PriorityCategory, a_right: PriorityCategory) -> int:
        """Compare two categories.

        Args:
            a_left: Left category to compare.
            a_right: Right category to compare.

        Returns:
            -1 if left has higher authority (lower level number),
            0 if equal authority,
            1 if left has lower authority (higher level number).
        """
        left_level: int = self._levels_index[a_left].level
        right_level: int = self._levels_index[a_right].level
        if left_level < right_level:
            return -1
        elif left_level == right_level:
            return 0
        return 1

    # Standardized access methods
    @property
    def category_ids(self) -> List[PriorityCategory]:
        """Return all category IDs in order."""
        return [level.id for level in self.levels]

    @property
    def category_titles(self) -> List[str]:
        """Return all category titles in order."""
        return [level.title for level in self.levels]

    def highest(self) -> PriorityLevel:
        """Return the highest authority level."""
        return self.levels[0]

    def lowest(self) -> PriorityLevel:
        """Return the lowest authority level."""
        return self.levels[-1]

    def get_all(self) -> Tuple[PriorityLevel, ...]:
        """Return all levels in order."""
        return self.levels
