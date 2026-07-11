"""Writing principles — validated tuple alias (YAML list root)."""

from __future__ import annotations

from typing import Annotated

from pydantic import AfterValidator, Field

from domain.base import DomainValueObject, require_unique
from domain.identifiers import GovernanceText, WritingPrincipleId


class WritingPrinciple(DomainValueObject):
    """A governance principle that guides rule authors."""

    id: WritingPrincipleId = Field(description="Unique principle identifier")
    title: GovernanceText = Field(description="Short principle name")
    description: GovernanceText = Field(description="Detailed guidance")


def _validate_writing_principles(
    principles: tuple[WritingPrinciple, ...],
) -> tuple[WritingPrinciple, ...]:
    if not principles:
        raise ValueError("Writing principles collection must not be empty")
    require_unique([str(item.id) for item in principles], label="IDs")
    return principles


type WritingPrinciples = Annotated[
    tuple[WritingPrinciple, ...],
    Field(min_length=1),
    AfterValidator(_validate_writing_principles),
]


def find_principle(
    principles: WritingPrinciples,
    key: str,
) -> WritingPrinciple | None:
    """Return the writing principle for ``key``, or None."""
    return next((item for item in principles if str(item.id) == key), None)