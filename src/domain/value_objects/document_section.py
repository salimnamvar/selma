from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from domain.enums import ContentType
from domain.identifiers import Prose, SectionId


class DocumentSection(BaseModel):
    """A structural section defining the composition of a governance document."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: SectionId = Field(description="Unique section identifier")
    title: str = Field(description="Human-readable section title")
    required: bool = Field(description="Whether this section must be present")
    content_type: ContentType = Field(description="Expected content format")
    guidance: Prose = Field(description="Authoring guidance for this section")
    columns: Optional[tuple[str, ...]] = Field(default=None, description="Table column headers")
    children: Optional[tuple["DocumentSection", ...]] = Field(default=None, description="Subsections")
    schema_encoding: Optional[Prose] = Field(default=None, description="Schema encoding instructions")
