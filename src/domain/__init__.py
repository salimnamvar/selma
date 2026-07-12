"""Policy Doctrine domain model.

YAML 1:1 field mapping, native tuples for collections, aggregate-root validation.
"""

from __future__ import annotations

from domain.policy_doctrine import PolicyDoctrine
from domain.value_objects import (
    ConflictResolutionBinding,
    ContaminationGuard,
    ContentType,
    CrossLayerBinding,
    CrossLayerPrecedence,
    FieldLegality,
    IdentityResolution,
    Intent,
    Level,
    LifecycleDefinition,
    MachineIdSemantics,
    PriorityCategory,
    PriorityHierarchy,
    ProhibitedField,
    Section,
    SemanticVersion,
    VersionStrategy,
    WritingPrinciple,
)

__all__ = [
    "ConflictResolutionBinding",
    "ContaminationGuard",
    "ContentType",
    "CrossLayerBinding",
    "CrossLayerPrecedence",
    "FieldLegality",
    "IdentityResolution",
    "Intent",
    "Level",
    "LifecycleDefinition",
    "MachineIdSemantics",
    "PolicyDoctrine",
    "PriorityCategory",
    "PriorityHierarchy",
    "ProhibitedField",
    "Section",
    "SemanticVersion",
    "VersionStrategy",
    "WritingPrinciple",
]
