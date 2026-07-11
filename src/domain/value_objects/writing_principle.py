"""Writing principle value object."""

from pydantic import BaseModel, ConfigDict, Field

from domain.identifiers import WritingPrincipleId


class WritingPrinciple(BaseModel):
    """A governance principle that guides rule authors in writing directives."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: WritingPrincipleId = Field(description="Unique principle identifier")
    title: str = Field(description="Short principle name")
    description: str = Field(description="Detailed guidance for applying this principle")
