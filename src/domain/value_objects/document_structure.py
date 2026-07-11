from typing import Generator

from pydantic import BaseModel, ConfigDict, Field

from domain.value_objects.section_definition import SectionDefinition


class DocumentStructure(BaseModel):
    """The complete document section tree with depth constraint."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    sections: tuple[SectionDefinition, ...] = Field(description="Root-level sections")
    max_depth: int = Field(default=3, ge=1, description="Maximum allowed nesting depth")

    def validate_depth(self) -> None:
        """Raise ValueError if any section exceeds max_depth."""

        def _depth(section: SectionDefinition, current: int = 1) -> int:
            if not section.children:
                return current
            return max(_depth(child, current + 1) for child in section.children)

        for section in self.sections:
            d = _depth(section)
            if d > self.max_depth:
                raise ValueError(f"Section '{section.id}' has depth {d}, exceeds maximum {self.max_depth}")

    def all_ids(self) -> Generator[str]:
        """Recursively yield every section id."""

        def _ids(section: SectionDefinition) -> Generator[str]:
            yield section.id
            for child in section.children:
                yield from _ids(child)

        for section in self.sections:
            yield from _ids(section)
