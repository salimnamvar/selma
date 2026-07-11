"""Sections — universal document section structure (policy_doctrine.yaml: sections)."""

from __future__ import annotations

from collections.abc import Iterator
from typing import Annotated, ClassVar, Self

from pydantic import BaseModel, BeforeValidator, ConfigDict, Field, model_validator

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

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
    )

    MAX_DEPTH: ClassVar[int] = 3
    _TABULAR_CONTENT_TYPES: ClassVar[frozenset[ContentType]] = frozenset(
        {
            ContentType.TABLE,
            ContentType.PROSE_OR_TABLE,
            ContentType.MIXED,
        }
    )

    id: str = Field(
        pattern=r"^[a-z][a-z0-9_]*$",
        description="Unique section identifier",
    )
    title: str = Field(min_length=1, description="Human-readable section title")
    required: bool = Field(default=True, description="Whether this section must be present")
    content_type: ContentType = Field(description="Expected content format")
    guidance: str | None = Field(default=None, min_length=1, description="Authoring guidance")
    columns: Annotated[tuple[str, ...], BeforeValidator(none_as_empty)] = Field(
        default=(),
        min_length=1,
        description="Table column headers",
    )
    children: Annotated[tuple[Section, ...], BeforeValidator(none_as_empty)] = Field(
        default=(),
        description="Subsections",
    )
    schema_encoding: str | None = Field(
        default=None,
        min_length=1,
        description="Authoring guidance for schema mapping (descriptive only)",
    )

    @model_validator(mode="after")
    def _validate_content(self) -> Self:
        if self.columns and self.content_type not in self._TABULAR_CONTENT_TYPES:
            raise ValueError(f"Section '{self.id}': columns require tabular content type, got {self.content_type}")
        if self.max_depth() > self.MAX_DEPTH:
            raise ValueError(f"Section '{self.id}' has depth {self.max_depth()}, exceeds maximum {self.MAX_DEPTH}")
        return self

    def traverse(self) -> Iterator[Section]:
        """Yield this node and all descendants in pre-order."""
        yield self
        for child in self.children:
            yield from child.traverse()

    def max_depth(self, current: int = 1) -> int:
        """Return maximum depth from this node (leaf depth = ``current``)."""
        result = current
        if self.children:
            result = max(child.max_depth(current + 1) for child in self.children)
        return result
