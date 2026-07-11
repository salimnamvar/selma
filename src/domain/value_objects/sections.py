"""Sections — universal document section structure (policy_doctrine.yaml: sections)."""

from __future__ import annotations

from collections.abc import Iterator
from typing import Annotated, Any, ClassVar, Self

from pydantic import BaseModel, BeforeValidator, Field, model_validator

from domain.base import VO_CONFIG
from domain.enums import ContentType
from domain.identifiers import GovernanceText

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


def _none_as_empty(value: Any) -> Any:
    return () if value is None else value


class Section(BaseModel):
    """One entry in the policy_doctrine.yaml ``sections`` collection."""

    model_config = VO_CONFIG

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
    title: GovernanceText = Field(description="Human-readable section title")
    required: bool = Field(default=True, description="Whether this section must be present")
    content_type: ContentType = Field(description="Expected content format")
    guidance: GovernanceText | None = Field(default=None, description="Authoring guidance")
    columns: Annotated[tuple[GovernanceText, ...], BeforeValidator(_none_as_empty)] = Field(
        default=(),
        description="Table column headers",
    )
    children: Annotated[tuple[Section, ...], BeforeValidator(_none_as_empty)] = Field(
        default=(),
        description="Subsections",
    )
    schema_encoding: GovernanceText | None = Field(
        default=None,
        description="Authoring guidance for schema mapping (descriptive only)",
    )

    @model_validator(mode="after")
    def _validate_content(self) -> Self:
        if self.columns and self.content_type not in self._TABULAR_CONTENT_TYPES:
            raise ValueError(
                f"Section '{self.id}': columns require tabular content type, got {self.content_type}"
            )
        if self.max_depth() > self.MAX_DEPTH:
            raise ValueError(
                f"Section '{self.id}' has depth {self.max_depth()}, exceeds maximum {self.MAX_DEPTH}"
            )
        return self

    def traverse(self) -> Iterator[Section]:
        """Yield this node and all descendants in pre-order."""
        yield self
        for child in self.children:
            yield from child.traverse()

    def iter_ids(self) -> Iterator[str]:
        """Yield ``id`` values for this node and all descendants."""
        for node in self.traverse():
            yield str(node.id)

    def max_depth(self, current: int = 1) -> int:
        """Return maximum depth from this node (leaf depth = ``current``)."""
        result = current
        if self.children:
            result = max(child.max_depth(current + 1) for child in self.children)
        return result