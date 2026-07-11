from typing import List, Optional

from pydantic import BaseModel, Field

from domain.enums import ContentType


class DocumentSection(BaseModel):
    """A structural section defining the composition of a governance document."""

    id: str = Field(description="Unique section identifier")
    title: str = Field(description="Human-readable section title")
    required: bool = Field(description="Whether this section must be present")
    content_type: ContentType = Field(description="Expected content format")
    guidance: str = Field(description="Authoring guidance for this section")
    columns: Optional[List[str]] = Field(default=None, description="Table column headers when content_type is table")
    children: Optional[List["DocumentSection"]] = Field(default=None, description="Subsections")
    schema_encoding: Optional[str] = Field(default=None, description="Schema encoding instructions")
