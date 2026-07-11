"""Document template — universal document section structure."""

from __future__ import annotations

from collections.abc import Iterator
from functools import cached_property
from typing import Annotated, ClassVar, Self, cast

from pydantic import BeforeValidator, Field, model_validator

from domain.base import DomainValueObject, NameableMixin, TreeNodeMixin, none_as_empty, require_unique
from domain.collections import IdentifiedCollection
from domain.enums import ContentType
from domain.identifiers import GovernanceGuidance, SectionId


class DocumentSection(DomainValueObject, NameableMixin, TreeNodeMixin):
    """A structural section defining governance document composition.

    Depth is node-counted (leaf = 1). WP-003: max nesting is 3 levels.
    ``schema_encoding`` is authoring guidance only (YAML prose), not executable
    schema configuration.
    """

    MAX_DEPTH: ClassVar[int] = 3
    _TABULAR_CONTENT_TYPES: ClassVar[frozenset[ContentType]] = frozenset(
        {
            ContentType.TABLE,
            ContentType.PROSE_OR_TABLE,
            ContentType.MIXED,
        }
    )

    id: SectionId = Field(description="Unique section identifier")
    title: GovernanceGuidance = Field(description="Human-readable section title")
    required: bool = Field(
        default=True,
        description="Whether this section must be present in a complete document",
    )
    content_type: ContentType = Field(description="Expected content format")
    guidance: GovernanceGuidance | None = Field(
        default=None,
        description="Authoring guidance for this section (optional on nested sections)",
    )
    columns: Annotated[tuple[GovernanceGuidance, ...], BeforeValidator(none_as_empty)] = Field(
        default=(),
        description="Table column headers (empty when not tabular)",
    )
    children: Annotated[tuple[DocumentSection, ...], BeforeValidator(none_as_empty)] = Field(
        default=(),
        description="Subsections",
    )
    schema_encoding: GovernanceGuidance | None = Field(
        default=None,
        description=(
            "Authoring guidance for how this section maps to the rule schema. "
            "Descriptive only — not machine-executable configuration."
        ),
    )

    @model_validator(mode="after")
    def _validate_content(self) -> Self:
        if self.columns and self.content_type not in self._TABULAR_CONTENT_TYPES:
            raise ValueError(
                f"Section '{self.id}': columns require tabular content type, got {self.content_type}"
            )
        depth = self.max_depth()
        if depth > self.MAX_DEPTH:
            raise ValueError(f"Section '{self.id}' has depth {depth}, exceeds maximum {self.MAX_DEPTH}")
        return self

    def iter_ids(self) -> Iterator[SectionId]:
        """Yield this section ID and all descendant IDs."""
        for node in self.iter_nodes():
            yield node.id

    def collect_required(self) -> list[DocumentSection]:
        """Return all required sections in this subtree (pre-order)."""
        return cast(list[DocumentSection], self.collect_where(lambda node: node.required))

    @property
    def is_tabular(self) -> bool:
        """Return True when this section may carry table columns."""
        return self.content_type in self._TABULAR_CONTENT_TYPES or bool(self.columns)


class DocumentTemplate(IdentifiedCollection[str, DocumentSection]):
    """Validated tree of universal document sections (YAML list root).

    Lookup is tree-wide (any nested section id).
    """

    REQUIRED_SECTION_IDS: ClassVar[frozenset[str]] = frozenset(
        {
            "preamble",
            "governance",
            "definitions",
            "principles",
            "directives",
            "sanctions",
        }
    )
    DIRECTIVES_CHILD_IDS: ClassVar[frozenset[str]] = frozenset(
        {
            "specific_directives",
            "flexible_standards",
        }
    )

    @model_validator(mode="after")
    def _validate_ids(self) -> Self:
        """Enforce required sections, unique nested IDs, and directives children."""
        present = {str(section.id) for section in self.root}
        missing = self.REQUIRED_SECTION_IDS - present
        if missing:
            raise ValueError(f"Missing required sections: {sorted(missing)}")

        nested_ids = [str(section_id) for section in self.root for section_id in section.iter_ids()]
        require_unique(nested_ids, label="section ID")

        directives = self.get("directives")
        if directives is not None and directives.children:
            child_ids = {str(child.id) for child in directives.children}
            missing_children = self.DIRECTIVES_CHILD_IDS - child_ids
            if missing_children:
                raise ValueError(
                    f"Directives section missing expected children: {sorted(missing_children)}"
                )

        return self

    @property
    def sections(self) -> tuple[DocumentSection, ...]:
        """Return top-level document sections."""
        return self.items

    @cached_property
    def _index(self) -> dict[str, DocumentSection]:
        """Index every section in the tree for O(1) lookup."""
        return {
            str(section.id): section
            for root in self.root
            for section in root.iter_nodes()
        }


# YAML key remains sections; historical name retained as alias.
DocumentStructure = DocumentTemplate
