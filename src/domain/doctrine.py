"""Policy Doctrine aggregate root."""

from __future__ import annotations

from collections.abc import Iterable
from typing import Self

from pydantic import BaseModel, Field, model_validator

from domain.base import VO_CONFIG
from domain.enums import IdentityOperation, PriorityCategory, ProhibitedField
from domain.identifiers import GovernanceText, RuleContractId, SemanticVersion, is_major_compatible
from domain.value_objects.contamination_guard import ContaminationGuard
from domain.value_objects.cross_layer_binding import CrossLayerBinding
from domain.value_objects.document_section import DocumentSection, DocumentTemplate
from domain.value_objects.identity_resolution import IdentityResolution
from domain.value_objects.lifecycle_guidance import LifecycleGuidance
from domain.value_objects.priority_hierarchy import AuthorityHierarchy
from domain.value_objects.versioning_intent import VersioningIntent
from domain.value_objects.writing_principle import WritingPrinciple, WritingPrinciples


class DoctrineMetadata(BaseModel):
    """Identity and compatibility metadata for a policy doctrine document."""

    model_config = VO_CONFIG

    name: str = Field(min_length=1, description="Unique doctrine identifier")
    version: SemanticVersion = Field(description="Doctrine version")
    description: GovernanceText = Field(description="Human-readable purpose statement")
    spec_version: SemanticVersion = Field(description="Compatible specification version")
    schema_version: SemanticVersion = Field(description="Compatible rule schema version")
    schema_id: RuleContractId = Field(description="Identifier of the compatible rule schema")

    def is_compatible_with(
        self,
        spec_version: SemanticVersion,
        schema_version: SemanticVersion,
    ) -> bool:
        """Return True when doctrine MAJOR matches both artifact versions."""
        return is_major_compatible(self.version, spec_version) and is_major_compatible(
            self.version, schema_version
        )


class PolicyDoctrine(BaseModel):
    """Aggregate root for the complete governance doctrine."""

    model_config = VO_CONFIG

    doctrine: DoctrineMetadata = Field(description="Doctrine identity and version matrix")
    cross_layer_binding: CrossLayerBinding = Field(description="Layer relationship constraints")
    identity_resolution: IdentityResolution = Field(description="Identity mapping policy")
    lifecycle_definition: LifecycleGuidance = Field(description="Lifecycle operation governance")
    contamination_guard: ContaminationGuard = Field(description="Policy-layer field constraints")
    writing_principles: WritingPrinciples = Field(description="Authoring principles")
    priority_hierarchy: AuthorityHierarchy = Field(
        description="Authority levels and conflict-resolution intent"
    )
    version_strategy: VersioningIntent = Field(description="Versioning intent")
    sections: DocumentTemplate = Field(description="Universal document section definitions")

    @model_validator(mode="after")
    def _validate_versions(self) -> Self:
        """Enforce MAJOR version compatibility across doctrine artifacts."""
        if not is_major_compatible(self.doctrine.version, self.doctrine.spec_version):
            raise ValueError(
                f"MAJOR version mismatch: doctrine={self.doctrine.version} "
                f"vs spec={self.doctrine.spec_version}"
            )
        if not is_major_compatible(self.doctrine.version, self.doctrine.schema_version):
            raise ValueError(
                f"MAJOR version mismatch: doctrine={self.doctrine.version} "
                f"vs schema={self.doctrine.schema_version}"
            )
        return self

    def is_compatible_with(
        self,
        spec_version: SemanticVersion,
        schema_version: SemanticVersion,
    ) -> bool:
        """Return True when this doctrine is MAJOR-compatible with both artifacts."""
        return self.doctrine.is_compatible_with(spec_version, schema_version)

    def is_policy_field_allowed(self, field: str | ProhibitedField) -> bool:
        """Return True when ``field`` may appear in policy-layer prose."""
        return self.contamination_guard.is_allowed(field)

    def validate_policy_fields(self, fields: Iterable[str | ProhibitedField]) -> None:
        """Raise when any field is prohibited in the policy layer."""
        self.contamination_guard.validate_fields(fields)

    def outranks(self, left: PriorityCategory, right: PriorityCategory) -> bool:
        """Return True when ``left`` has higher authority than ``right``."""
        return self.priority_hierarchy.outranks(left, right)

    def get_section(self, key: str) -> DocumentSection | None:
        """Return a document section by id (tree-wide), or None."""
        return self.sections.get(key)

    def require_section(self, key: str) -> DocumentSection:
        """Return a document section by id, or raise KeyError."""
        return self.sections.require(key)

    def get_principle(self, key: str) -> WritingPrinciple | None:
        """Return a writing principle by id, or None."""
        return self.writing_principles.get(key)

    def get_lifecycle_guidance(self, operation: IdentityOperation) -> str:
        """Return lifecycle guidance text for an identity operation."""
        return self.lifecycle_definition.get_guidance(operation)