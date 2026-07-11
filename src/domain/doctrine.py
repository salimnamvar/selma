"""Policy Doctrine Aggregate Root.

Complete governance doctrine for the policy authoring layer.
"""

from __future__ import annotations

from typing import Any, Dict, Optional, Tuple

from pydantic import Field, model_validator

from domain.base import DomainValueObject
from domain.enums import PriorityCategory
from domain.identifiers import RuleContractId, SectionId, SemanticVersion, WritingPrincipleId
from domain.value_objects.contamination_guard import ContaminationGuard
from domain.value_objects.cross_layer_binding import CrossLayerBinding
from domain.value_objects.document_section import DocumentSection, DocumentStructure
from domain.value_objects.identity_lifecycle import IdentityLifecycleIntent
from domain.value_objects.identity_resolution import IdentityResolution
from domain.value_objects.priority_hierarchy import PriorityHierarchy, PriorityLevel
from domain.value_objects.versioning_strategy import VersioningStrategy
from domain.value_objects.writing_principle import WritingPrinciple, WritingPrinciples


class PolicyDoctrine(DomainValueObject):
    """Aggregate root representing the complete governance doctrine.

    Attributes:
        name (str): Unique doctrine identifier.
        version (SemanticVersion): Doctrine version.
        description (str): Human-readable purpose statement.
        spec_version (SemanticVersion): Compatible specification version.
        rule_contract_version (SemanticVersion): Compatible rule schema version.
        rule_contract_id (RuleContractId): Compatible rule schema identifier.
        cross_layer_binding (CrossLayerBinding): Layer relationship constraints.
        identity_resolution (IdentityResolution): Identity mapping policy.
        identity_lifecycle (IdentityLifecycleIntent): Lifecycle operation governance.
        contamination_guard (ContaminationGuard): Policy-layer field constraints.
        writing_principles (WritingPrinciples): Authoring principles.
        priority_hierarchy (PriorityHierarchy): Authority levels and conflict resolution.
        versioning_strategy (VersioningStrategy): Versioning intent.
        document_structure (DocumentStructure): Universal document section definitions.
    """

    name: str = Field(min_length=1, description="Unique doctrine identifier")
    version: SemanticVersion = Field(description="Doctrine version")
    description: str = Field(min_length=1, description="Human-readable purpose statement")
    spec_version: SemanticVersion = Field(description="Compatible specification version")
    rule_contract_version: SemanticVersion = Field(description="Compatible rule schema version")
    rule_contract_id: RuleContractId = Field(description="Identifier of the compatible rule schema")

    cross_layer_binding: CrossLayerBinding = Field(description="Layer relationship constraints")
    identity_resolution: IdentityResolution = Field(description="Identity mapping policy")
    identity_lifecycle: IdentityLifecycleIntent = Field(
        alias="identity_lifecycle_intent",
        description="Lifecycle operation governance",
    )
    contamination_guard: ContaminationGuard = Field(description="Policy-layer field constraints")
    writing_principles: WritingPrinciples = Field(description="Authoring principles")
    priority_hierarchy: PriorityHierarchy = Field(description="Authority levels and conflict resolution")
    versioning_strategy: VersioningStrategy = Field(description="Versioning intent")
    document_structure: DocumentStructure = Field(
        alias="sections",
        description="Universal document section definitions",
    )

    @model_validator(mode="after")
    def check_version_compatibility(self) -> PolicyDoctrine:
        """Enforce MAJOR version compatibility across doctrine artifacts.

        Returns:
            PolicyDoctrine: Validated instance.

        Raises:
            ValueError: If MAJOR versions diverge.
        """
        result: PolicyDoctrine = self
        if not self.version.is_compatible_with(self.spec_version):
            msg: str = f"MAJOR version mismatch: doctrine={self.version} vs spec={self.spec_version}"
            raise ValueError(msg)
        if not self.version.is_compatible_with(self.rule_contract_version):
            msg = f"MAJOR version mismatch: doctrine={self.version} vs rule_contract={self.rule_contract_version}"
            raise ValueError(msg)
        return result

    @property
    def sections(self) -> Tuple[DocumentSection, ...]:
        """Return top-level document sections.

        Returns:
            Tuple[DocumentSection, ...]: Top-level sections.
        """
        result: Tuple[DocumentSection, ...] = self.document_structure.sections
        return result

    def get_section(self, a_section_id: SectionId) -> Optional[DocumentSection]:
        """Retrieve a document section by ID.

        Args:
            a_section_id (SectionId): Section identifier to search for.

        Returns:
            Optional[DocumentSection]: Matching section, or None.
        """
        result: Optional[DocumentSection] = self.document_structure.get(a_section_id)
        return result

    def get_writing_principle(
        self,
        a_principle_id: WritingPrincipleId,
    ) -> Optional[WritingPrinciple]:
        """Retrieve a writing principle by identifier.

        Args:
            a_principle_id (WritingPrincipleId): Principle identifier.

        Returns:
            Optional[WritingPrinciple]: Matching principle, or None.
        """
        result: Optional[WritingPrinciple] = self.writing_principles.get(a_principle_id)
        return result

    def get_priority_level(self, a_category: PriorityCategory) -> Optional[PriorityLevel]:
        """Retrieve a priority level by category.

        Args:
            a_category (PriorityCategory): Authority category.

        Returns:
            Optional[PriorityLevel]: Matching level, or None.
        """
        result: Optional[PriorityLevel] = self.priority_hierarchy.get_level(a_category)
        return result

    @classmethod
    def from_document(cls, a_document: Dict[str, Any]) -> PolicyDoctrine:
        """Build a doctrine aggregate from a policy_doctrine document mapping.

        Args:
            a_document (Dict[str, Any]): Full top-level policy_doctrine YAML mapping.

        Returns:
            PolicyDoctrine: Validated aggregate root.

        Raises:
            ValueError: If the doctrine metadata block is missing.
        """
        if "doctrine" not in a_document:
            msg: str = "Document must contain a top-level 'doctrine' metadata block"
            raise ValueError(msg)

        meta: Dict[str, Any] = a_document["doctrine"]
        payload: Dict[str, Any] = {
            **meta,
            "cross_layer_binding": a_document["cross_layer_binding"],
            "identity_resolution": a_document["identity_resolution"],
            "identity_lifecycle_intent": a_document["identity_lifecycle_intent"],
            "contamination_guard": a_document["contamination_guard"],
            "writing_principles": a_document["writing_principles"],
            "priority_hierarchy": a_document["priority_hierarchy"],
            "versioning_strategy": a_document["versioning_strategy"],
            "sections": a_document["sections"],
        }
        result: PolicyDoctrine = cls.model_validate(payload)
        return result
