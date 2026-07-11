"""Writing principles — authoring guidance for rule documents."""

from __future__ import annotations

from typing import Self

from pydantic import Field, model_validator

from domain.base import DomainValueObject, NameableMixin
from domain.collections import IdentifiedCollection
from domain.identifiers import GovernanceDescription, GovernanceGuidance, WritingPrincipleId


class WritingPrinciple(DomainValueObject, NameableMixin):
    """A governance principle that guides rule authors."""

    id: WritingPrincipleId = Field(description="Unique principle identifier")
    title: GovernanceGuidance = Field(description="Short principle name")
    description: GovernanceDescription = Field(
        description="Detailed guidance for applying this principle"
    )


class WritingPrinciples(IdentifiedCollection[str, WritingPrinciple]):
    """Collection of writing principles validated as a YAML list root."""

    @model_validator(mode="after")
    def _validate_non_empty(self) -> Self:
        if not self.root:
            raise ValueError("Writing principles collection must not be empty")
        return self

    @property
    def principles(self) -> tuple[WritingPrinciple, ...]:
        """Return principles in declaration order (alias for ``items``)."""
        return self.items
