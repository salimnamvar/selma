"""Writing Principle Value Objects.

Authoring principles that guide directive writers.
"""

from __future__ import annotations

from typing import Tuple

from pydantic import Field

from domain.base import DomainValueObject
from domain.collections import IdentifiedCollection
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


class WritingPrinciples(IdentifiedCollection[WritingPrincipleId, WritingPrinciple]):
    """Collection of writing principles validated as a YAML list root.

    Uniqueness and indexing come from :class:`IdentifiedCollection`.
    Construct via ``WritingPrinciples.model_validate([...])`` or the RootModel
    constructor; no custom factory is required.
    """

    @property
    def principles(self) -> Tuple[WritingPrinciple, ...]:
        """Return principles in declaration order.

        Returns:
            Tuple[WritingPrinciple, ...]: Authoring principles.
        """
        result: Tuple[WritingPrinciple, ...] = self.root
        return result
