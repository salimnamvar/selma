"""Writing principles — authoring guidance collection (inline RootModel)."""

from __future__ import annotations

from collections.abc import Iterator
from typing import Self

from pydantic import Field, RootModel, model_validator

from domain.base import DomainValueObject, require_unique
from domain.identifiers import GovernanceText, WritingPrincipleId


class WritingPrinciple(DomainValueObject):
    """A governance principle that guides rule authors."""

    id: WritingPrincipleId = Field(description="Unique principle identifier")
    title: GovernanceText = Field(description="Short principle name")
    description: GovernanceText = Field(description="Detailed guidance")


class WritingPrinciples(RootModel[tuple[WritingPrinciple, ...]]):
    """Collection of writing principles validated as a YAML list root."""

    model_config = {"frozen": True}

    @model_validator(mode="after")
    def _validate(self) -> Self:
        if not self.root:
            raise ValueError("Writing principles collection must not be empty")
        require_unique([str(item.id) for item in self.root], label="IDs")
        return self

    def get(self, key: str) -> WritingPrinciple | None:
        """Return the principle for ``key``, or None."""
        return next((item for item in self.root if str(item.id) == key), None)

    def require(self, key: str) -> WritingPrinciple:
        """Return the principle for ``key``, or raise KeyError."""
        result = self.get(key)
        if result is None:
            raise KeyError(f"Item with key '{key}' not found")
        return result

    def __iter__(self) -> Iterator[WritingPrinciple]:  # type: ignore[override]
        yield from self.root

    def __len__(self) -> int:
        return len(self.root)

    def __contains__(self, item: object) -> bool:
        key = str(item.id) if hasattr(item, "id") else str(item)  # type: ignore[attr-defined]
        return self.get(key) is not None