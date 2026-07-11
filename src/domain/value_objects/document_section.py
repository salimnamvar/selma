"""Document template — universal document section structure (no mixins)."""

from __future__ import annotations

from collections.abc import Callable, Iterator
from functools import cached_property
from typing import Annotated, ClassVar, Self

from pydantic import BeforeValidator, Field, RootModel, model_validator

from domain.base import DomainValueObject, none_as_empty, require_unique
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
    def name(self) -> str:
        """Human-readable name (title)."""
        return self.title

    @property
    def is_tabular(self) -> bool:
        """Return True when this section may carry table columns."""
        return self.content_type in self._TABULAR_CONTENT_TYPES or bool(self.columns)

    def traverse(self) -> Iterator[DocumentSection]:
        """Yield this node and all descendants in pre-order."""
        yield self
        for child in self.children:
            yield from child.traverse()

    def iter_nodes(self) -> Iterator[DocumentSection]:
        """Alias for :meth:`traverse`."""
        yield from self.traverse()

    def get(self, key: str) -> DocumentSection | None:
        """Return the first node whose id equals ``key``, or None."""
        result: DocumentSection | None = None
        for node in self.traverse():
            if str(node.id) == key:
                result = node
                break
        return result

    def require(self, key: str) -> DocumentSection:
        """Return the node for ``key``, or raise KeyError."""
        result = self.get(key)
        if result is None:
            raise KeyError(f"Item with key '{key}' not found")
        return result

    def has(self, key: str) -> bool:
        """Return True if a node with id ``key`` exists."""
        return self.get(key) is not None

    def get_where(self, predicate: Callable[[DocumentSection], bool]) -> DocumentSection | None:
        """Return the first node matching ``predicate``, or None."""
        result: DocumentSection | None = None
        for node in self.traverse():
            if predicate(node):
                result = node
                break
        return result

    def collect_where(self, predicate: Callable[[DocumentSection], bool]) -> list[DocumentSection]:
        """Return all nodes matching ``predicate`` (pre-order)."""
        return [node for node in self.traverse() if predicate(node)]

    def collect_required(self) -> list[DocumentSection]:
        """Return all required sections in this subtree."""
        return self.collect_where(lambda node: node.required)

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

    model_config = {"frozen": True}

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
        return {
            str(section.id): section
            for root in self.root
            for section in root.traverse()
        }

    def get(self, key: str) -> DocumentSection | None:
        """Return a section by id (tree-wide), or None."""
        return self._index.get(key)

    def require(self, key: str) -> DocumentSection:
        """Return a section by id, or raise KeyError."""
        result = self.get(key)
        if result is None:
            raise KeyError(f"Item with key '{key}' not found")
        return result

    def has(self, key: str) -> bool:
        """Return True if section id exists in the tree."""
        return key in self._index

    @property
    def ids(self) -> tuple[str, ...]:
        """Return all section ids in index order."""
        return tuple(self._index)

    @property
    def sections(self) -> tuple[DocumentSection, ...]:
        """Return top-level document sections."""
        return self.root

    @property
    def items(self) -> tuple[DocumentSection, ...]:
        """Return top-level document sections."""
        return self.root

    def __iter__(self) -> Iterator[DocumentSection]:  # type: ignore[override]
        yield from self.root

    def __len__(self) -> int:
        return len(self.root)

    def __contains__(self, item: object) -> bool:
        key = str(item.id) if hasattr(item, "id") else str(item)  # type: ignore[attr-defined]
        return self.has(key)
