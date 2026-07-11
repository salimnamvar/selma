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


class PolicyDoctrine(BaseModel):
    """Aggregate root representing the complete governance doctrine."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    name: str = Field(description="Unique doctrine identifier")
    version: SemanticVersion = Field(description="Doctrine version")
    description: str = Field(description="Human-readable purpose statement")
    spec_version: SemanticVersion = Field(description="Compatible specification version")
    rule_contract_version: SemanticVersion = Field(description="Compatible rule schema version")
    rule_contract_id: str = Field(description="Identifier of the compatible rule schema")

    cross_layer_binding: CrossLayerBinding = Field(description="Layer relationship constraints")
    identity_resolution: IdentityResolution = Field(description="Identity mapping policy")
    identity_lifecycle: IdentityLifecycleIntent = Field(description="Lifecycle operation governance")
    contamination_guard: ContaminationGuard = Field(description="Policy-layer field constraints")
    writing_principles: tuple[WritingPrinciple, ...] = Field(description="Authoring principles")
    priority_hierarchy: PriorityHierarchy = Field(description="Authority levels and conflict resolution")
    versioning_strategy: VersioningStrategy = Field(description="Versioning intent")
    sections: tuple[DocumentSection, ...] = Field(description="Universal document section definitions")

    @model_validator(mode="after")
    def check_major_version_synchronization(self) -> "PolicyDoctrine":
        """Enforce MAJOR version compatibility across doctrine, spec, and rule contract."""
        if not (self.version.major == self.spec_version.major == self.rule_contract_version.major):
            raise ValueError("Doctrine, specification, and rule contract MUST share the same MAJOR version")
        return self

    @model_validator(mode="after")
    def check_no_duplicate_sections(self) -> "PolicyDoctrine":
        ids = [s.id for s in self.sections]
        if len(ids) != len(set(ids)):
            duplicates = {sid for sid in ids if ids.count(sid) > 1}
            raise ValueError(f"Duplicate section IDs: {duplicates}")
        return self

    @model_validator(mode="after")
    def check_required_sections_present(self) -> "PolicyDoctrine":
        present = {s.id for s in self.sections}
        missing = REQUIRED_SECTION_IDS - present
        if missing:
            raise ValueError(f"Missing required sections: {missing}")
        return self

    @model_validator(mode="after")
    def check_section_depth(self) -> "PolicyDoctrine":
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
        return next((s for s in self.sections if s.id == section_id), None)

    def get_writing_principle(self, principle_id: WritingPrincipleId) -> Optional[WritingPrinciple]:
        return next((p for p in self.writing_principles if p.id == principle_id), None)

    def get_priority_level(self, category: PriorityCategory) -> Optional[PriorityLevel]:
        return next((lvl for lvl in self.priority_hierarchy.levels if lvl.id == category), None)
