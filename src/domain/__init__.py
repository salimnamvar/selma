"""Policy Doctrine domain model.

Models governance-intent concerns of docs/Regulation/policy_doctrine.yaml.

Method naming convention:
    get / get_where / get_*   optional retrieval (T | None)
    require / require_*       mandatory retrieval or invariant (raises)
    has / is_*                boolean predicates
    iter_* / collect_*        multi-result walks / gathers
    from_*                    factories
    _validate_*               private validators
"""

from __future__ import annotations

from domain.base import (
    DomainValueObject,
    EnumGuidedVO,
    Identifiable,
    IndexedLookupMixin,
    Nameable,
    NameableMixin,
    StringCoercibleVO,
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
    IdentityResolution,
    LifecycleDefinition,
    MachineIdSemantics,
    PriorityHierarchy,
    PriorityLevel,
    VersionIntent,
    VersionStrategy,
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
    "EnumGuidedVO",
    "FieldLegality",
    "FieldPath",
    "GovernanceText",
    "Identifiable",
    "IdentifiedCollection",
    "IdentifiedItem",
    "IdentityOperation",
    "IdentityResolution",
    "IndexedLookupMixin",
    "LifecycleDefinition",
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
    "StringCoercibleVO",
    "TreeNodeMixin",
    "VersionIntent",
    "VersionStrategy",
    "WritingPrinciple",
    "WritingPrincipleId",
    "WritingPrinciples",
    "none_as_empty",
    "require_unique",
]
