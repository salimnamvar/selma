"""Sections — universal document section structure (policy_doctrine.yaml: sections)."""

from __future__ import annotations

from typing import Annotated

from pydantic import BaseModel
from pydantic import BeforeValidator
from pydantic import ConfigDict
from pydantic import Field

from domain.base import none_as_empty
from domain.enums import ContentType

REQUIRED_SECTION_IDS: frozenset[str] = frozenset(
    {
        "preamble",
        "governance",
        "definitions",
        "principles",
        "directives",
        "sanctions",
    }
)
DIRECTIVES_CHILD_IDS: frozenset[str] = frozenset(
    {
        "specific_directives",
        "flexible_standards",
    }
)


class Section(BaseModel):
    """One entry in the policy_doctrine.yaml ``sections`` collection."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str = Field(pattern=r"^[a-z][a-z0-9_]*$", description="Unique section identifier")
    title: str = Field(min_length=1, description="Human-readable section title")
    required: bool = Field(default=True, description="Whether this section must be present")
    content_type: ContentType = Field(description="Expected content format")
    guidance: str | None = Field(default=None, min_length=1, description="Authoring guidance")
    columns: Annotated[tuple[str, ...], BeforeValidator(none_as_empty)] = Field(
        default=(), min_length=1, description="Table column headers"
    )
    children: Annotated[tuple[Section, ...], BeforeValidator(none_as_empty)] = Field(
        default=(), description="Subsections"
    )
    schema_encoding: str | None = Field(
        default=None, min_length=1, description="Authoring guidance for schema mapping (descriptive only)"
    )
