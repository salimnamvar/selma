from pydantic import BaseModel, ConfigDict, Field, computed_field, model_validator

from domain.enums import PriorityCategory
from domain.identifiers import SectionId, WritingPrincipleId
from domain.value_objects.doctrine_metadata import DoctrineMetadata
from domain.value_objects.document_structure import DocumentStructure
from domain.value_objects.governance_constraints import GovernanceConstraints
from domain.value_objects.identity_policy import IdentityPolicy
from domain.value_objects.priority_system import PriorityLevel, PrioritySystem
from domain.value_objects.section_definition import SectionDefinition
from domain.value_objects.versioning_policy import VersioningPolicy
from domain.value_objects.writing_principle import WritingPrinciple
from domain.value_objects.writing_principle_set import WritingPrincipleSet

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

    metadata: DoctrineMetadata = Field(description="Doctrine identity and versioning")
    identity_policy: IdentityPolicy = Field(description="Identity governance policy")
    governance_constraints: GovernanceConstraints = Field(description="Governance constraints")
    writing_principles: WritingPrincipleSet = Field(description="Authoring principles")
    document_structure: DocumentStructure = Field(description="Document section definitions")
    priority_system: PrioritySystem = Field(description="Priority levels and conflict resolution")
    versioning: VersioningPolicy = Field(description="Versioning intent")

    @model_validator(mode="after")
    def check_major_version_synchronization(self) -> "PolicyDoctrine":
        """Enforce MAJOR version compatibility across doctrine, spec, and rule contract."""
        doctrine_major = self.metadata.version.major
        spec_major = self.metadata.spec_version.major
        contract_major = self.metadata.contract.version.major
        if not (doctrine_major == spec_major == contract_major):
            raise ValueError("Doctrine, specification, and rule contract MUST share the same MAJOR version")
        return self

    @model_validator(mode="after")
    def validate_document_structure(self) -> "PolicyDoctrine":
        """Delegate structural validation to DocumentStructure."""
        self.document_structure.validate_no_duplicate_ids()
        self.document_structure.validate_required_sections(REQUIRED_SECTION_IDS)
        self.document_structure.validate_depth()
        return self

    @model_validator(mode="after")
    def check_priority_level_completeness(self) -> "PolicyDoctrine":
        """Ensure all PriorityCategory enum values are represented."""
        present = {level.category for level in self.priority_system.levels}
        expected = set(PriorityCategory)
        if present != expected:
            missing = expected - present
            extra = present - expected
            parts: list[str] = []
            if missing:
                parts.append(f"Missing: {missing}")
            if extra:
                parts.append(f"Extra: {extra}")
            raise ValueError(f"Priority level mismatch: {'; '.join(parts)}")
        return self

    @computed_field  # type: ignore[prop-decorator]
    @property
    def sections(self) -> tuple[SectionDefinition, ...]:
        """Direct access to document sections."""
        return self.document_structure.sections

    @computed_field  # type: ignore[prop-decorator]
    @property
    def sections_by_id(self) -> dict[SectionId, SectionDefinition]:
        """O(1) lookup mapping from section id to section."""
        return {s.id: s for s in self.document_structure.sections}

    @computed_field  # type: ignore[prop-decorator]
    @property
    def writing_principles_by_id(self) -> dict[WritingPrincipleId, WritingPrinciple]:
        """O(1) lookup mapping from principle id to principle."""
        return {p.id: p for p in self.writing_principles}

    def get_section(self, section_id: SectionId) -> SectionDefinition | None:
        """Retrieve a document section by its identifier."""
        return self.sections_by_id.get(section_id)

    def get_writing_principle(self, principle_id: WritingPrincipleId) -> WritingPrinciple | None:
        """Retrieve a writing principle by its identifier."""
        return self.writing_principles_by_id.get(principle_id)

    def get_priority_level(self, category: PriorityCategory) -> PriorityLevel | None:
        """Retrieve a priority level by its category."""
        return self.priority_system.get_level(category)
