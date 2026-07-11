"""Policy Doctrine domain model.

Idiomatic Pydantic v2: frozen value objects, Annotated type aliases for scalars
and collections, exact YAML field-name mapping, and domain validation via
Field constraints and AfterValidator.
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
    is_major_compatible,
    major_version,
)
from domain.value_objects import (
    DIRECTIVES_CHILD_IDS,
    REQUIRED_SECTION_IDS,
    AuthorityHierarchy,
    ConflictResolutionIntent,
    ContaminationGuard,
    CrossLayerBinding,
    CrossLayerPrecedence,
    DocumentSection,
    DocumentSections,
    FieldLegality,
    IdentityResolution,
    LifecycleGuidance,
    MachineIdSemantics,
    PriorityLevel,
    VersionComponentIntent,
    VersioningIntent,
    WritingPrinciple,
    WritingPrinciples,
    find_principle,
    find_section,
)

__all__ = [
    "DIRECTIVES_CHILD_IDS",
    "REQUIRED_SECTION_IDS",
    "AuthorityHierarchy",
    "ConflictResolutionIntent",
    "ContaminationGuard",
    "ContentType",
    "CrossLayerBinding",
    "CrossLayerPrecedence",
    "DoctrineMetadata",
    "DocumentSection",
    "DocumentSections",
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
    "find_principle",
    "find_section",
    "is_major_compatible",
    "major_version",
    "none_as_empty",
    "require_unique",
]