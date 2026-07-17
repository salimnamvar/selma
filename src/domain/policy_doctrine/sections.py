"""Sections — universal document section structure (policy_doctrine.yaml: sections)."""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


class ContentType(StrEnum):
    """Content formats permitted in document sections."""

    PROSE = "prose"
    TABLE = "table"
    PROSE_OR_TABLE = "prose_or_table"
    MIXED = "mixed"


class Section(BaseModel):
    """Universal document section structure."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str = Field(pattern=r"^[a-z][a-z0-9_]*$", description="Unique section identifier")
    title: str = Field(min_length=1, description="Human-readable section title")
    required: bool = Field(default=True, description="Whether this section must be present")
    content_type: ContentType = Field(description="Expected content format")
    guidance: str | None = Field(default=None, min_length=1, description="Authoring guidance")
    columns: tuple[str, ...] | None = Field(default=None, min_length=1, description="Table column headers")
    children: tuple[Section, ...] | None = Field(default=None, description="Subsections")
    schema_encoding: str | None = Field(
        default=None, min_length=1, description="Authoring guidance for schema mapping (descriptive only)"
    )
