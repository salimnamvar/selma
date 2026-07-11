"""Document Section Value Objects."""

from __future__ import annotations

from collections.abc import Iterator
from functools import cached_property
from typing import Annotated, ClassVar

from pydantic import BeforeValidator, Field, model_validator

from domain.base import DomainValueObject, NameableMixin, TreeNodeMixin, none_as_empty
from domain.collections import IdentifiedCollection
from domain.enums import ContentType
from domain.identifiers import GovernanceText, SectionId

_OptionalTuple = Annotated[tuple[GovernanceText, ...], BeforeValidator(none_as_empty)]
_OptionalChildren = Annotated[tuple["DocumentSection", ...], BeforeValidator(none_as_empty)]


class DocumentSection(DomainValueObject, NameableMixin, TreeNodeMixin):
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
    required: bool = Field(
        default=True,
        description="Whether this section must be present in a complete document",
    )
    content_type: ContentType = Field(description="Expected content format")
    guidance: GovernanceText | None = Field(
        default=None,
        description="Authoring guidance for this section",
    )
    columns: _OptionalTuple = Field(
        default=(),
        description="Table column headers (empty when not tabular)",
    )
    children: _OptionalChildren = Field(
        default=(),
        description="Subsections",
    )
    schema_encoding: GovernanceText | None = Field(
        default=None,
        description=(
            "Authoring guidance for how this section maps to the rule schema. "
            "Descriptive only — not machine-executable configuration."
        ),
    )

    @model_validator(mode="after")
    def _validate_content(self) -> DocumentSection:
        """Validate columns vs content type and local nesting depth."""
        if self.columns and self.content_type == ContentType.PROSE:
            raise ValueError(f"Section '{self.id}': columns are not applicable for prose-only content")
        if self.columns and self.content_type not in self._TABULAR_CONTENT_TYPES:
            raise ValueError(f"Section '{self.id}': columns require tabular content type, got {self.content_type}")
        depth = self.max_depth()
        if depth > self.MAX_DEPTH:
            raise ValueError(f"Section '{self.id}' has depth {depth}, exceeds maximum {self.MAX_DEPTH}")
        return self

    def max_depth(self, a_current: int = 1) -> int:
        """Return the maximum nesting depth from this section (leaf = 1)."""
        return a_current if not self.children else max(child.max_depth(a_current + 1) for child in self.children)

    def all_ids(self) -> Iterator[SectionId]:
        """Yield this section ID and all descendant IDs."""
        yield self.id
        for child in self.children:
            yield from child.all_ids()

    def find_required(self) -> list[DocumentSection]:
        """Return all required sections in this subtree."""
        result: list[DocumentSection] = [self] if self.required else []
        for child in self.children:
            result.extend(child.find_required())
        return result

    @property
    def is_tabular(self) -> bool:
        """Return True when this section may carry table columns."""
        return self.content_type in self._TABULAR_CONTENT_TYPES or bool(self.columns)


class DocumentStructure(IdentifiedCollection[SectionId, DocumentSection]):
    """Validated tree of universal document sections as a YAML list root."""

    REQUIRED_SECTION_IDS: ClassVar[frozenset[SectionId]] = frozenset(
        {
            "preamble",
            "governance",
            "definitions",
            "principles",
            "directives",
            "sanctions",
        }
    )
    DIRECTIVES_CHILD_IDS: ClassVar[frozenset[SectionId]] = frozenset(
        {
            "specific_directives",
            "flexible_standards",
        }
    )

    @model_validator(mode="after")
    def _validate_ids(self) -> DocumentStructure:
        """Enforce required sections, unique nested IDs, and directives children."""
        present: set[SectionId] = {section.id for section in self.root}
        missing: frozenset[SectionId] = self.REQUIRED_SECTION_IDS - present
        if missing:
            raise ValueError(f"Missing required sections: {sorted(missing)}")

        seen: set[SectionId] = set()
        for section in self.root:
            for section_id in section.all_ids():
                if section_id in seen:
                    raise ValueError(f"Duplicate section ID: {section_id}")
                seen.add(section_id)

        directives: DocumentSection | None = next(
            (section for section in self.root if section.id == "directives"),
            None,
        )
        if directives is not None and directives.children:
            child_ids: set[SectionId] = {child.id for child in directives.children}
            missing_children: frozenset[SectionId] = self.DIRECTIVES_CHILD_IDS - child_ids
            if missing_children:
                raise ValueError(f"Directives section missing expected children: {sorted(missing_children)}")

        return self

    @property
    def sections(self) -> tuple[DocumentSection, ...]:
        """Return top-level document sections."""
        return self.root

    @cached_property
    def _index(self) -> dict[SectionId, DocumentSection]:
        """Index every section in the tree for O(1) lookup."""
        mapping: dict[SectionId, DocumentSection] = {}
        for root_section in self.root:
            for section in root_section.traverse():
                mapping[section.id] = section
        return mapping

    def all_ids(self) -> frozenset[SectionId]:
        """Return every section ID in the tree."""
        return frozenset(self._index)
