"""Writing Principle Value Objects."""

from __future__ import annotations

from pydantic import Field

from domain.base import DomainValueObject, NameableMixin
from domain.collections import IdentifiedCollection
from domain.identifiers import GovernanceText, WritingPrincipleId


class WritingPrinciple(DomainValueObject, NameableMixin):
    """A governance principle that guides rule authors."""

    id: WritingPrincipleId = Field(description="Unique principle identifier")
    title: GovernanceText = Field(description="Short principle name")
    description: GovernanceText = Field(description="Detailed guidance for applying this principle")


class WritingPrinciples(IdentifiedCollection[WritingPrincipleId, WritingPrinciple]):
    """Collection of writing principles validated as a YAML list root."""

    @property
    def principles(self) -> tuple[WritingPrinciple, ...]:
        """Return principles in declaration order."""
        return self.root
