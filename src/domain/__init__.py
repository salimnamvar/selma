"""Policy Doctrine Domain Model.

Models governance-intent concerns of docs/Regulation/policy_doctrine.yaml.

Conventions:
    - Value objects: model_validate / model_dump (Pydantic v2)
    - Collections: get(), find(), get_by(), find_by(), filter(), map()
    - Trees: traverse(), find(), find_by_id(), depth()
"""

from __future__ import annotations

from domain.base import (
    DomainValueObject,
    Identifiable,
    Nameable,
    NameableMixin,
    TreeNodeMixin,
    none_as_empty,
    require_unique,
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
    "Identifiable",
    "IdentifiedCollection",
    "IdentifiedItem",
    "IdentityLifecycleIntent",
    "IdentityOperation",
    "IdentityResolution",
    "MachineId",
    "MachineIdSemantics",
    "Nameable",
    "NameableMixin",
    "PolicyDoctrine",
    "PriorityCategory",
    "PriorityHierarchy",
    "PriorityLevel",
    "ProhibitedField",
    "ResolutionStrategy",
    "RuleContractId",
    "SectionId",
    "SemanticVersion",
    "TreeNodeMixin",
    "VersionIntent",
    "VersioningStrategy",
    "WritingPrinciple",
    "WritingPrincipleId",
    "WritingPrinciples",
    "none_as_empty",
    "require_unique",
]
