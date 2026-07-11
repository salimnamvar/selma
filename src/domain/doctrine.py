from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator

from domain.enums import PriorityCategory
from domain.identifiers import WritingPrincipleId
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
    def check_no_duplicate_sections(self) -> "PolicyDoctrine":
        ids = list(self.document_structure.all_ids())
        from collections import Counter

        duplicates = [sid for sid, count in Counter(ids).items() if count > 1]
        if duplicates:
            raise ValueError(f"Duplicate section IDs: {duplicates}")
        return self

    @model_validator(mode="after")
    def check_required_sections_present(self) -> "PolicyDoctrine":
        present = {s.id for s in self.document_structure.sections}
        missing = REQUIRED_SECTION_IDS - present
        if missing:
            raise ValueError(f"Missing required sections: {missing}")
        return self

    @model_validator(mode="after")
    def check_section_depth(self) -> "PolicyDoctrine":
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

    def get_section(self, section_id: str) -> Optional[SectionDefinition]:
        return next((s for s in self.document_structure.sections if s.id == section_id), None)

    def get_writing_principle(self, principle_id: WritingPrincipleId) -> Optional[WritingPrinciple]:
        return self.writing_principles.get(principle_id)

    def get_priority_level(self, category: PriorityCategory) -> Optional[PriorityLevel]:
        return self.priority_system.get_level(category)
