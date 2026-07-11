from pydantic import BaseModel, ConfigDict, Field, computed_field

from domain.enums import PriorityCategory
from domain.identifiers import Prose


class PriorityLevel(BaseModel):
    """An authority level in the governance priority hierarchy."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    category: PriorityCategory = Field(description="Unique level identifier")
    rank: int = Field(ge=1, le=5, description="Numeric authority rank (1 = highest)")
    title: str = Field(description="Human-readable level name")
    description: Prose = Field(description="Scope and authority of this level")


class PrioritySystem(BaseModel):
    """Declares the authority levels and conflict resolution intent."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    levels: tuple[PriorityLevel, ...] = Field(description="Ordered authority levels")
    resolution_intent: Prose = Field(description="Governance intent for conflict resolution")

    @computed_field  # type: ignore[prop-decorator]
    @property
    def levels_by_category(self) -> dict[PriorityCategory, PriorityLevel]:
        """O(1) lookup mapping from category to level."""
        return {level.category: level for level in self.levels}

    def get_level(self, category: PriorityCategory) -> PriorityLevel | None:
        """Retrieve a priority level by its category."""
        return self.levels_by_category.get(category)
