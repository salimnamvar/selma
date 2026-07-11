from collections import Counter
from typing import Generator

from pydantic import Field, computed_field, model_validator

from domain.enums import PriorityCategory
from domain.identifiers import SectionId, WritingPrincipleId
from domain.value_objects.base import DomainValueObject
from domain.value_objects.contamination_guard import ContaminationGuard
from domain.value_objects.cross_layer_binding import CrossLayerBinding
from domain.value_objects.document_section import DocumentSection
from domain.value_objects.identity_policy import IdentityPolicy
from domain.value_objects.priority_hierarchy import PriorityHierarchy, PriorityLevel
from domain.value_objects.semantic_version import SemanticVersion
from domain.value_objects.versioning_strategy import VersioningStrategy
from domain.value_objects.writing_principle import WritingPrinciple
from domain.value_objects.writing_principles import WritingPrinciples

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


class PolicyDoctrine(DomainValueObject):
    """Aggregate root representing the complete governance doctrine.

    Owns all governance metadata, identity policies, writing principles,
    priority hierarchy, document structure, and versioning strategy.
    """

    name: str = Field(description="Unique doctrine identifier")
    version: SemanticVersion = Field(description="Doctrine version")
    description: str = Field(description="Human-readable purpose statement")
    spec_version: SemanticVersion = Field(description="Compatible specification version")
    rule_contract_version: SemanticVersion = Field(description="Compatible rule schema version")
    rule_contract_id: str = Field(description="Identifier of the compatible rule schema")

    cross_layer_binding: CrossLayerBinding = Field(description="Layer relationship constraints")
    identity_policy: IdentityPolicy = Field(description="Identity governance policy")
    contamination_guard: ContaminationGuard = Field(description="Policy-layer field constraints")
    writing_principles: WritingPrinciples = Field(description="Authoring principles with uniqueness invariant")
    priority_hierarchy: PriorityHierarchy = Field(description="Authority levels and conflict resolution")
    versioning_strategy: VersioningStrategy = Field(description="Versioning intent")
    sections: tuple[DocumentSection, ...] = Field(description="Universal document section definitions")

    @model_validator(mode="after")
    def check_version_compatibility(self) -> "PolicyDoctrine":
        """Enforce MAJOR version compatibility across doctrine, spec, and rule contract."""
        if not self.version.is_compatible_with(self.spec_version):
            raise ValueError(f"MAJOR version mismatch: doctrine={self.version} vs spec={self.spec_version}")
        if not self.version.is_compatible_with(self.rule_contract_version):
            raise ValueError(
                f"MAJOR version mismatch: doctrine={self.version} vs rule_contract={self.rule_contract_version}"
            )
        return self

    @model_validator(mode="after")
    def check_no_duplicate_sections(self) -> "PolicyDoctrine":
        ids = list(self._iter_section_ids())
        duplicates = [sid for sid, count in Counter(ids).items() if count > 1]
        if duplicates:
            raise ValueError(f"Duplicate section IDs found: {duplicates}")
        return self

    def _iter_section_ids(self) -> Generator[SectionId]:
        """Recursively yield every SectionId in the document tree."""
        for section in self.sections:
            yield from section.all_ids()

    @model_validator(mode="after")
    def check_required_sections_present(self) -> "PolicyDoctrine":
        present = {s.id for s in self.sections}
        missing = REQUIRED_SECTION_IDS - present
        if missing:
            raise ValueError(f"Missing required sections: {missing}")
        return self

    @model_validator(mode="after")
    def check_priority_level_completeness(self) -> "PolicyDoctrine":
        """Ensure all PriorityCategory enum values are represented."""
        levels = self.priority_hierarchy.levels
        present_ids = {level.id for level in levels}
        expected_ids = set(PriorityCategory)
        if present_ids != expected_ids:
            missing = expected_ids - present_ids
            extra = present_ids - expected_ids
            parts: list[str] = []
            if missing:
                parts.append(f"Missing: {missing}")
            if extra:
                parts.append(f"Extra: {extra}")
            raise ValueError(f"Priority level mismatch: {'; '.join(parts)}")
        return self

    @model_validator(mode="after")
    def check_section_depth(self) -> "PolicyDoctrine":
        for section in self.sections:
            section.validate_max_depth(MAX_SECTION_DEPTH)
        return self

    @computed_field  # type: ignore[prop-decorator]
    @property
    def sections_by_id(self) -> dict[SectionId, DocumentSection]:
        """O(1) lookup mapping from section id to section."""
        return {s.id: s for s in self.sections}

    @computed_field  # type: ignore[prop-decorator]
    @property
    def writing_principles_by_id(self) -> dict[WritingPrincipleId, WritingPrinciple]:
        """O(1) lookup mapping from principle id to principle."""
        return {p.id: p for p in self.writing_principles}

    def get_section(self, section_id: SectionId) -> DocumentSection | None:
        """Retrieve a document section by its identifier."""
        return self.sections_by_id.get(section_id)

    def get_writing_principle(self, principle_id: WritingPrincipleId) -> WritingPrinciple | None:
        """Retrieve a writing principle by its identifier."""
        return self.writing_principles.get(principle_id)

    def get_priority_level(self, category: PriorityCategory) -> PriorityLevel | None:
        """Retrieve a priority level by its category."""
        return self.priority_hierarchy.get_level(category)
