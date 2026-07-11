"""Document section and document structure value objects."""

from __future__ import annotations

from collections.abc import Generator, Iterable, Sequence
from functools import cached_property
from typing import cast

from pydantic import ConfigDict, Field, model_validator

from domain.base import DomainValueObject
from domain.enums import ContentType
from domain.identifiers import GovernanceText, SectionId

# Doctrine WP-003 / structural integrity: max three levels of nested sections.
MAX_SECTION_DEPTH = 3

# Top-level sections required by the universal document template.
REQUIRED_SECTION_IDS: frozenset[SectionId] = frozenset(
    {
        "preamble",
        "governance",
        "definitions",
        "principles",
        "directives",
        "sanctions",
    }
)

# Expected children of the directives section (when present).
DIRECTIVES_CHILD_IDS: frozenset[SectionId] = frozenset(
    {
        "specific_directives",
        "flexible_standards",
    }
)

_TABULAR_CONTENT_TYPES = frozenset(
    {
        ContentType.TABLE,
        ContentType.PROSE_OR_TABLE,
        ContentType.MIXED,
    }
)


class DocumentSection(DomainValueObject):
    """A structural section defining the composition of a governance document."""

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
    columns: tuple[GovernanceText, ...] = Field(
        default=(),
        description="Table column headers (empty when not tabular)",
    )
    children: tuple[DocumentSection, ...] = Field(
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

    @model_validator(mode="before")
    @classmethod
    def _normalize_optional_collections(cls, data: object) -> object:
        """Coerce YAML null/missing collections to empty tuples."""
        if not isinstance(data, dict):
            return data
        raw: dict[str, object] = dict(data)  # type: ignore[arg-type]
        normalized: dict[str, object] = dict(raw)
        if normalized.get("columns") is None:
            normalized["columns"] = ()
        else:
            columns = normalized.get("columns")
            if isinstance(columns, list):
                column_items = cast(Sequence[object], columns)
                normalized["columns"] = tuple(column_items)
        if normalized.get("children") is None:
            normalized["children"] = ()
        return normalized

    @model_validator(mode="after")
    def check_content_invariants(self) -> DocumentSection:
        """Validate columns vs content type and local nesting depth."""
        if self.columns and self.content_type == ContentType.PROSE:
            msg = f"Section '{self.id}': columns are not applicable for prose-only content"
            raise ValueError(msg)
        if self.columns and self.content_type not in _TABULAR_CONTENT_TYPES:
            msg = f"Section '{self.id}': columns require tabular content type, got {self.content_type}"
            raise ValueError(msg)
        depth = self.max_depth()
        if depth > MAX_SECTION_DEPTH:
            msg = f"Section '{self.id}' has depth {depth}, exceeds maximum {MAX_SECTION_DEPTH}"
            raise ValueError(msg)
        return self

    def max_depth(self, current: int = 1) -> int:
        """Return the maximum nesting depth from this section (this node = 1)."""
        if not self.children:
            return current
        return max(child.max_depth(current + 1) for child in self.children)

    def all_ids(self) -> Generator[SectionId]:
        """Yield this section's ID and all descendant IDs in tree order."""
        yield self.id
        for child in self.children:
            yield from child.all_ids()

    def traverse(self) -> Generator[DocumentSection]:
        """Yield this section and all descendants in pre-order."""
        yield self
        for child in self.children:
            yield from child.traverse()

    def find(self, section_id: SectionId) -> DocumentSection | None:
        """Find a section by ID within this subtree (including self)."""
        if self.id == section_id:
            return self
        for child in self.children:
            found = child.find(section_id)
            if found is not None:
                return found
        return None

    @property
    def is_tabular(self) -> bool:
        """Return True when this section may carry table columns."""
        return self.content_type in _TABULAR_CONTENT_TYPES or bool(self.columns)


class DocumentStructure(DomainValueObject):
    """Validated tree of universal document sections.

    Owns structural invariants (required roots, unique IDs, depth, directives
    children) so the aggregate root does not micromanage the tree.
    """

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
        ignored_types=(cached_property,),
    )

    sections: tuple[DocumentSection, ...] = Field(
        min_length=1,
        description="Top-level document sections",
    )

    @model_validator(mode="after")
    def check_structure(self) -> DocumentStructure:
        """Enforce required sections, unique IDs, and directives children."""
        present = {section.id for section in self.sections}
        missing = REQUIRED_SECTION_IDS - present
        if missing:
            raise ValueError(f"Missing required sections: {sorted(missing)}")

        seen: set[SectionId] = set()
        for section in self.sections:
            for section_id in section.all_ids():
                if section_id in seen:
                    raise ValueError(f"Duplicate section ID: {section_id}")
                seen.add(section_id)

        directives = next((s for s in self.sections if s.id == "directives"), None)
        if directives is not None and directives.children:
            child_ids = {c.id for c in directives.children}
            missing_children = DIRECTIVES_CHILD_IDS - child_ids
            if missing_children:
                raise ValueError(f"Directives section missing expected children: {sorted(missing_children)}")

        return self

    @cached_property
    def _index(self) -> dict[SectionId, DocumentSection]:
        mapping: dict[SectionId, DocumentSection] = {}
        for root in self.sections:
            for section in root.traverse():
                mapping[section.id] = section
        return mapping

    def get(self, section_id: SectionId) -> DocumentSection | None:
        """Return a section by ID from the full tree, or None."""
        return self._index.get(section_id)

    def all_section_ids(self) -> frozenset[SectionId]:
        """Return every section ID in the tree."""
        return frozenset(self._index)

    def __iter__(self):  # type: ignore[no-untyped-def]
        return iter(self.sections)

    def __len__(self) -> int:
        return len(self.sections)

    @classmethod
    def from_sections(cls, sections: Iterable[DocumentSection]) -> DocumentStructure:
        """Build a validated structure from an iterable of top-level sections."""
        return cls(sections=tuple(sections))
