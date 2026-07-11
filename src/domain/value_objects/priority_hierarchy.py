"""Authority hierarchy — priority ranks and conflict-resolution intent."""

from __future__ import annotations

from functools import cached_property
from typing import Self

from pydantic import Field, model_validator

from domain.base import DomainValueObject, require_unique
from domain.enums import PriorityCategory
from domain.identifiers import GovernanceText


class PriorityLevel(DomainValueObject):
    """An authority rank in the governance priority hierarchy."""

    category: PriorityCategory = Field(description="Unique rank identifier")
    rank: int = Field(ge=1, description="Numeric authority rank (1 = highest)")
    title: GovernanceText = Field(description="Human-readable rank name")
    description: GovernanceText = Field(description="Scope and authority of this rank")
    examples: tuple[GovernanceText, ...] = Field(default=(), description="Typical rules")

    @model_validator(mode="after")
    def _validate_rank(self) -> Self:
        if self.rank != self.category.rank:
            raise ValueError(
                f"Priority rank '{self.category}' has rank={self.rank}, "
                f"expected canonical rank {self.category.rank}"
            )
        return self

    @property
    def name(self) -> str:
        """Human-readable name (title)."""
        return self.title


class CrossLayerPrecedence(DomainValueObject):
    """Declarative precedence intent across layers (not an algorithm)."""

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


class AuthorityHierarchy(DomainValueObject):
    """Declares authority levels and conflict-resolution intent."""

    description: GovernanceText = Field(description="How priority hierarchy works")
    levels: tuple[PriorityLevel, ...] = Field(min_length=1, description="Ordered authority levels")
    conflict_resolution: GovernanceText = Field(
        description="Governance intent for how priority affects conflict resolution"
    )
    cross_layer_precedence: CrossLayerPrecedence = Field(
        description="How precedence maps across policy/schema/spec layers"
    )

    @model_validator(mode="after")
    def _validate_levels(self) -> Self:
        for index, level in enumerate(self.levels, start=1):
            if level.rank != index:
                raise ValueError(
                    f"Priority rank '{level.category}' at position {index} has "
                    f"rank={level.rank}, expected {index}. Levels must be "
                    "ordered and contiguous starting from 1."
                )
        require_unique([level.category for level in self.levels], label="priority categories")
        missing = set(PriorityCategory) - {level.category for level in self.levels}
        if missing:
            raise ValueError(
                f"Priority hierarchy missing categories: {sorted(c.value for c in missing)}"
            )
        return self

    @cached_property
    def _index(self) -> dict[PriorityCategory, PriorityLevel]:
        return {level.category: level for level in self.levels}

    def get(self, key: PriorityCategory) -> PriorityLevel | None:
        """Return the level for ``key``, or None."""
        return self._index.get(key)

    def require(self, key: PriorityCategory) -> PriorityLevel:
        """Return the level for ``key``, or raise KeyError."""
        result = self.get(key)
        if result is None:
            raise KeyError(f"Priority rank for category '{key}' not found")
        return result

    def has(self, key: PriorityCategory) -> bool:
        """Return True if a level for ``key`` exists."""
        return key in self._index

    def outranks(self, left: PriorityCategory, right: PriorityCategory) -> bool:
        """Return True if left has higher authority than right."""
        return self.require(left).rank < self.require(right).rank

    def get_highest(self) -> PriorityLevel:
        """Return the highest authority rank."""
        return self.levels[0]

    def get_lowest(self) -> PriorityLevel:
        """Return the lowest authority rank."""
        return self.levels[-1]
