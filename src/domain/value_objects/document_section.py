"""Document template — universal document section structure."""

from __future__ import annotations

from collections.abc import Iterator
from typing import Annotated, ClassVar, Self

from pydantic import BaseModel, BeforeValidator, Field, RootModel, computed_field, model_validator

from domain.base import ROOT_CONFIG, VO_CONFIG, none_as_empty, require_unique
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


class DocumentSection(BaseModel):
    """A structural section defining governance document composition."""

    model_config = VO_CONFIG

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


class DocumentTemplate(RootModel[tuple[DocumentSection, ...]]):
    """Validated tree of universal document sections (YAML list root)."""

    model_config = ROOT_CONFIG

    @model_validator(mode="after")
    def _validate_structure(self) -> Self:
        present = {str(section.id) for section in self.root}
        missing = REQUIRED_SECTION_IDS - present
        if missing:
            raise ValueError(f"Missing required sections: {sorted(missing)}")

        nested_ids = [str(section_id) for section in self.root for section_id in section.iter_ids()]
        require_unique(nested_ids, label="section ID")

        directives = self.get("directives")
        if directives is not None and directives.children:
            child_ids = {str(child.id) for child in directives.children}
            missing_children = DIRECTIVES_CHILD_IDS - child_ids
            if missing_children:
                raise ValueError(
                    f"Directives section missing expected children: {sorted(missing_children)}"
                )
        return self

    @computed_field  # type: ignore[prop-decorator]
    @property
    def index(self) -> dict[str, DocumentSection]:
        """Lookup index keyed by section id (tree-wide)."""
        return {
            str(section.id): section
            for root in self.root
            for section in root.traverse()
        }

    def get(self, key: str) -> DocumentSection | None:
        """Return a section by id (tree-wide), or None."""
        return self.index.get(key)

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
        return key in self.index