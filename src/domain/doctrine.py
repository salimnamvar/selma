from pydantic import BaseModel, ConfigDict, Field, model_validator

from domain.enums import PriorityCategory
from domain.identifiers import RuleContractId, SectionId, SemanticVersion, WritingPrincipleId
from domain.value_objects.contamination_guard import ContaminationGuard
from domain.value_objects.cross_layer_binding import CrossLayerBinding
from domain.value_objects.document_section import DocumentSection
from domain.value_objects.identity_lifecycle import IdentityLifecycleIntent
from domain.value_objects.identity_resolution import IdentityResolution
from domain.value_objects.priority_hierarchy import PriorityHierarchy, PriorityLevel
from domain.value_objects.versioning_strategy import VersioningStrategy
from domain.value_objects.writing_principle import WritingPrinciple

MAX_SECTION_DEPTH = 3

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

    model_config = ConfigDict(frozen=True, extra="forbid")

    name: str = Field(description="Unique doctrine identifier")
    version: SemanticVersion = Field(description="Doctrine version")
    description: str = Field(description="Human-readable purpose statement")
    spec_version: SemanticVersion = Field(description="Compatible specification version")
    rule_contract_version: SemanticVersion = Field(description="Compatible rule schema version")
    rule_contract_id: RuleContractId = Field(description="Identifier of the compatible rule schema")

    cross_layer_binding: CrossLayerBinding = Field(description="Layer relationship constraints")
    identity_resolution: IdentityResolution = Field(description="Identity mapping policy")
    identity_lifecycle: IdentityLifecycleIntent = Field(description="Lifecycle operation governance")
    contamination_guard: ContaminationGuard = Field(description="Policy-layer field constraints")
    writing_principles: tuple[WritingPrinciple, ...] = Field(description="Authoring principles")
    priority_hierarchy: PriorityHierarchy = Field(description="Authority levels and conflict resolution")
    versioning_strategy: VersioningStrategy = Field(description="Versioning intent")
    sections: tuple[DocumentSection, ...] = Field(description="Universal document section definitions")

    @model_validator(mode="after")
    def check_no_duplicate_sections(self) -> "PolicyDoctrine":
        seen: set[str] = set()
        for section in self.sections:
            if section.id in seen:
                raise ValueError(f"Duplicate section ID: {section.id}")
            seen.add(section.id)
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
        for section in self.sections:
            depth = section.max_depth()
            if depth > MAX_SECTION_DEPTH:
                raise ValueError(f"Section '{section.id}' has depth {depth}, exceeds maximum {MAX_SECTION_DEPTH}")
        return self

    def get_section(self, section_id: SectionId) -> DocumentSection | None:
        """Retrieve a document section by its identifier."""
        for section in self.sections:
            if section.id == section_id:
                return section
        return None

    def get_writing_principle(self, principle_id: WritingPrincipleId) -> WritingPrinciple | None:
        """Retrieve a writing principle by its identifier."""
        for principle in self.writing_principles:
            if principle.id == principle_id:
                return principle
        return None

    def get_priority_level(self, category: PriorityCategory) -> PriorityLevel | None:
        """Retrieve a priority level by its category."""
        for level in self.priority_hierarchy.levels:
            if level.id == category:
                return level
        return None
