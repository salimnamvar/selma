"""Writing principles — RootModel collection (YAML list root)."""

from __future__ import annotations

from collections.abc import Iterator
from typing import Self

from pydantic import BaseModel, Field, RootModel, computed_field, model_validator

from domain.base import ROOT_CONFIG, VO_CONFIG, require_unique
from domain.identifiers import GovernanceText, WritingPrincipleId


class WritingPrinciple(BaseModel):
    """A governance principle that guides rule authors."""

    model_config = VO_CONFIG

    id: WritingPrincipleId = Field(description="Unique principle identifier")
    title: GovernanceText = Field(description="Short principle name")
    description: GovernanceText = Field(description="Detailed guidance")


class WritingPrinciples(RootModel[tuple[WritingPrinciple, ...]]):
    """Validated collection of writing principles."""

    model_config = ROOT_CONFIG

    @model_validator(mode="after")
    def _validate(self) -> Self:
        if not self.root:
            raise ValueError("Writing principles collection must not be empty")
        require_unique([str(item.id) for item in self.root], label="IDs")
        return self

    @computed_field  # type: ignore[prop-decorator]
    @property
    def index(self) -> dict[str, WritingPrinciple]:
        """Lookup index keyed by principle id."""
        return {str(item.id): item for item in self.root}

    def get(self, key: str) -> WritingPrinciple | None:
        """Return the principle for ``key``, or None."""
        return self.index.get(key)

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
        return key in self.index