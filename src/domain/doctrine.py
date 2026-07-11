"""Policy doctrine aggregate root."""

from __future__ import annotations

from functools import cached_property
from typing import Any

from pydantic import ConfigDict, Field, model_validator

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

    Owns governance metadata, identity policy, writing principles, priority
    hierarchy, document structure, and versioning strategy. Structural tree
    invariants live on :class:`DocumentStructure`; this root enforces only
    cross-cutting rules such as MAJOR version synchronization.
    """

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
        populate_by_name=True,
        ignored_types=(cached_property,),
    )

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

    @model_validator(mode="before")
    @classmethod
    def _normalize_collections(cls, data: Any) -> Any:
        """Accept bare lists for principles/sections as used in the YAML document."""
        if not isinstance(data, dict):
            return data
        raw: dict[str, Any] = dict(data)  # type: ignore[arg-type]
        normalized: dict[str, Any] = dict(raw)

        principles = normalized.get("writing_principles")
        if isinstance(principles, list):
            normalized["writing_principles"] = {"principles": principles}

        sections = normalized.get("sections")
        if isinstance(sections, list):
            normalized["sections"] = {"sections": sections}

        document_structure = normalized.get("document_structure")
        if isinstance(document_structure, list):
            normalized["document_structure"] = {"sections": document_structure}

        return normalized

    @model_validator(mode="after")
    def check_version_compatibility(self) -> PolicyDoctrine:
        """Enforce MAJOR version compatibility across doctrine, spec, and rule contract."""
        if not self.version.is_compatible_with(self.spec_version):
            msg = f"MAJOR version mismatch: doctrine={self.version} vs spec={self.spec_version}"
            raise ValueError(msg)
        if not self.version.is_compatible_with(self.rule_contract_version):
            msg = f"MAJOR version mismatch: doctrine={self.version} vs rule_contract={self.rule_contract_version}"
            raise ValueError(msg)
        return self

    # ── Convenience projections ──────────────────────────────────────────

    @property
    def sections(self) -> tuple[DocumentSection, ...]:
        """Top-level document sections (projection of document structure)."""
        return self.document_structure.sections

    @cached_property
    def _principle_index(self) -> dict[WritingPrincipleId, WritingPrinciple]:
        return {p.id: p for p in self.writing_principles.principles}

    def get_section(self, section_id: SectionId) -> DocumentSection | None:
        """Retrieve a document section by ID, searching the full tree."""
        return self.document_structure.get(section_id)

    def get_writing_principle(self, principle_id: WritingPrincipleId) -> WritingPrinciple | None:
        """Retrieve a writing principle by its identifier."""
        return self.writing_principles.get(principle_id)

    def get_priority_level(self, category: PriorityCategory) -> PriorityLevel | None:
        """Retrieve a priority level by its category."""
        return self.priority_hierarchy.get_level(category)

    @classmethod
    def from_document(cls, document: dict[str, Any]) -> PolicyDoctrine:
        """Build a doctrine aggregate from a full policy_doctrine document mapping.

        Expects the top-level shape of ``policy_doctrine.yaml``::

            doctrine: {name, version, ...}
            cross_layer_binding: {...}
            identity_resolution: {...}
            identity_lifecycle_intent: {...}
            contamination_guard: {...}
            writing_principles: [...]
            priority_hierarchy: {...}
            versioning_strategy: {...}
            sections: [...]
        """
        if "doctrine" not in document:
            msg = "Document must contain a top-level 'doctrine' metadata block"
            raise ValueError(msg)

        meta = document["doctrine"]
        payload: dict[str, Any] = {
            **meta,
            "cross_layer_binding": document["cross_layer_binding"],
            "identity_resolution": document["identity_resolution"],
            "identity_lifecycle_intent": document["identity_lifecycle_intent"],
            "contamination_guard": document["contamination_guard"],
            "writing_principles": document["writing_principles"],
            "priority_hierarchy": document["priority_hierarchy"],
            "versioning_strategy": document["versioning_strategy"],
            "sections": document["sections"],
        }
        return cls.model_validate(payload)
