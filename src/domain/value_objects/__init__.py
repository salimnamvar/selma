"""Value objects for the policy doctrine domain model."""

from __future__ import annotations

from domain.base import DomainValueObject
from domain.value_objects.contamination_guard import ContaminationGuard, ProhibitedFieldSet
from domain.value_objects.cross_layer_binding import (
    ConflictResolutionBinding,
    CrossLayerBinding,
    FieldLegality,
)
from domain.value_objects.document_section import (
    DIRECTIVES_CHILD_IDS,
    MAX_SECTION_DEPTH,
    REQUIRED_SECTION_IDS,
    DocumentSection,
    DocumentStructure,
)
from domain.value_objects.identity_lifecycle import IdentityLifecycleIntent, LifecycleOperationIntent
from domain.value_objects.identity_resolution import IdentityResolution, MachineIdSemantics
from domain.value_objects.priority_hierarchy import (
    CrossLayerPrecedence,
    PriorityHierarchy,
    PriorityLevel,
)
from domain.value_objects.versioning_strategy import VersioningStrategy, VersionIntent
from domain.value_objects.writing_principle import WritingPrinciple, WritingPrinciples

__all__ = [
    "DIRECTIVES_CHILD_IDS",
    "MAX_SECTION_DEPTH",
    "REQUIRED_SECTION_IDS",
    "ConflictResolutionBinding",
    "ContaminationGuard",
    "CrossLayerBinding",
    "CrossLayerPrecedence",
    "DocumentSection",
    "DocumentStructure",
    "DomainValueObject",
    "FieldLegality",
    "IdentityLifecycleIntent",
    "IdentityResolution",
    "LifecycleOperationIntent",
    "MachineIdSemantics",
    "PriorityHierarchy",
    "PriorityLevel",
    "ProhibitedFieldSet",
    "VersionIntent",
    "VersioningStrategy",
    "WritingPrinciple",
    "WritingPrinciples",
]
