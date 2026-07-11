"""Policy Doctrine Domain Model.

Models governance-intent concerns of docs/Regulation/policy_doctrine.yaml.

Standardized naming conventions:
    - Value Objects: from_dict(), from_json(), to_dict(), to_json(), validate()
    - Collections: get(), find(), get_all(), find_all(), has(), filter(), map()
    - Trees: traverse(), find(), find_by_id(), depth()
"""

from __future__ import annotations

from domain.base import (
    DomainValueObject,
    Identifiable,
    Nameable,
    NameableMixin,
    SerializableMixin,
    TreeNodeMixin,
    ensure_non_empty,
    none_as_empty,
    require_unique,
    validate_enum_coverage,
    validate_required_fields,
    validate_unique_field_values,
)
from domain.collections import IdentifiedCollection, IdentifiedItem
from domain.doctrine import PolicyDoctrine
from domain.enums import (
    ContentType,
    IdentityOperation,
    PriorityCategory,
    ProhibitedField,
    ResolutionStrategy,
)
from domain.identifiers import (
    FieldPath,
    GovernanceText,
    MachineId,
    RuleContractId,
    SectionId,
    SemanticVersion,
    WritingPrincipleId,
)
from domain.value_objects import (
    ConflictResolutionBinding,
    ContaminationGuard,
    CrossLayerBinding,
    CrossLayerPrecedence,
    DocumentSection,
    DocumentStructure,
    FieldLegality,
    IdentityLifecycleIntent,
    IdentityResolution,
    MachineIdSemantics,
    PriorityHierarchy,
    PriorityLevel,
    VersioningStrategy,
    VersionIntent,
    WritingPrinciple,
    WritingPrinciples,
)

__all__ = [
    "ConflictResolutionBinding",
    "ContaminationGuard",
    "ContentType",
    "CrossLayerBinding",
    "CrossLayerPrecedence",
    "DocumentSection",
    "DocumentStructure",
    "DomainValueObject",
    "FieldLegality",
    "FieldPath",
    "GovernanceText",
    "IdentifiedItem",
    "IdentityLifecycleIntent",
    "IdentityOperation",
    "IdentityResolution",
    "MachineId",
    "MachineIdSemantics",
    "PolicyDoctrine",
    "PriorityCategory",
    "PriorityHierarchy",
    "PriorityLevel",
    "ProhibitedField",
    "ResolutionStrategy",
    "RuleContractId",
    "SectionId",
    "SemanticVersion",
    "VersionIntent",
    "VersioningStrategy",
    "WritingPrinciple",
    "WritingPrincipleId",
    "WritingPrinciples",
]
