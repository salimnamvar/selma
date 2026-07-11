from pydantic import BaseModel, ConfigDict, Field, model_validator

from domain.enums import ContentType
from domain.identifiers import SectionId


class DocumentSection(BaseModel):
    """A structural section defining the composition of a governance document."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: SectionId = Field(description="Unique section identifier")
    title: str = Field(description="Human-readable section title")
    required: bool = Field(default=True, description="Whether this section must be present")
    content_type: ContentType = Field(description="Expected content format")
    guidance: str | None = Field(default=None, description="Authoring guidance for this section")
    columns: tuple[str, ...] | None = Field(default=None, description="Table column headers")
    children: tuple["DocumentSection", ...] | None = Field(default=None, description="Subsections")
    schema_encoding: str | None = Field(default=None, description="Schema encoding instructions")

    @model_validator(mode="after")
    def check_columns_require_tabular_content(self) -> "DocumentSection":
        if self.columns and self.content_type == ContentType.PROSE:
            raise ValueError(f"Section '{self.id}': columns are not applicable for prose-only content")
        return self

    def max_depth(self, current: int = 1) -> int:
        """Return the maximum nesting depth from this section."""
        if not self.children:
            return current
        return max(child.max_depth(current + 1) for child in self.children)
