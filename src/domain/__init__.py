"""Policy doctrine domain model.

Models the governance-intent concerns of ``docs/Regulation/policy_doctrine.yaml``.
This layer is descriptive of human authoring constraints; it is not loaded at
runtime by the evaluation engine.
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
    DIRECTIVES_CHILD_IDS,
    MAX_SECTION_DEPTH,
    REQUIRED_SECTION_IDS,
    ConflictResolutionBinding,
    ContaminationGuard,
    CrossLayerBinding,
    CrossLayerPrecedence,
    DocumentSection,
    DocumentStructure,
    FieldLegality,
    IdentityLifecycleIntent,
    IdentityResolution,
    LifecycleOperationIntent,
    MachineIdSemantics,
    PriorityHierarchy,
    PriorityLevel,
    ProhibitedFieldSet,
    VersioningStrategy,
    VersionIntent,
    WritingPrinciple,
    WritingPrinciples,
)

__all__ = [
    "DIRECTIVES_CHILD_IDS",
    "MAX_SECTION_DEPTH",
    "REQUIRED_SECTION_IDS",
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
    "LifecycleOperationIntent",
    "MachineId",
    "MachineIdSemantics",
    "PolicyDoctrine",
    "PriorityCategory",
    "PriorityHierarchy",
    "PriorityLevel",
    "PriorityRank",
    "ProhibitedField",
    "ProhibitedFieldSet",
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
