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
from domain.doctrine import DoctrineMetadata, PolicyDoctrine
from domain.enums import (
    ContentType,
    IdentityOperation,
    PriorityCategory,
    ProhibitedField,
)
from domain.identifiers import (
    DomainText,
    FieldPath,
    GovernanceConstraint,
    GovernanceDescription,
    GovernanceGuidance,
    GovernancePurpose,
    GovernanceText,
    MachineId,
    RuleContractId,
    SectionId,
    SemanticVersion,
    WritingPrincipleId,
)
from domain.value_objects import (
    AuthorityHierarchy,
    ConflictResolutionBinding,
    ConflictResolutionIntent,
    ContaminationGuard,
    CrossLayerBinding,
    CrossLayerPrecedence,
    DocumentSection,
    DocumentStructure,
    DocumentTemplate,
    FieldLegality,
    IdentityResolution,
    LifecycleGuidance,
    LifecycleOperationGuidance,
    MachineIdSemantics,
    PriorityHierarchy,
    PriorityLevel,
    VersionComponentIntent,
    VersioningIntent,
    VersionIntent,
    VersionStrategy,
    WritingPrinciple,
    WritingPrinciples,
)

__all__ = [
    "AuthorityHierarchy",
    "ConflictResolutionBinding",
    "ConflictResolutionIntent",
    "ContaminationGuard",
    "ContentType",
    "CrossLayerBinding",
    "CrossLayerPrecedence",
    "DoctrineMetadata",
    "DocumentSection",
    "DocumentStructure",
    "DocumentTemplate",
    "DomainText",
    "DomainValueObject",
    "FieldLegality",
    "FieldPath",
    "GovernanceConstraint",
    "GovernanceDescription",
    "GovernanceGuidance",
    "GovernancePurpose",
    "GovernanceText",
    "Identifiable",
    "IdentifiedCollection",
    "IdentifiedItem",
    "IdentityOperation",
    "IdentityResolution",
    "IndexedLookupMixin",
    "LifecycleGuidance",
    "LifecycleOperationGuidance",
    "MachineId",
    "MachineIdSemantics",
    "Nameable",
    "NameableMixin",
    "PolicyDoctrine",
    "PriorityCategory",
    "PriorityHierarchy",
    "PriorityLevel",
    "ProhibitedField",
    "RuleContractId",
    "SectionId",
    "SemanticVersion",
    "StringCoercibleVO",
    "TreeNodeMixin",
    "VersionComponentIntent",
    "VersionIntent",
    "VersionStrategy",
    "VersioningIntent",
    "WritingPrinciple",
    "WritingPrincipleId",
    "WritingPrinciples",
    "none_as_empty",
    "require_unique",
]
