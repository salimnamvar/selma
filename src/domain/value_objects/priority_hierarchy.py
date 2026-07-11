"""Priority hierarchy value objects."""

from pydantic import BaseModel, ConfigDict, Field, model_validator

from domain.enums import PriorityCategory


class PriorityLevel(BaseModel):
    """An authority level in the governance priority hierarchy."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: PriorityCategory = Field(description="Unique level identifier")
    level: int = Field(ge=1, description="Numeric authority rank (1 = highest)")
    title: str = Field(description="Human-readable level name")
    description: str = Field(description="Scope and authority of this level")
    examples: tuple[str, ...] = Field(description="Typical rules at this authority level")


class PriorityHierarchy(BaseModel):
    """Declares the authority levels and conflict resolution intent."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    description: str = Field(description="How priority hierarchy works")
    levels: tuple[PriorityLevel, ...] = Field(description="Ordered authority levels")
    conflict_resolution_intent: str = Field(
        description="Governance intent for how priority affects conflict resolution"
    )

    @model_validator(mode="after")
    def check_level_ordering(self) -> "PriorityHierarchy":
        """Validate priority levels are contiguous starting from 1."""
        sorted_levels = sorted(self.levels, key=lambda pl: pl.level)
        for i, level in enumerate(sorted_levels, start=1):
            if level.level != i:
                raise ValueError(
                    f"Priority level '{level.id}' has level={level.level}, "
                    f"expected {i}. Levels must be contiguous starting from 1."
                )
        return self
