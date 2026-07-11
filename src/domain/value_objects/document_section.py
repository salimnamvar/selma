"""Document template — universal document section structure (no mixins)."""

from __future__ import annotations

from collections.abc import Iterator
from functools import cached_property
from typing import Annotated, ClassVar, Self

from pydantic import BeforeValidator, ConfigDict, Field, RootModel, model_validator

from domain.base import DomainValueObject, build_index, none_as_empty, require_unique
from domain.enums import ContentType
from domain.identifiers import GovernanceText, SectionId


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

    @property
    def is_tabular(self) -> bool:
        """Return True when this section may carry table columns."""
        return self.content_type in self._TABULAR_CONTENT_TYPES or bool(self.columns)

    def traverse(self) -> Iterator[DocumentSection]:
        """Yield this node and all descendants in pre-order."""
        yield self
        for child in self.children:
            yield from child.traverse()

    def get(self, key: str) -> DocumentSection | None:
        """Return the first node whose id equals ``key``, or None."""
        return next((node for node in self.traverse() if str(node.id) == key), None)

    def require(self, key: str) -> DocumentSection:
        """Return the node for ``key``, or raise KeyError."""
        result = self.get(key)
        if result is None:
            raise KeyError(f"Item with key '{key}' not found")
        return result

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


class DocumentTemplate(RootModel[tuple[DocumentSection, ...]]):
    """Validated tree of universal document sections (YAML list root)."""

    model_config = ConfigDict(frozen=True, ignored_types=(cached_property,))

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
        present = {str(section.id) for section in self.root}
        missing = self.REQUIRED_SECTION_IDS - present
        if missing:
            raise ValueError(f"Missing required sections: {sorted(missing)}")

        nested_ids = [str(sid) for section in self.root for sid in section.iter_ids()]
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

    @cached_property
    def _index(self) -> dict[str, DocumentSection]:
        return build_index(
            (section for root in self.root for section in root.traverse()),
            key=lambda section: str(section.id),
        )

    def get(self, key: str) -> DocumentSection | None:
        """Return a section by id (tree-wide), or None."""
        return self._index.get(key)

    def require(self, key: str) -> DocumentSection:
        """Return a section by id, or raise KeyError."""
        result = self.get(key)
        if result is None:
            raise KeyError(f"Item with key '{key}' not found")
        return result

    def __iter__(self) -> Iterator[DocumentSection]:  # type: ignore[override]
        yield from self.root

    def __len__(self) -> int:
        return len(self.root)

    def __contains__(self, item: object) -> bool:
        key = str(item.id) if hasattr(item, "id") else str(item)  # type: ignore[attr-defined]
        return key in self._index