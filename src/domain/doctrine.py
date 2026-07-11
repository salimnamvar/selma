"""Policy Doctrine Aggregate Root."""

from __future__ import annotations

from typing import Any

from pydantic import Field, model_validator

from domain.base import DomainValueObject
from domain.identifiers import RuleContractId, SemanticVersion
from domain.value_objects.contamination_guard import ContaminationGuard
from domain.value_objects.cross_layer_binding import CrossLayerBinding
from domain.value_objects.document_section import DocumentStructure
from domain.value_objects.identity_lifecycle import IdentityLifecycleIntent
from domain.value_objects.identity_resolution import IdentityResolution
from domain.value_objects.priority_hierarchy import PriorityHierarchy
from domain.value_objects.versioning_strategy import VersioningStrategy
from domain.value_objects.writing_principle import WritingPrinciples


class PolicyDoctrine(DomainValueObject):
    """Aggregate root representing the complete governance doctrine."""

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
    sections: DocumentStructure = Field(description="Universal document section definitions")

    @model_validator(mode="after")
    def check_version_compatibility(self) -> PolicyDoctrine:
        """Enforce MAJOR version compatibility across doctrine artifacts."""
        if not self.version.is_compatible_with(self.spec_version):
            raise ValueError(f"MAJOR version mismatch: doctrine={self.version} vs spec={self.spec_version}")
        if not self.version.is_compatible_with(self.rule_contract_version):
            raise ValueError(
                f"MAJOR version mismatch: doctrine={self.version} vs rule_contract={self.rule_contract_version}"
            )
        return self

    @classmethod
    def from_document(cls, a_document: dict[str, Any]) -> PolicyDoctrine:
        """Build a doctrine aggregate from a policy_doctrine document mapping.

        The normative YAML nests metadata under a top-level ``doctrine`` key.
        This factory flattens that shape into the flat field layout expected by
        the model; type coercion and field validation are handled by Pydantic.
        """
        if "doctrine" not in a_document:
            raise ValueError("Document must contain a top-level 'doctrine' metadata block")

        meta = a_document["doctrine"]
        payload: dict[str, Any] = {
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
        return cls.model_validate(payload)
