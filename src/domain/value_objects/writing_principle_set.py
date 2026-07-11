from collections import Counter

from pydantic import BaseModel, ConfigDict, Field, model_validator

from domain.identifiers import WritingPrincipleId
from domain.value_objects.writing_principle import WritingPrinciple


class WritingPrincipleSet(BaseModel):
    """Collection of writing principles enforcing uniqueness."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    principles: tuple[WritingPrinciple, ...] = Field(default_factory=tuple, description="Ordered writing principles")

    @model_validator(mode="after")
    def _unique_ids(self) -> "WritingPrincipleSet":
        ids = [p.id for p in self.principles]
        duplicates = [pid for pid, count in Counter(ids).items() if count > 1]
        if duplicates:
            raise ValueError(f"Duplicate WritingPrinciple IDs: {duplicates}")
        return self

    def get(self, principle_id: WritingPrincipleId) -> WritingPrinciple | None:
        """Retrieve a writing principle by its identifier."""
        return next((p for p in self.principles if p.id == principle_id), None)

    def __len__(self) -> int:
        return len(self.principles)

    def __iter__(self):  # type: ignore[override]
        return iter(self.principles)
