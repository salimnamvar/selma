"""Document section value object."""

from __future__ import annotations

from typing import Optional, Tuple

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
    guidance: Optional[str] = Field(default=None, description="Authoring guidance for this section")
    columns: Optional[Tuple[str, ...]] = Field(default=None, description="Table column headers")
    children: Optional[Tuple[DocumentSection, ...]] = Field(default=None, description="Subsections")
    schema_encoding: Optional[str] = Field(default=None, description="Schema encoding instructions")

    @model_validator(mode="after")
    def check_columns_require_tabular_content(self) -> DocumentSection:
        """Validate columns are only present for tabular content types."""
        if self.columns and self.content_type == ContentType.PROSE:
            raise ValueError(f"Section '{self.id}': columns are not applicable for prose-only content")
        return self

    def max_depth(self, a_current: int = 1) -> int:
        """Return the maximum nesting depth from this section.

        Args:
            a_current (int): Current depth counter. Defaults to 1.

        Returns:
            int: Maximum nesting depth.
        """
        if not self.children:
            result: int = a_current
        else:
            result = max(child.max_depth(a_current + 1) for child in self.children)
        return result
