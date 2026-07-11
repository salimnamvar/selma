"""Document template — universal document section structure."""

from __future__ import annotations

from collections.abc import Iterator
from typing import Annotated, ClassVar

from pydantic import AfterValidator, BeforeValidator, Field, model_validator

from domain.base import DomainValueObject, none_as_empty, require_unique
from domain.enums import ContentType
from domain.identifiers import GovernanceText, SectionId

# Domain constants derived from policy_doctrine.yaml governance rules.
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


class DocumentSection(DomainValueObject):
    """A structural section defining governance document composition."""

    MAX_DEPTH: ClassVar[int] = 3
    _TABULAR_CONTENT_TYPES: ClassVar[frozenset[ContentType]] = frozenset(
        {
            ContentType.TABLE,
            ContentType.PROSE_OR_TABLE,
            ContentType.MIXED,
        }
    )

    id: SectionId = Field(description="Unique section identifier")
    title: GovernanceText = Field(description="Human-readable section title")
    required: bool = Field(default=True, description="Whether this section must be present")
    content_type: ContentType = Field(description="Expected content format")
    guidance: GovernanceText | None = Field(default=None, description="Authoring guidance")
    columns: Annotated[tuple[GovernanceText, ...], BeforeValidator(none_as_empty)] = Field(
        default=(),
        description="Table column headers",
    )
    children: Annotated[tuple[DocumentSection, ...], BeforeValidator(none_as_empty)] = Field(
        default=(),
        description="Subsections",
    )
    schema_encoding: GovernanceText | None = Field(
        default=None,
        description="Authoring guidance for schema mapping (descriptive only)",
    )

    @model_validator(mode="after")
    def _validate_content(self) -> DocumentSection:
        if self.columns and self.content_type not in self._TABULAR_CONTENT_TYPES:
            raise ValueError(
                f"Section '{self.id}': columns require tabular content type, got {self.content_type}"
            )
        if self.max_depth() > self.MAX_DEPTH:
            raise ValueError(
                f"Section '{self.id}' has depth {self.max_depth()}, exceeds maximum {self.MAX_DEPTH}"
            )
        return self

    def traverse(self) -> Iterator[DocumentSection]:
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

    def iter_ids(self) -> Iterator[SectionId]:
        """Yield this section ID and all descendant IDs."""
        for node in self.traverse():
            yield node.id


def find_section(
    sections: tuple[DocumentSection, ...],
    key: str,
) -> DocumentSection | None:
    """Return the first section whose id equals ``key`` in the tree, or None."""
    return next(
        (node for root in sections for node in root.traverse() if str(node.id) == key),
        None,
    )


def _validate_document_sections(
    sections: tuple[DocumentSection, ...],
) -> tuple[DocumentSection, ...]:
    present = {str(section.id) for section in sections}
    missing = REQUIRED_SECTION_IDS - present
    if missing:
        raise ValueError(f"Missing required sections: {sorted(missing)}")

    nested_ids = [str(section_id) for section in sections for section_id in section.iter_ids()]
    require_unique(nested_ids, label="section ID")

    directives = find_section(sections, "directives")
    if directives is not None and directives.children:
        child_ids = {str(child.id) for child in directives.children}
        missing_children = DIRECTIVES_CHILD_IDS - child_ids
        if missing_children:
            raise ValueError(
                f"Directives section missing expected children: {sorted(missing_children)}"
            )
    return sections


type DocumentSections = Annotated[
    tuple[DocumentSection, ...],
    Field(min_length=1),
    AfterValidator(_validate_document_sections),
]