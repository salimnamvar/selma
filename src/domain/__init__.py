"""Policy Doctrine domain model.

YAML 1:1 field mapping, native tuples for collections, aggregate-root validation.
"""

from __future__ import annotations

from domain.base import VO_CONFIG, require_unique
from domain.enums import ContentType, IdentityOperation, PriorityCategory, ProhibitedField
from domain.identifiers import (
    MachineId,
    SchemaId,
    SemanticVersion,
)
from domain.policy_doctrine import PolicyDoctrine
from domain.value_objects import (
    DIRECTIVES_CHILD_IDS,
    REQUIRED_SECTION_IDS,
    ConflictResolutionBinding,
    ContaminationGuard,
    CrossLayerBinding,
    CrossLayerPrecedence,
    FieldLegality,
    IdentityResolution,
    Intent,
    Level,
    LifecycleDefinition,
    MachineIdSemantics,
    PriorityHierarchy,
    Section,
    VersionStrategy,
    WritingPrinciple,
)

__all__ = [
    "DIRECTIVES_CHILD_IDS",
    "REQUIRED_SECTION_IDS",
    "VO_CONFIG",
    "ConflictResolutionBinding",
    "ContaminationGuard",
    "ContentType",
    "CrossLayerBinding",
    "CrossLayerPrecedence",
    "FieldLegality",
    "IdentityOperation",
    "IdentityResolution",
    "Intent",
    "Level",
    "LifecycleDefinition",
    "MachineId",
    "MachineIdSemantics",
    "PolicyDoctrine",
    "PriorityCategory",
    "PriorityHierarchy",
    "ProhibitedField",
    "SchemaId",
    "Section",
    "SemanticVersion",
    "VersionStrategy",
    "WritingPrinciple",
    "require_unique",
]