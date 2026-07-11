"""Policy Doctrine Value Objects.

Public value-object surface for the governance domain.

Standardized naming conventions:
    - Value Objects: from_dict(), from_json(), to_dict(), to_json(), validate()
    - Collections: get(), find(), get_all(), find_all(), has(), filter(), map()
    - Trees: traverse(), find(), find_by_id(), depth()
"""

from __future__ import annotations

from domain.base import DomainValueObject, SerializableMixin
from domain.value_objects.contamination_guard import ContaminationGuard
from domain.value_objects.cross_layer_binding import (
    ConflictResolutionBinding,
    CrossLayerBinding,
    FieldLegality,
)
from domain.value_objects.document_section import DocumentSection, DocumentStructure
from domain.value_objects.identity_lifecycle import IdentityLifecycleIntent
from domain.value_objects.identity_resolution import IdentityResolution, MachineIdSemantics
from domain.value_objects.priority_hierarchy import (
    CrossLayerPrecedence,
    PriorityHierarchy,
    PriorityLevel,
)
from domain.value_objects.versioning_strategy import VersioningStrategy, VersionIntent
from domain.value_objects.writing_principle import WritingPrinciple, WritingPrinciples

__all__ = [
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
    "MachineIdSemantics",
    "PriorityHierarchy",
    "PriorityLevel",
    "SerializableMixin",
    "VersionIntent",
    "VersioningStrategy",
    "WritingPrinciple",
    "WritingPrinciples",
]
