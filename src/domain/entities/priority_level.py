from typing import List

from pydantic import BaseModel, Field

from domain.enums import PriorityCategory


class PriorityLevel(BaseModel):
    """An authority level in the governance priority hierarchy."""

    id: PriorityCategory = Field(description="Unique level identifier")
    level: int = Field(description="Numeric authority rank (1 = highest)")
    title: str = Field(description="Human-readable level name")
    description: str = Field(description="Scope and authority of this level")
    examples: List[str] = Field(description="Typical rules at this authority level")
