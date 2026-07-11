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


class PolicyDoctrine(BaseModel):
    """Aggregate root representing the complete governance doctrine.

    Owns all governance metadata, identity policies, writing principles,
    priority hierarchy, document structure, and versioning strategy.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    _MAX_SECTION_DEPTH: int = 3
    _REQUIRED_SECTION_IDS: frozenset[str] = frozenset(
        {
            "preamble",
            "governance",
            "definitions",
            "principles",
            "directives",
            "sanctions",
        }
    )

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
    def check_version_compatibility(self) -> "PolicyDoctrine":
        """Enforce MAJOR version compatibility across doctrine, spec, and rule contract."""
        doctrine_major: int = int(self.version.split(".")[0])
        spec_major: int = int(self.spec_version.split(".")[0])
        contract_major: int = int(self.rule_contract_version.split(".")[0])
        if doctrine_major != spec_major:
            raise ValueError(f"MAJOR version mismatch: doctrine={self.version} vs spec={self.spec_version}")
        if doctrine_major != contract_major:
            raise ValueError(
                f"MAJOR version mismatch: doctrine={self.version} vs rule_contract={self.rule_contract_version}"
            )
        return self

    @model_validator(mode="after")
    def check_no_duplicate_sections(self) -> "PolicyDoctrine":
        """Validate no duplicate section IDs exist (recursive)."""
        seen: set[str] = set()
        for section in self.sections:
            for section_id in section.all_ids():
                if section_id in seen:
                    raise ValueError(f"Duplicate section ID: {section_id}")
                seen.add(section_id)
        return self

    @model_validator(mode="after")
    def check_required_sections_present(self) -> "PolicyDoctrine":
        """Validate all required sections are present."""
        present: set[str] = {s.id for s in self.sections}
        missing: frozenset[str] = self._REQUIRED_SECTION_IDS - present
        if missing:
            raise ValueError(f"Missing required sections: {missing}")
        return self

    @model_validator(mode="after")
    def check_section_depth(self) -> "PolicyDoctrine":
        """Validate section tree depth does not exceed maximum."""
        for section in self.sections:
            depth: int = section.max_depth()
            if depth > self._MAX_SECTION_DEPTH:
                raise ValueError(f"Section '{section.id}' has depth {depth}, exceeds maximum {self._MAX_SECTION_DEPTH}")
        return self

    def get_section(self, a_section_id: SectionId) -> DocumentSection | None:
        """Retrieve a document section by its identifier, searching recursively.

        Args:
            a_section_id (SectionId): The section identifier to search for.

        Returns:
            DocumentSection | None: The section if found, None otherwise.
        """
        result: DocumentSection | None = None
        for section in self.sections:
            result = self._find_in_tree(section, a_section_id)
            if result is not None:
                break
        return result

    @staticmethod
    def _find_in_tree(a_section: DocumentSection, a_section_id: SectionId) -> DocumentSection | None:
        """Recursively search for a section by ID in the tree."""
        result: DocumentSection | None = None
        if a_section.id == a_section_id:
            result = a_section
        elif a_section.children:
            for child in a_section.children:
                result = PolicyDoctrine._find_in_tree(child, a_section_id)
                if result is not None:
                    break
        return result

    def get_writing_principle(self, a_principle_id: WritingPrincipleId) -> WritingPrinciple | None:
        """Retrieve a writing principle by its identifier.

        Args:
            a_principle_id (WritingPrincipleId): The principle identifier to search for.

        Returns:
            WritingPrinciple | None: The principle if found, None otherwise.
        """
        result: WritingPrinciple | None = None
        for principle in self.writing_principles:
            if principle.id == a_principle_id:
                result = principle
                break
        return result

    def get_priority_level(self, a_category: PriorityCategory) -> PriorityLevel | None:
        """Retrieve a priority level by its category.

        Args:
            a_category (PriorityCategory): The category to search for.

        Returns:
            PriorityLevel | None: The level if found, None otherwise.
        """
        result: PriorityLevel | None = None
        for level in self.priority_hierarchy.levels:
            if level.id == a_category:
                result = level
                break
        return result
