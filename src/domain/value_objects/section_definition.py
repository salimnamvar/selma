from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from domain.enums import ContentType
from domain.identifiers import Prose, SectionId
from domain.value_objects.table_column import TableColumn


class TableSchema(BaseModel):
    """Defines the column structure for tabular sections."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    columns: tuple[TableColumn, ...] = Field(description="Ordered column definitions")


class SectionDefinition(BaseModel):
    """A structural section defining the composition of a governance document."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: SectionId = Field(description="Unique section identifier")
    title: str = Field(description="Human-readable section title")
    required: bool = Field(description="Whether this section must be present")
    content_type: ContentType = Field(description="Expected content format")
    guidance: Prose = Field(description="Authoring guidance for this section")
    table_schema: Optional[TableSchema] = Field(default=None, description="Table column structure")
    children: tuple["SectionDefinition", ...] = Field(default_factory=tuple, description="Subsections")
