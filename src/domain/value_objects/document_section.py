"""Document Section Value Objects.

Structural sections and validated document structure for governance documents.
"""

from __future__ import annotations

from functools import cached_property
from typing import Annotated, ClassVar, Dict, FrozenSet, Iterator, Optional, Set, Tuple

from pydantic import BeforeValidator, Field, model_validator

from domain.base import DomainValueObject, none_as_empty
from domain.collections import IdentifiedCollection
from domain.enums import ContentType
from domain.identifiers import GovernanceText, SectionId

_OptionalTuple = Annotated[Tuple[GovernanceText, ...], BeforeValidator(none_as_empty)]
_OptionalChildren = Annotated[Tuple["DocumentSection", ...], BeforeValidator(none_as_empty)]


class DocumentSection(DomainValueObject):
    """A structural section defining governance document composition.

    Attributes:
        id (SectionId): Unique section identifier.
        title (GovernanceText): Human-readable section title.
        required (bool): Whether this section must be present.
        content_type (ContentType): Expected content format.
        guidance (Optional[GovernanceText]): Authoring guidance.
        columns (Tuple[GovernanceText, ...]): Table column headers.
        children (Tuple[DocumentSection, ...]): Subsections.
        schema_encoding (Optional[GovernanceText]): Schema mapping guidance.
    """

    MAX_DEPTH: ClassVar[int] = 3
    _TABULAR_CONTENT_TYPES: ClassVar[FrozenSet[ContentType]] = frozenset(
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
    guidance: Optional[GovernanceText] = Field(
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
    schema_encoding: Optional[GovernanceText] = Field(
        default=None,
        description=(
            "Authoring guidance for how this section maps to the rule schema. "
            "Descriptive only — not machine-executable configuration."
        ),
    )

    @model_validator(mode="after")
    def check_content_invariants(self) -> DocumentSection:
        """Validate columns vs content type and local nesting depth."""
        if self.columns and self.content_type == ContentType.PROSE:
            raise ValueError(f"Section '{self.id}': columns are not applicable for prose-only content")
        if self.columns and self.content_type not in self._TABULAR_CONTENT_TYPES:
            raise ValueError(f"Section '{self.id}': columns require tabular content type, got {self.content_type}")
        depth: int = self.max_depth()
        if depth > self.MAX_DEPTH:
            raise ValueError(f"Section '{self.id}' has depth {depth}, exceeds maximum {self.MAX_DEPTH}")
        return self

    def max_depth(self, a_current: int = 1) -> int:
        """Return the maximum nesting depth from this section."""
        result: int = a_current
        if self.children:
            result = max(child.max_depth(a_current + 1) for child in self.children)
        return result

    def all_ids(self) -> Iterator[SectionId]:
        """Yield this section ID and all descendant IDs."""
        yield self.id
        for child in self.children:
            yield from child.all_ids()

    def traverse(self) -> Iterator[DocumentSection]:
        """Yield this section and all descendants in pre-order."""
        yield self
        for child in self.children:
            yield from child.traverse()

    def get(self, a_section_id: SectionId) -> Optional[DocumentSection]:
        """Find a section by ID within this subtree."""
        result: Optional[DocumentSection] = None
        if self.id == a_section_id:
            result = self
        else:
            for child in self.children:
                found: Optional[DocumentSection] = child.get(a_section_id)
                if found is not None:
                    result = found
                    break
        return result

    @property
    def is_tabular(self) -> bool:
        """Return True when this section may carry table columns."""
        result: bool = self.content_type in self._TABULAR_CONTENT_TYPES or bool(self.columns)
        return result


class DocumentStructure(IdentifiedCollection[SectionId, DocumentSection]):
    """Validated tree of universal document sections as a YAML list root.

    RootModel accepts the bare ``sections:`` list from the doctrine document.
    Construct via ``DocumentStructure.model_validate([...])`` or the RootModel
    constructor. Nested uniqueness and required-section rules are domain
    validators beyond the base collection index.
    """

    REQUIRED_SECTION_IDS: ClassVar[FrozenSet[SectionId]] = frozenset(
        {
            "preamble",
            "governance",
            "definitions",
            "principles",
            "directives",
            "sanctions",
        }
    )
    DIRECTIVES_CHILD_IDS: ClassVar[FrozenSet[SectionId]] = frozenset(
        {
            "specific_directives",
            "flexible_standards",
        }
    )

    def item_id(self, a_item: DocumentSection) -> SectionId:
        """Return the top-level section identifier."""
        result: SectionId = a_item.id
        return result

    @model_validator(mode="after")
    def check_unique_ids(self) -> DocumentStructure:
        """Enforce required sections, unique nested IDs, and directives children.

        Overrides the base top-level uniqueness check with full-tree rules.
        """
        present: Set[SectionId] = {section.id for section in self.root}
        missing: FrozenSet[SectionId] = self.REQUIRED_SECTION_IDS - present
        if missing:
            raise ValueError(f"Missing required sections: {sorted(missing)}")

        seen: Set[SectionId] = set()
        for section in self.root:
            for section_id in section.all_ids():
                if section_id in seen:
                    raise ValueError(f"Duplicate section ID: {section_id}")
                seen.add(section_id)

        directives: Optional[DocumentSection] = next(
            (section for section in self.root if section.id == "directives"),
            None,
        )
        if directives is not None and directives.children:
            child_ids: Set[SectionId] = {child.id for child in directives.children}
            missing_children: FrozenSet[SectionId] = self.DIRECTIVES_CHILD_IDS - child_ids
            if missing_children:
                raise ValueError(f"Directives section missing expected children: {sorted(missing_children)}")

        return self

    @property
    def sections(self) -> Tuple[DocumentSection, ...]:
        """Return top-level document sections."""
        result: Tuple[DocumentSection, ...] = self.root
        return result

    @cached_property
    def _index(self) -> Dict[SectionId, DocumentSection]:
        mapping: Dict[SectionId, DocumentSection] = {}
        for root_section in self.root:
            for section in root_section.traverse():
                mapping[section.id] = section
        return mapping

    def all_ids(self) -> FrozenSet[SectionId]:
        """Return every section ID in the tree."""
        result: FrozenSet[SectionId] = frozenset(self._index)
        return result
