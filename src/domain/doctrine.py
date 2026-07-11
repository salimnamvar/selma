from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator

from domain.enums import PriorityCategory
from domain.identifiers import SectionId, SemanticVersion, WritingPrincipleId
from domain.value_objects.contamination_guard import ContaminationGuard
from domain.value_objects.cross_layer_binding import CrossLayerBinding
from domain.value_objects.document_section import DocumentSection
from domain.value_objects.identity_lifecycle import IdentityLifecycleIntent
from domain.value_objects.identity_resolution import IdentityResolution
from domain.value_objects.priority_hierarchy import PriorityHierarchy, PriorityLevel
from domain.value_objects.versioning_strategy import VersioningStrategy
from domain.value_objects.writing_principle import WritingPrinciple

MAX_SECTION_DEPTH = 3

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


class PolicyDoctrine(BaseModel):
    """Aggregate root representing the complete governance doctrine.

    Owns all governance metadata, identity policies, writing principles,
    priority hierarchy, document structure, and versioning strategy.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    name: str = Field(description="Unique doctrine identifier")
    version: SemanticVersion
    description: str = Field(description="Human-readable purpose statement")
    spec_version: SemanticVersion
    rule_contract_version: SemanticVersion
    rule_contract_id: str = Field(description="Identifier of the compatible rule schema")

    cross_layer_binding: CrossLayerBinding
    identity_resolution: IdentityResolution
    identity_lifecycle: IdentityLifecycleIntent
    contamination_guard: ContaminationGuard
    writing_principles: tuple[WritingPrinciple, ...]
    priority_hierarchy: PriorityHierarchy
    versioning_strategy: VersioningStrategy
    sections: tuple[DocumentSection, ...]

    @model_validator(mode="after")
    def _check_no_duplicate_sections(self) -> PolicyDoctrine:
        ids = [s.id for s in self.sections]
        if len(ids) != len(set(ids)):
            duplicates = {sid for sid in ids if ids.count(sid) > 1}
            raise ValueError(f"Duplicate section IDs: {duplicates}")
        return self

    @model_validator(mode="after")
    def _check_required_sections_present(self) -> PolicyDoctrine:
        present = {s.id for s in self.sections}
        missing = REQUIRED_SECTION_IDS - present
        if missing:
            raise ValueError(f"Missing required sections: {missing}")
        return self

    @model_validator(mode="after")
    def _check_priority_levels_unique(self) -> PolicyDoctrine:
        seen: set[int] = set()
        for pl in self.priority_hierarchy.levels:
            if pl.level in seen:
                raise ValueError(f"Duplicate priority level number: {pl.level}")
            seen.add(pl.level)
        return self

    @model_validator(mode="after")
    def _check_section_depth(self) -> PolicyDoctrine:
        def _max_depth(section: DocumentSection, current: int = 1) -> int:
            if not section.children:
                return current
            return max(_max_depth(child, current + 1) for child in section.children)

        for section in self.sections:
            depth = _max_depth(section)
            if depth > MAX_SECTION_DEPTH:
                raise ValueError(f"Section '{section.id}' has depth {depth}, exceeds maximum {MAX_SECTION_DEPTH}")
        return self

    def get_section(self, section_id: SectionId) -> Optional[DocumentSection]:
        """Retrieve a document section by its identifier, searching recursively."""

        def _search(sections: tuple[DocumentSection, ...]) -> Optional[DocumentSection]:
            for section in sections:
                if section.id == section_id:
                    return section
                if section.children:
                    found = _search(section.children)
                    if found is not None:
                        return found
            return None

        return _search(self.sections)

    def get_writing_principle(self, principle_id: WritingPrincipleId) -> Optional[WritingPrinciple]:
        """Retrieve a writing principle by its identifier."""
        for principle in self.writing_principles:
            if principle.id == principle_id:
                return principle
        return None

    def get_priority_level(self, category: PriorityCategory) -> Optional[PriorityLevel]:
        """Retrieve a priority level by its category."""
        for level in self.priority_hierarchy.levels:
            if level.id == category:
                return level
        return None
