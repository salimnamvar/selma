"""Policy Doctrine domain model.

Minimal Pydantic v2 design: DomainValueObject config base, constrained string
aliases, packaging-backed SemanticVersion, and value objects with inlined
lookup/tree methods (no mixins, no type name aliases).
"""

from __future__ import annotations

from domain.base import DomainValueObject, none_as_empty, require_unique
from domain.doctrine import DoctrineMetadata, PolicyDoctrine
from domain.enums import ContentType, IdentityOperation, PriorityCategory, ProhibitedField
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
    AuthorityHierarchy,
    ConflictResolutionIntent,
    ContaminationGuard,
    CrossLayerBinding,
    CrossLayerPrecedence,
    DocumentSection,
    DocumentTemplate,
    FieldLegality,
    IdentityResolution,
    LifecycleGuidance,
    MachineIdSemantics,
    PriorityLevel,
    VersionComponentIntent,
    VersioningIntent,
    WritingPrinciple,
    WritingPrinciples,
)

__all__ = [
    "AuthorityHierarchy",
    "ConflictResolutionIntent",
    "ContaminationGuard",
    "ContentType",
    "CrossLayerBinding",
    "CrossLayerPrecedence",
    "DoctrineMetadata",
    "DocumentSection",
    "DocumentTemplate",
    "DomainValueObject",
    "FieldLegality",
    "FieldPath",
    "GovernanceText",
    "IdentityOperation",
    "IdentityResolution",
    "LifecycleGuidance",
    "MachineId",
    "MachineIdSemantics",
    "PolicyDoctrine",
    "PriorityCategory",
    "PriorityLevel",
    "ProhibitedField",
    "RuleContractId",
    "SectionId",
    "SemanticVersion",
    "VersionComponentIntent",
    "VersioningIntent",
    "WritingPrinciple",
    "WritingPrincipleId",
    "WritingPrinciples",
    "none_as_empty",
    "require_unique",
]
