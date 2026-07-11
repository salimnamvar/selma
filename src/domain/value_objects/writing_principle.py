from pydantic import BaseModel, ConfigDict, Field

from domain.identifiers import Description, WritingPrincipleId


class WritingPrinciple(BaseModel):
    """A governance principle that guides rule authors in writing directives."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: WritingPrincipleId = Field(description="Unique principle identifier")
    title: str = Field(description="Short principle name")
    description: Description = Field(description="Detailed guidance for applying this principle")
