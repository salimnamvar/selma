from typing import List, Optional

from pydantic import BaseModel, Field, model_validator

from domain.entities.document_section import DocumentSection
from domain.entities.priority_level import PriorityLevel
from domain.entities.writing_principle import WritingPrinciple
from domain.enums import PriorityCategory
from domain.value_objects.contamination_guard import ContaminationGuard
from domain.value_objects.cross_layer_binding import CrossLayerBinding
from domain.value_objects.doctrine_metadata import DoctrineMetadata
from domain.value_objects.identity_lifecycle import IdentityLifecycleIntent
from domain.value_objects.identity_resolution import IdentityResolution
from domain.value_objects.priority_hierarchy import PriorityHierarchy
from domain.value_objects.versioning_strategy import VersioningStrategy

REQUIRED_SECTION_IDS = frozenset(
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

    metadata: DoctrineMetadata = Field(description="Doctrine identifying information")
    cross_layer_binding: CrossLayerBinding = Field(description="Layer relationship constraints")
    identity_resolution: IdentityResolution = Field(description="Identity mapping policy")
    identity_lifecycle: IdentityLifecycleIntent = Field(description="Lifecycle operation governance")
    contamination_guard: ContaminationGuard = Field(description="Policy-layer field constraints")
    writing_principles: List[WritingPrinciple] = Field(description="Authoring principles for rule documents")
    priority_hierarchy: PriorityHierarchy = Field(description="Authority levels and conflict resolution")
    versioning_strategy: VersioningStrategy = Field(description="Versioning intent across documents")
    sections: List[DocumentSection] = Field(description="Universal document section definitions")

    @model_validator(mode="after")
    def check_no_duplicate_sections(self) -> "PolicyDoctrine":
        ids = [s.id for s in self.sections]
        if len(ids) != len(set(ids)):
            duplicates = {id for id in ids if ids.count(id) > 1}
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
    def check_priority_level_ordering(self) -> "PolicyDoctrine":
        levels = sorted(self.priority_hierarchy.levels, key=lambda pl: pl.level)
        for i, level in enumerate(levels, start=1):
            if level.level != i:
                raise ValueError(f"Priority level {level.id} has level={level.level}, expected {i}")
        return self

    def get_section(self, section_id: str) -> Optional[DocumentSection]:
        """Retrieve a document section by its identifier."""
        for section in self.sections:
            if section.id == section_id:
                return section
        return None

    def get_writing_principle(self, principle_id: str) -> Optional[WritingPrinciple]:
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
