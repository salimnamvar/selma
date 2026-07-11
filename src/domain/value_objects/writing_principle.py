"""Writing principle value objects."""

from __future__ import annotations

from functools import cached_property

from pydantic import ConfigDict, Field, model_validator

from domain.base import DomainValueObject
from domain.identifiers import GovernanceText, WritingPrincipleId


class WritingPrinciple(DomainValueObject):
    """A governance principle that guides rule authors in writing directives."""

    id: WritingPrincipleId = Field(description="Unique principle identifier")
    title: GovernanceText = Field(description="Short principle name")
    description: GovernanceText = Field(description="Detailed guidance for applying this principle")


class WritingPrinciples(DomainValueObject):
    """Collection of writing principles with uniqueness and O(1) lookup."""

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
        ignored_types=(cached_property,),
    )

    principles: tuple[WritingPrinciple, ...] = Field(
        min_length=1,
        description="Authoring principles",
    )

    @model_validator(mode="after")
    def check_unique_ids(self) -> WritingPrinciples:
        """Reject collections that contain duplicate principle IDs."""
        ids = [p.id for p in self.principles]
        if len(ids) != len(set(ids)):
            raise ValueError("Duplicate writing principle IDs are not allowed")
        return self

    @cached_property
    def _index(self) -> dict[WritingPrincipleId, WritingPrinciple]:
        return {p.id: p for p in self.principles}

    def get(self, principle_id: WritingPrincipleId) -> WritingPrinciple | None:
        """Return a principle by ID, or None if absent."""
        return self._index.get(principle_id)

    def __iter__(self):  # type: ignore[no-untyped-def]
        return iter(self.principles)

    def __len__(self) -> int:
        return len(self.principles)

    def __contains__(self, item: object) -> bool:
        if isinstance(item, str):
            return item in self._index
        return False
