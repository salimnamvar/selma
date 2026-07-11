"""Policy Doctrine aggregate root."""

from __future__ import annotations

from typing import Any, ClassVar, Self

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
    """Aggregate root representing the complete governance doctrine.

    Field names match policy_doctrine.yaml section keys for a 1:1 mapping.
    """

    # YAML top-level keys that compose the aggregate (excluding nested ``doctrine`` meta).
    _SECTION_KEYS: ClassVar[tuple[str, ...]] = (
        "cross_layer_binding",
        "identity_resolution",
        "lifecycle_definition",
        "contamination_guard",
        "writing_principles",
        "priority_hierarchy",
        "version_strategy",
        "sections",
    )

    name: str = Field(min_length=1, description="Unique doctrine identifier")
    version: SemanticVersion = Field(description="Doctrine version")
    description: str = Field(min_length=1, description="Human-readable purpose statement")
    spec_version: SemanticVersion = Field(description="Compatible specification version")
    schema_version: SemanticVersion = Field(description="Compatible rule schema version")
    schema_id: RuleContractId = Field(description="Identifier of the compatible rule schema")

    cross_layer_binding: CrossLayerBinding = Field(description="Layer relationship constraints")
    identity_resolution: IdentityResolution = Field(description="Identity mapping policy")
    lifecycle_definition: LifecycleDefinition = Field(description="Lifecycle operation governance")
    contamination_guard: ContaminationGuard = Field(description="Policy-layer field constraints")
    writing_principles: WritingPrinciples = Field(description="Authoring principles")
    priority_hierarchy: PriorityHierarchy = Field(
        description="Authority levels and conflict resolution"
    )
    version_strategy: VersionStrategy = Field(description="Versioning intent")
    sections: DocumentStructure = Field(description="Universal document section definitions")

    @model_validator(mode="after")
    def _validate_versions(self) -> Self:
        """Enforce MAJOR version compatibility across doctrine artifacts."""
        if not self.version.is_compatible(self.spec_version):
            raise ValueError(
                f"MAJOR version mismatch: doctrine={self.version} vs spec={self.spec_version}"
            )
        if not self.version.is_compatible(self.schema_version):
            raise ValueError(
                f"MAJOR version mismatch: doctrine={self.version} vs schema={self.schema_version}"
            )
        return self

    @classmethod
    def from_dict(cls, document: dict[str, Any]) -> PolicyDoctrine:
        """Build a doctrine aggregate from the normative YAML document shape.

        The governance YAML nests metadata under a top-level ``doctrine`` key.
        This anti-corruption factory flattens that document into the aggregate
        field layout; type coercion and validation are handled by Pydantic.
        """
        if "doctrine" not in document:
            raise ValueError("Document must contain a top-level 'doctrine' metadata block")

        meta = document["doctrine"]
        payload: dict[str, Any] = {**meta}
        for key in cls._SECTION_KEYS:
            if key not in document:
                raise ValueError(f"Document missing required section '{key}'")
            payload[key] = document[key]
        return cls.model_validate(payload)
