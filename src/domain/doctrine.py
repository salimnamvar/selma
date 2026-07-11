"""Policy Doctrine Aggregate Root.

Complete governance doctrine for the policy authoring layer.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from pydantic import Field, model_validator

from domain.base import DomainValueObject
from domain.identifiers import RuleContractId, SemanticVersion
from domain.value_objects.contamination_guard import ContaminationGuard
from domain.value_objects.cross_layer_binding import CrossLayerBinding
from domain.value_objects.document_section import DocumentSection, DocumentStructure
from domain.value_objects.identity_lifecycle import IdentityLifecycleIntent
from domain.value_objects.identity_resolution import IdentityResolution, MachineIdSemantics
from domain.value_objects.priority_hierarchy import PriorityHierarchy, PriorityLevel
from domain.value_objects.versioning_strategy import VersioningStrategy
from domain.value_objects.writing_principle import WritingPrinciple, WritingPrinciples


class PolicyDoctrine(DomainValueObject):
    """Aggregate root representing the complete governance doctrine.

    Nested collections expose a uniform ``get`` API
    (``sections.get``, ``writing_principles.get``, ``priority_hierarchy.get``).
    Construction from the normative YAML document shape uses
    :meth:`model_validate` after :meth:`from_document` flattens the top-level
    ``doctrine`` metadata block.

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
        sections (DocumentStructure): Universal document section definitions.
    
    Standardized methods:
        - from_document(data) -> PolicyDoctrine: Factory from YAML document
        - from_dict(data) -> PolicyDoctrine: Create from dictionary
        - from_json(json_str) -> PolicyDoctrine: Create from JSON string
        - to_dict() -> dict: Convert to dictionary
        - to_json() -> str: Convert to JSON string
        - validate() -> PolicyDoctrine: Validate the model
        
    Standardized section access:
        - get_section(id) -> Optional[DocumentSection]: Find section by ID
        - find_section(id) -> DocumentSection: Find section by ID (raises)
        - get_writing_principle(id) -> Optional[WritingPrinciple]: Find principle by ID
        - find_writing_principle(id) -> WritingPrinciple: Find principle by ID (raises)
        - get_priority_level(category) -> Optional[PriorityLevel]: Find level by category
        - find_priority_level(category) -> PriorityLevel: Find level by category (raises)
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
    sections: DocumentStructure = Field(description="Universal document section definitions")

    @model_validator(mode="after")
    def check_version_compatibility(self) -> PolicyDoctrine:
        """Enforce MAJOR version compatibility across doctrine artifacts."""
        result: PolicyDoctrine = self
        if not self.version.is_compatible_with(self.spec_version):
            raise ValueError(f"MAJOR version mismatch: doctrine={self.version} vs spec={self.spec_version}")
        if not self.version.is_compatible_with(self.rule_contract_version):
            raise ValueError(
                f"MAJOR version mismatch: doctrine={self.version} vs rule_contract={self.rule_contract_version}"
            )
        return result

    @classmethod
    def from_document(cls, a_document: Dict[str, Any]) -> PolicyDoctrine:
        """Build a doctrine aggregate from a policy_doctrine document mapping.

        The normative YAML nests metadata under a top-level ``doctrine`` key.
        This factory flattens that shape into the flat field layout expected by
        the model; all type coercion and field validation is then handled by
        Pydantic ``model_validate``.

        Args:
            a_document: Parsed policy_doctrine YAML mapping.

        Returns:
            Validated PolicyDoctrine aggregate.

        Raises:
            ValueError: If the top-level ``doctrine`` metadata block is missing.
            ValidationError: If nested payload fails domain validation.
        """
        if "doctrine" not in a_document:
            raise ValueError("Document must contain a top-level 'doctrine' metadata block")

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

    # Standardized section access methods
    def get_section(self, a_section_id: str) -> Optional[DocumentSection]:
        """Find a section by ID in the entire document structure.

        Args:
            a_section_id: Section identifier to search for.

        Returns:
            Section with matching ID, or None if not found.
        """
        return self.sections.get_tree(a_section_id)

    def find_section(self, a_section_id: str) -> DocumentSection:
        """Find a section by ID in the entire document structure, raising if not found.

        Args:
            a_section_id: Section identifier to search for.

        Returns:
            Section with matching ID.

        Raises:
            KeyError: If the section ID is not found.
        """
        return self.sections.find_tree(a_section_id)

    # Standardized writing principle access methods
    def get_writing_principle(self, a_principle_id: str) -> Optional[WritingPrinciple]:
        """Find a writing principle by ID.

        Args:
            a_principle_id: Principle identifier to search for.

        Returns:
            Writing principle with matching ID, or None if not found.
        """
        return self.writing_principles.get(a_principle_id)

    def find_writing_principle(self, a_principle_id: str) -> WritingPrinciple:
        """Find a writing principle by ID, raising if not found.

        Args:
            a_principle_id: Principle identifier to search for.

        Returns:
            Writing principle with matching ID.

        Raises:
            KeyError: If the principle ID is not found.
        """
        return self.writing_principles.find(a_principle_id)

    # Standardized priority level access methods
    def get_priority_level(self, a_category: Any) -> Optional[PriorityLevel]:
        """Find a priority level by category.

        Args:
            a_category: Priority category to search for.

        Returns:
            Priority level with matching category, or None if not found.
        """
        return self.priority_hierarchy.get(a_category)

    def find_priority_level(self, a_category: Any) -> PriorityLevel:
        """Find a priority level by category, raising if not found.

        Args:
            a_category: Priority category to search for.

        Returns:
            Priority level with matching category.

        Raises:
            KeyError: If the category is not found.
        """
        return self.priority_hierarchy.find(a_category)

    # Standardized property access
    @property
    def section_ids(self) -> List[str]:
        """Return all section IDs in the document structure."""
        return list(self.sections.all_ids())

    @property
    def writing_principle_ids(self) -> List[str]:
        """Return all writing principle IDs."""
        return self.writing_principles.ids

    @property
    def priority_categories(self) -> List[Any]:
        """Return all priority categories."""
        return self.priority_hierarchy.category_ids

    # Standardized validation
    def validate(self) -> PolicyDoctrine:
        """Validate the doctrine aggregate.

        Returns:
            Self, for method chaining.
        """
        # Pydantic validation is automatic, but we can add custom logic here
        return self
