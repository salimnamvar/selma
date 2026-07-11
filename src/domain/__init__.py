"""Policy Doctrine Domain Model.

Models governance-intent concerns of docs/Regulation/policy_doctrine.yaml.
"""

from __future__ import annotations

from domain.base import DomainValueObject
from domain.doctrine import PolicyDoctrine
from domain.enums import (
    ContentType,
    IdentityOperation,
    PriorityCategory,
    PriorityRank,
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
    "IdentityLifecycleIntent",
    "IdentityOperation",
    "IdentityResolution",
    "MachineId",
    "MachineIdSemantics",
    "PolicyDoctrine",
    "PriorityCategory",
    "PriorityHierarchy",
    "PriorityLevel",
    "PriorityRank",
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
