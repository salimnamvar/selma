"""Writing Principle Value Objects.

Authoring principles that guide directive writers.
"""

from __future__ import annotations

from pydantic import Field

from domain.base import DomainValueObject, NameableMixin
from domain.collections import IdentifiedCollection
from domain.identifiers import GovernanceText, WritingPrincipleId


class WritingPrinciple(DomainValueObject, NameableMixin):
    """A governance principle that guides rule authors.

    Attributes:
        id: Unique principle identifier.
        title: Short principle name.
        description: Detailed application guidance.
    """

    id: WritingPrincipleId = Field(description="Unique principle identifier")
    title: GovernanceText = Field(description="Short principle name")
    description: GovernanceText = Field(description="Detailed guidance for applying this principle")


class WritingPrinciples(IdentifiedCollection[WritingPrincipleId, WritingPrinciple]):
    """Collection of writing principles validated as a YAML list root.

    Uniqueness and indexing come from :class:`IdentifiedCollection`.
    Secondary lookups: ``get_by("title", ...)`` / ``find_by("title", ...)``.
    """

    @property
    def principles(self) -> tuple[WritingPrinciple, ...]:
        """Return principles in declaration order."""
        return self.root
