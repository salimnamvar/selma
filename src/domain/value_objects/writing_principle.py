"""Writing principles — authoring guidance collection (inline RootModel)."""

from __future__ import annotations

from collections.abc import Iterator
from functools import cached_property
from typing import Self

from pydantic import ConfigDict, Field, RootModel, model_validator

from domain.base import DomainValueObject, build_index, require_unique
from domain.identifiers import GovernanceText, WritingPrincipleId


class WritingPrinciple(DomainValueObject):
    """A governance principle that guides rule authors."""

    id: WritingPrincipleId = Field(description="Unique principle identifier")
    title: GovernanceText = Field(description="Short principle name")
    description: GovernanceText = Field(description="Detailed guidance")


class WritingPrinciples(RootModel[tuple[WritingPrinciple, ...]]):
    """Collection of writing principles validated as a YAML list root."""

    model_config = ConfigDict(frozen=True, ignored_types=(cached_property,))

    @model_validator(mode="after")
    def _validate(self) -> Self:
        if not self.root:
            raise ValueError("Writing principles collection must not be empty")
        require_unique([str(item.id) for item in self.root], label="IDs")
        return self

    @cached_property
    def _index(self) -> dict[str, WritingPrinciple]:
        return build_index(self.root, key=lambda item: str(item.id))

    def get(self, key: str) -> WritingPrinciple | None:
        """Return the principle for ``key``, or None."""
        return self._index.get(key)

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
        return key in self._index