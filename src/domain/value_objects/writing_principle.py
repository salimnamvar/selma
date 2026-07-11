"""Writing Principle Value Objects.

Authoring principles that guide directive writers.
"""

from __future__ import annotations

from functools import cached_property
from typing import Dict, List, Optional, Tuple

from pydantic import ConfigDict, Field, RootModel, model_validator

from domain.base import DomainValueObject
from domain.identifiers import GovernanceText, WritingPrincipleId


class WritingPrinciple(DomainValueObject):
    """A governance principle that guides rule authors.

    Attributes:
        id (WritingPrincipleId): Unique principle identifier.
        title (GovernanceText): Short principle name.
        description (GovernanceText): Detailed application guidance.
    """

    id: WritingPrincipleId = Field(description="Unique principle identifier")
    title: GovernanceText = Field(description="Short principle name")
    description: GovernanceText = Field(description="Detailed guidance for applying this principle")


class WritingPrinciples(RootModel[Tuple[WritingPrinciple, ...]]):
    """Collection of writing principles validated as a YAML list root.

    RootModel lets Pydantic accept a bare list from YAML without a wrapper
    reshape. Uniqueness is the only domain invariant beyond Field constraints.
    """

    model_config = ConfigDict(frozen=True)

    root: Tuple[WritingPrinciple, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def check_unique_ids(self) -> WritingPrinciples:
        """Reject collections that contain duplicate principle IDs.

        Returns:
            WritingPrinciples: Validated instance.

        Raises:
            ValueError: If principle IDs are duplicated.
        """
        result: WritingPrinciples = self
        ids: List[WritingPrincipleId] = [principle.id for principle in self.root]
        if len(ids) != len(set(ids)):
            raise ValueError("Duplicate writing principle IDs are not allowed")
        return result

    @property
    def principles(self) -> Tuple[WritingPrinciple, ...]:
        """Return principles in declaration order.

        Returns:
            Tuple[WritingPrinciple, ...]: Authoring principles.
        """
        result: Tuple[WritingPrinciple, ...] = self.root
        return result

    @cached_property
    def _index(self) -> Dict[WritingPrincipleId, WritingPrinciple]:
        result: Dict[WritingPrincipleId, WritingPrinciple] = {principle.id: principle for principle in self.root}
        return result

    def get(self, a_principle_id: WritingPrincipleId) -> Optional[WritingPrinciple]:
        """Return a principle by ID.

        Args:
            a_principle_id (WritingPrincipleId): Principle identifier.

        Returns:
            Optional[WritingPrinciple]: Matching principle, or None.
        """
        result: Optional[WritingPrinciple] = self._index.get(a_principle_id)
        return result

    def __len__(self) -> int:
        return len(self.root)

    def __contains__(self, a_item: object) -> bool:
        result: bool = isinstance(a_item, str) and a_item in self._index
        return result
