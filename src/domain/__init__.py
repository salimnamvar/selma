"""Policy Doctrine domain model.

Idiomatic Pydantic v2: shared ``VO_CONFIG``, Annotated scalar aliases,
``RootModel`` collections with ``@computed_field`` indexes, and direct
``model_validate`` from YAML with 1:1 field-name mapping.
"""

from __future__ import annotations

from domain.base import VO_CONFIG, none_as_empty, require_unique
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
    field_path_collection,
    field_path_field,
    field_path_is_field,
    is_major_compatible,
    major_version,
    parse_semver,
    split_field_path,
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
    "DIRECTIVES_CHILD_IDS",
    "REQUIRED_SECTION_IDS",
    "VO_CONFIG",
    "AuthorityHierarchy",
    "ConflictResolutionIntent",
    "ContaminationGuard",
    "ContentType",
    "CrossLayerBinding",
    "CrossLayerPrecedence",
    "DoctrineMetadata",
    "DocumentSection",
    "DocumentTemplate",
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
    "field_path_collection",
    "field_path_field",
    "field_path_is_field",
    "is_major_compatible",
    "major_version",
    "none_as_empty",
    "parse_semver",
    "require_unique",
    "split_field_path",
]