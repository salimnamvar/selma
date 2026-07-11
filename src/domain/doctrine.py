"""Policy Doctrine Aggregate Root."""

from __future__ import annotations

from typing import Any

from pydantic import Field, model_validator

from domain.base import DomainValueObject
from domain.identifiers import RuleContractId, SemanticVersion
from domain.value_objects.contamination_guard import ContaminationGuard
from domain.value_objects.cross_layer_binding import CrossLayerBinding
from domain.value_objects.document_section import DocumentStructure
from domain.value_objects.identity_resolution import IdentityResolution
from domain.value_objects.lifecycle_definition import LifecycleDefinition
from domain.value_objects.priority_hierarchy import PriorityHierarchy
from domain.value_objects.version_strategy import VersionStrategy
from domain.value_objects.writing_principle import WritingPrinciples


class PolicyDoctrine(DomainValueObject):
    """Aggregate root representing the complete governance doctrine."""

    name: str = Field(min_length=1, description="Unique doctrine identifier")
    version: SemanticVersion = Field(description="Doctrine version")
    description: str = Field(min_length=1, description="Human-readable purpose statement")
    spec_version: SemanticVersion = Field(description="Compatible specification version")
    schema_version: SemanticVersion = Field(description="Compatible rule schema version")
    schema_id: RuleContractId = Field(description="Identifier of the compatible rule schema")

    cross_layer_binding: CrossLayerBinding = Field(description="Layer relationship constraints")
    identity_resolution: IdentityResolution = Field(description="Identity mapping policy")
    lifecycle_definition: LifecycleDefinition = Field(
        description="Lifecycle operation governance",
    )
    contamination_guard: ContaminationGuard = Field(description="Policy-layer field constraints")
    writing_principles: WritingPrinciples = Field(description="Authoring principles")
    priority_hierarchy: PriorityHierarchy = Field(description="Authority levels and conflict resolution")
    version_strategy: VersionStrategy = Field(description="Versioning intent")
    sections: DocumentStructure = Field(description="Universal document section definitions")

    @model_validator(mode="after")
    def _validate_versions(self) -> PolicyDoctrine:
        """Enforce MAJOR version compatibility across doctrine artifacts."""
        if not self.version.is_compatible(self.spec_version):
            raise ValueError(f"MAJOR version mismatch: doctrine={self.version} vs spec={self.spec_version}")
        if not self.version.is_compatible(self.schema_version):
            raise ValueError(
                f"MAJOR version mismatch: doctrine={self.version} vs schema={self.schema_version}"
            )
        return self

    @classmethod
    def from_dict(cls, a_data: dict[str, Any]) -> PolicyDoctrine:
        """Build a doctrine aggregate from a dict mapping.

        The normative YAML nests metadata under a top-level ``doctrine`` key.
        This factory flattens that shape into the flat field layout expected by
        the model; type coercion and field validation are handled by Pydantic.
        """
        if "doctrine" not in a_data:
            raise ValueError("Document must contain a top-level 'doctrine' metadata block")

        meta = a_data["doctrine"]
        payload: dict[str, Any] = {
            **meta,
            "cross_layer_binding": a_data["cross_layer_binding"],
            "identity_resolution": a_data["identity_resolution"],
            "lifecycle_definition": a_data["lifecycle_definition"],
            "contamination_guard": a_data["contamination_guard"],
            "writing_principles": a_data["writing_principles"],
            "priority_hierarchy": a_data["priority_hierarchy"],
            "version_strategy": a_data["version_strategy"],
            "sections": a_data["sections"],
        }
        return cls.model_validate(payload)
