"""Policy Doctrine aggregate root."""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any, ClassVar, Self

from pydantic import Field, model_validator

from domain.base import DomainValueObject
from domain.enums import IdentityOperation, PriorityCategory, ProhibitedField
from domain.identifiers import GovernanceText, RuleContractId, SemanticVersion
from domain.value_objects.contamination_guard import ContaminationGuard
from domain.value_objects.cross_layer_binding import CrossLayerBinding
from domain.value_objects.document_section import DocumentSection, DocumentTemplate
from domain.value_objects.identity_resolution import IdentityResolution
from domain.value_objects.lifecycle_guidance import LifecycleGuidance
from domain.value_objects.priority_hierarchy import AuthorityHierarchy
from domain.value_objects.versioning_intent import VersioningIntent
from domain.value_objects.writing_principle import WritingPrinciple, WritingPrinciples


class DoctrineMetadata(DomainValueObject):
    """Identity and compatibility metadata for a policy doctrine document."""

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
        return self.version.is_compatible(spec_version) and self.version.is_compatible(schema_version)


class PolicyDoctrine(DomainValueObject):
    """Aggregate root for the complete governance doctrine."""

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

    metadata: DoctrineMetadata = Field(description="Doctrine identity and version matrix")
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

    @property
    def name(self) -> str:
        """Doctrine name."""
        return self.metadata.name

    @property
    def version(self) -> SemanticVersion:
        """Doctrine version."""
        return self.metadata.version

    @property
    def description(self) -> str:
        """Doctrine purpose statement."""
        return self.metadata.description

    @property
    def spec_version(self) -> SemanticVersion:
        """Compatible specification version."""
        return self.metadata.spec_version

    @property
    def schema_version(self) -> SemanticVersion:
        """Compatible rule schema version."""
        return self.metadata.schema_version

    @property
    def schema_id(self) -> RuleContractId:
        """Compatible rule schema identifier."""
        return self.metadata.schema_id

    @model_validator(mode="before")
    @classmethod
    def _from_yaml_document(cls, value: Any) -> Any:
        """Map normative YAML top-level keys onto aggregate fields."""
        if not isinstance(value, dict) or "metadata" in value:
            return value
        if "doctrine" not in value:
            raise ValueError("Document must contain a top-level 'doctrine' metadata block")
        for key in cls._SECTION_KEYS:
            if key not in value:
                raise ValueError(f"Document missing required section '{key}'")
        return {
            "metadata": value["doctrine"],
            **{key: value[key] for key in cls._SECTION_KEYS},
        }

    @model_validator(mode="after")
    def _validate_versions(self) -> Self:
        """Enforce MAJOR version compatibility across doctrine artifacts."""
        if not self.metadata.is_compatible_with(self.metadata.spec_version, self.metadata.schema_version):
            if not self.version.is_compatible(self.spec_version):
                raise ValueError(
                    f"MAJOR version mismatch: doctrine={self.version} vs spec={self.spec_version}"
                )
            raise ValueError(
                f"MAJOR version mismatch: doctrine={self.version} vs schema={self.schema_version}"
            )
        return self

    def is_compatible_with(
        self,
        spec_version: SemanticVersion,
        schema_version: SemanticVersion,
    ) -> bool:
        """Return True when this doctrine is MAJOR-compatible with both artifacts."""
        return self.metadata.is_compatible_with(spec_version, schema_version)

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

    @classmethod
    def from_dict(cls, document: dict[str, Any]) -> PolicyDoctrine:
        """Build a doctrine aggregate from the normative YAML document shape."""
        return cls.model_validate(document)
