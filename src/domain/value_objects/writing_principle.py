"""Writing Principle Value Objects.

Authoring principles that guide directive writers.
"""

from __future__ import annotations

from typing import Optional

from pydantic import Field

from domain.base import DomainValueObject, NameableMixin
from domain.collections import IdentifiedCollection
from domain.identifiers import GovernanceText
from domain.identifiers import WritingPrincipleId


class WritingPrinciple(DomainValueObject, NameableMixin):
    """A governance principle that guides rule authors.

    Attributes:
        id (WritingPrincipleId): Unique principle identifier.
        title (GovernanceText): Short principle name.
        description (GovernanceText): Detailed application guidance.

    Standardized methods:
        - to_dict() -> dict: Convert to dictionary
        - to_json() -> str: Convert to JSON string
        - from_dict(data) -> WritingPrinciple: Create from dictionary
        - from_json(json_str) -> WritingPrinciple: Create from JSON string
        - validate() -> WritingPrinciple: Validate the model
        - name -> str: Human-readable name (alias for title, from NameableMixin)
    """

    id: WritingPrincipleId = Field(description="Unique principle identifier")
    title: GovernanceText = Field(description="Short principle name")
    description: GovernanceText = Field(description="Detailed guidance for applying this principle")


class WritingPrinciples(IdentifiedCollection[WritingPrincipleId, WritingPrinciple]):
    """Collection of writing principles validated as a YAML list root.

    Uniqueness and indexing come from :class:`IdentifiedCollection`.
    Construct via ``WritingPrinciples.model_validate([...])`` or the RootModel
    constructor; no custom factory is required.

    Standardized methods:
        - get(id) -> Optional[WritingPrinciple]: Safe lookup
        - find(id) -> WritingPrinciple: Strict lookup (raises KeyError)
        - get_all(ids) -> list[WritingPrinciple]: Batch safe lookup
        - find_all(ids) -> list[WritingPrinciple]: Batch strict lookup
        - has(id) -> bool: Check if ID exists
        - filter(predicate) -> list[WritingPrinciple]: Filter by predicate
        - map(func) -> list[Any]: Apply function to all items
    """

    @property
    def principles(self) -> tuple[WritingPrinciple, ...]:
        """Return principles in declaration order.

        Returns:
            tuple[WritingPrinciple, ...]: Authoring principles.
        """
        result: tuple[WritingPrinciple, ...] = self.root
        return result

    @property
    def titles(self) -> list[str]:
        """Return all principle titles."""
        return [principle.title for principle in self.root]

    @property
    def descriptions(self) -> list[str]:
        """Return all principle descriptions."""
        return [principle.description for principle in self.root]

    # Standardized lookup by title
    def get_by_title(self, a_title: str) -> Optional[WritingPrinciple]:
        """Find principle by title.

        Args:
            a_title: Title to search for.

        Returns:
            Principle with matching title, or None if not found.
        """
        for principle in self.root:
            if principle.title == a_title:
                return principle
        return None

    def find_by_title(self, a_title: str) -> WritingPrinciple:
        """Find principle by title, raising if not found.

        Args:
            a_title: Title to search for.

        Returns:
            Principle with matching title.

        Raises:
            KeyError: If no principle with the given title exists.
        """
        result = self.get_by_title(a_title)
        if result is None:
            raise KeyError(f"Writing principle with title '{a_title}' not found")
        return result
