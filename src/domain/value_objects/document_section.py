from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from domain.enums import ContentType
from domain.identifiers import SectionId


class DocumentSection(BaseModel):
    """A structural section defining the composition of a governance document."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: SectionId
    title: str
    required: bool
    content_type: ContentType
    guidance: str = Field(description="Authoring guidance for this section")
    columns: Optional[tuple[str, ...]] = Field(default=None, description="Table column headers")
    children: Optional[tuple["DocumentSection", ...]] = Field(default=None, description="Subsections")
    schema_encoding: Optional[str] = Field(default=None, description="Schema encoding instructions")
