from typing import Iterator

from pydantic import Field

from domain.value_objects.base import DomainValueObject


class DocumentSection(DomainValueObject):
    """A structural section defining the composition of a governance document."""

    id: str = Field(description="Unique section identifier")
    title: str = Field(description="Human-readable section title")
    required: bool = Field(description="Whether this section must be present")
    content_type: str = Field(description="Expected content format")
    guidance: str = Field(description="Authoring guidance for this section")
    columns: tuple[str, ...] | None = Field(default=None, description="Table column headers")
    children: tuple["DocumentSection", ...] = Field(default_factory=tuple, description="Subsections")
    schema_encoding: str | None = Field(default=None, description="Schema encoding instructions")

    def all_ids(self) -> Iterator[str]:
        """Yield this section's id and all descendant ids."""
        yield self.id
        for child in self.children:
            yield from child.all_ids()

    def depth(self) -> int:
        """Return the maximum depth of this section tree."""
        if not self.children:
            return 1
        return 1 + max(child.depth() for child in self.children)

    def validate_max_depth(self, max_depth: int) -> None:
        """Raise ValueError if this section tree exceeds max_depth."""
        d = self.depth()
        if d > max_depth:
            raise ValueError(f"Section '{self.id}' has depth {d}, exceeds maximum {max_depth}")
