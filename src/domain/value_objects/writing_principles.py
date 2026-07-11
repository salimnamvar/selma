from collections import Counter
from typing import Optional

from pydantic import Field, model_validator

from domain.identifiers import WritingPrincipleId
from domain.value_objects.base import DomainValueObject
from domain.value_objects.writing_principle import WritingPrinciple


class WritingPrinciples(DomainValueObject):
    """Collection of writing principles enforcing uniqueness and providing lookup."""

    principles: tuple[WritingPrinciple, ...] = Field(default_factory=tuple, description="Ordered writing principles")

    @model_validator(mode="after")
    def _unique_ids(self) -> "WritingPrinciples":
        ids = [p.id for p in self.principles]
        duplicates = [pid for pid, count in Counter(ids).items() if count > 1]
        if duplicates:
            raise ValueError(f"Duplicate WritingPrinciple IDs: {duplicates}")
        return self

    def get(self, principle_id: WritingPrincipleId) -> Optional[WritingPrinciple]:
        """Retrieve a writing principle by its identifier."""
        return next((p for p in self.principles if p.id == principle_id), None)

    def __len__(self) -> int:
        return len(self.principles)

    def __iter__(self):  # type: ignore[override]
        return iter(self.principles)
