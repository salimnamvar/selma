"""Document Section Value Objects.

Structural sections and validated document structure for governance documents.
"""

from __future__ import annotations

from collections.abc import Generator, Iterable
from functools import cached_property
from typing import Any, ClassVar, Dict, FrozenSet, Optional, Set, Tuple

from pydantic import ConfigDict, Field, RootModel, field_validator, model_validator

from domain.base import DomainValueObject
from domain.enums import ContentType
from domain.identifiers import GovernanceText, SectionId


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
    columns: Tuple[GovernanceText, ...] = Field(
        default=(),
        description="Table column headers (empty when not tabular)",
    )
    children: Tuple[DocumentSection, ...] = Field(
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

    @field_validator("columns", "children", mode="before")
    @classmethod
    def _none_as_empty(cls, a_value: Any) -> Any:
        """Coerce YAML null to empty tuple; lists coerce to tuples automatically.

        Args:
            a_value (Any): Raw field value.

        Returns:
            Any: Empty tuple when null, otherwise original value.
        """
        result: Any = () if a_value is None else a_value
        return result

    @model_validator(mode="after")
    def check_content_invariants(self) -> DocumentSection:
        """Validate columns vs content type and local nesting depth.

        Returns:
            DocumentSection: Validated instance.

        Raises:
            ValueError: If columns or depth violate section rules.
        """
        result: DocumentSection = self
        if self.columns and self.content_type == ContentType.PROSE:
            msg: str = f"Section '{self.id}': columns are not applicable for prose-only content"
            raise ValueError(msg)
        if self.columns and self.content_type not in self._TABULAR_CONTENT_TYPES:
            msg = f"Section '{self.id}': columns require tabular content type, got {self.content_type}"
            raise ValueError(msg)
        depth: int = self.max_depth()
        if depth > self.MAX_DEPTH:
            msg = f"Section '{self.id}' has depth {depth}, exceeds maximum {self.MAX_DEPTH}"
            raise ValueError(msg)
        return result

    def max_depth(self, a_current: int = 1) -> int:
        """Return the maximum nesting depth from this section.

        Args:
            a_current (int): Current depth counter. Defaults to 1.

        Returns:
            int: Maximum nesting depth.
        """
        result: int = a_current if not self.children else max(child.max_depth(a_current + 1) for child in self.children)
        return result

    def all_ids(self) -> Generator[SectionId]:
        """Yield this section ID and all descendant IDs.

        Yields:
            SectionId: Section IDs in tree order.
        """
        yield self.id
        for child in self.children:
            yield from child.all_ids()

    def traverse(self) -> Generator[DocumentSection]:
        """Yield this section and all descendants in pre-order.

        Yields:
            DocumentSection: Sections in pre-order.
        """
        yield self
        for child in self.children:
            yield from child.traverse()

    def find(self, a_section_id: SectionId) -> Optional[DocumentSection]:
        """Find a section by ID within this subtree.

        Args:
            a_section_id (SectionId): Section identifier to locate.

        Returns:
            Optional[DocumentSection]: Matching section, or None.
        """
        result: Optional[DocumentSection] = None
        if self.id == a_section_id:
            result = self
        else:
            for child in self.children:
                found: Optional[DocumentSection] = child.find(a_section_id)
                if found is not None:
                    result = found
                    break
        return result

    @property
    def is_tabular(self) -> bool:
        """Return True when this section may carry table columns.

        Returns:
            bool: True if content type is tabular or columns are present.
        """
        result: bool = self.content_type in self._TABULAR_CONTENT_TYPES or bool(self.columns)
        return result


class DocumentStructure(RootModel[Tuple[DocumentSection, ...]]):
    """Validated tree of universal document sections as a YAML list root.

    RootModel accepts the bare ``sections:`` list from the doctrine document.
    Domain invariants (required roots, unique IDs, directives children) are
    the only custom validation beyond Field constraints.
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

    model_config = ConfigDict(frozen=True)

    root: Tuple[DocumentSection, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def check_structure(self) -> DocumentStructure:
        """Enforce required sections, unique IDs, and directives children.

        Returns:
            DocumentStructure: Validated instance.

        Raises:
            ValueError: If structure invariants are violated.
        """
        result: DocumentStructure = self
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

        return result

    @property
    def sections(self) -> Tuple[DocumentSection, ...]:
        """Return top-level document sections.

        Returns:
            Tuple[DocumentSection, ...]: Top-level sections.
        """
        result: Tuple[DocumentSection, ...] = self.root
        return result

    @cached_property
    def _index(self) -> Dict[SectionId, DocumentSection]:
        mapping: Dict[SectionId, DocumentSection] = {}
        for root_section in self.root:
            for section in root_section.traverse():
                mapping[section.id] = section
        return mapping

    def get(self, a_section_id: SectionId) -> Optional[DocumentSection]:
        """Return a section by ID from the full tree.

        Args:
            a_section_id (SectionId): Section identifier.

        Returns:
            Optional[DocumentSection]: Matching section, or None.
        """
        result: Optional[DocumentSection] = self._index.get(a_section_id)
        return result

    def all_section_ids(self) -> FrozenSet[SectionId]:
        """Return every section ID in the tree.

        Returns:
            FrozenSet[SectionId]: All section identifiers.
        """
        result: FrozenSet[SectionId] = frozenset(self._index)
        return result

    def __len__(self) -> int:
        return len(self.root)

    @classmethod
    def from_sections(cls, a_sections: Iterable[DocumentSection]) -> DocumentStructure:
        """Build a validated structure from top-level sections.

        Args:
            a_sections (Iterable[DocumentSection]): Top-level sections.

        Returns:
            DocumentStructure: Validated document structure.
        """
        result: DocumentStructure = cls(tuple(a_sections))
        return result
