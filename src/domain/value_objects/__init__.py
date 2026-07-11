"""Policy doctrine value objects."""

from __future__ import annotations

from domain.value_objects.contamination_guard import ContaminationGuard
from domain.value_objects.cross_layer_binding import (
    ConflictResolutionBinding,
    ConflictResolutionIntent,
    CrossLayerBinding,
    FieldLegality,
)
from domain.value_objects.document_section import (
    DocumentSection,
    DocumentStructure,
    DocumentTemplate,
)
from domain.value_objects.identity_resolution import IdentityResolution, MachineIdSemantics
from domain.value_objects.lifecycle_guidance import LifecycleGuidance, LifecycleOperationGuidance
from domain.value_objects.priority_hierarchy import (
    AuthorityHierarchy,
    CrossLayerPrecedence,
    PriorityHierarchy,
    PriorityLevel,
)
from domain.value_objects.versioning_intent import (
    VersionComponentIntent,
    VersioningIntent,
    VersionIntent,
    VersionStrategy,
)
from domain.value_objects.writing_principle import WritingPrinciple, WritingPrinciples

__all__ = [
    "AuthorityHierarchy",
    "ConflictResolutionBinding",
    "ConflictResolutionIntent",
    "ContaminationGuard",
    "CrossLayerBinding",
    "CrossLayerPrecedence",
    "DocumentSection",
    "DocumentStructure",
    "DocumentTemplate",
    "FieldLegality",
    "IdentityResolution",
    "LifecycleGuidance",
    "LifecycleOperationGuidance",
    "MachineIdSemantics",
    "PriorityHierarchy",
    "PriorityLevel",
    "VersionComponentIntent",
    "VersionIntent",
    "VersionStrategy",
    "VersioningIntent",
    "WritingPrinciple",
    "WritingPrinciples",
]
